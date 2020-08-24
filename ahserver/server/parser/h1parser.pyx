# encoding=utf-8
# cython: language_level=3
# cython: embedsignature=True

import logging

from libc.errno cimport *

from ..protocol import HttpMethod, HttpVersion, HttpHeader
from .ahparser cimport *
from .buffer cimport Buffer

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

ctypedef parser_ctrl (*parser_state_proc)(H1Parser);

cdef enum body_transfer_type:
    BODY_TRANSFER_LENGTH
    BODY_TRANSFER_CHUNKED

cdef class H1Parser:
    """Http parser

    the python wrapper of ahparser
    """

    cdef:
        int _errno  # parser 调用错误码

        parser_state _state, _last_state
        parser_state_proc _state_proc[STATE_SIZE]  # 状态机处理器

        Buffer _buffer
        ahp_parser_t _parser

        object _create_request  # request工厂
        object _on_request  # http 报文头解析完成回调
        object _on_pri_request

        object _request

        body_transfer_type _transfer_type
        long _transfer_length

    def __dealloc__(self):
        pass

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

        # 注册 parser 回调
        self._parser.data = <void*> self
        self._parser.on_request_line = __request_line_callback
        self._parser.on_request_line_ext = __request_line_ext_callback
        self._parser.on_message_header = __message_header_callback
        self._parser.on_message_body = __message_body_callback
        ahp_parse_reset(&self._parser)

    def __init__(self, buffer, create_request, on_request, on_pri_request=None):
        self._buffer = buffer  # 注入msgbuf
        self._create_request = create_request  # 注入request工厂
        self._on_request = on_request  # 注入request处理回调
        self._on_pri_request = on_pri_request
        self._request = None

    cdef void _change_state(self, parser_state state):
        self._state, self._last_state = state, self._state

    def free(self):
        self._change_state(STATE_IDLE)

    def parse(self):
        """接收新数据"""
        cdef parser_ctrl ctrl

        # 执行状态机
        while 1:
            ctrl = self._state_proc[self._state](self)
            if ctrl == CTRL_PAUSE:
                break
            elif ctrl == CTRL_CONTINUE:
                continue
            else:
                return -1

        return 0

    cdef parser_ctrl _proc_idle(self):
        """准备解析新请求"""

        ahp_parse_reset(&self._parser)
        self._request = self._create_request()

        self._change_state(STATE_WAIT_HEADER)

        return CTRL_CONTINUE

    cdef parser_ctrl _proc_wait_header(self):
        """读取 request headers"""

        # parse http request message
        self._errno = ahp_parse_request(&self._parser, &self._buffer._buffer)
        if self._errno == 0:
            # 报文头完整
            self._change_state(STATE_HAVE_HEADER)
        elif self._errno == EAGAIN:
            # 不能构成完整请求，等待更多数据
            return CTRL_PAUSE
        else:
            self._change_state(STATE_ERROR)

        return CTRL_CONTINUE

    cdef parser_ctrl _proc_have_header(self):
        # 获取到完整的 request header, 判断 request 是否存在 body

        # If a message is received with both a Transfer-Encoding and a
        # Content-Length header field, the Transfer-Encoding overrides the
        # Content-Length.
        if HttpHeader.TRANSFER_ENCODING in self._request:
            encoding = self._request[HttpHeader.TRANSFER_ENCODING]
            if encoding[-7:] == b"chunked":
                # chunked
                self._transfer_type = BODY_TRANSFER_CHUNKED
                self._change_state(STATE_TOUCH_BODY)
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

        if self._state == STATE_HAVE_MESSAGE or self._state == STATE_TOUCH_BODY:
            self._on_request(self._request)

        return CTRL_CONTINUE

    cdef parser_ctrl _proc_touch_body(self):
        # 检测 request body 类型

        if self._transfer_type == BODY_TRANSFER_LENGTH:
            if self._transfer_length > 0:
                self._errno = ahp_parse_body_length(&self._parser, &self._buffer._buffer, self._transfer_length)
        elif self._transfer_type == BODY_TRANSFER_CHUNKED:
            self._errno = ahp_parse_body_chunked(&self._parser, &self._buffer._buffer)

        if self._errno == 0:
            self._change_state(STATE_HAVE_BODY)
        elif self._errno == EAGAIN:
            self._change_state(STATE_WAIT_BODY)
            return CTRL_PAUSE
        else:
            self._change_state(STATE_ERROR)

        return CTRL_CONTINUE

    cdef parser_ctrl _proc_wait_body(self):
        # 读取 request body

        self._errno = ahp_parse_body(&self._parser, &self._buffer._buffer)
        if self._errno == 0:
            self._change_state(STATE_HAVE_BODY)
        elif self._errno == EAGAIN:
            return CTRL_PAUSE
        else:
            self._change_state(STATE_ERROR)

        return CTRL_CONTINUE

    cdef parser_ctrl _proc_have_body(self):
        # 获取到完整的 request body

        self._change_state(STATE_HAVE_MESSAGE)

        return CTRL_CONTINUE

    cdef parser_ctrl _proc_have_message(self):
        # 获取到完整的 request

        self._change_state(STATE_BUSY)
        self._request.body.eof_received()
        # self._on_request(self._request)

        return CTRL_PAUSE

    cdef parser_ctrl _proc_touch_pri_body(self):
        self._errno = ahp_parse_body_length(&self._parser, &self._buffer._buffer, 6)
        if self._errno == 0:
            self._change_state(STATE_HAVE_PRI_MESSAGE)
        elif self._errno == EAGAIN:
            self._change_state(STATE_WAIT_PRI_BODY)
            return CTRL_PAUSE
        else:
            self._change_state(STATE_ERROR)

        return CTRL_CONTINUE

    cdef parser_ctrl _proc_wait_pri_body(self):

        self._errno = ahp_parse_body(&self._parser, &self._buffer._buffer)
        if self._errno == 0:
            self._change_state(STATE_HAVE_PRI_MESSAGE)
        elif self._errno == EAGAIN:
            return CTRL_PAUSE
        else:
            self._change_state(STATE_ERROR)

        return CTRL_CONTINUE

    cdef parser_ctrl _proc_have_pri_message(self):

        self._change_state(STATE_BUSY)
        if self._request.body.getvalue() == b"SM\r\n\r\n":
            self._on_pri_request(self._request)
            return CTRL_PAUSE
        else:
            self._change_state(STATE_ERROR)

        return CTRL_CONTINUE

    cdef parser_ctrl _proc_busy(self):
        self._errno = EBUSY
        self._change_state(STATE_ERROR)

        return CTRL_CONTINUE

    cdef parser_ctrl _proc_error(self):
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
        except Exception:
            return -1

        self._request.uri = uri.str[:uri.len]
        self._request.version = http_version_table[version]

        # http 2.0 连接前言:
        #   PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n
        if self._request.method == HttpMethod.PRI and self._request.uri == b"*" and \
                self._request.version == HttpVersion.V20 and self._on_pri_request is not None:
            return 0

        return -1

    cdef int _on_message_header(self, ahp_strlen_t *name, ahp_strlen_t *value):
        field_name = name.str[:name.len]
        self._request[field_name] = value.str[:value.len]
        return 0

    cdef int _on_message_body(self, ahp_strlen_t *body):
        try:
            self._request.body.write(body.str[:body.len])
            return 0
        except Exception:
            return -1


cdef int __request_line_callback(ahp_parser_t *parser, ahp_method_t method, ahp_strlen_t *uri, ahp_version_t version):
    cdef H1Parser obj = <H1Parser> parser.data
    return obj._on_request_line(method, uri, version)


cdef int __request_line_ext_callback(ahp_parser_t *parser, ahp_strlen_t *method, ahp_strlen_t *uri, ahp_version_t version):
    cdef H1Parser obj = <H1Parser> parser.data
    return obj._on_request_line_ext(method, uri, version)


cdef int __message_header_callback(ahp_parser_t *parser, ahp_strlen_t *name, ahp_strlen_t *value):
    cdef H1Parser obj = <H1Parser> parser.data
    return obj._on_message_header(name, value)


cdef int __message_body_callback(ahp_parser_t *parser, ahp_strlen_t *body):
    cdef H1Parser obj = <H1Parser> parser.data
    return obj._on_message_body(body)
