# encoding=utf-8

__all__ = ["Request", "HttpRequest"]

from typing import Union

from uvloop.loop import TCPTransport

from .protocol import *
from ..structures.dict import CaseInsensitiveDict


class Request:
    def __init__(self, connection: TCPTransport = None):
        self.connection = connection


class HttpRequest(Request):

    def __init__(self, method=HttpMethod.GET, version=HttpVersion.V11):
        super().__init__()

        # 使用 bytes 存储，保留数据的原始格式

        self.method = method
        self.uri = b"/"
        self.version = version
        self.headers = CaseInsensitiveDict()
        self.body = None

    @property
    def method(self) -> HttpMethod:
        return self._method

    @method.setter
    def method(self, method: Union[str, HttpMethod]):
        if isinstance(method, HttpMethod):
            self._method = method
        else:
            self._method = HttpMethod.parse(method)

    @property
    def version(self) -> HttpVersion:
        return self._version

    @version.setter
    def version(self, version: Union[str, HttpVersion]):
        if isinstance(version, HttpVersion):
            self._version = version
        else:
            self._version = HttpVersion.parse(version)

    def __str__(self):
        return "{} {} HTTP/{}\n".format(self.method, self.uri.decode(), self.version) + \
               "\n".join(["{}: {}".format(name, value.decode()) for name, value in self.headers.items()]) + \
               "\n"
