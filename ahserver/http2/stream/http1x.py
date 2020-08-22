# encoding: utf-8

__all__ = ["Http1xStream"]

import logging

from asyncio import Task, CancelledError

from . import HttpStream
from ..h2parser import H2Parser
from ..protocol import HttpVersion, HttpStatus, HttpHeader, PopularHeaders
from ..response import HttpResponse

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Callable, Optional
    from ahserver.protocol.http2 import Http2Protocol
    from ..request import HttpRequest


logger = logging.getLogger()


class Http1xStream(HttpStream):
    def __init__(self, protocol, request_factory, enable_upgrade2=False):
        # type: (Http2Protocol, Callable[..., HttpRequest], bool) -> None
        super(Http1xStream, self).__init__(protocol)

        self.enable_upgrade2 = enable_upgrade2
        self.parser = H2Parser(request_factory, self.on_message, self.protocol.on_http2_preface)

    def data_received(self, data):  # type: (bytes) -> int
        # 递送给 parser 解协议
        return self.parser.feed(data, len(data))

    def eof_received(self):
        # 递送给 parser 解协议
        if self.parser.feed_eof():
            self.protocol.close()

    def on_message(self, request):  # type: (HttpRequest) -> None
        # 收到 http 请求
        request.stream = self

        if request.version != HttpVersion.V10 and request.version != HttpVersion.V11:
            response = HttpResponse(request, HttpStatus.HTTP_VERSION_NOT_UNSUPPORTED, PopularHeaders.CONNECTION_CLOSE)
            self.send_response(response)
            return

        # http 1.1 升级 http 2.0
        if request.get(HttpHeader.UPGRADE) == b"h2c" and request.version == HttpVersion.V11:
            if self.enable_upgrade2:
                if self.protocol.http_upgrade2(request):
                    response = HttpResponse(
                        request,
                        HttpStatus.SWITCHING_PROTOCOL,
                        PopularHeaders.union(PopularHeaders.CONTENT_EMPTY, PopularHeaders.UPGRADE_H2C),
                    )
                    self.send_response(response)
                    # TODO: send Connection Preface
                    return

        # dispatch request
        self.protocol.dispatch_request(request, callback=self._respond)

    def send_data(self, data):  # type: (bytes) -> None
        self.protocol.send_data(data)

    async def send_response(self, response):  # type: (HttpResponse) -> None
        # write response
        data = await response.respond(self)
        if data is not None:
            self.send_data(data)

    async def _respond(self, task):  # type: (Task[Optional[HttpResponse]]) -> None
        """dispatch 任务回调，回复 http 响应"""
        try:
            response = task.result()
            if response is not None:
                await self.send_response(response)
                # close connect
                if response.will_close():
                    self.protocol.close()
        except CancelledError:
            logging.debug("task is cancelled.")
        except Exception:
            logger.exception("encounter unexpected exception.")
        finally:
            # TODO: http1.1 pipeline
            self.parser.free()
