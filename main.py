#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urls
import os.path
import tornado.web

from init_db import db
from tornado.options import define, options

define('port', default=8888, help='run on the given port', type=int)

class Application(tornado.web.Application):
    def __init__(self):
        settings = dict(
            static_path = os.path.join(os.path.dirname(__file__), "static"),
            template_path = os.path.join(os.path.dirname(__file__), "templates"),
            autoescape = None,
            blog_name = site_name,
            blog_url = site_url,
            role = {3: 'Member',2: 'Admin',1: 'Lord'},
            cookie_secret = cookie_secret,
            login_url = "/login",
            debug = Debug,
        )
        tornado.web.Application.__init__(self, urls.handlers, **settings)

        self.db = db

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()