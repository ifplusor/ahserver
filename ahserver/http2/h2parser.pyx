# encoding=utf-8

import logging

from libc.errno cimport *
from .ahp cimport *
from .protocol import HttpMethod
from .request import HttpRequest

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

cdef enum parser_state:
    STATE_IDLE  # 初始状态
    STATE_WAIT_HEADER  # 等待 header 数据
    STATE_HAVE_HEADER  # 收到 header
    STATE_TOUCH_BODY  # 解析完 header 后，检查 buffer 中是否有完整的 body
    STATE_WAIT_BODY  # 等待 body 数据
    STATE_HAVE_BODY  # 收到 body
    STATE_HAVE_MESSAGE  # 收到 request
    STATE_BUSY  # 处理 request
    STATE_ERROR

cdef enum body_transfer_type:
    BODY_TRANSFER_LENGTH
    BODY_TRANSFER_CHUNKED

cdef class H2Parser:
    """Http parser

    ahparser 的 python 封装

    TODO: 支持 http 2.0 多路复用
    """

    cdef:
        parser_state _state
        ahp_msgbuf_t _buffer  # parser 只负责向缓冲区追加数据
        ahp_parser_t _parser
        body_transfer_type _transfer_type
        long _transfer_length
        object _request
        object _on_message  # 完整 http 报文解析完成回调

    def __cinit__(self):
        self._state = STATE_IDLE

        ahp_msgbuf_init(&self._buffer, -1)

        self._parser.data = <void*> self
        self._parser.on_request_line = __request_line_callback
        self._parser.on_request_line_cm = __request_line_cm_callback
        self._parser.on_message_header = __message_header_callback
        self._parser.on_message_body = __message_body_callback

    def __dealloc__(self):
        ahp_msgbuf_free(&self._buffer)

    def __init__(self, on_message):
        self._on_message = on_message  # 注入请求处理回调
        self._request = None

    def free(self):
        self._state = STATE_IDLE

    def feed(self, data: bytes, len: int):
        cdef:
            int err

        err = 0
        while 1:
            if self._state == STATE_IDLE:
                # 准备解析新请求

                ahp_msgbuf_reset(&self._buffer)
                ahp_parse_reset(&self._parser)
                self._request = HttpRequest()
                self._state = STATE_WAIT_HEADER

            if self._state == STATE_WAIT_HEADER:
                # 读取 request headers

                # buffer data
                ahp_msgbuf_append(&self._buffer, data, len)

                # parse http request message
                err = ahp_parse_request(&self._parser, &self._buffer)
                if err == 0:
                    # 报文头完整
                    self._state = STATE_HAVE_HEADER
                elif err == EAGAIN:
                    # 不能构成完整请求，等待更多数据
                    break
                else:
                    self._state = STATE_ERROR

            if self._state == STATE_HAVE_HEADER:
                # 获取到完整的 request header, 判断 request 是否存在 body

                # http 消息不能同时都包括内容长度(Content-Length)头域和非identity传输编码(Transfer-Encoding)
                if "Transfer-Encoding" in self._request.headers:
                    encoding = self._request.headers["Transfer-Encoding"]
                    if encoding == b"chunked":
                        # chunked
                        self._transfer_type = BODY_TRANSFER_CHUNKED
                        self._state = STATE_TOUCH_BODY
                    elif encoding == b"identity":
                        # identity
                        self._state = STATE_ERROR
                    else:
                        # others
                        self._state = STATE_ERROR

                elif "Content-Length" in self._request.headers:
                    length = self._request.headers["Content-Length"]
                    self._transfer_length = int(length)
                    self._transfer_type = BODY_TRANSFER_LENGTH
                    self._state = STATE_TOUCH_BODY

                else:
                    if self._request.method in http_method_need_body:
                        # FIXME: 服务器如果不能判断消息长度的话应该以 400 响应(错误的请求)，或者以 411 响应(要求长度)
                        self._state = STATE_ERROR
                    else:
                        self._state = STATE_HAVE_MESSAGE

            if self._state == STATE_TOUCH_BODY:
                # 检测 request body 类型

                if self._transfer_type == BODY_TRANSFER_LENGTH:
                    if self._transfer_length > 0:
                        err = ahp_parse_body_length(&self._parser, &self._buffer, self._transfer_length)
                elif self._transfer_type == BODY_TRANSFER_CHUNKED:
                    err = ahp_parse_body_chunked(&self._parser, &self._buffer)

                if err == 0:
                    self._state = STATE_HAVE_BODY
                elif err == EAGAIN:
                    self._state = STATE_WAIT_BODY
                    break
                else:
                    self._state = STATE_ERROR

            if self._state == STATE_WAIT_BODY:
                # 读取 request body

                # buffer data
                ahp_msgbuf_append(&self._buffer, data, len)

                err = ahp_parse_body(&self._parser, &self._buffer)
                if err == 0:
                    self._state = STATE_HAVE_BODY
                elif err == EAGAIN:
                    break
                else:
                    self._state = STATE_ERROR

            if self._state == STATE_HAVE_BODY:
                # 获取到完整的 request body

                self._state = STATE_HAVE_MESSAGE

            if self._state == STATE_HAVE_MESSAGE:
                # 获取到完整的 request

                self._state = STATE_BUSY
                self._on_message(self._request)
                break

            if self._state == STATE_BUSY:
                err = EBUSY
                self._state = STATE_ERROR

            if self._state == STATE_ERROR:
                # if err == EBADMSG:
                #     # 报文格式错误
                #     pass
                # elif err == EMSGSIZE:
                #     # 报文超长
                #     pass
                # else:
                #     # 其它错误
                #     pass

                logger.warning('encounter error when parser')
                self._state = STATE_IDLE

                return -1

            break

        return 0

    def feed_eof(self):
        # server 端不以 eof 作为 body 结束定位符
        return 1

    cdef int _on_request_line(self, ahp_method_t method, ahp_strlen_t *uri, ahp_version_t version):
        # TODO: 验证 uri

        self._request.method = http_method_table[method]
        self._request.uri = uri.str[:uri.len]
        self._request.version = http_version_table[version]

        return 0

    cdef int _on_request_line_cm(self, ahp_strlen_t *method, ahp_strlen_t *uri, ahp_version_t version):
        # print("CUSTOM METHOD!!!")

        self._request.method = method.str[:method.len]
        self._request.uri = uri.str[:uri.len]
        self._request.version = http_version_table[version]

        return 1

    cdef int _on_message_header(self, ahp_strlen_t *name, ahp_strlen_t *value):
        field_name = name.str[:name.len]
        field_name = field_name.decode(encoding='ascii')
        self._request.headers[field_name] = value.str[:value.len]
        return 0

    cdef int _on_message_body(self, ahp_strlen_t *body):
        self._request.body = body.str[:body.len]
        return 0

cdef int __request_line_callback(ahp_parser_t *parser, ahp_method_t method, ahp_strlen_t *uri, ahp_version_t version):
    cdef:
        H2Parser h2parser

    h2parser = <H2Parser> parser.data
    return h2parser._on_request_line(method, uri, version)

cdef int __request_line_cm_callback(ahp_parser_t *parser, ahp_strlen_t *method, ahp_strlen_t *uri,
                                    ahp_version_t version):
    cdef:
        H2Parser h2parser

    h2parser = <H2Parser> parser.data
    return h2parser._on_request_line_cm(method, uri, version)

cdef int __message_header_callback(ahp_parser_t *parser, ahp_strlen_t *name, ahp_strlen_t *value):
    cdef:
        H2Parser h2parser

    h2parser = <H2Parser> parser.data
    return h2parser._on_message_header(name, value)

cdef int __message_body_callback(ahp_parser_t *parser, ahp_strlen_t *body):
    cdef:
        H2Parser h2parser

    h2parser = <H2Parser> parser.data
    return h2parser._on_message_body(body)
