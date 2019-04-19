# encoding=utf-8

__all__ = ["add_dispatcher", "dispatch_request", "AsyncDispatcher", "HttpDispatcher"]

try:
    from typing import TYPE_CHECKING, Optional
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from ..request import HttpRequest
    from ..response import HttpResponse


class HttpDispatcher:
    def dispatch(self, request):
        # type: (HttpRequest) -> Optional[HttpResponse]
        return NotImplemented


class AsyncDispatcher(HttpDispatcher):
    async def dispatch(self, request):
        # type: (HttpRequest) -> Optional[HttpResponse]
        return NotImplemented


try:
    from .root import add_dispatcher, dispatch_request
finally:
    pass
