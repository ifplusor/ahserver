# encoding=utf-8

__all__ = ["Request", "HttpRequest"]

from .protocol import HttpHeader, HttpMethod, HttpVersion
from ..util.dict import CaseInsensitiveDict
from ..util.stream import StreamIO

try:
    from typing import TYPE_CHECKING, Optional, Union
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from .stream import HttpStream


class Request:
    def __init__(self, stream=None):  # type: (Optional[HttpStream]) -> None
        self.stream = stream

    @property
    def stream(self):
        return self._stream

    @stream.setter
    def stream(self, stream):
        self._stream = stream


class HttpRequest(Request):
    def __init__(self, method=HttpMethod.GET, uri=b"/", version=HttpVersion.V11):
        super(HttpRequest, self).__init__()

        # 使用 bytes 存储，保留数据的原始格式

        self.method = method
        self.uri = uri
        self.version = version
        self.headers = CaseInsensitiveDict()
        self.body: StreamIO

    @property
    def method(self) -> HttpMethod:
        return self._method

    @method.setter
    def method(self, method: Union[HttpMethod, str]):
        if isinstance(method, HttpMethod):
            self._method = method
        else:
            self._method = HttpMethod.parse(method)

    @property
    def version(self) -> HttpVersion:
        return self._version

    @version.setter
    def version(self, version: Union[HttpVersion, str]):
        if isinstance(version, HttpVersion):
            self._version = version
        else:
            self._version = HttpVersion.parse(version)

    def get(self, field_name: Union[HttpHeader, str], default=None):
        return self.headers.get(field_name, default)

    def __contains__(self, field_name: Union[HttpHeader, str]) -> bool:
        return field_name in self.headers

    def __setitem__(self, field_name: Union[HttpHeader, str], value):
        if field_name in self.headers:
            self.headers[field_name] += b"," + value
        else:
            self.headers[field_name] = value

    def __getitem__(self, field_name: Union[HttpHeader, str]):
        return self.headers[field_name]

    def __delitem__(self, field_name: Union[HttpHeader, str]):
        del self.headers[field_name]

    def __str__(self):
        return (
            "{} {} HTTP/{}\n".format(self.method, self.uri.decode(), self.version)
            + "\n".join(["{}: {}".format(name, value.decode()) for name, value in self.headers.items()])
            + "\n"
        )
