# encoding=utf-8

__all__ = ["AsyncPipe"]

from asyncio import Queue


class AsyncPipe:
    def __init__(self, maxsize=3):
        self._queue = Queue(maxsize=maxsize)

    async def close(self):
        await self._queue.put(None)

    async def write(self, data):
        if data is not None:
            await self._queue.put(data)

    async def read(self):
        return await self._queue.get()

    def __aiter__(self):
        return self

    async def __anext__(self):
        body = await self.read()
        if body is None:
            raise StopAsyncIteration
        return body
