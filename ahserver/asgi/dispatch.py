# encoding=utf-8

__all__ = ["ASGIDispatcher"]

from asgiref.compatibility import guarantee_single_callable

from .response import ASGIHttpResponse
from ..http2.constant import LATIN1_ENCODING
from ..http2.dispatch import AsyncDispatcher

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Dict
    from .request import ASGIHttpRequest


class ASGIDispatcher(AsyncDispatcher):
    def __init__(self, loop, application, server_name, server_port, on_https=False):
        self.loop = loop
        self.application = application
        self.server_name = server_name
        self.server_port = server_port
        self.on_https = on_https

    def get_scope(self, request):  # type: (ASGIHttpRequest) -> Dict[str]
        path_and_query = request.uri.split(b"?", 1)
        path = path_and_query[0]
        if len(path_and_query) > 1:
            query = path_and_query[1]
        else:
            query = b""

        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.1"},
            "http_version": str(request.version),
            "method": str(request.method),
            "scheme": "https" if self.on_https else "http",
            "path": path.decode(LATIN1_ENCODING),
            "raw_path": path,
            "query_string": query,
            "root_path": "",
            "headers": request.headers.lower_items(),
            "client": None,
            "server": (self.server_name, self.server_port),
        }

        return scope

    async def dispatch(self, request):  # type: (ASGIHttpRequest) -> ASGIHttpResponse
        response = ASGIHttpResponse(request, self.loop)
        scope = self.get_scope(request)

        async def receive():
            nonlocal request
            body = await request.body.read()
            more_body = not request.body.read_eof()
            event = {"type": "http.request", "body": body, "more_body": more_body}
            return event

        await guarantee_single_callable(self.application)(scope, receive, response.send)
        return response
