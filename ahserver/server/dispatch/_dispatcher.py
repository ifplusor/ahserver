# encoding=utf-8

__all__ = ["HttpDispatcher"]

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Optional
    from ..request import HttpRequest
    from ..response import HttpResponse


class HttpDispatcher:
    async def dispatch(self, request):
        # type: (HttpRequest) -> Optional[HttpResponse]
        return NotImplemented
