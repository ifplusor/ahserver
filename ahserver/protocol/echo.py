# encoding=utf-8

from asyncio.protocols import Protocol
from uvloop.loop import TCPTransport


class EchoProtocol(Protocol):
    def __init__(self):
        self.transport = None

    def connection_made(self, transport: TCPTransport):
        print("connect established")
        self.transport = transport

    def connection_lost(self, exc):
        print("connect lost")
        print(exc)

    def data_received(self, data):
        print(type(data))
        self.transport.write(data)

    def eof_received(self):
        print("received eof")
