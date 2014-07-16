#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import time
import hashlib

import tornado.web

class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    def format_time(self, t):
        t = time.gmtime(t)
        utc = time.strftime('%Y-%m-%dT%H:%M:%SZ', t)
        return '<time datetime="%s"></time>' % utc

    def get_current_user(self):
        token = self.get_secure_cookie('token')
        user = self.application.db.users.find_one({'token': token})
        if user and user['role'] < 0:
            return False
        if not user:
            return None
        return user

    def get_ua(self):
        return self.request.headers.get("User-Agent", "bot")

    def get_source(self):
        ua = self.get_ua()
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

    def get_lord(self):
        return self.db.users.find_one({'role': 1})

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

    def send_notification(self, content, topic_id):
        if not isinstance(topic_id, ObjectId):
            topic_id = ObjectId(topic_id)
        user_name = self.get_current_user()['name_lower']
        mention = re.compile('class="mention">@(\w+)')
        for name in set(mention.findall(content)):
            user = self.db.users.find_one({'name_lower': name.lower()})
            if not user:
                continue
            if user_name == user['name_lower']:
                continue
            self.db.notifications.insert({
                'topic': topic_id,
                'from': user_name,
                'to': user['name_lower'],
                'content': content,
                'read': False,
                'created': time.time(),
            })