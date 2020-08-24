# encoding: utf-8

__all__ = ["Http1xContext"]

import logging

from asyncio import CancelledError

from ahserver.server.constant import LATIN1_ENCODING
from ahserver.server.parser import H1Parser
from ahserver.server.protocol import HttpVersion, HttpStatus, HttpHeader, PopularHeaders
from ahserver.server.response import HttpResponse, SGIHttpResponse

from ._context import HttpContext

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from asyncio import Task
    from typing import Optional
    from ahserver.server.request import HttpRequest
    from ..httpproto import HttpProtocolStack


class Http1xContext(HttpContext):
    def __init__(self, protocol_stack):  # type: (HttpProtocolStack) -> None
        super(Http1xContext, self).__init__(protocol_stack)

        self.parser = H1Parser(
            self.protocol_stack.message_buffer,
            self.create_request,
            self.on_request,
            self.protocol_stack.on_http2_preface,
        )

    def send_data(self, *args):  # type: (...) -> None
        for data in args:
            self.send(data)

    def parse(self):  # type: () -> int
        return self.parser.parse()

    def on_request(self, request):  # type: (HttpRequest) -> None
        # 收到 http 请求

        if request.version != HttpVersion.V10 and request.version != HttpVersion.V11:
            response = HttpResponse(request, HttpStatus.HTTP_VERSION_NOT_UNSUPPORTED, PopularHeaders.CONNECTION_CLOSE)
            self.send_response(response)
            return

        # upgrade
        if HttpHeader.UPGRADE in request and self.on_upgrade(request):
            return

        super(Http1xContext, self).on_request(request, self._respond)

    def on_upgrade(self, request):
        identifier = request[HttpHeader.UPGRADE]

        if request.version == HttpVersion.V11:
            # http 1.1 升级 http 2.0
            if identifier == b"h2c":
                if self.protocol_stack.upgrade_http2(request):

                    # send upgrade response
                    response = HttpResponse(
                        request,
                        HttpStatus.SWITCHING_PROTOCOL,
                        PopularHeaders.union(PopularHeaders.CONTENT_EMPTY, PopularHeaders.UPGRADE_H2C),
                    )
                    self.send_raw_response(response)

                    self.parser.free()

                    return True

        return False

    def send_status_line(self, response):  # type: (HttpResponse) -> None
        # render status line
        #   Status-Line = HTTP-Version SP Status-Code SP Reason-Phrase CRLF
        self.send_data(
            b"HTTP/",
            str(response.request.version).encode(LATIN1_ENCODING),
            b" ",
            str(response.status).encode(LATIN1_ENCODING),
            b"\r\n",
        )

    def send_headers(self, response):  # type: (HttpResponse) -> None
        # render headers
        header_dict = response.headers
        for field_name, field_value in header_dict.items():
            self.send_data(field_name, b": ", field_value, b"\r\n")

    def send_status_and_headers(self, response):  # type: (HttpResponse) -> None
        self.send_status_line(response)
        self.send_headers(response)
        self.send(b"\r\n")

    def send_chunk(self, data):  # type: (bytes) -> None
        length = hex(len(data))[2:]
        self.send_data(length.encode(LATIN1_ENCODING), b"\r\n", data, b"\r\n")

    def send_last_chunk(self):
        self.send(b"0\r\n\r\n")

    async def send_sgi_response(self, response):  # type: (SGIHttpResponse) -> None
        headers_sent = False
        send_chunked = False

        async for body in response.body:
            if not body:  # don't send headers until body appears
                continue

            if not headers_sent:
                response.normalize_headers()

                if response.headers.get(HttpHeader.TRANSFER_ENCODING) == b"chunked":
                    send_chunked = True
                elif HttpHeader.CONTENT_LENGTH not in response.headers:
                    send_chunked = True
                    response.headers[HttpHeader.TRANSFER_ENCODING] = b"chunked"

                self.send_status_and_headers(response)

                headers_sent = True

            if send_chunked:
                self.send_chunk(body)
            else:
                self.send_data(body)

        if not headers_sent:  # send headers now if body was empty
            self.send_status_and_headers(response)

        if send_chunked:
            self.send_last_chunk()

    def send_raw_response(self, response):  # type: (HttpResponse) -> None
        body = response.body

        if HttpHeader.CONTENT_LENGTH not in response.headers:
            if body is not None:
                response.headers[HttpHeader.CONTENT_LENGTH] = str(len(body)).encode(LATIN1_ENCODING)
            else:
                response.headers[HttpHeader.CONTENT_LENGTH] = 0

        self.send_status_and_headers(response)

        if body is not None:
            self.send_data(body)

    async def send_response(self, response):  # type: (HttpResponse) -> None
        # write response
        if isinstance(response, SGIHttpResponse):
            try:
                return await self.send_sgi_response(response)
            finally:
                response.close()
        else:
            return self.send_raw_response(response)

    async def _respond(self, task):  # type: (Task[Optional[HttpResponse]]) -> None
        """dispatch 任务回调，回复 http 响应"""
        try:
            response = task.result()
            if response is not None:
                await self.send_response(response)
                # close connect
                if response.get(HttpHeader.CONNECTION) == "close":
                    self.protocol_stack.connection.close()
        except CancelledError:
            logging.debug("task is cancelled.")
        except Exception:
            logging.exception("encounter unexpected exception.")
        finally:
            # TODO: http1.1 pipeline
            self.parser.free()
