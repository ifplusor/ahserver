# encoding=utf-8

__all__ = ["ASGIHttpResponse"]

from ..http2.constant import LATIN1_ENCODING
from ..http2.protocol import HttpHeader, HttpStatus
from ..http2.response import SGIHttpResponse
from ..util.pipe import AsyncPipe

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from typing import AsyncIterator, Dict
    from ..http2 import HttpRequest


class ASGIHttpResponse(SGIHttpResponse):
    def __init__(self, request, loop=None):  # type: (HttpRequest, AbstractEventLoop) -> None
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

    def body_iterator(self):  # type: () -> AsyncIterator[bytes]
        return self.body_pipe
