# encoding=utf-8

__all__ = ["Response", "HttpResponse"]

import six

from abc import ABCMeta, abstractmethod

from .constant import LATIN1_ENCODING
from .protocol import HttpStatus, HttpHeader
from ..util.dict import CaseInsensitiveDict

try:
    from typing import TYPE_CHECKING, Dict, Optional, Union
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from .request import HttpRequest
    from .stream import HttpStream


@six.add_metaclass(ABCMeta)
class Response:
    def __init__(self, stream=None):  # type: (Optional[HttpStream]) -> None
        self._stream = stream

    @property
    def stream(self):
        return self._stream

    @abstractmethod
    async def respond(self, stream):  # type: (HttpStream) -> Optional[None]
        raise NotImplementedError()


class HttpResponse(Response):
    def __init__(self, request, status=HttpStatus.OK, headers=None, body=None):
        # type: (HttpRequest, Optional[Union[str, HttpStatus]], Optional[Dict[HttpHeader, str]], Optional[bytes]) -> None
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
