# encoding=utf-8

__all__ = ["WSGIHttpRequest"]

from ..http2 import HttpRequest
from ..util.stream import SyncStreamIO


class WSGIHttpRequest(HttpRequest):
    def __init__(self) -> None:
        super(WSGIHttpRequest, self).__init__()
        self.body: SyncStreamIO = SyncStreamIO()
