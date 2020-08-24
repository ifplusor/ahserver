# encoding=utf-8

__all__ = ["HttpConnection"]

from ..kernel import HttpProtocolStack
from ._connection import Connection

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Callable
    from ..server import HttpServer


class HttpConnection(Connection):
    """http连接

    Connection是对IO和Event Loop的抽象，运行在Event Loop中，将到达的数据和事件传递给协议栈
    """

    def __init__(self, server):  # type: (HttpServer) -> None
        super(HttpConnection, self).__init__()
        self.server = server
        self.protocol_stack = None

    def made(self, close_delegate, send_delegate, selected_protocol):
        # type: (Callable[[], None], Callable[[bytes], None], str) -> None
        """连接建立

        注入委托和连接信息
        """
        super(HttpConnection, self).made(close_delegate, send_delegate, selected_protocol)
        self.protocol_stack = HttpProtocolStack(
            self.server, self, selected_protocol is not None, selected_protocol == "h2"
        )

    def data_received(self, data):  # type: (bytes) -> None
        """数据到达"""
        self.protocol_stack.data_received(data)

    def eof_received(self):
        """对端关闭"""
        return self.protocol_stack.eof_received()

    def lost(self):
        """连接断开"""
        self.protocol_stack.lost()
