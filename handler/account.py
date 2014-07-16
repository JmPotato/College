#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import hashlib

import tornado.web

from . import BaseHandler

class SignupHandler(BaseHandler):
    def get(self):
        if self.get_current_user():
            self.redirect('/')
        self.render('account/signup.html')

    def post(self):
        pass

class SigninHandler(BaseHandler):
    def get(self):
        if self.get_current_user():
            self.redirect('/')
        self.render('account/signin.html')

    def post(self):
        pass

class SignoutHandler(BaseHandler):
    def get(self):
        name = self.get_argument('user', None)
        if self.get_current_user()['name'] != name:
            raise tornado.web.HTTPError(403)
        self.clear_all_cookie()
        self.redirect('/')

class SettingsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        pass

    @tornado.web.authenticated
    def post(self):
        pass

class NotificationsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        pass

class NotificationsClearHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.db.notifications.remove({'to': self.current_user['name_lower']})
        self.redirect('/')

class NotificationsRemoveHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, id):
        self.db.notifications.remove({'_id': ObjectId(id)})
        self.redirect(self.get_argument('next', '/account/notifications'))

handlers = [
    (r'/account/signup', SignupHandler),
    (r'/account/signin', SigninHandler),
    (r'/account/signout', SignoutHandler),
    (r'/account/settings', SettingsHandler),
    (r'/account/notifications', NotificationsHandler),
    (r'/account/notifications/clear', NotificationsClearHandler),
    (r'/account/notifications/(\w+)/remove', NotificationsRemoveHandler),
]