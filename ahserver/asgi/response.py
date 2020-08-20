# encoding=utf-8

__all__ = ["ASGIHttpResponse"]

from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime

from .. import __version__

from ..http2 import HttpRequest, HttpResponse
from ..http2.constant import LATIN1_ENCODING
from ..http2.protocol import HttpHeader, HttpStatus
from ..util.pipe import AsyncPipe

try:
    from typing import Dict
except Exception:
    pass

server_version = "AHServer {}".format(__version__)


def date_now():
    now = datetime.now()
    stamp = mktime(now.timetuple())
    return format_date_time(stamp)


class ASGIHttpResponse(HttpResponse):
    def __init__(self, request: HttpRequest, loop=None) -> None:
        super(ASGIHttpResponse, self).__init__(request)
        self.loop = loop
        self.headers_sent = False
        self.body_pipe = AsyncPipe()

    async def send(self, message):  # type: (Dict[str]) -> None
        if message["type"] == "http.response.body":
            await self._send_body(message)
        elif message["type"] == "http.response.start":
            self._send_start(message)
        else:
            raise Exception("Unknown message type")

    def _send_start(self, message):
        self.status = HttpStatus.parse(message["status"])
        for field_name, field_value in message["headers"]:
            try:
                field_name = HttpHeader.parse(field_name)
                field_value = field_value.decode(LATIN1_ENCODING)
                self.headers[field_name] = field_value
            except Exception:
                pass

    async def _send_body(self, message):
        await self.body_pipe.write(message["body"])
        if not message.get("more_body", False):
            await self.body_pipe.close()

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
        pipe = self.body_pipe
        async for body in pipe:
            if not body:  # don't send headers until body appears
                continue
            self.send_body(stream, body)
        if not self.headers_sent:  # send headers now if body was empty
            self.send_status_and_headers(stream)
