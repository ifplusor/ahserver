# encoding=utf-8

__all__ = ["Http2Protocol"]

import logging
import os
from asyncio import Task, CancelledError
from asyncio.protocols import Protocol

from uvloop.loop import Loop, TCPTransport

from ..http2.dispatchs import RDispatcher
from ..http2.h2parser import H2Parser
from ..http2.request import HttpRequest

# settings from env
print_request = os.getenv("ahserver_request_print", "false").lower() == "true"
print_response = os.getenv("ahserver_response_print", "false").lower() == "true"

logger = logging.getLogger()


class Http2Protocol(Protocol):
    """Http 协议栈实现

    Note: 每个 socket 连接 (TCPTransport 对象) 都会创建一个 protocol 实例
    """

    def __init__(self, loop: Loop):
        self.loop = loop
        self.transport = None
        self.parser = H2Parser(self.on_message)
        self.task_pool = set()

    def connection_made(self, transport: TCPTransport):
        # 注入 transport
        logger.debug("connection established")
        self.transport = transport

    def connection_lost(self, exc):
        # 连接断开
        logger.debug("connection lost\nexc: %s", exc)

        for task in self.task_pool:
            task.cancel()

    def data_received(self, data):
        # 数据到达

        # logger.debug(data)

        # 递送给 parser 解协议
        err = self.parser.feed(data, len(data))
        if err:
            # 解析出错，断开连接
            self.transport.close()

    def eof_received(self):
        # 客户端断开连接
        logger.debug("received eof")

        # 递送给 parser 解协议
        if self.parser.feed_eof():
            self.transport.close()

    def on_message(self, request: HttpRequest):
        # 收到 http 请求

        if print_request:
            logger.info(request)
            if request.body is not None:
                logger.info("Body: [{}]\n{}\n".format(len(request.body), request.body))

        # dispatch request
        dispatch_task = self.loop.create_task(RDispatcher.dispatch(request))
        self.task_pool.add(dispatch_task)
        dispatch_task.add_done_callback(self.send_response)

    def send_response(self, task: Task):
        # 回复 http 响应

        self.task_pool.remove(task)

        if self.transport.is_closing():
            # when transport is closed, pass
            logger.debug('transport is closed, abort response.')
            return

        try:
            response = task.result()

            # write response
            # logger.debug('write response')
            resp_msg = response.render()

            if print_response:
                logger.info(resp_msg)

            self.transport.write(resp_msg)

            if response.will_close():
                self.transport.close()

        except CancelledError:
            logging.debug('task is cancelled.')
        except Exception:
            logger.exception("encounter exception.")

        self.parser.free()
