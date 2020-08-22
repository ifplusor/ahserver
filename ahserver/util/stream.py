# encoding=utf-8

__all__ = ["AsyncStreamIO", "SyncStreamIO"]

import asyncio

from abc import ABCMeta, abstractmethod
from asyncio import Condition as ACondition, Lock as ALock
from io import BytesIO, SEEK_END, SEEK_SET
from six import add_metaclass
from threading import Condition as TCondition, RLock as TLock

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import ByteString, List, Optional


@add_metaclass(ABCMeta)
class StreamIO:
    def __init__(self, initial_bytes):  # type: (Optional[bytes]) -> None
        self._buf = BytesIO(initial_bytes)
        self._pos = 0
        self._has_eof = False

    def auto_reduce(self):
        return self._buf.tell()

    @abstractmethod
    def write(self, b):  # type: (bytes) -> None
        raise NotImplementedError()

    def eof_received(self):
        raise NotImplementedError()


class AsyncStreamIO(StreamIO):
    def __init__(self, initial_bytes=None):  # type: (Optional[bytes]) -> None
        super(AsyncStreamIO, self).__init__(initial_bytes)
        self._alock = ALock()
        self._acond = ACondition(self._alock)
        self._wake_task = None

    async def read(self):
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

    async def _wake_read(self):
        async with self._acond:
            self._acond.notify()

    def _reset_wake_task(self, task):
        if self._wake_task is task:
            self._wake_task = None

    def wake_read(self):
        if self._wake_task is None or self._wake_task.done():
            loop = asyncio.get_event_loop()
            self._wake_task = loop.create_task(self._wake_read())
            self._wake_task.add_done_callback(self._reset_wake_task)

    def write(self, b: bytes):
        self._buf.seek(0, SEEK_END)
        self._buf.write(b)
        self.wake_read()

    def read_eof(self):
        return self._has_eof and self._buf.seek(0, SEEK_END) == self._pos

    def eof_received(self):
        self._has_eof = True
        self.wake_read()


class SyncStreamIO(StreamIO):
    def __init__(self, initial_bytes=None):  # type: (Optional[bytes]) -> None
        super(SyncStreamIO, self).__init__(initial_bytes)
        self._lock = TLock()
        self._cond = TCondition(self._lock)

    def read(self, size=-1):  # type: (int) -> ByteString
        self._cond.acquire()
        try:
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
                    self._cond.wait(timeout=3)
                    self._buf.seek(self._pos, SEEK_SET)
            finally:
                self._pos = self.auto_reduce()
        finally:
            self._cond.release()

    def readline(self, size=-1):  # type: (int) -> ByteString
        self._cond.acquire()
        try:
            self._buf.seek(self._pos, SEEK_SET)
            try:
                data = bytearray()
                while True:
                    b = self._buf.readline(size)
                    data += b
                    if data[-1] == b"\n" or (size != -1 and len(b) >= size) or self._has_eof:
                        return data
                    if size != -1:
                        size -= len(b)

                    self._pos = self.auto_reduce()
                    self._cond.wait()
                    self._buf.seek(self._pos, SEEK_SET)
            finally:
                self._pos = self.auto_reduce()
        finally:
            self._cond.release()

    def readlines(self, hint=-1):  # type: (int) -> List[bytes]
        self._cond.acquire()
        try:
            while not self._has_eof:
                self._cond.wait()
            self._buf.seek(self._pos, SEEK_SET)
            try:
                return self._buf.readlines(hint)
            finally:
                self._pos = self.auto_reduce()
        finally:
            self._cond.release()

    def __iter__(self):
        self._cond.acquire()
        try:
            while not self._has_eof:
                self._cond.wait()
            self._buf.seek(0, SEEK_SET)
            return self
        finally:
            self._cond.release()

    def __next__(self):
        return self._buf.__next__()

    def flush(self):
        self._cond.acquire()
        try:
            self._buf.flush()
        finally:
            self._cond.release()

    def write(self, b):  # type: (bytes) -> None
        self._cond.acquire()
        try:
            self._buf.seek(0, SEEK_END)
            self._buf.write(b)
            self._cond.notify()
        finally:
            self._cond.release()

    def writelines(self, lines):  # type: (List[bytes]) -> None
        self._cond.acquire()
        try:
            self._buf.seek(0, SEEK_END)
            self._buf.writelines(lines)
            self._cond.notify()
        finally:
            self._cond.release()

    def eof_received(self):
        self._cond.acquire()
        try:
            self._has_eof = True
            self._cond.notify()
        finally:
            self._cond.release()
