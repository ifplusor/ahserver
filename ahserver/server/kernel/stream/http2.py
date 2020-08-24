# encoding=utf-8

__all__ = ["Http2Stream", "Http2SuperStream", "Http2PlainStream"]

import logging

from asyncio import CancelledError
from ahserver.exception import AHServerProtocolError
from ahserver.server.frame import (
    HttpFrameType,
    HttpFrameFlag,
    HttpDataFrame,
    HttpHeadersFrame,
    HttpSettingsFrame,
    HttpWindowUpdateFrame,
    HttpContinuationFrame,
)
from ahserver.server.response import HttpResponse, SGIHttpResponse

from ._stream import HttpStream

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from asyncio import Task
    from typing import Optional
    from ahserver.server.frame import HttpFrame
    from ..context.http2 import Http2Context


class StreamState:
    """The State of Stream"""

    IDLE = 0
    OPEN = 1
    CLOSED = 2
    RESERVED_LOCAL = 3
    RESERVED_REMOTE = 4
    HALF_CLOSED_LOCAL = 5
    HALF_CLOSED_REMOTE = 6


class Http2Stream(HttpStream):
    r"""Stream in http/2.0

    The lifecycle of a stream:

                                 +--------+
                         send PP |        | recv PP
                        ,--------|  idle  |--------.
                       /         |        |         \
                      v          +--------+          v
               +----------+          |           +----------+
               |          |          | send H /  |          |
        ,------| reserved |          | recv H    | reserved |------.
        |      | (local)  |          |           | (remote) |      |
        |      +----------+          v           +----------+      |
        |          |             +--------+             |          |
        |          |     recv ES |        | send ES     |          |
        |   send H |     ,-------|  open  |-------.     | recv H   |
        |          |    /        |        |        \    |          |
        |          v   v         +--------+         v   v          |
        |      +----------+          |           +----------+      |
        |      |   half   |          |           |   half   |      |
        |      |  closed  |          | send R /  |  closed  |      |
        |      | (remote) |          | recv R    | (local)  |      |
        |      +----------+          |           +----------+      |
        |           |                |                 |           |
        |           | send ES /      |       recv ES / |           |
        |           | send R /       v        send R / |           |
        |           | recv R     +--------+   recv R   |           |
        | send R /  `----------->|        |<-----------'  send R / |
        | recv R                 | closed |               recv R   |
        `----------------------->|        |<----------------------'
                                 +--------+

            send:   endpoint sends this frame
            recv:   endpoint receives this frame

            H:  HEADERS frame (with implied CONTINUATIONs)
            PP: PUSH_PROMISE frame (with implied CONTINUATIONs)
            ES: END_STREAM flag
            R:  RST_STREAM frame
    """

    def __init__(self, context, identifier):
        # type: (Http2Context, int) -> None
        super(Http2Stream, self).__init__(context)
        self.state = StreamState.IDLE
        self.identifier = identifier
        self._identifier_bytes = identifier.to_bytes(length=4, byteorder="big", signed=False)
        self.dependency = 0

    def frame_received(self, frame):  # type: (HttpFrame) -> int
        return self._trans_state_by_recv(frame.type)

    def _trans_state_by_recv(self, frame_type):  # type: (HttpFrameType) -> int
        if self.state == StreamState.IDLE:
            if frame_type == HttpFrameType.HEADERS:
                self.state = StreamState.OPEN
                return 0

        # raise AHServerProtocolError()
        return 0

    def _trans_state_by_send(self, frame_type):  # type: (int) -> None
        if self.state == StreamState.IDLE:
            if frame_type == HttpFrameType.HEADERS:
                self.state = StreamState.OPEN
                return
        elif self.state == StreamState.RESERVED_LOCAL:
            pass
        elif self.state == StreamState.RESERVED_REMOTE:
            pass
        elif self.state == StreamState.OPEN:
            pass
        elif self.state == StreamState.HALF_CLOSED_LOCAL:
            pass
        elif self.state == StreamState.HALF_CLOSED_REMOTE:
            pass
        else:  # StreamState.CLOSED
            pass

        # raise AHServerProtocolError()

    def send_frame(self, frame_type, flags, body=None):  # type: (int, int, bytes) -> None
        self._trans_state_by_send(frame_type)

        # send lenght
        if body is not None:
            length = len(body)
        else:
            length = 0
        self.send_data(length.to_bytes(length=3, byteorder="big", signed=False))

        # send type
        self.send_data(frame_type.to_bytes(length=1, byteorder="big", signed=False))

        # send flag
        self.send_data(flags.to_bytes(length=1, byteorder="big", signed=False))

        # send identifier
        self.send_data(self._identifier_bytes)

        # send body
        if body is not None:
            self.send_data(body)

    def send_status_and_headers(self, response):  # type: (HttpResponse) -> None
        # self.send_status_line(response)
        # self.send_headers(response)
        self.send(b"\r\n")

    async def send_sgi_response(self, response):  # type: (SGIHttpResponse) -> None
        headers_sent = False

        async for body in response.body:
            if not body:  # don't send headers until body appears
                continue

            if not headers_sent:
                response.normalize_headers()
                self.send_status_and_headers(response)
                headers_sent = True

            self.send_frame(HttpFrameType.DATA, 0, body)

        if not headers_sent:  # send headers now if body was empty
            self.send_status_and_headers(response)

    def send_raw_response(self, response):  # type: (HttpResponse) -> None
        body = response.body

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
        except CancelledError:
            logging.debug("task is cancelled.")
        except Exception:
            logging.exception("encounter unexpected exception.")


class Http2SuperStream(Http2Stream):
    def __init__(self, context, identifier):
        # type: (Http2Context, int) -> None
        super(Http2SuperStream, self).__init__(context, identifier)

    def frame_received(self, frame):  # type: (HttpFrame) -> int
        if frame.type == HttpFrameType.SETTINGS:
            return self.settings_frame_received(frame)
        elif frame.type == HttpFrameType.WINDOW_UPDATE:
            return self.window_update_frame_received(frame)
        return 0

    def settings_frame_received(self, frame):  # type: (HttpSettingsFrame) -> int
        if frame.flags & HttpFrameFlag.ACK:
            return 0
        else:
            self.send_frame(HttpFrameType.SETTINGS, HttpFrameFlag.ACK)
            return 0

    def window_update_frame_received(self, frame):  # type: (HttpWindowUpdateFrame) -> int
        return 0


class Http2PlainStream(Http2Stream):
    def __init__(self, protocol_stack, identifier):
        # type: (Http2Context, int) -> None
        super(Http2PlainStream, self).__init__(protocol_stack, identifier)
        self.request = None

    def frame_received(self, frame):  # type: (HttpFrame) -> int
        return self._frame_proc[frame.type](self, frame)

    def data_frame_received(self, frame):  # type: (HttpDataFrame) -> int
        self.request.body.write(frame.data)
        return 0

    def headers_frame_received(self, frame):  # type: (HttpHeadersFrame) -> int
        if self.request is None:
            self.request = frame.request
            if frame.flags & HttpFrameFlag.END_HEADERS:
                self.context.on_request(self.request, self._respond)
        return 0

    def continuation_frame_received(self, frame):  # type: (HttpContinuationFrame) -> int
        if frame.flags & HttpFrameFlag.END_HEADERS:
            self.context.on_request(frame.request, self._respond)
        return 0

    _frame_proc = (
        # DATA = 0
        data_frame_received,
        # HEADERS = 1
        headers_frame_received,
        # PRIORITY = 2
        Http2Stream.frame_received,
        # RST_STREAM = 3
        Http2Stream.frame_received,
        # SETTINGS = 4
        Http2Stream.frame_received,
        # PUSH_PROMISE = 5
        Http2Stream.frame_received,
        # PING = 6
        Http2Stream.frame_received,
        # GOAWAY = 7
        Http2Stream.frame_received,
        # WINDOW_UPDATE = 8
        Http2Stream.frame_received,
        # CONTINUATION = 9
        continuation_frame_received,
    )
