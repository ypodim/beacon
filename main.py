 
import asyncio
import tornado.web
import tornado.websocket
import os
import json
import datetime

import random


class Store(object):
    def __init__(self, name):
        self.name = name.strip()
        self._store = {}
        self.buffer = []
        self.filename = "data_%s.json" % self.name
        print("store for %s created" % self.name)

    def load(self):
        pass

    def save(self, entry):
        pass

    def set(self, key, value):
        self._store[key] = value
    def get(self, key):
        return self._store.get(key)

class DefaultHandler(tornado.web.RequestHandler):
    def initialize(self, manager):
        self.manager = manager
    def get(self):
        self.render("index.html")
    def post(self):
        data = json.loads(self.request.body)
        self.manager.set("temperature", data.get("temperature"))
        self.write(dict(result="ok"))


class AHandler(tornado.web.RequestHandler):
    def initialize(self, manager):
        self.manager = manager
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
    def options(self, *args):
        # no body
        # `*args` is for route with `path arguments` supports
        self.set_status(204)
        self.finish()
    def get(self):
        self.write(dict(response=self.manager.get("temperature")))

class LiveSocket(tornado.websocket.WebSocketHandler):
    clients = set()
    def initialize(self, manager):
        self.manager = manager

    def open(self):
        LiveSocket.clients.add(self)

    def on_message(self, message):
        # self.write_message(u"You said: " + message)
        print("got", message)

    def on_close(self):
        LiveSocket.clients.remove(self)

    @classmethod
    def send_message(cls, message: str):
        # print(f"Sending message {message} to {len(cls.clients)} client(s).")
        for client in cls.clients:
            client.write_message(message)


class Application(tornado.web.Application):
    def __init__(self, manager):
        handlers = [
            (r"/ws", LiveSocket, dict(manager=manager)),
            (r'/favicon.ico', tornado.web.StaticFileHandler),
            (r'/static/', tornado.web.StaticFileHandler),
            (r"/a", AHandler, dict(manager=manager)),
            (r"/.*", DefaultHandler, dict(manager=manager)),

        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "html"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            login_url="/auth/login",
            debug=True,
        )
        super(Application, self).__init__(handlers, **settings)


async def main():
    manager = Store("filename")
    app = Application(manager)
    http_server = tornado.httpserver.HTTPServer(app, ssl_options={
        "certfile": "/home/pol/ws/beacon/keys/node.polychronis.gr.pem",
        "keyfile": "/home/pol/ws/beacon/keys/node.polychronis.gr-key.pem",
    })
    http_server.listen(443)
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("exiting")
