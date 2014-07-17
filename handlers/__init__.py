#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import time
import random
import string
import hashlib

import tornado.web

class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    @property
    def messages(self):
        if not hasattr(self, '_messages'):
            messages = self.get_secure_cookie('saved_message')
            self._messages = []
            if messages:
                self._messages = tornado.escape.json_decode(messages)
        return self._messages

    def send_message(self, message, type = 'danger'):
        self.messages.append((type, message))
        self.set_secure_cookie('saved_message',
                               tornado.escape.json_encode(self.messages))

    def get_message(self):
        messages = self.messages
        self._messages = []
        self.clear_cookie('saved_message')
        return messages

    def generate_invitation(self):
        code = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        self.application.db.invitations.insert({
            'code' : code,
        })
        return code

    def check_invitation(self, invitation_code):
        if not self.application.db.invitations.find_one({'code': invitation_code}):
            return False
        self.application.db.invitations.remove({'code': invitation_code})
        return True

    def format_time(self, t):
        t = time.gmtime(t)
        utc = time.strftime('%Y-%m-%dT%H:%M:%SZ', t)
        return '<time datetime="%s"></time>' % utc

    def get_current_user(self):
        token = self.get_secure_cookie('token')
        user = self.application.db.users.find_one({'token': token})
        if user and user['role'] < 0:
            self.send_message('你的帐号已被封禁')
            self.clear_cookie('token')
            return None
        print user
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
            raise tornado.web.HTTPError(404)
        return user

    def get_topic(self, topic_id):
        topic = self.db.topics.find_one({'_id': ObjectId(topic_id)})
        if not topic:
            raise tornado.web.HTTPError(404)
        return topic

    def get_node(self, node_name):
        node_name = node_name.lower()
        node = self.db.nodes.find_one({'name_lower': node_name})
        if not node:
            raise tornado.web.HTTPError(404)
        return node

    def get_page_num(self, count, per_page):
        return int((count + per_page - 1) / per_page)

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