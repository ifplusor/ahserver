# encoding: utf-8

__all__ = ["HttpContext"]

from abc import ABCMeta, abstractmethod
from six import add_metaclass

from ahserver.server.request import HttpRequest

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from asyncio import Task
    from typing import Any, Callable, Coroutine, Optional
    from ahserver.server.response import HttpResponse
    from ..httpproto import HttpProtocolStack


@add_metaclass(ABCMeta)
class HttpContext:
    def __init__(self, protocol_stack):  # type: (HttpProtocolStack) -> None
        self.protocol_stack = protocol_stack
        self.send = self.protocol_stack.connection.send

    @abstractmethod
    def parse(self):  # type: () -> int
        raise NotImplementedError()

    def create_request(self):  # type: () -> HttpRequest
        return HttpRequest()

    def on_request(self, request, callback=None):
        # type: (HttpRequest, Callable[[Task[Optional[HttpResponse]]], Optional[Coroutine[Any, Any, None]]]) -> None

        # dispatch request
        self.protocol_stack.dispatch_request(request, callback)
