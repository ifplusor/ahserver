# encoding=utf-8

__all__ = ["Response", "HttpResponse", "SGIHttpResponse"]

from abc import ABCMeta, abstractmethod
from datetime import datetime
from six import add_metaclass
from time import mktime
from wsgiref.handlers import format_date_time

from .constant import LATIN1_ENCODING
from .protocol import HttpStatus, HttpHeader
from .. import __version__
from ..util.dict import CaseInsensitiveDict

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import AsyncIterator, Dict, Optional, Union
    from .request import HttpRequest
    from .stream import HttpStream


@add_metaclass(ABCMeta)
class Response:
    def __init__(self, stream=None):  # type: (HttpStream) -> None
        self._stream = stream

    @property
    def stream(self):
        return self._stream

    @abstractmethod
    async def respond(self, stream):  # type: (HttpStream) -> Optional[bytes]
        raise NotImplementedError()


class HttpResponse(Response):
    def __init__(self, request, status=HttpStatus.OK, headers=None, body=None):
        # type: (HttpRequest, Union[str, HttpStatus], Dict[HttpHeader, str], bytes) -> None
        super(HttpResponse, self).__init__(request.stream)
        self._request = request

        self.status = status
        self.headers = CaseInsensitiveDict(headers)
        self.body = body

    def render_status_line(self):
        # render status line
        #   Status-Line = HTTP-Version SP Status-Code SP Reason-Phrase CRLF
        status_line = "HTTP/{} {}\r\n".format(self._request.version, self.status).encode(LATIN1_ENCODING)
        return status_line

    def render_headers(self):
        # render headers
        header_dict = self.headers
        headers = "".join(
            ["{}: {}\r\n".format(field_name, field_value) for field_name, field_value in header_dict.items()]
        ).encode(LATIN1_ENCODING)
        return headers

    async def respond(self, stream):
        msg = self.render_status_line() + self.render_headers() + b"\r\n"
        if self.body is not None:
            msg += self.body
        return msg

    def will_close(self):
        return self.headers.get(HttpHeader.CONNECTION) == "close"


server_version = "AHServer {}".format(__version__)


def date_now():
    now = datetime.now()
    stamp = mktime(now.timetuple())
    return format_date_time(stamp)


class SGIHttpResponse(HttpResponse):
    def __init__(self, request, status=HttpStatus.OK, headers=None) -> None:
        # type: (HttpRequest, Union[str, HttpStatus], Dict[HttpHeader, str]) -> None
        super(SGIHttpResponse, self).__init__(request, status, headers)
        self.send_chunked = False

    def normalize_headers(self):
        if HttpHeader.DATE not in self.headers:
            self.headers[HttpHeader.DATE] = date_now()
        if HttpHeader.SERVER not in self.headers:
            self.headers[HttpHeader.SERVER] = server_version

        if self.headers.get(HttpHeader.TRANSFER_ENCODING) == "chunked":
            self.send_chunked = True
        elif HttpHeader.CONTENT_LENGTH not in self.headers:
            self.send_chunked = True
            self.headers[HttpHeader.TRANSFER_ENCODING] = "chunked"

    def send_status_and_headers(self, stream):
        self.normalize_headers()

        stream.send_data(self.render_status_line())
        stream.send_data(self.render_headers())
        stream.send_data(b"\r\n")

    def send_chunk(self, stream, data):
        stream.send_data(hex(len(data))[2:].encode(LATIN1_ENCODING))
        stream.send_data(b"\r\n")
        stream.send_data(data)
        stream.send_data(b"\r\n")

    def send_last_chunk(self, stream):
        stream.send_data(b"0\r\n\r\n")

    def send_body(self, stream, body):
        if not self.headers_sent:
            self.headers_sent = True
            self.send_status_and_headers(stream)

        if self.send_chunked:
            self.send_chunk(stream, body)
        else:
            stream.send_data(body)

    @abstractmethod
    def body_iterator(self):  # type: () -> AsyncIterator[bytes]
        raise NotImplementedError()

    def close(self):
        pass

    async def respond(self, stream):
        body_iter = self.body_iterator()
        try:
            async for body in body_iter:
                if not body:  # don't send headers until body appears
                    continue
                self.send_body(stream, body)
            if not self.headers_sent:  # send headers now if body was empty
                self.send_status_and_headers(stream)
            if self.send_chunked:
                self.send_last_chunk(stream)
        finally:
            self.close()
