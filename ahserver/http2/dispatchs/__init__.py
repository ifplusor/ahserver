# encoding=utf-8

__all__ = ["HttpDispatcher", "AsyncDispatcher", "RDispatcher", "add_dispatcher"]

from ..protocol import HttpStatus
from ..request import HttpRequest
from ..response import HttpResponse


class HttpDispatcher:

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        return NotImplemented


class AsyncDispatcher(HttpDispatcher):

    async def dispatch(self, request: HttpRequest) -> HttpDispatcher:
        return NotImplemented


class RootDispatcher(AsyncDispatcher):
    """根调度器.

    以职责链模式处理 http 请求
    """

    def __init__(self):
        super().__init__()
        self.dispatchers = list()  # 职责链

    def add_dispatcher(self, dispatcher: HttpDispatcher):
        self.dispatchers.append(dispatcher)

    async def dispatch(self, request):
        # 为支持异步 http 路由，根调调度器需要异步环境

        for dispatcher in self.dispatchers:
            # 职责链需要顺序阻塞调用
            if isinstance(dispatcher, AsyncDispatcher):
                resp = await dispatcher.dispatch(request)
            else:
                resp = dispatcher.dispatch(request)

            if resp != NotImplemented:
                break
        else:
            # report 404
            resp = HttpResponse(request, HttpStatus.Not_Found, {"Connection": "close"})

        return resp


RDispatcher = RootDispatcher()


def add_dispatcher(dispatcher: HttpDispatcher):
    RDispatcher.add_dispatcher(dispatcher)
