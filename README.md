# AHServer

AHServer is a lightweight asynchronous http server, implement both WSGI and ASGI specifications.

## Example

### WSGI: Flash

```python
# encoding=utf-8

if __name__ == "__main__":
    import asyncio
    import uvloop

    from ahserver.wsgi import server

    # 设置 uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    # 启动服务
    server(__file__ + ":app", worker_nums=1)
else:

    def create_application():
        from flask import Flask, Response, request

        app = Flask(__name__)

        @app.route("/hello")
        def hello_world():
            return Response("Hello, welcome to Flask world!\n", mimetype="text/plain")

        @app.route("/post", methods=["POST"])
        def get_user_posts():
            data = request.get_data()
            return data

        return app.wsgi_app

    app = create_application()

```

### ASGI: FastAPI

```python
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

```

## CLI

### WSGI: ahwsgi

```text
Usage: ahwsgi [options] module:callable

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -H HOST, --addr=HOST  listen address
  -P PORT, --port=PORT  listen port
  -n NUM, --worker-nums=NUM
                        worker number
  -t NUM, --thread-nums=NUM
                        thread number
  --https               enable https mode
  --cert-path=PATH      cert file path
  --key-path=PATH       key file path
  --disable-uvloop      diable uvloop
```

### ASGI: ahasgi

```text
Usage: ahasgi [options] module:callable

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -H HOST, --addr=HOST  listen address
  -P PORT, --port=PORT  listen port
  -n NUM, --worker-nums=NUM
                        worker number
  --https               enable https mode
  --cert-path=PATH      cert file path
  --key-path=PATH       key file path
  --disable-uvloop      diable uvloop
```
