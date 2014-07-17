#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import time
import hashlib

import tornado.web

from . import BaseHandler

username_validator = re.compile(r'^[a-zA-Z0-9]+$')
email_validator = re.compile(r'^.+@[^.].*\.[a-z]{2,10}$', re.IGNORECASE)

class SignupHandler(BaseHandler):
    def get(self):
        if self.get_current_user():
            self.redirect(self.get_argument('next', '/'))
        self.render('account/signup.html')

    def post(self):
        username = self.get_argument('username', None)
        email = self.get_argument('email', None)
        password = self.get_argument('password', None)
        r_password = self.get_argument('r_password', None)
        if not (username and email and password and r_password):
            self.send_message("请完整填写信息")
        if password != r_password:
            self.send_message("两次输入的密码不匹配")
        if email and not email_validator.match(email):
            self.send_message("请输入有效的邮箱")
        if username and not username_validator.match(username):
            self.send_message("请输入有效的用户名")
        if username and self.db.users.find_one({'name_lower': username.lower()}):
            self.send_message('用户名已被注册')
        if email and self.db.users.find_one({'email': email}):
            self.send_message('邮箱已被注册')
        if self.messages:
            self.render('account/signup.html')
        token = hashlib.sha1(password + username.lower()).hexdigest()
        role = 3
        if not self.db.users.count():
            role = 1
        self.db.users.insert({
            'name': username,
            'name_lower': username.lower(),
            'token': token,
            'email': email,
            'website': '',
            'description': '',
            'created': time.time(),
            'role': role,
            'like': [],
            'follow': [],
            'favorite': [],
        })
        self.set_secure_cookie('token', token, expires_days=30)
        self.redirect(self.get_argument('next', '/'))

class SigninHandler(BaseHandler):
    def get(self):
        if self.get_current_user():
            self.redirect(self.get_argument('next', '/'))
        self.render('account/signin.html')

    def post(self):
        username = self.get_argument('username', '').lower()
        password = self.get_argument('password', None)
        if not (username and password):
            self.send_message("请完整填写信息")
        token = hashlib.sha1(password + username.lower()).hexdigest()
        user = self.db.users.find_one({'name_lower': username, 'token': token})
        if not user:
            self.send_message('无效的账户或密码')
            self.render('account/signin.html')
            return
        self.set_secure_cookie('token', token, expires_days=30)
        self.redirect(self.get_argument('next', '/'))

class SignoutHandler(BaseHandler):
    def get(self):
        name = self.get_argument('user', None)
        if self.get_current_user()['name'] != name:
            raise tornado.web.HTTPError(403)
        self.clear_all_cookies()
        self.redirect(self.get_argument('next', '/'))

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
        self.db.notifications.remove({'to': self.get_current_user()['name_lower']})
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