# encoding=utf-8

import asyncio
import optparse

from .server import server
from .. import __version__


def main(args=None):
    # 验证并解析参数
    usage = "usage: %prog [options] module:callable"
    parser = optparse.OptionParser(usage=usage, version=__version__)

    # basic params
    parser.add_option("-H", "--addr", dest="host", metavar="HOST", default="localhost", help="listen address")
    parser.add_option("-P", "--port", dest="port", metavar="PORT", default=8080, type="int", help="listen port")
    parser.add_option(
        "-n", "--worker-nums", dest="worker_nums", metavar="NUM", default=1, type="int", help="worker number"
    )

    # ssl params
    parser.add_option("--https", dest="enable_https", action="store_true", default=False, help="enable https mode")
    parser.add_option("--cert-path", dest="certfile", metavar="PATH", help="cert file path")
    parser.add_option("--key-path", dest="keyfile", metavar="PATH", help="key file path")

    # other params
    parser.add_option(
        "--disable-uvloop", dest="disable_uvloop", action="store_true", default=False, help="diable uvloop"
    )

    options, args = parser.parse_args(args=args)

    if len(args) != 1:
        parser.print_help()

    if not options.disable_uvloop:
        import uvloop

        # 设置 uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    server(
        app=args[0],
        host=options.host,
        port=options.port,
        worker_nums=options.worker_nums,
        enable_https=options.enable_https,
        certfile=options.certfile,
        keyfile=options.keyfile,
    )


if __name__ == "__main__":
    main()
