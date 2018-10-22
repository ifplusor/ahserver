# encoding=utf-8

import asyncio
import logging
import signal

import uvloop

from ahserver.http2 import HttpRequest, HttpResponse
from ahserver.http2.dispatchs import add_dispatcher, HttpDispatcher, AsyncDispatcher
from ahserver.protocols.http2 import Http2Protocol

logging.basicConfig(level=logging.DEBUG)


class SyncHttpDispatcher(HttpDispatcher):

    def dispatch(self, request: HttpRequest):
        if request.uri == b"/hello":
            return HttpResponse(request, body="hello world!")
        else:
            return NotImplemented


class AsyncHttpDispatcher(AsyncDispatcher):

    async def dispatch(self, request: HttpRequest):
        logging.debug('before sleep')

        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError as e:
            logging.debug('sleep is cancelled.')
            raise e

        logging.debug('after sleep')
        return HttpResponse(request, body="this is async dispatcher")


add_dispatcher(SyncHttpDispatcher())
add_dispatcher(AsyncHttpDispatcher())

if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()

    server_coro = loop.create_server(protocol_factory=lambda: Http2Protocol(loop), host="127.0.0.1", port=8080)
    server = loop.run_until_complete(server_coro)

    loop.add_signal_handler(signal.SIGTERM, loop.stop)
    loop.add_signal_handler(signal.SIGINT, loop.stop)

    try:
        loop.run_forever()
    finally:
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()
