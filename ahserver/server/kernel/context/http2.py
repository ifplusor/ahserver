# encoding: utf-8

__all__ = ["Http2Context"]

from ahserver.server.frame import create_frame, HttpFrameType
from ahserver.server.parser import H2Parser
from ahserver.server.protocol import HttpVersion
from ahserver.server.request import HttpRequest

from ._context import HttpContext
from ..stream.http2 import Http2PlainStream, Http2SuperStream, StreamState

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Dict
    from ahserver.server.frame import HttpFrame, HttpHeadersFrame, HttpContinuationFrame
    from ..httpproto import HttpProtocolStack
    from ..stream.http2 import Http2Stream


class Http2Context(HttpContext):
    def __init__(self, protocol_stack):  # type: (HttpProtocolStack) -> None
        super(Http2Context, self).__init__(protocol_stack)

        self.splitter = H2Parser(self.protocol_stack.message_buffer, self.create_frame, self.frame_received)
        self.super_stream = Http2SuperStream(self, 0)

        self.stream_table = {0: self.super_stream}  # type: Dict[int, Http2Stream]

    def on_http1_request(self, request):
        stream = Http2PlainStream(self, 1)
        stream.state = StreamState.HALF_CLOSED_REMOTE
        stream.request = request
        self.stream_table[1] = stream
        self.on_request(request, stream._respond)

    def get_stream_request(self, identifier):
        stream = self.stream_table.get(identifier)
        if isinstance(stream, Http2PlainStream):
            return stream.request
        return None

    def create_frame(self, frame_type, flags, identifier):
        if frame_type == HttpFrameType.HEADERS:
            request = self.get_stream_request(identifier)
            if request is None:
                request = HttpRequest(version=HttpVersion.V20)
            header_frame = create_frame(frame_type, flags, identifier)  # type: HttpHeadersFrame
            header_frame.request = request
            return header_frame
        elif frame_type == HttpFrameType.CONTINUATION:
            request = self.get_stream_request(identifier)
            if request is None:
                return None
            continuation_frame = create_frame(frame_type, flags, identifier)  # type: HttpContinuationFrame
            continuation_frame.request = request
            return continuation_frame
        else:
            return create_frame(frame_type, flags, identifier)

    def parse(self):  # type: () -> int
        return self.splitter.parse()

    def frame_received(self, frame):  # type: (HttpFrame) -> int
        stream = self.stream_table.get(frame.identifier)
        if stream is None:
            stream = Http2PlainStream(self, frame.identifier)
            self.stream_table[frame.identifier] = stream
        return stream.frame_received(frame)

    def send_preface(self):
        self.super_stream.send_frame(HttpFrameType.SETTINGS, 0)
