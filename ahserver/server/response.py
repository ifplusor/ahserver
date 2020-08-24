# encoding=utf-8

__all__ = ["Response", "HttpResponse", "SGIHttpResponse"]

from abc import ABCMeta, abstractmethod
from six import add_metaclass

from .. import __version__
from ..util.date import date_now
from .constant import LATIN1_ENCODING
from .headersdict import HeadersDict
from .protocol import HttpStatus, HttpHeader

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import AnyStr, AsyncIterator, Dict, Union
    from .request import HttpRequest


server_version = "AHServer {}".format(__version__).encode(LATIN1_ENCODING)


@add_metaclass(ABCMeta)
class Response:
    def __init__(self):  # type: () -> None
        super(Response, self).__init__()


class HttpResponse(Response, HeadersDict):
    def __init__(self, request, status=HttpStatus.OK, headers=None, body=None):
        # type: (HttpRequest, Union[str, HttpStatus], Dict[AnyStr, AnyStr], bytes) -> None
        super(HttpResponse, self).__init__()
        self.request = request

        self.status = status

        if headers is not None:
            self.update(headers)

        self._body = body

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, body):
        self._body = body

    def normalize_headers(self):
        if HttpHeader.DATE not in self:
            self[HttpHeader.DATE] = date_now().encode(LATIN1_ENCODING)
        if HttpHeader.SERVER not in self:
            self[HttpHeader.SERVER] = server_version


class SGIHttpResponse(HttpResponse):
    def __init__(self, request, status=HttpStatus.OK, headers=None) -> None:
        # type: (HttpRequest, Union[str, HttpStatus], Dict[AnyStr, AnyStr]) -> None
        super(SGIHttpResponse, self).__init__(request, status, headers)

    @abstractmethod
    def body_iterator(self):  # type: () -> AsyncIterator[bytes]
        raise NotImplementedError()

    @property
    def body(self):  # type: () -> AsyncIterator[bytes]
        return self.body_iterator()

    def close(self):
        pass
