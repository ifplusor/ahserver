# encoding=utf-8

__all__ = ["HttpProtocolStack"]

import asyncio

from inspect import iscoroutinefunction

from ..parser import Buffer
from ..protocol import HttpHeader
from ..request import HttpRequest
from .context.http1x import Http1xContext
from .context.http2 import Http2Context

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop, Task
    from typing import Any, Callable, Coroutine, Optional
    from ..response import HttpResponse
    from ..server import HttpServer
    from ..connection.http import HttpConnection


class HttpProtocolStack:
    def __init__(self, server, connection, on_ssl=False, is_h2=False, loop=None):
        # type: (HttpServer, HttpConnection, bool, bool, AbstractEventLoop) -> None
        if loop is None:
            loop = asyncio.get_running_loop()

        self.loop = loop
        self.server = server
        self.connection = connection

        self.on_ssl = on_ssl
        self.is_h2 = is_h2

        self.message_buffer = Buffer()
        self.context = Http1xContext(self)

        self.request_before_upgrade = None

        self._task_pool = set()

    def data_received(self, data):  # type: (bytes) -> None
        """数据到达"""

        print(data)

        # 追加到buffer
        self.message_buffer.append(data)

        # 解协议
        err = self.context.parse()
        if err != 0:
            # 解析出错，断开连接
            self.connection.close()

    def eof_received(self):
        """对端关闭"""
        return None

    def lost(self):
        """连接断开"""
        for task in self._task_pool:
            task.cancel()

    def dispatch_request(self, request, callback=None):
        # type: (HttpRequest, Callable[[Task[Optional[HttpResponse]]], Optional[Coroutine[Any, Any, None]]]) -> None
        dispatch_task = self.loop.create_task(self.server.dispatch_request(request))
        self._task_pool.add(dispatch_task)

        def _callback_wrapper(task):  # type: (Task) -> None
            self._task_pool.remove(task)

            if callback is not None:
                if iscoroutinefunction(callback):
                    self.loop.create_task(callback(task))
                else:
                    callback(task)

        dispatch_task.add_done_callback(_callback_wrapper)

    def on_http2_preface(self, request):  # type: (HttpRequest) -> None
        """收到客户端的 http2 连接前言"""

        if self.is_h2:
            self.context = Http2Context(self)

            # send connection preface(server side)
            self.context.send_preface()

            # 解码缓存区剩余数据
            self.context.parse()

            # upgrade from http1.1
            if not self.on_ssl:
                self.context.on_http1_request(self.request_before_upgrade)
                self.request_before_upgrade = None

    def upgrade_http2(self, request):  # type: (HttpRequest) -> bool
        """升级 http2"""

        if not self.on_ssl and request[HttpHeader.UPGRADE] == b"h2c":
            if HttpHeader.HTTP2_SETTINGS in request:
                self.is_h2 = True
                self.request_before_upgrade = request
                return True

        return False
