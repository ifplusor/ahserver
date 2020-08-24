# encoding=utf-8

__all__ = ["HttpProtocol", "HttpProtocolFactory"]

import asyncio

from asyncio.protocols import Protocol
from asyncio.sslproto import SSLProtocol

try:
    import ssl
except Exception:

    class ssl:
        HAS_ALPN = False
        HAS_NPN = False


try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from asyncio.transports import Transport
    from ssl import SSLContext
    from ..server.connection import Connection
    from ..server.server import HttpServer


class HttpProtocol(Protocol):
    """Http 协议实现

    Note: 每个 socket 连接 (TCPTransport 对象) 都会创建一个 protocol 实例
    """

    def __init__(self, connection, on_ssl=False):
        # type: (Connection, bool) -> None
        self.connection = connection
        self.on_ssl = on_ssl
        self._transport = None

    def connection_made(self, transport):  # type: (Transport) -> None
        """连接建立"""

        # 注入 transport
        self._transport = transport

        # TLS 应用层协议协商
        if self.on_ssl:
            ssl_object = self._transport.get_extra_info("ssl_object")

            selected = None
            if selected is None and ssl.HAS_ALPN:
                selected = ssl_object.selected_alpn_protocol()
            if selected is None and ssl.HAS_NPN:
                selected = ssl_object.selected_npn_protocol()
        else:
            selected = None

        return self.connection.made(transport.close, transport.write, selected)

    def connection_lost(self, exc):  # type: (Exception) -> None
        """连接断开"""
        return self.connection.lost()

    def data_received(self, data):  # type: (bytes) -> None
        """数据到达"""
        return self.connection.data_received(data)

    def eof_received(self):
        """客户端断开连接"""
        return self.connection.eof_received()

    def close(self):
        self._transport.close()


class HttpProtocolFactory:
    def __init__(self, server, ssl_context=None):  # type: (HttpServer, SSLContext) -> None
        self.server = server
        self.ssl_context = ssl_context

    def create_protocol(self):  # type: () -> Protocol
        connection = self.server.new_connection()
        if self.ssl_context is not None:
            protocol = HttpProtocol(connection, on_ssl=True)
            protocol = SSLProtocol(
                loop=asyncio.get_running_loop(),
                app_protocol=protocol,
                sslcontext=self.ssl_context,
                waiter=None,
                server_side=True,
            )
        else:
            protocol = HttpProtocol(connection, on_ssl=False)
        return protocol

    def __call__(self):  # type: () -> Protocol
        return self.create_protocol()
