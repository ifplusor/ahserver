# encoding=utf-8

if __name__ == "__main__":
    import asyncio
    import os
    import uvloop

    from ahserver.application.asgi import server

    # 设置 uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    # 启动服务
    server(
        __file__ + ":app",
        port=8080,
        # port=8443,
        worker_nums=1,
        # enable_https=True,
        certfile=os.path.join(os.path.dirname(__file__), "test.crt"),
        keyfile=os.path.join(os.path.dirname(__file__), "test.key"),
    )
else:

    def create_application():
        from typing import Optional
        from fastapi import FastAPI, Body

        app = FastAPI()

        @app.get("/")
        def read_root():
            return {"Hello": "World"}

        @app.get("/items/{item_id}")
        def read_item(item_id: int, q: Optional[str] = None):
            return {"item_id": item_id, "q": q}

        @app.post("/post")
        def read_body(body=Body(...)):
            return body

        return app

    app = create_application()
