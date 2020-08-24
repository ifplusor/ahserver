# encoding=utf-8

__all__ = ["server"]

import multiprocessing
import os
import signal
import socket
import sys


signames = {int(v): v.name for _, v in signal.__dict__.items() if isinstance(v, signal.Signals)}


def create_ssl_context(certfile, keyfile):
    import ssl

    print("ssl has ALPN: {}".format(ssl.HAS_ALPN))
    print("ssl has NPN: {}".format(ssl.HAS_NPN))

    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile=certfile, keyfile=keyfile)

    if ssl.HAS_ALPN:
        ssl_context.set_alpn_protocols(["h2", "http/1.1", "http/1.0"])

    if ssl.HAS_NPN:
        ssl_context.set_npn_protocols(["h2", "http/1.1", "http/1.0"])

    return ssl_context


def server(app, host="127.0.0.1", port=8080, worker_nums=1, enable_https=False, certfile=None, keyfile=None, loop=None):

    kwargs = {"app": app, "host": host, "port": port, "loop": loop}

    if enable_https:
        kwargs["ssl_context"] = create_ssl_context(certfile=certfile, keyfile=keyfile)

    # create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    kwargs["sock"] = sock

    if worker_nums <= 1:  # single-process
        serve(**kwargs)
    else:  # multi-process
        os.set_inheritable(sock.fileno(), True)  # 子进程继承 socket

        workers = set()
        terminating = False

        def stop(sig, frame):
            nonlocal terminating  # nonlocal允许在内嵌的函数中修改闭包变量

            if not terminating:
                terminating = True
                print("Termination request received")

            for w in workers:
                w.terminate()

        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)

        # 创建 worker 子进程
        for _ in range(1):
            worker = multiprocessing.Process(target=serve, kwargs=kwargs)
            worker.daemon = True
            worker.start()
            workers.add(worker)

        sock.close()  # 父进程要主动关闭 socket

        for worker in workers:
            worker.join()

            if worker.exitcode > 0:
                print("Worker exited with code {}".format(worker.exitcode))
            elif worker.exitcode < 0:
                try:
                    signame = signames[-worker.exitcode]
                    print("Worker crashed on signal {}!".format(signame))
                except KeyError:
                    print("Worker crashed with unknown code {}!".format(worker.exitcode))


def import_application(path):
    module_path, object_path = path.split(":", 1)
    try:
        target = __import__(module_path)
    except ModuleNotFoundError as e:
        if os.path.exists(module_path):
            file_path = os.path.abspath(module_path)
            dir_path = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1]
            if file_ext != ".py":
                raise e
            module_name = file_name[: -len(file_ext)]
            if dir_path not in sys.path:
                sys.path.insert(0, dir_path)
            target = __import__(module_name)
        else:
            raise e
    for bit in object_path.split("."):
        target = getattr(target, bit)
    return target


def serve(app, host, port, sock, ssl_context=None, loop=None):
    import asyncio
    from ahserver.server import HttpServer
    from ahserver.network.asyncio import HttpProtocolFactory
    from .dispatch import ASGIDispatcher

    if isinstance(app, str):
        app = import_application(app)

    if loop is None:
        loop = asyncio.get_event_loop()

    http_server = HttpServer()
    http_server.add_dispatcher(ASGIDispatcher(loop, app, host, port, on_https=ssl_context is not None))

    protocol_factory = HttpProtocolFactory(http_server, ssl_context)

    # 创建 TCP Server
    if sock is None:
        server_coro = loop.create_server(protocol_factory=protocol_factory, host=host, port=port)
    else:
        server_coro = loop.create_server(protocol_factory=protocol_factory, sock=sock)
    server = loop.run_until_complete(server_coro)

    loop.add_signal_handler(signal.SIGTERM, loop.stop)
    loop.add_signal_handler(signal.SIGINT, loop.stop)

    try:
        loop.run_forever()
    finally:
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()
