# encoding=utf-8

__all__ = ["WSGIDispatcher"]

import os
import sys

from concurrent.futures import ThreadPoolExecutor

from .response import WSGIHttpResponse
from ..http2.constant import LATIN1_ENCODING
from ..http2.dispatch import AsyncDispatcher
from ..http2.protocol import HttpHeader

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Any, Dict
    from .request import WSGIHttpRequest


enc, esc = sys.getfilesystemencoding(), "surrogateescape"


def unicode_to_wsgi(u):
    # Convert an environment variable to a WSGI "bytes-as-unicode" string
    return u.encode(enc, esc).decode(LATIN1_ENCODING)


class WSGIDispatcher(AsyncDispatcher):
    def __init__(self, loop, application, server_name, server_port, on_https=False, max_workers=None):
        self.loop = loop
        self.application = application
        self.server_name = server_name
        self.server_port = str(server_port)
        self.on_https = on_https
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="app")

    def get_environ(self, request):  # type: (WSGIHttpRequest) -> Dict[str]
        environ = {k: unicode_to_wsgi(v) for k, v in os.environ.items()}  # type: Dict[str, Any]

        #
        # Required CGI variables

        environ["REQUEST_METHOD"] = str(request.method)
        environ["SCRIPT_NAME"] = ""
        path_and_query = request.uri.decode(LATIN1_ENCODING).split("?", 1)
        environ["PATH_INFO"] = path_and_query[0]
        if len(path_and_query) > 1:
            environ["QUERY_STRING"] = path_and_query[1]
        environ["SERVER_NAME"] = self.server_name
        environ["SERVER_PORT"] = self.server_port
        environ["SERVER_PROTOCOL"] = "HTTP/{}".format(request.version)

        # HTTP_Variables
        for field_name, field_value in request.headers.items():
            if field_name == HttpHeader.CONTENT_LENGTH:
                environ["CONTENT_LENGTH"] = field_value.decode(LATIN1_ENCODING)
            elif field_name == HttpHeader.CONTENT_TYPE:
                environ["CONTENT_TYPE"] = field_value.decode(LATIN1_ENCODING)
            else:
                field_name = field_name.upper().replace("-", "_")
                field_name = "HTTP_{}".format(field_name)
                field_value = field_value.decode(LATIN1_ENCODING)
                environ[field_name] = field_value

        if request.get(HttpHeader.TRANSFER_ENCODING) == b"chunked":
            environ["wsgi.input_terminated"] = True

        #
        # Required WSGI variables

        environ["wsgi.version"] = (1, 0)
        environ["wsgi.url_scheme"] = "https" if self.on_https else "http"
        environ["wsgi.input"] = request.body
        environ["wsgi.errors"] = sys.stderr
        environ["wsgi.multithread"] = True
        environ["wsgi.multiprocess"] = True
        environ["wsgi.run_once"] = False

        return environ

    async def dispatch(self, request):  # type: (WSGIHttpRequest) -> WSGIHttpResponse
        # TODO: HTTP 1.1 Expect/Continue
        response = WSGIHttpResponse(request, self.loop, self.executor)
        environ = self.get_environ(request)
        result = await self.loop.run_in_executor(self.executor, self.application, environ, response.start_response)
        response.set_result(result)
        return response
