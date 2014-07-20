#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import time
import hashlib

import tornado.web

from . import BaseHandler
from bson.objectid import ObjectId

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
            self.send_message('请完整填写信息喵')
        if password != r_password:
            self.send_message('两次输入的密码都不一样，你脑子瓦特了？')
        if email and not email_validator.match(email):
            self.send_message('请输入有效的邮箱，要不然伦家怎么给你联系（捂脸')
        if username and not username_validator.match(username):
            self.send_message('起个正常点的英文名......别想搞非主流')
        if username and self.db.users.find_one({'name_lower': username.lower()}):
            self.send_message('真不巧，你的用户名被人抢先了')
        if email and self.db.users.find_one({'email': email}):
            self.send_message('邮箱已被注册')
        if self.messages:
            self.render('account/signup.html')
            return
        token = hashlib.sha1(password + username.lower()).hexdigest()
        role = 1
        if not self.db.users.count():
            role = 3
        self.db.users.insert({
            'name': username,
            'name_lower': username.lower(),
            'avatar_url': '',
            'avatar_name': '',
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
            self.send_message('请完整填写信息喵')
        token = hashlib.sha1(password + username.lower()).hexdigest()
        user = self.db.users.find_one({'name_lower': username, 'token': token})
        if not user:
            self.send_message('查无此喵（无效的账户或密码）')
            self.render('account/signin.html')
            return
        self.set_secure_cookie('token', token, expires_days=30)
        self.redirect(self.get_argument('next', '/'))

class SignoutHandler(BaseHandler):
    def get(self):
        self.clear_all_cookies()
        self.redirect('/')

class SettingsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('account/settings.html')

    @tornado.web.authenticated
    def post(self):
        website = self.get_argument('website', '')
        description = self.get_argument('description', '')
        if len(description) > 1500:
            self.send_message('你这是要写自传的节奏嘛，简介太长了！')
        self.db.users.update({'_id': self.current_user['_id']}, {'$set': {
            'website': website,
            'description': description,
        }})
        self.send_message('修改成功', type='success')
        self.redirect('/account/settings')

class ChangeAvatarHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        try:
            file_metas = self.request.files['avatar_file'][0]
        except:
            self.send_message('头像半路走丢了，再试一次吧')
            self.render('account/settings.html')
            return
        with open(file_metas['filename'], 'w') as f:
            f.write(file_metas['body'])
        if not self.upload_avatar(self.current_user, file_metas['filename'], file_metas['filename']):
            os.remove(file_metas['filename'])
            self.send_message('头像上传失败')
            self.render('account/settings.html')
            return
        os.remove(file_metas['filename'])
        self.send_message('头像更换成功', type='success')
        self.redirect('/account/settings')

class ChangePasswordHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        old_password = self.get_argument('old_password', None)
        new_password = self.get_argument('new_password', None)
        if not (old_password and new_password):
            self.send_message('请完整填写信息喵')
        key = old_password + self.current_user['name'].lower()
        password = hashlib.sha1(key).hexdigest()
        if password != self.current_user['token']:
            self.send_message('密码错误！')
        if self.messages:
            self.redirect('/account/settings')
            return
        key = new_password + self.current_user['name'].lower()
        token = str(hashlib.sha1(key).hexdigest())
        self.db.users.update({'_id': self.current_user['_id']},
                               {'$set': {'token': token}})
        self.set_secure_cookie('token', token, expires_days=30)
        self.send_message('修改成功', type='success')
        self.redirect('/account/settings')

class NotificationsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        p = int(self.get_argument('p', 1))
        notis = self.db.notifications.find({
            'to': self.current_user['name_lower']
        }, sort=[('created', -1)])
        notis_count = notis.count()
        per_page = 20
        notis = notis[(p - 1) * per_page:p * per_page]
        self.render('account/notifications.html', notis=notis,
                    notis_count=notis_count, p=p)

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

class CodeHandler(BaseHandler):
    def get(self):
        self.check_role()
        code = self.generate_invitation()
        self.write(code)

handlers = [
    (r'/invite/code', CodeHandler),
    (r'/account/signup', SignupHandler),
    (r'/account/signin', SigninHandler),
    (r'/account/signout', SignoutHandler),
    (r'/account/settings', SettingsHandler),
    (r'/account/avatar', ChangeAvatarHandler),
    (r'/account/password', ChangePasswordHandler),
    (r'/account/notifications', NotificationsHandler),
    (r'/account/notifications/clear', NotificationsClearHandler),
    (r'/account/notifications/(\w+)/remove', NotificationsRemoveHandler),
]