# encoding=utf8

__all__ = ["create_frame"]

from ._frame import HttpFrameType
from .frames import (
    HttpDataFrame,
    HttpHeadersFrame,
    HttpPriorityFrame,
    HttpRstStreamFrame,
    HttpSettingsFrame,
    HttpPushPromiseFrame,
    HttpPingFrame,
    HttpGoawayFrame,
    HttpWindowUpdateFrame,
    HttpContinuationFrame,
)

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from ._frame import HttpFrame


_type2class_map_ = {
    HttpFrameType.DATA: HttpDataFrame,
    HttpFrameType.HEADERS: HttpHeadersFrame,
    HttpFrameType.PRIORITY: HttpPriorityFrame,
    HttpFrameType.RST_STREAM: HttpRstStreamFrame,
    HttpFrameType.SETTINGS: HttpSettingsFrame,
    HttpFrameType.PUSH_PROMISE: HttpPushPromiseFrame,
    HttpFrameType.PING: HttpPingFrame,
    HttpFrameType.GOAWAY: HttpGoawayFrame,
    HttpFrameType.WINDOW_UPDATE: HttpWindowUpdateFrame,
    HttpFrameType.CONTINUATION: HttpContinuationFrame,
}


def create_frame(frame_type, flags, identifier):
    # type: (int, int, int) -> HttpFrame
    return _type2class_map_[frame_type](frame_type, flags, identifier)
