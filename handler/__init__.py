#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import hashlib

import tornado.web

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        token = self.get_secure_cookie('token')
        user = self.application.db.users.find_one({'token': token})
        if user and user['role'] < 0:
            return False
        if not user:
            return None
        return user

    def get_source(self):
        ua = self.request.headers.get("User-Agent", "bot")
        sources = dict(
            iPhone = 'iPhone',
            iPad = 'iPad',
            iPod = 'iPod',
            Android = 'Android',
            Kindle = 'Kindle',
            silk = 'Kindle Fire',
            BlackBerry = 'BlackBerry',
            TouchPad = 'TouchPad',
        )
        for key, vaule in sources.items():
            if key in ua:
                return vaule
        if 'Windows Phone' in ua:
            return 'Windows Phone'
        if 'Nokia' in ua:
            return 'Nokia'
        return None

    @property
    def db(self):
        return self.application.db

    def get_user(self, name):
        user = self.db.users.find_one({'name_lower': name.lower()})
        if not user:
            return False
        return user

    def get_topic(self, topic_id):
        topic = self.db.topics.find_one({'_id': ObjectId(topic_id)})
        if not topic:
            return False
        return topic

    def get_avatar_img(self, user, size = 48):
        hashed_email = hashlib.md5(user['email']).hexdigest()
        url = 'http://cn.gravatar.com/avatar/' + hashed_email
        url += '?s=%s' % size
        return url

    def get_avatar(self, user, size = 48):
        size *= 2
        url = self.get_avatar_img(user, size)
        return '<a href="/user/%s" class="avatar"><img src="%s" /></a>' % (user['name'], url)

    def format_time(self, t):
        t = time.gmtime(t)
        utc = time.strftime('%Y-%m-%dT%H:%M:%SZ', t)
        return '<time datetime="%s"></time>' % utc
