# encoding=utf-8

__all__ = ["ASGIDispatcher"]

from asgiref.compatibility import guarantee_single_callable

from ahserver.server.constant import LATIN1_ENCODING
from ahserver.server.dispatch import HttpDispatcher
from ahserver.server.protocol import HttpVersion

from .response import ASGIHttpResponse

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Dict
    from ahserver.server import HttpRequest


class ASGIDispatcher(HttpDispatcher):
    def __init__(self, loop, application, server_name, server_port, on_https=False):
        self.loop = loop
        self.application = application
        self.server_name = server_name
        self.server_port = server_port
        self.on_https = on_https

    def get_scope(self, request):  # type: (HttpRequest) -> Dict[str]
        path_and_query = request.uri.split(b"?", 1)
        path = path_and_query[0]
        if len(path_and_query) > 1:
            query = path_and_query[1]
        else:
            query = b""

        if request.version == HttpVersion.V20:
            http_version = "2"
        else:
            http_version = str(request.version)

        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.1"},
            "http_version": http_version,
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

    async def dispatch(self, request):  # type: (HttpRequest) -> ASGIHttpResponse
        response = ASGIHttpResponse(request, self.loop)
        scope = self.get_scope(request)

        async def receive():
            nonlocal request
            body = await request.body.read1()
            more_body = not await request.body.at_eof()
            event = {"type": "http.request", "body": body, "more_body": more_body}
            return event

        await guarantee_single_callable(self.application)(scope, receive, response.send)
        return response
