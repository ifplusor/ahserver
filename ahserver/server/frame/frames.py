# encoding=utf-8

__all__ = [
    "HttpDataFrame",
    "HttpHeadersFrame",
    "HttpPriorityFrame",
    "HttpRstStreamFrame",
    "HttpSettingsFrame",
    "HttpPushPromiseFrame",
    "HttpPingFrame",
    "HttpGoawayFrame",
    "HttpWindowUpdateFrame",
    "HttpContinuationFrame",
]

from ._frame import HttpFrame

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Dict
    from ..request import HttpRequest


class HttpDataFrame(HttpFrame):
    def __init__(self, type, flags, identifier):  # type: (int, int, int) -> None
        super(HttpDataFrame, self).__init__(type, flags, identifier)
        self.data = None  # type: bytes


class HttpHeadersFrame(HttpFrame):
    def __init__(self, type, flags, identifier):  # type: (int, int, int) -> None
        super(HttpHeadersFrame, self).__init__(type, flags, identifier)
        self.request = None  # type: HttpRequest


class HttpPriorityFrame(HttpFrame):
    def __init__(self, type, flags, identifier):  # type: (int, int, int) -> None
        super(HttpPriorityFrame, self).__init__(type, flags, identifier)


class HttpRstStreamFrame(HttpFrame):
    def __init__(self, type, flags, identifier):  # type: (int, int, int) -> None
        super(HttpRstStreamFrame, self).__init__(type, flags, identifier)


class HttpSettingsFrame(HttpFrame):
    def __init__(self, type, flags, identifier):  # type: (int, int, int) -> None
        super(HttpSettingsFrame, self).__init__(type, flags, identifier)
        self.settings = dict()  # type: Dict[int, int]


class HttpPushPromiseFrame(HttpFrame):
    def __init__(self, type, flags, identifier):  # type: (int, int, int) -> None
        super(HttpPushPromiseFrame, self).__init__(type, flags, identifier)


class HttpPingFrame(HttpFrame):
    def __init__(self, type, flags, identifier):  # type: (int, int, int) -> None
        super(HttpPingFrame, self).__init__(type, flags, identifier)


class HttpGoawayFrame(HttpFrame):
    def __init__(self, type, flags, identifier):  # type: (int, int, int) -> None
        super(HttpGoawayFrame, self).__init__(type, flags, identifier)


class HttpWindowUpdateFrame(HttpFrame):
    def __init__(self, type, flags, identifier):  # type: (int, int, int) -> None
        super(HttpWindowUpdateFrame, self).__init__(type, flags, identifier)
        self.increment = 0


class HttpContinuationFrame(HttpFrame):
    def __init__(self, type, flags, identifier):  # type: (int, int, int) -> None
        super(HttpContinuationFrame, self).__init__(type, flags, identifier)
        self.request = None  # type: HttpRequest
