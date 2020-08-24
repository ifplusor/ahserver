# encoding=utf-8

if __name__ == "__main__":
    import asyncio
    import os
    import uvloop

    from ahserver.application.wsgi import server

    # 设置 uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    # 启动服务
    server(
        __file__ + ":app",
        # port=8080,
        port=8443,
        worker_nums=1,
        enable_https=True,
        certfile=os.path.join(os.path.dirname(__file__), "test.crt"),
        keyfile=os.path.join(os.path.dirname(__file__), "test.key"),
    )
else:

    def create_application():
        from flask import Flask, Response, request

        app = Flask(__name__)

        @app.route("/hello")
        def hello_world():
            return Response("Hello, welcome to Flask world!\n", mimetype="text/plain")

        @app.route("/post", methods=["POST"])
        def get_user_post():
            data = request.get_data()
            return data

        @app.route("/stream")
        def return_stream():
            def generate():
                yield "hello, "
                yield "world! "
                yield "from stream"

            return Response(generate())

        return app.wsgi_app

    app = create_application()
