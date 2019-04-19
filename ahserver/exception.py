# encoding=utf-8

__all__ = [
    "AHServerException",
    "AHServerConnectionError",
    "AHServerProtocolError",
]


class AHServerException(Exception):
    pass


class AHServerConnectionError(AHServerException):
    pass


class AHServerProtocolError(AHServerConnectionError):
    pass
