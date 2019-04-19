# encoding: utf-8

__all__ = ["Http1xStream"]

import logging
import os

from asyncio import Task, CancelledError

from . import HttpStream
from ..h2parser import H2Parser
from ..protocol import HttpVersion, HttpStatus, HttpHeader, PopularHeaders
from ..request import HttpRequest
from ..response import HttpResponse

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from ahserver.protocol.http2 import Http2Protocol


logger = logging.getLogger()

# settings from env
print_request = os.getenv("ahserver_request_print", "false").lower() == "true"
print_response = os.getenv("ahserver_response_print", "false").lower() == "true"
enable_upgrade2 = os.getenv("ahserver_enable_upgrade2", "false").lower() == "true"


class Http1xStream(HttpStream):
    def __init__(self, protocol, enable_upgrade2=False):
        # type: (Http2Protocol, bool) -> None
        super(Http1xStream, self).__init__(protocol)

        self.enable_upgrade2 = enable_upgrade2
        self.parser = H2Parser(self.on_message, self.protocol.on_http2_preface)

    def data_received(self, data: bytes):
        # 递送给 parser 解协议
        return self.parser.feed(data, len(data))

    def eof_received(self):
        # 递送给 parser 解协议
        if self.parser.feed_eof():
            self.protocol.close()

    def on_message(self, request: HttpRequest):
        # 收到 http 请求
        request.stream = self

        if print_request:
            logger.info("request detail:\n\n----------\n%s", request)
            if request.body is not None:
                logger.info("Body: [%d]\n%s\n", len(request.body), request.body)

        if request.version != HttpVersion.V10 and request.version != HttpVersion.V11:
            response = HttpResponse(request, HttpStatus.HTTP_VERSION_NOT_UNSUPPORTED, PopularHeaders.CONNECTION_CLOSE)
            self.send_response(response)
            return

        # http 1.1 升级 http 2.0
        if (
            HttpHeader.UPGRADE in request
            and request[HttpHeader.UPGRADE] == b"h2c"
            and request.version == HttpVersion.V11
        ):
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

    def send_data(self, data):
        if print_response:
            logger.info(data)
        self.protocol.send_data(data)

    async def send_response(self, response: HttpResponse):
        # write response
        data = await response.respond(self)
        if data is not None:
            self.send_data(data)

    async def _respond(self, task: Task):
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
            self.parser.free()
