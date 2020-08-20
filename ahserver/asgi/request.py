# encoding=utf-8

__all__ = ["ASGIHttpRequest"]

from ..http2 import HttpRequest
from ..util.stream import AsyncStreamIO


class ASGIHttpRequest(HttpRequest):
    def __init__(self) -> None:
        super(ASGIHttpRequest, self).__init__()
        self.body: AsyncStreamIO = AsyncStreamIO()
