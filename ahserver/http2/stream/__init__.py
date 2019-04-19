# encoding: utf-8

__all__ = ["HttpStream"]

import six

from abc import ABCMeta, abstractmethod

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from ahserver.protocol.http2 import Http2Protocol


@six.add_metaclass(ABCMeta)
class HttpStream:
    def __init__(self, protocol):  # type: (Http2Protocol) -> None
        self.protocol = protocol

    @abstractmethod
    def send_data(self, data):  # type: (bytes) -> None
        raise NotImplementedError()
