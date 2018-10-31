# encoding=utf-8
from asyncio import CancelledError

__all__ = ["HttpDispatcher", "AsyncDispatcher", "RDispatcher", "add_dispatcher"]

from ..protocol import HttpStatus, PopularHttpHeaders
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
            try:
                if isinstance(dispatcher, AsyncDispatcher):
                    resp = await dispatcher.dispatch(request)
                else:
                    resp = dispatcher.dispatch(request)
            except CancelledError as e:
                raise e
            except Exception as e:
                resp = HttpResponse(request, HttpStatus.Internal_Server_Error, PopularHttpHeaders.connection_close)

            if resp != NotImplemented:
                break
        else:
            # report 404
            resp = HttpResponse(request, HttpStatus.Not_Found, PopularHttpHeaders.connection_close)

        return resp


RDispatcher = RootDispatcher()


def add_dispatcher(dispatcher: HttpDispatcher):
    RDispatcher.add_dispatcher(dispatcher)
