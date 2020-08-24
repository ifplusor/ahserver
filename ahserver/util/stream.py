# encoding=utf-8

__all__ = ["StreamIO", "InputStreamWrapper"]

import asyncio

from abc import ABCMeta, abstractmethod
from asyncio import Condition as ACondition, Lock as ALock
from io import BytesIO, SEEK_END, SEEK_SET
from six import add_metaclass

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from typing import ByteString, List, Optional, Union


@add_metaclass(ABCMeta)
class StreamIOBase:
    def __init__(self, initial_bytes):  # type: (Optional[bytes]) -> None
        self._buf = BytesIO(initial_bytes)
        self._pos = 0
        self._has_eof = False

    def getvalue(self):
        return self._buf.getvalue()

    def auto_reduce(self):
        return self._buf.tell()

    @abstractmethod
    def write(self, b):  # type: (bytes) -> None
        raise NotImplementedError()

    def eof_received(self):
        raise NotImplementedError()


class StreamIO(StreamIOBase):
    def __init__(self, initial_bytes=None):  # type: (Optional[bytes]) -> None
        super(StreamIO, self).__init__(initial_bytes)
        self._alock = ALock()
        self._acond = ACondition(self._alock)
        self._wake_task = None

    async def at_eof(self):
        return self._has_eof and self._buf.seek(0, SEEK_END) == self._pos

    async def read1(self):
        async with self._acond:
            self._buf.seek(self._pos, SEEK_SET)
            try:
                data = self._buf.read()
                if len(data) <= 0 and not self._has_eof:
                    await self._acond.wait()
                    return self._buf.read()
                return data
            finally:
                self._pos = self.auto_reduce()

    async def read(self, size=-1):
        async with self._acond:
            self._buf.seek(self._pos, SEEK_SET)
            try:
                data = bytearray()
                while True:
                    b = self._buf.read(size)
                    data += b
                    if (size != -1 and len(b) >= size) or self._has_eof:
                        return data
                    if size != -1:
                        size -= len(b)

                    self._pos = self.auto_reduce()
                    await self._acond.wait()
                    self._buf.seek(self._pos, SEEK_SET)
            finally:
                self._pos = self.auto_reduce()

    async def readline(self, size=-1):
        async with self._acond:
            self._buf.seek(self._pos, SEEK_SET)
            try:
                data = bytearray()
                while True:
                    b = self._buf.readline(size)
                    data += b
                    if (len(data) > 0 and data[-1] == b"\n") or (size != -1 and len(b) >= size) or self._has_eof:
                        return data
                    if size != -1:
                        size -= len(b)

                    self._pos = self.auto_reduce()
                    await self._acond.wait()
                    self._buf.seek(self._pos, SEEK_SET)
            finally:
                self._pos = self.auto_reduce()

    async def readlines(self, hint=-1):
        async with self._acond:
            while not self._has_eof:
                await self._acond.wait()
            self._buf.seek(self._pos, SEEK_SET)
            try:
                return self._buf.readlines(hint)
            finally:
                self._pos = self.auto_reduce()

    async def _wake_read(self):
        async with self._acond:
            self._acond.notify()

    def _reset_wake_task(self, task):
        if self._wake_task is task:
            self._wake_task = None

    def wake_read(self):
        if self._wake_task is None or self._wake_task.done():
            loop = asyncio.get_running_loop()
            self._wake_task = loop.create_task(self._wake_read())
            self._wake_task.add_done_callback(self._reset_wake_task)

    def write(self, b):  # type: (Union[bytes, bytearray]) -> None
        """write data in event loop"""
        self._buf.seek(0, SEEK_END)
        self._buf.write(b)
        self.wake_read()

    def eof_received(self):
        self._has_eof = True
        self.wake_read()


class InputStreamWrapper:
    def __init__(self, stream, loop=None):  # type: (StreamIO, AbstractEventLoop) -> None
        self._stream = stream
        self._loop = loop or asyncio.get_running_loop()

    def read(self, size=-1):  # type: (int) -> ByteString
        return asyncio.run_coroutine_threadsafe(self._stream.read(size), self._loop).result()

    def readline(self, size=-1):  # type: (int) -> ByteString
        return asyncio.run_coroutine_threadsafe(self._stream.readline(size), self._loop).result()

    def readlines(self, hint=-1):  # type: (int) -> List[bytes]
        return asyncio.run_coroutine_threadsafe(self._stream.readlines(hint), self._loop).result()

    def __iter__(self):
        return self

    def __next__(self):
        return self.readline()
