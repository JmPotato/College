#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.web

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        pass

    def get_source(self):
        pass
