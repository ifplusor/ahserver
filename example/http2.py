# encoding=utf-8

import asyncio
import logging
import signal
from asyncio.sslproto import SSLProtocol

import uvloop

from ahserver.application.response import DefaultHttpResponse
from ahserver.http2 import HttpRequest, HttpResponse
from ahserver.http2.dispatch import AsyncDispatcher, HttpDispatcher, add_dispatcher
from ahserver.http2.protocol import HttpStatus, PopularHeaders
from ahserver.protocol.http2 import Http2Protocol

logging.basicConfig(level=logging.DEBUG)


class SyncHttpDispatcher(HttpDispatcher):
    def dispatch(self, request: HttpRequest) -> HttpResponse:
        if request.uri == b"/favicon.ico":
            return HttpResponse(request, status=HttpStatus.NOT_FOUND, headers=PopularHeaders.CONTENT_EMPTY)
        elif request.uri == b"/hello":
            return DefaultHttpResponse(request, headers=PopularHeaders.TYPE_PLAIN, body="测试: hello world!\n")
        else:
            return NotImplemented


class AsyncHttpDispatcher(AsyncDispatcher):
    async def dispatch(self, request: HttpRequest) -> HttpResponse:
        logging.debug("before sleep")

        try:
            await asyncio.sleep(3)
        except asyncio.CancelledError as e:
            logging.debug("sleep is cancelled.")
            raise e

        logging.debug("after sleep")
        return DefaultHttpResponse(
            request,
            body="response by async dispatcher for '{}'\n".format(request.uri.decode()),
            headers=PopularHeaders.TYPE_PLAIN,
        )


add_dispatcher(SyncHttpDispatcher())
add_dispatcher(AsyncHttpDispatcher())


loop = None
ssl_context = None


def http_protocol_factory():
    global loop
    return Http2Protocol(loop=loop, is_https=False)


def https_protocol_factory():
    global loop
    global ssl_context
    protocol = Http2Protocol(loop=loop, is_https=True)
    return SSLProtocol(loop=loop, app_protocol=protocol, sslcontext=ssl_context, waiter=None, server_side=True)


def init_ssl():
    global ssl_context

    import ssl

    print("ssl has ALPN: {}".format(ssl.HAS_ALPN))
    print("ssl has NPN: {}".format(ssl.HAS_NPN))

    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile="simple/test.crt", keyfile="simple/test.key")

    if ssl.HAS_ALPN:
        ssl_context.set_alpn_protocols(["http/1.1", "http/1.0"])

    if ssl.HAS_NPN:
        ssl_context.set_npn_protocols(["http/1.1", "http/1.0"])


if __name__ == "__main__":
    enable_https = True

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()

    if enable_https:
        init_ssl()
        server_coro = loop.create_server(protocol_factory=https_protocol_factory, host="127.0.0.1", port=8443)
    else:
        server_coro = loop.create_server(protocol_factory=http_protocol_factory, host="127.0.0.1", port=8080)

    server = loop.run_until_complete(server_coro)

    loop.add_signal_handler(signal.SIGTERM, loop.stop)
    loop.add_signal_handler(signal.SIGINT, loop.stop)

    try:
        loop.run_forever()
    finally:
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()
