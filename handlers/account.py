#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import time
import hashlib

import tornado.web
from tornado import gen

from . import BaseHandler
from bson.objectid import ObjectId

username_validator = re.compile(r'^[A-Za-z][A-Za-z0-9._]{0,9}$')
email_validator = re.compile(r'^.+@[^.].*\.[a-z]{2,10}$', re.IGNORECASE)

class SignupHandler(BaseHandler):
    def get(self):
        if self.get_current_user():
            self.redirect(self.get_argument('next', '/'))
        self.render('account/signup.html')

    @gen.coroutine
    def post(self):
        username = self.get_escaped_argument('username', None)
        email = self.get_escaped_argument('email', None)
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
        if not (yield self.async_db.users.count()):
            role = 3
        yield self.async_db.users.insert({
            'name': username,
            'name_lower': username.lower(),
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

    @gen.coroutine
    def post(self):
        username = self.get_argument('username', '').lower()
        password = self.get_argument('password', None)
        if not (username and password):
            self.send_message('请完整填写信息喵')
        token = hashlib.sha1(password + username.lower()).hexdigest()
        user = yield self.async_db.users.find_one({'name_lower': username, 'token': token})
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
    @gen.coroutine
    def post(self):
        website = self.get_escaped_argument('website', '')
        if website:
            if website[0:7] != 'http://' and website[0:8] != 'https://':
                website = 'http://' + website
        description = self.get_escaped_argument('description', '')
        enterCount = 0
        for c in description:
            if c == '\n':
                enterCount += 1
                if enterCount >= 10:
                    self.send_message('喵了个咪简介最多10行！！！')
                    self.redirect('/account/settings')
                    return
                    break
        if len(description) > 310:
            self.send_message('你这是要写自传的节奏嘛，简介太长了！')
            self.redirect('/account/settings')
            return
        yield self.async_db.users.update({'_id': self.current_user['_id']}, {'$set': {
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
        if str(file_metas['body'][0:3]).lower() == 'gif':
            self.send_message('妈蛋上传这种头像是想闪瞎我们么（掀桌')
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

class RemoveAvatarHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def post(self):
        if not self.current_user['avatar_name']:
            self.send_message('你在 College 根本没有头像嘛，浪费感情')
            self.render('account/settings.html')
            return
        yield self.async_db.users.update({'_id': self.current_user['_id']},
                             {'$set': {'avatar_name': ''}})
        self.send_message('头像移除成功', type='success')
        self.redirect('/account/settings')

class ChangePasswordHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
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
        yield self.async_db.users.update({'_id': self.current_user['_id']},
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
    @gen.coroutine
    def get(self):
        yield self.async_db.notifications.remove({'to': self.current_user['name_lower']})
        self.redirect('/')

class NotificationsRemoveHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def get(self, id):
        yield self.async_db.notifications.remove({'_id': ObjectId(id)})
        self.redirect(self.get_argument('next', '/account/notifications'))

handlers = [
    (r'/account/signup', SignupHandler),
    (r'/account/signin', SigninHandler),
    (r'/account/signout', SignoutHandler),
    (r'/account/settings', SettingsHandler),
    (r'/account/avatar', ChangeAvatarHandler),
    (r'/account/avatar/remove', RemoveAvatarHandler),
    (r'/account/password', ChangePasswordHandler),
    (r'/account/notifications', NotificationsHandler),
    (r'/account/notifications/clear', NotificationsClearHandler),
    (r'/account/notifications/(\w+)/remove', NotificationsRemoveHandler),
]