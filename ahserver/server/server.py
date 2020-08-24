# encoding=utf-8

__all__ = ["HttpServer"]

from .dispatch.root import RootDispatcher
from .connection.http import HttpConnection

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Optional
    from .dispatch import HttpDispatcher
    from .request import HttpRequest
    from .response import HttpResponse


class HttpServer:
    def __init__(self):
        self.root_dispatcher = RootDispatcher()

    def add_dispatcher(self, dispatcher):  # type: (HttpDispatcher) -> None
        self.root_dispatcher.add_dispatcher(dispatcher)

    async def dispatch_request(self, request):  # type: (HttpRequest) -> Optional[HttpResponse]
        return await self.root_dispatcher.dispatch(request)

    def new_connection(self):  # type: () -> HttpConnection
        return HttpConnection(self)
