# encoding=utf-8


__all__ = ["Response", "HttpResponse"]

from .protocol import HttpStatus
from .request import HttpRequest
from ..structures.dict import CaseInsensitiveDict


class Response:
    def __init__(self, connection=None):
        self._connection = connection


class HttpResponse(Response):

    def __init__(self, request: HttpRequest, status=HttpStatus.OK, headers: dict = None, body=None):
        super().__init__(request.connection)
        self._request = request

        self.status = status
        self.headers = CaseInsensitiveDict(headers)
        self.body = body

    def render(self):
        # Status-Line = HTTP-Version SP Status-Code SP Reason-Phrase CRLF
        status_line = "HTTP/{} {} {}\r\n".format(self._request.version, self.status.value[0], self.status.value[1])

        headers = ""
        for header in self.headers:
            headers += "{}: {}\r\n".format(header, self.headers[header])

        if self.body is not None:
            if isinstance(self.body, bytes):
                body = self.body
            else:
                body = str(self.body).encode("utf-8")
            headers += "{}: {}\r\n".format("Content-length", len(body))
        else:
            body = b""

        return "{}{}\r\n".format(status_line, headers).encode("utf-8") + body

    def will_close(self):
        return self.headers.get("Connection", "") == "close"
