# encoding=utf-8

__all__ = ["WSGIHttpResponse"]

from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime

from .. import __version__

from ..http2 import HttpRequest, HttpResponse
from ..http2.protocol import HttpHeader
from ..util.iterator import AsyncIteratorWrapper

server_version = "AHServer {}".format(__version__)


def date_now():
    now = datetime.now()
    stamp = mktime(now.timetuple())
    return format_date_time(stamp)


class WSGIHttpResponse(HttpResponse):
    def __init__(self, request: HttpRequest, loop=None, executor=None) -> None:
        super(WSGIHttpResponse, self).__init__(request)
        self.loop = loop
        self.executor = executor
        self.headers_sent = False
        self.result = None

    def start_response(self, status, response_headers, exc_info=None):
        global server_version

        if exc_info:
            try:
                if self.headers_sent:
                    # 如果报头已发送，则重新抛出原始的异常。
                    exc_info[1].with_traceback(exc_info[2])
            finally:
                exc_info = None  # 避免死循环。
        elif self.headers:
            raise AssertionError("Headers already set!")

        self.status = status
        self.headers.clear()
        # FIXME: Set-Cookie
        self.headers.update(response_headers)

    def set_result(self, result):
        self.result = result

    def normalize_headers(self):
        if HttpHeader.DATE not in self.headers:
            self.headers[HttpHeader.DATE] = date_now()
        if HttpHeader.SERVER not in self.headers:
            self.headers[HttpHeader.SERVER] = server_version

    def send_status_and_headers(self, stream):
        self.normalize_headers()

        stream.send_data(self.render_status_line())
        stream.send_data(self.render_headers())
        stream.send_data(b"\r\n")

    def send_body(self, stream, body):
        if not self.headers_sent:
            self.headers_sent = True
            self.send_status_and_headers(stream)

        stream.send_data(body)

    async def respond(self, stream):
        result = self.result
        try:
            async for body in AsyncIteratorWrapper(result, loop=self.loop, executor=self.executor):
                if not body:  # don't send headers until body appears
                    continue
                self.send_body(stream, body)
            if not self.headers_sent:  # send headers now if body was empty
                self.send_status_and_headers(stream)
        finally:
            if hasattr(result, "close"):
                result.close()
