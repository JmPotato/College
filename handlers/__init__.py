#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import time
import random
import string
import hashlib

import qiniu.io
import qiniu.rs
import qiniu.rsf
import qiniu.conf
import tornado.web
from bson.objectid import ObjectId

#Use Qiniu to store avatars
qiniu.conf.ACCESS_KEY = ""
qiniu.conf.SECRET_KEY = ""

bucket_name = ''

policy = qiniu.rs.PutPolicy(bucket_name)
uptoken = policy.token()

os.environ['TZ'] = 'Asia/Shanghai'
time.tzset()

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

    def format_time(self, t):
        now = time.time()
        diff = abs(now - t)
        if diff < 60:
            utc = '%d 秒前' % (diff if diff > 1 else 1)
        elif diff < 3600:
            utc = '%d 分钟前' % (diff / 60)
        elif diff < 3600 * 24:
            utc = '%d 小时前' % (diff / 3600)
        elif diff <= 3600 * 24 * 7:
            utc = '%d 天前' % (diff / 3600 / 24)
        else:
            now = time.localtime(now)
            t = time.localtime(t)
            if t.tm_year == now.tm_year:
                utc = time.strftime('%m-%d %H:%M:%S', t)
            else:
                utc = time.strftime('%Y-%m-%d %H:%M:%S', t)
        return utc

    def get_current_user(self):
        token = self.get_secure_cookie('token')
        user = self.application.db.users.find_one({'token': token})
        if user and user['role'] < 0:
            self.send_message('你被关小黑屋了么么哒')
            self.clear_cookie('token')
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

    def check_role(self, role_min = 2, owner_name = '', return_bool = False):
        user = self.current_user
        if user and (user['name'] == owner_name or user['role'] >= role_min):
            return True
        if return_bool:
            return False
        raise tornado.web.HTTPError(403)

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

    def upload_img(self, img, file_name):
        code = ''.join(random.sample(string.ascii_letters + string.digits, 5))
        file = "img-%s.%s" % (code, file_name.lower().split('.')[-1:][0])
        ret, err = qiniu.io.put_file(uptoken, file, img)
        if err is not None:
            print err
            return False
        return qiniu.rs.make_base_url(bucket_name + '.qiniudn.com', file)

    def upload_avatar(self, user, img, file_name):
        file = "%s.%s" % (user['name_lower'], file_name.lower().split('.')[-1:][0])
        rets, err = qiniu.rsf.Client().list_prefix(bucket_name)
        for i in rets['items']:
            if file == i['key']:
                ret, err = qiniu.rs.Client().delete(bucket_name, file)
                break
        ret, err = qiniu.io.put_file(uptoken, file, img)
        if err is not None:
            print err
            return False
        self.db.users.update({'_id': self.current_user['_id']},
                             {'$set': {'avatar_name': file}})
        return True

    def get_avatar_img(self, user):
        if not user['avatar_name']:
            hashed_email = hashlib.md5(user['email']).hexdigest()
            return 'http://cn.gravatar.com/avatar/%s?size=98' % hashed_email
        url = qiniu.rs.make_base_url(bucket_name + '.qiniudn.com', user['avatar_name'])
        return url

    def get_avatar(self, user):
        url = self.get_avatar_img(user)
        return '<a href="/member/%s" class="avatar"><img src="%s" /></a>' % (user['name'], url)

    def send_notification(self, content, topic_id):
        if not isinstance(topic_id, ObjectId):
            topic_id = ObjectId(topic_id)
        user_name = self.current_user['name_lower']
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