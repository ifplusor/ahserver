# encoding=utf-8

__all__ = ["Http2Stream", "Http2SuperStream"]

from enum import IntEnum
from typing import Union

from ahserver.exception import AHServerProtocolError
from ahserver.util.parser import IntEnumParser

from . import HttpStream
from ..frame import HttpFrame, HttpFrameType

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from ahserver.protocol.http2 import Http2Protocol


@IntEnumParser("stream_state")
class StreamState(IntEnum):
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

    def __init__(self, protocol):
        # type: (Http2Protocol) -> None
        super(Http2Stream, self).__init__(protocol)
        self.state = StreamState.IDLE
        self.dependency = 0

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state: Union[StreamState, int]):
        if isinstance(state, StreamState):
            self._state = state
        else:
            self._state = StreamState.parse(state)

    def frame_received(self, frame: HttpFrame):
        return self._trans_state_by_recv(frame.type)

    def _trans_state_by_recv(self, frame_type: HttpFrameType):
        if self.state is StreamState.IDLE:
            if frame_type is HttpFrameType.HEADERS:
                self.state = StreamState.OPEN
                return 0

        raise AHServerProtocolError()

    def send_frame(self, frame: HttpFrame):
        self._trans_state_by_send(frame.type)

    def _trans_state_by_send(self, frame_type: HttpFrameType):
        if self.state is StreamState.IDLE:
            if frame_type is HttpFrameType.HEADERS:
                self.state = StreamState.OPEN
                return
        elif self.state is StreamState.RESERVED_LOCAL:
            pass
        elif self.state is StreamState.RESERVED_REMOTE:
            pass
        elif self.state is StreamState.OPEN:
            pass
        elif self.state is StreamState.HALF_CLOSED_LOCAL:
            pass
        elif self.state is StreamState.HALF_CLOSED_REMOTE:
            pass
        else:  # StreamState.CLOSED
            pass

        raise AHServerProtocolError()

    def trans_state_by_recv(self, frame_type: HttpFrameType):
        if self.state is StreamState.IDLE:
            if frame_type is HttpFrameType.HEADERS:
                self.state = StreamState.OPEN

        raise AHServerProtocolError()


class Http2SuperStream(Http2Stream):
    def __init__(self, protocol):
        # type: (Http2Protocol) -> None
        super(Http2SuperStream, self).__init__(protocol)

    def frame_received(self, frame: HttpFrame):
        pass
