# encoding: utf-8

__all__ = ["HttpStream"]

from abc import ABCMeta
from six import add_metaclass

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from ..context import HttpContext


@add_metaclass(ABCMeta)
class HttpStream:
    def __init__(self, context):  # type: (HttpContext) -> None
        self.context = context
        self.send = self.context.send

    def send_data(self, *args):  # type: (...) -> None
        for data in args:
            self.send(data)
