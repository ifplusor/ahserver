# encoding=utf-8
# cython: language_level=3
# cython: embedsignature=True

import logging

from libc.errno cimport *
from cpython.ref cimport Py_INCREF, Py_DECREF

from typing import Callable

from .ahparser cimport *
from .constant import LATIN1_ENCODING
from .frame import HttpFrame, HttpDataFrame, HttpHeadersFrame, HttpSettingsFrame
from .protocol import HttpMethod, HttpVersion, HttpHeader

logger = logging.getLogger()

http_method_table = [
    "OPTIONS", "GET", "HEAD", "POST", "PUT", "DELETE", "TRACE", "CONNECT"
]

http_version_table = [
    "1.0", "1.1", "2.0"
]

http_method_need_body = {
    HttpMethod.POST, HttpMethod.PUT
}

cdef enum:
    STATE_IDLE = 0  # 初始状态

    STATE_WAIT_HEADER  # 等待 header 数据
    STATE_HAVE_HEADER  # 收到 header

    STATE_TOUCH_BODY  # 解析完 header 后，检查 buffer 中是否有完整的 body
    STATE_WAIT_BODY  # 等待 body 数据
    STATE_HAVE_BODY  # 收到 body
    STATE_HAVE_MESSAGE  # 收到 request

    # Preface message
    STATE_TOUCH_PRI_BODY
    STATE_WAIT_PRI_BODY
    STATE_HAVE_PRI_MESSAGE

    STATE_BUSY  # 正在处理 request
    STATE_ERROR

    STATE_SIZE

ctypedef int parser_state

cdef enum parser_ctrl:
    CTRL_CONTINUE
    CTRL_PAUSE
    CTRL_ERROR

ctypedef parser_ctrl (*parser_state_proc)(H2Parser, bytes, int);

cdef enum body_transfer_type:
    BODY_TRANSFER_LENGTH
    BODY_TRANSFER_CHUNKED

cdef class H2Parser:
    """Http parser

    the python wrapper of ahparser
    """

    cdef:
        int _errno  # parser 调用错误码

        parser_state _state, _last_state
        parser_state_proc _state_proc[STATE_SIZE]  # 状态机处理器

        ahp_msgbuf_t _buffer  # parser 只负责向缓冲区追加数据
        ahp_parser_t _parser

        body_transfer_type _transfer_type
        long _transfer_length

        object _request

        object _create_request  # 请求工厂
        object _on_message  # 完整 http 报文解析完成回调
        object _on_pri_message

    def __dealloc__(self):
        ahp_msgbuf_free(&self._buffer)

    def __cinit__(self):
        # 初始化状态机
        self._state = self._last_state = STATE_IDLE
        self._state_proc[STATE_IDLE] = self._proc_idle
        self._state_proc[STATE_WAIT_HEADER] = self._proc_wait_header
        self._state_proc[STATE_HAVE_HEADER] = self._proc_have_header
        self._state_proc[STATE_TOUCH_BODY] = self._proc_touch_body
        self._state_proc[STATE_WAIT_BODY] = self._proc_wait_body
        self._state_proc[STATE_HAVE_BODY] = self._proc_have_body
        self._state_proc[STATE_HAVE_MESSAGE] = self._proc_have_message
        self._state_proc[STATE_TOUCH_PRI_BODY] = self._proc_touch_pri_body
        self._state_proc[STATE_WAIT_PRI_BODY] = self._proc_wait_pri_body
        self._state_proc[STATE_HAVE_PRI_MESSAGE] = self._proc_have_pri_message
        self._state_proc[STATE_BUSY] = self._proc_busy
        self._state_proc[STATE_ERROR] = self._proc_error

        # 初始化 msgbuf
        self._errno = ahp_msgbuf_init(&self._buffer, -1)
        if self._errno != 0:
            raise Exception("Failed to init msgbuf. errno:{}".format(self._errno))

        # 注册 parser 回调
        self._parser.data = <void*> self
        self._parser.on_request_line = __request_line_callback
        self._parser.on_request_line_ext = __request_line_ext_callback
        self._parser.on_message_header = __message_header_callback
        self._parser.on_message_body = __message_body_callback

    def __init__(self, create_request, on_message, on_pri_message=None):
        self._create_request = create_request  # 注入请求工厂
        self._on_message = on_message  # 注入请求处理回调
        self._on_pri_message = on_pri_message
        self._request = None

    cdef void _change_state(self, parser_state state):
        self._state, self._last_state = state, self._state

    def free(self):
        self._change_state(STATE_IDLE)

    def feed(self, data: bytes, size: int):
        """接收新数据"""
        cdef parser_ctrl ctrl
        # 执行状态机
        while 1:
            ctrl = self._state_proc[self._state](self, data, size)
            if ctrl == CTRL_PAUSE:
                break
            elif ctrl == CTRL_CONTINUE:
                continue
            else:
                return -1

        return 0

    def feed_eof(self):
        # server 端不以 eof 作为 body 结束定位符
        return 1

    def take_buffer(self):
        data = ahp_msgbuf_data(&self._buffer)[:ahp_msgbuf_length(&self._buffer)]
        ahp_msgbuf_reset(&self._buffer)
        return data

    cdef parser_ctrl _proc_idle(self, bytes data, int size):
        """准备解析新请求"""

        ahp_msgbuf_reset(&self._buffer)
        ahp_parse_reset(&self._parser)
        self._request = self._create_request()

        self._change_state(STATE_WAIT_HEADER)

        return CTRL_CONTINUE

    cdef parser_ctrl _proc_wait_header(self, bytes data, int size):
        """读取 request headers"""

        # buffer data
        self._errno = ahp_msgbuf_append(&self._buffer, data, size)
        if self._errno != 0:
            self._change_state(STATE_ERROR)
            return CTRL_CONTINUE

        # parse http request message
        self._errno = ahp_parse_request(&self._parser, &self._buffer)
        if self._errno == 0:
            # 报文头完整
            self._change_state(STATE_HAVE_HEADER)
        elif self._errno == EAGAIN:
            # 不能构成完整请求，等待更多数据
            return CTRL_PAUSE
        else:
            self._change_state(STATE_ERROR)

        return CTRL_CONTINUE

    cdef parser_ctrl _proc_have_header(self, bytes data, int size):
        # 获取到完整的 request header, 判断 request 是否存在 body

        # http 消息不能同时都包括内容长度(Content-Length)头域和非identity传输编码(Transfer-Encoding)
        if HttpHeader.TRANSFER_ENCODING in self._request:
            encoding = self._request[HttpHeader.TRANSFER_ENCODING]
            if encoding == b"chunked":
                # chunked
                self._transfer_type = BODY_TRANSFER_CHUNKED
                self._change_state(STATE_TOUCH_BODY)
            elif encoding == b"identity":
                # identity
                self._change_state(STATE_ERROR)
            else:
                # others
                self._change_state(STATE_ERROR)

        elif HttpHeader.CONTENT_LENGTH in self._request:
            length = self._request[HttpHeader.CONTENT_LENGTH]
            self._transfer_length = int(length)
            self._transfer_type = BODY_TRANSFER_LENGTH
            self._change_state(STATE_TOUCH_BODY)

        else:
            if self._request.method in http_method_need_body:
                # FIXME: 服务器如果不能判断消息长度的话应该以 400 响应(错误的请求)，或者以 411 响应(要求长度)
                self._change_state(STATE_ERROR)
            elif self._request.method == HttpMethod.PRI:
                self._change_state(STATE_TOUCH_PRI_BODY)
            else:
                self._change_state(STATE_HAVE_MESSAGE)

        if self._state != STATE_ERROR:
            self._on_message(self._request)

        return CTRL_CONTINUE

    cdef parser_ctrl _proc_touch_body(self, bytes data, int size):
        # 检测 request body 类型

        if self._transfer_type == BODY_TRANSFER_LENGTH:
            if self._transfer_length > 0:
                self._errno = ahp_parse_body_length(&self._parser, &self._buffer, self._transfer_length)
        elif self._transfer_type == BODY_TRANSFER_CHUNKED:
            self._errno = ahp_parse_body_chunked(&self._parser, &self._buffer)

        if self._errno == 0:
            self._change_state(STATE_HAVE_BODY)
        elif self._errno == EAGAIN:
            self._change_state(STATE_WAIT_BODY)
            return CTRL_PAUSE
        else:
            self._change_state(STATE_ERROR)

        return CTRL_CONTINUE

    cdef parser_ctrl _proc_wait_body(self, bytes data, int size):
        # 读取 request body

        # buffer data
        ahp_msgbuf_append(&self._buffer, data, size)

        self._errno = ahp_parse_body(&self._parser, &self._buffer)
        if self._errno == 0:
            self._change_state(STATE_HAVE_BODY)
        elif self._errno == EAGAIN:
            return CTRL_PAUSE
        else:
            self._change_state(STATE_ERROR)

        return CTRL_CONTINUE

    cdef parser_ctrl _proc_have_body(self, bytes data, int size):
        # 获取到完整的 request body

        self._change_state(STATE_HAVE_MESSAGE)

        return CTRL_CONTINUE

    cdef parser_ctrl _proc_have_message(self, bytes data, int size):
        # 获取到完整的 request

        self._change_state(STATE_BUSY)
        self._request.body.eof_received()
        # self._on_message(self._request)

        return CTRL_PAUSE

    cdef parser_ctrl _proc_touch_pri_body(self, bytes data, int size):
        self._errno = ahp_parse_body_length(&self._parser, &self._buffer, 6)
        if self._errno == 0:
            self._change_state(STATE_HAVE_PRI_MESSAGE)
        elif self._errno == EAGAIN:
            self._change_state(STATE_WAIT_PRI_BODY)
            return CTRL_PAUSE
        else:
            self._change_state(STATE_ERROR)

        return CTRL_CONTINUE

    cdef parser_ctrl _proc_wait_pri_body(self, bytes data, int size):
        ahp_msgbuf_append(&self._buffer, data, size)

        self._errno = ahp_parse_body(&self._parser, &self._buffer)
        if self._errno == 0:
            self._change_state(STATE_HAVE_PRI_MESSAGE)
        elif self._errno == EAGAIN:
            return CTRL_PAUSE
        else:
            self._change_state(STATE_ERROR)

        return CTRL_CONTINUE

    cdef parser_ctrl _proc_have_pri_message(self, bytes data, int size):

        self._change_state(STATE_BUSY)
        if self._request.body == b"SM\r\n\r\n":
            self._on_pri_message(self._request)
            return CTRL_ERROR
        else:
            self._change_state(STATE_ERROR)

        return CTRL_CONTINUE

    cdef parser_ctrl _proc_busy(self, bytes data, int size):
        self._errno = EBUSY
        self._change_state(STATE_ERROR)

        return CTRL_CONTINUE

    cdef parser_ctrl _proc_error(self, bytes data, int size):
        # if self._errno == EBADMSG:
        #     # 报文格式错误
        #     pass
        # elif self._errno == EMSGSIZE:
        #     # 报文超长
        #     pass
        # else:
        #     # 其它错误
        #     pass

        logger.warning('encounter error when parser on state:%d, errno:%d', self._last_state, self._errno)

        return CTRL_ERROR

    cdef int _on_request_line(self, ahp_method_t method, ahp_strlen_t *uri, ahp_version_t version):
        # TODO: 验证 uri

        self._request.method = http_method_table[method]
        self._request.uri = uri.str[:uri.len]
        self._request.version = http_version_table[version]

        return 0

    cdef int _on_request_line_ext(self, ahp_strlen_t *method, ahp_strlen_t *uri, ahp_version_t version):
        # CUSTOM METHOD!!!

        try:
            self._request.method = method.str[:method.len]
        except:
            return 0

        self._request.uri = uri.str[:uri.len]
        self._request.version = http_version_table[version]

        # http 2.0 连接前言:
        #   PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n
        if self._request.method == HttpMethod.PRI and self._request.uri == b"*" and \
                self._request.version == HttpVersion.V20 and self._on_pri_message is not None:
            _ahp_request_header_will_end(&self._parser)
            return 0

        return 1

    cdef int _on_message_header(self, ahp_strlen_t *name, ahp_strlen_t *value):
        field_name = name.str[:name.len]
        field_name = field_name.decode(encoding=LATIN1_ENCODING)
        self._request[field_name] = value.str[:value.len]
        return 0

    cdef int _on_message_body(self, ahp_strlen_t *body):
        try:
            self._request.body.write(body.str[:body.len])
            return 0
        except Exception:
            return 1

cdef int __request_line_callback(ahp_parser_t *parser, ahp_method_t method, ahp_strlen_t *uri, ahp_version_t version):
    cdef H2Parser h2parser = <H2Parser> parser.data
    return h2parser._on_request_line(method, uri, version)

cdef int __request_line_ext_callback(ahp_parser_t *parser, ahp_strlen_t *method, ahp_strlen_t *uri, ahp_version_t version):
    cdef H2Parser h2parser = <H2Parser> parser.data
    return h2parser._on_request_line_ext(method, uri, version)

cdef int __message_header_callback(ahp_parser_t *parser, ahp_strlen_t *name, ahp_strlen_t *value):
    cdef H2Parser h2parser = <H2Parser> parser.data
    return h2parser._on_message_header(name, value)

cdef int __message_body_callback(ahp_parser_t *parser, ahp_strlen_t *body):
    cdef H2Parser h2parser = <H2Parser> parser.data
    return h2parser._on_message_body(body)


cdef class H2Splitter:
    cdef:
        int _errno  # splitter 调用错误码

        ahp_msgbuf_t _buffer
        ahp_splitter_t _splitter

        object _on_frame  # 完整 http frame 解析完成回调

    def __cinit__(self):

        # 初始化 msgbuf
        self._errno = ahp_msgbuf_init(&self._buffer, -1)
        if self._errno != 0:
            raise Exception("Failed to init msgbuf. errno:{}".format(self._errno))

        # 注册 splitter 回调
        self._splitter.data = <void*> self
        self._splitter.alloc_frame = __alloc_frame_delegate
        self._splitter.free_frame = __free_frame_delegate
        self._splitter.on_frame_received = __frame_received_callback
        self._splitter.on_data_frame = __data_frame_callback
        self._splitter.on_settings_frame = __settings_frame_callback

    def __dealloc__(self):
        ahp_msgbuf_free(&self._buffer)

    def __init__(self, on_frame: Callable[[HttpFrame], int]):
        self._on_frame = on_frame  # 注入 frame 处理回调

    def feed(self, data: bytes, size: int):
        # NOTE: 数据拷贝(data)
        self._errno = ahp_msgbuf_append(&self._buffer, data, size)
        if self._errno != 0:
            return -1

        self._errno = ahp_split_frame(&self._splitter, &self._buffer)
        if self._errno == EAGAIN:
            return 0
        else:
            return -1

    cdef void* _alloc_frame(self, uint8_t type, uint8_t flags, uint32_t identifier, ahp_strlen_t *payload):
        frame: HttpFrame = HttpFrame.create_frame(type, flags, identifier)
        if frame is None:
            return NULL
        # 将frame传递到c库中, 加引用
        Py_INCREF(frame)
        return <void*>frame

    cdef void _free_frame(self, void *frame_ptr):
        frame: HttpFrame = <object> frame_ptr
        # c库释放frame, 减引用
        Py_INCREF(frame)

    cdef int _on_frame_received(self, void *frame_ptr):
        frame: HttpFrame = <object> frame_ptr
        return self._on_frame(frame)

    cdef int _on_data_frame(self, void *frame_ptr, ahp_strlen_t *data):
        frame: HttpDataFrame = <object> frame_ptr
        # NOTE: 数据拷贝(payload)
        frame.data = data.str[:data.len]
        return 0

    cdef int _on_headers_frame(self, void *frame_ptr, ahp_strlen_t *header_block_fragment):
        frame: HttpHeadersFrame = <object> frame_ptr
        # NOTE: 数据拷贝(payload)
        frame.header_block_fragment = header_block_fragment.str[:header_block_fragment.len]
        return 0

    cdef int _on_settings_frame(self, void *frame_ptr, uint16_t identifier, uint32_t value):
        frame: HttpSettingsFrame = <object> frame_ptr
        frame.settings[identifier] = value
        return 0


cdef void* __alloc_frame_delegate(ahp_splitter_t *splitter, uint8_t type, uint8_t flags, uint32_t identifier, ahp_strlen_t *payload):
    cdef H2Splitter h2splitter = <H2Splitter> splitter.data
    return h2splitter._alloc_frame(type, flags, identifier, payload)

cdef void __free_frame_delegate(ahp_splitter_t *splitter, void *frame):
    cdef H2Splitter h2splitter = <H2Splitter> splitter.data
    h2splitter._free_frame(frame)

cdef int __frame_received_callback(ahp_splitter_t *splitter, void *frame):
    cdef H2Splitter h2splitter = <H2Splitter> splitter.data
    return h2splitter._on_frame_received(frame)

cdef int __data_frame_callback(ahp_splitter_t *splitter, void *frame, ahp_strlen_t *data):
    cdef H2Splitter h2splitter = <H2Splitter> splitter.data
    return h2splitter._on_data_frame(frame, data)

cdef int __headers_frame_callback(ahp_splitter_t *splitter, void *frame, ahp_strlen_t *header_block_fragment):
    cdef H2Splitter h2splitter = <H2Splitter> splitter.data
    return h2splitter._on_headers_frame(frame, header_block_fragment)

cdef int __settings_frame_callback(ahp_splitter_t *splitter, void *frame, uint16_t identifier, uint32_t value):
    cdef H2Splitter h2splitter = <H2Splitter> splitter.data
    return h2splitter._on_settings_frame(frame, identifier, value)
