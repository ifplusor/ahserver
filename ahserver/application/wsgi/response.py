# encoding=utf-8

__all__ = ["WSGIHttpResponse"]

from ahserver.server.response import SGIHttpResponse
from ahserver.util.iterator import AsyncIteratorWrapper

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from concurrent.futures import Executor
    from typing import AsyncIterator, Dict, Iterable, Optional, Type, Tuple, TracebackType
    from ahserver.server import HttpRequest


class WSGIHttpResponse(SGIHttpResponse):
    def __init__(self, request, loop=None, executor=None):
        # type: (HttpRequest, AbstractEventLoop, Executor) -> None
        super(WSGIHttpResponse, self).__init__(request)
        self.loop = loop
        self.executor = executor
        self.headers_sent = False
        self.result = None

    def start_response(self, status, response_headers, exc_info=None):
        # type: (int, Dict[str, str], Optional[Tuple[Type[BaseException], BaseException, TracebackType]]) -> None
        global server_version

        if exc_info:
            try:
                if self.headers_sent:
                    # 如果报头已发送，则重新抛出原始的异常。
                    exc_info[1].with_traceback(exc_info[2])
            finally:
                exc_info = None  # 避免死循环。
        elif self.headers:
            raise AssertionError("Headers already set!")

        self.status = status
        self.clear()
        # FIXME: Set-Cookie
        self.update(response_headers)

    def set_result(self, result):  # type: (Iterable[bytes]) -> None
        self.result = result

    def body_iterator(self):  # type: () -> AsyncIterator[bytes]
        return AsyncIteratorWrapper(self.result, loop=self.loop, executor=self.executor)

    def close(self):
        if hasattr(self.result, "close"):
            self.result.close()
