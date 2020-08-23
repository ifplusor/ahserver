# encoding=utf-8

if __name__ == "__main__":
    import asyncio
    import uvloop

    from ahserver.asgi import server

    # 设置 uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    # 启动服务
    server(__file__ + ":app", worker_nums=1)
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
