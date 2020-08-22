# encoding=utf-8

__all__ = ["Http2Protocol"]

import asyncio
import logging

from asyncio import iscoroutinefunction
from asyncio.protocols import Protocol

try:
    import ssl
except Exception:

    class ssl:
        HAS_ALPN = False
        HAS_NPN = False


from ..http2.dispatch import dispatch_request
from ..http2.h2parser import H2Splitter
from ..http2.protocol import HttpHeader
from ..http2.stream.http1x import Http1xStream
from ..http2.stream.http2 import Http2Stream, Http2SuperStream

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from asyncio import Task
    from asyncio.events import AbstractEventLoop
    from asyncio.transports import Transport
    from typing import Any, Callable, Dict, Optional, Coroutine
    from ..http2 import HttpRequest, HttpResponse
    from ..http2.frame import HttpFrame


logger = logging.getLogger()


class Http2Protocol(Protocol):
    """Http 2.0 协议实现

    Note: 每个 socket 连接 (TCPTransport 对象) 都会创建一个 protocol 实例
    """

    def __init__(self, request_factory, loop=None, is_https=False, is_h2=False):
        # type: (Callable[..., HttpRequest], AbstractEventLoop, bool, bool) -> None
        if loop is None:
            loop = asyncio.get_event_loop()

        self._loop = loop
        self._transport = None
        self._task_pool = set()

        self.is_https = is_https
        self.is_h2 = is_h2
        self.run_on_h2 = False

        self.default_stream = Http1xStream(self, request_factory)

        self.frame_splitter: H2Splitter
        self.stream_table: Dict[int, Http2Stream]

    def connection_made(self, transport):  # type: (Transport) -> None
        """连接建立"""

        logger.debug("connection established")

        # 注入 transport
        self._transport = transport

        # TLS 应用层协议协商
        if self.is_https:
            ssl_object = self._transport.get_extra_info("ssl_object")

            selected = None
            if selected is None and ssl.HAS_ALPN:
                selected = ssl_object.selected_alpn_protocol()
            if selected is None and ssl.HAS_NPN:
                selected = ssl_object.selected_npn_protocol()

            self.is_h2 = selected == "h2"

    def connection_lost(self, exc: Exception):
        """连接断开"""

        logger.debug("connection lost\nexc: %s", exc)

        for task in self._task_pool:
            task.cancel()

    def data_received(self, data: bytes):
        """数据到达"""

        logger.debug(data)

        if self.run_on_h2:
            err = self.frame_splitter.feed(data, len(data))
        else:
            err = self.default_stream.data_received(data)

        if err != 0:
            # 解析出错，断开连接
            self.close()

    def eof_received(self):
        """客户端断开连接"""

        logger.debug("received eof")

        if not self.run_on_h2:
            self.default_stream.eof_received()

    def close(self):
        self._transport.close()

    def frame_received(self, frame):  # type: (HttpFrame) -> int
        stream = self.stream_table.get(frame.identifier)
        if stream is None:
            stream = Http2Stream(self)
            self.stream_table[frame.identifier] = stream
        return stream.frame_received(frame)

    def dispatch_request(self, request, callback=None):
        # type: (HttpRequest, Callable[[Task[Optional[HttpResponse]]], Optional[Coroutine[Any, Any, None]]]) -> None
        dispatch_task = self._loop.create_task(dispatch_request(request))
        self._task_pool.add(dispatch_task)

        def _callback_wrapper(task):  # type: (Task) -> None
            self._task_pool.remove(task)

            if self._transport.is_closing():
                # when transport is closed, pass
                logger.debug("transport is closed, abort response.")
                return

            if callback is not None:
                if iscoroutinefunction(callback):
                    self._loop.create_task(callback(task))
                else:
                    callback(task)

        dispatch_task.add_done_callback(_callback_wrapper)

    def send_data(self, data: bytes):
        self._transport.write(data)

    def http_upgrade2(self, request):  # type: (HttpRequest) -> bool
        """http 升级"""

        if not self.is_https and request[HttpHeader.UPGRADE] == b"h2c":
            if HttpHeader.HTTP2_SETTINGS in request:
                self.is_h2 = True
                return True

        return False

    def on_http2_preface(self, request):  # type: (HttpRequest) -> None
        """收到客户端的 http2 连接前言"""

        if self.is_h2 and not self.run_on_h2:
            self.frame_splitter = H2Splitter(self.frame_received)
            self.stream_table = dict()
            self.stream_table[0] = Http2SuperStream(self)

            # 启动 http 2.0 splitter
            self.run_on_h2 = True

            # 将 default_stream 缓存区剩余数据写入 frame_splitter
            remain = self.default_stream.parser.take_buffer()
            self.frame_splitter.feed(remain, len(remain))
