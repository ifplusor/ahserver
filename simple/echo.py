# encoding=utf-8

import asyncio
import signal
import uvloop
from ahserver.protocols.echo import EchoProtocol


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()

    server_coro = loop.create_server(protocol_factory=EchoProtocol, host="127.0.0.1", port=8080)
    server = loop.run_until_complete(server_coro)

    loop.add_signal_handler(signal.SIGTERM, loop.stop)
    loop.add_signal_handler(signal.SIGINT, loop.stop)

    try:
        loop.run_forever()
    finally:
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()
