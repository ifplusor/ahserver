# encoding=utf-8

__all__ = ["Connection"]

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Callable


def _close():  # type: () -> None
    raise NotImplementedError()


def _send(data):  # type: (bytes) -> None
    raise NotImplementedError()


class Connection:
    def __init__(self):  # type: () -> None
        self.close = _close
        self.send = _send

    def made(self, close_delegate, send_delegate, selected_protocol=None):
        # type: (Callable[[], None], Callable[[bytes], None], str) -> None
        """连接建立"""
        self.close = close_delegate
        self.send = send_delegate

    def data_received(self, data):  # type: (bytes) -> None
        """数据到达"""
        pass

    def eof_received(self):
        """对端关闭"""
        return None

    def lost(self):
        """连接断开"""
        pass
