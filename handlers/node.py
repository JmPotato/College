#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.web
from . import BaseHandler

class NodeListHandler(BaseHandler):
    def get(self):
        nodes = self.db.nodes.find()
        self.render('node/list.html', nodes = nodes)

class AddHandler(BaseHandler):
    def get(self):
        pass

class NodeHandler(BaseHandler):
    def get(self):
        pass

class EditHandler(BaseHandler):
    def get(self):
        pass

class RemoveHandler(BaseHandler):
    def get(self):
        pass

handlers = [
    (r'/node', NodeListHandler),
    (r'/node/add', AddHandler),
    (r'/node/([%A-Za-z0-9.-]+)', NodeHandler),
    (r'/node/([%A-Za-z0-9.-]+)/edit', EditHandler),
    (r'/node/([%A-Za-z0-9.-]+)/remove', RemoveHandler),
]