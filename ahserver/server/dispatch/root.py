# encoding=utf-8

__all__ = ["RootDispatcher"]

import logging

from asyncio import CancelledError

from ..protocol import HttpStatus, PopularHeaders
from ..response import HttpResponse
from ._dispatcher import HttpDispatcher

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import List, Optional
    from ..request import HttpRequest


class RootDispatcher(HttpDispatcher):
    """根调度器.

    以职责链模式处理 http 请求
    """

    def __init__(self):
        super(RootDispatcher, self).__init__()
        # 职责链
        self.dispatchers = list()  # type: List[HttpDispatcher]

    def add_dispatcher(self, dispatcher):  # type: (HttpDispatcher) -> None
        self.dispatchers.append(dispatcher)

    async def dispatch(self, request):  # type: (HttpRequest) -> Optional[HttpResponse]
        # 为支持异步 http 路由，根调调度器需要异步环境

        for dispatcher in self.dispatchers:
            # 职责链需要顺序阻塞调用
            try:
                resp = await dispatcher.dispatch(request)
            except CancelledError as e:
                # re-raise CancelledError, and process in Http1xStream._send_response.
                raise e
            except Exception:
                logging.exception("encounter unexpected exception")
                resp = HttpResponse(request, HttpStatus.INTERNAL_SERVER_ERROR, PopularHeaders.CONNECTION_CLOSE)

            if resp is not NotImplemented:
                break
        else:
            # report 404
            resp = HttpResponse(request, HttpStatus.NOT_FOUND, PopularHeaders.CONNECTION_CLOSE)

        return resp
