#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import hashlib
import tornado.web

from . import BaseHandler

class SignupHandler(BaseHandler):
    def get(self):
        pass

    def post(self):
        pass

class SigninHandler(BaseHandler):
    def get(self):
        pass

    def post(self):
        pass

class SignoutHandler(BaseHandler):
    def get(self):
        pass

    def post(self):
        pass

class SettingsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        pass

    @tornado.web.authenticated
    def post(self):
        pass
