# encoding=utf8

__all__ = ["HttpFrameType", "HttpFrameFlag", "HttpFrame"]

from abc import ABCMeta
from six import add_metaclass

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import ByteString


class HttpFrameType:
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


class HttpFrameFlag:
    ACK = 0x01
    END_STREAM = 0x01
    END_HEADERS = 0x04
    PADDED = 0x08
    PRIORITY = 0x20


@add_metaclass(ABCMeta)
class HttpFrame:
    """frame in http/2"""

    def __init__(self, frame_type, flags, identifier):  # type: (int, int, int) -> None
        self.type = frame_type
        self.flags = flags
        self.identifier = identifier

    # @abstractmethod
    def package_body(self):  # type: () -> ByteString
        # raise NotImplementedError()
        return b""

    def __str__(self):
        return "type: {:x}\nflags: {:b}\nidentifier: {}\n".format(self.type, self.flags, self.identifier)
