# encoding=utf-8

__all__ = ["Request", "HttpRequest"]

from ahserver.server.constant import LATIN1_ENCODING

from ..util.stream import StreamIO
from .headersdict import HeadersDict
from .protocol import HttpMethod, HttpVersion

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Union


class Request:
    def __init__(self):  # type: () -> None
        super(Request, self).__init__()


class HttpRequest(Request, HeadersDict):
    def __init__(self, method=HttpMethod.GET, uri=b"/", version=HttpVersion.V11):
        # type: (Union[HttpMethod, str], bytes, Union[HttpVersion, str]) -> None
        super(HttpRequest, self).__init__()
        self.method = method
        self.uri = uri
        self.version = version
        self.body = StreamIO()

    @property
    def method(self):  # type: () -> HttpMethod
        return self._method

    @method.setter
    def method(self, method):  # type: (Union[HttpMethod, str]) -> None
        if isinstance(method, HttpMethod):
            self._method = method
        else:
            self._method = HttpMethod.parse(method)

    @property
    def version(self):  # type: () -> HttpVersion
        return self._version

    @version.setter
    def version(self, version):  # type (Union[HttpVersion, str]) -> None
        if isinstance(version, HttpVersion):
            self._version = version
        else:
            self._version = HttpVersion.parse(version)

    def __str__(self):
        return (
            "{} {} HTTP/{}\n".format(self.method, self.uri.decode(), self.version)
            + "\n".join(
                [
                    "{}: {}".format(name.decode(LATIN1_ENCODING), value.decode(LATIN1_ENCODING))
                    for name, value in self.items()
                ]
            )
            + "\n"
        )
