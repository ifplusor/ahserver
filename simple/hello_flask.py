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
        from flask import Flask, Response

        app = Flask(__name__)

        @app.route("/hello")
        def hello_world():
            return Response("Hello world from Flask!\n", mimetype="text/plain")

        return app.wsgi_app

    app = create_application()