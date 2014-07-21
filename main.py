#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os.path

import tornado.web
import tornado.ioloop
import tornado.httpserver

import urls
from init_db import db
from settings import *
from tornado.options import define, options

major = sys.version_info[0]
if major < 3:
    reload(sys)
    sys.setdefaultencoding('utf-8')

define('port', default=8888, help='run on the given port', type=int)

class Application(tornado.web.Application):
    def __init__(self):
        settings = dict(
            static_path = os.path.join(os.path.dirname(__file__), "static"),
            template_path = os.path.join(os.path.dirname(__file__), "templates"),
            autoescape = None,
            site_name = site_name,
            site_url = site_url,
            google_analytics = google_analytics.lstrip(),
            role = {1: 'Member',2: 'Admin',3: 'Lord'},
            cookie_secret = cookie_secret,
            xsrf_cookies = True,
            login_url = "/account/signin",
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
