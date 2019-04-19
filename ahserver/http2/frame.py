# encoding=utf-8

__all__ = [
    "HttpFrameType",
    "HttpFrame",
    "HttpDataFrame",
    "HttpHeadersFrame",
    "HttpSettingsFrame",
]

from enum import IntEnum

try:
    from typing import Dict, Union
except Exception:
    pass

from ..util.parser import IntEnumParser


@IntEnumParser("frame_type")
class HttpFrameType(IntEnum):
    DATA = 0
    HEADERS = 1
    PRIORITY = 2
    RST_STREAM = 3
    SETTINGS = 4
    PUSH_PROMISE = 5
    PING = 6
    GOAWAY = 7
    WINDOW_UPDATE = 8
    CONTINUATION = 9


class HttpFrame:
    """frame in http/2"""

    _type_class = dict()

    @staticmethod
    def create_frame(type, flags, identifier):
        # type: (Union[HttpFrameType, int], int, int) -> HttpFrame
        if isinstance(type, int):
            type = HttpFrameType.parse(type)
        return HttpFrame._type_class[type](type, flags, identifier)

    def __init__(self, type: HttpFrameType, flags: int, identifier: int):
        self.type = type
        self.flags = flags
        self.identifier = identifier

    def __str__(self):
        return "type: {}\nflags: {}\nidentifier: {}\n".format(self.type, self.flags, self.identifier)


class HttpDataFrame(HttpFrame):
    def __init__(
        self, type: HttpFrameType, flags: int, identifier: int,
    ):
        super(HttpDataFrame, self).__init__(type, flags, identifier)
        self.data: bytes


HttpFrame._type_class[HttpFrameType.DATA] = HttpDataFrame


class HttpHeadersFrame(HttpFrame):
    def __init__(
        self, type: HttpFrameType, flags: int, identifier: int,
    ):
        super(HttpHeadersFrame, self).__init__(type, flags, identifier)
        self.header_block_fragment: bytes


HttpFrame._type_class[HttpFrameType.HEADERS] = HttpDataFrame


class HttpSettingsFrame(HttpFrame):
    def __init__(
        self, type: HttpFrameType, flags: int, identifier: int,
    ):
        super(HttpSettingsFrame, self).__init__(type, flags, identifier)
        self.settings: Dict[int, int] = dict()


HttpFrame._type_class[HttpFrameType.SETTINGS] = HttpSettingsFrame
