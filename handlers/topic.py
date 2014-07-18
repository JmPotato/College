#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

import tornado.web

from . import BaseHandler
from .utils import make_content
from bson.objectid import ObjectId

class TopicListHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.render('home.html')
        topics = self.db.topics.find(sort=[('last_reply_time', -1)])
        topics_count = topics.count()
        p = int(self.get_argument('p', 1))
        self.render(
            'topic/list.html',
            topics = topics,
            topics_count = topics_count,
            p = p,
        )

class TopicHandler(BaseHandler):
    def get(self, topic_id):
        topic = self.get_topic(topic_id)
        if self.current_user:
            self.db.notifications.update({
                'topic': ObjectId(topic_id),
                'to': self.current_user['name_lower']
            }, {'$set': {'read': True}}, multi = True)
            if 'read' in topic:
                self.db.topics.update(
                    {'_id': ObjectId(topic_id)},
                    {'$addToSet': {'read': self.current_user['name_lower']}}
                )
            else:
                self.db.topics.update(
                    {'_id': ObjectId(topic_id)},
                    {'$set': {'read': [self.current_user['name_lower']]}}
                )
        replies = self.db.replies.find({'topic': topic_id},
                                       sort=[('index', 1)])
        replies_count = replies.count()
        p = int(self.get_argument('p', 1))
        if p < 1:
            p = 1

        self.render('topic/topic.html',
                    topic = topic,
                    replies = replies,
                    replies_count = replies_count,
                    p = p,
        )

class CreateHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        node_name = self.get_argument("node", "")
        self.render('topic/create.html', node_name = node_name)

    @tornado.web.authenticated
    def post(self):
        node = self.get_argument("node", None)
        title = self.get_argument('title', None)
        content = self.get_argument('content', None)
        if not (node and title and content):
            self.send_message('请完整填写信息')
        if len(title) > 100:
            self.send_message('艾玛标题太长了')
        if len(content) > 20000:
            self.send_message('艾玛内容太多了')
        if not self.get_node(node):
            raise tornado.web.HTTPError(403)
        if self.messages:
            self.render('topic/create.html', node_name=node)
            return
        topic = self.db.topics.find_one({
            'title': title,
            'content': content,
            'author': self.current_user['name']
        })
        if topic:
            self.redirect('/topic/%s' % topic['_id'])
            return
        time_now = time.time()
        content_html = make_content(content)
        data = {
            'title': title,
            'content': content,
            'content_html': content_html,
            'author': self.current_user['name'],
            'node': node,
            'created': time_now,
            'appended': time_now,
            'last_reply_time': time_now,
            'index': 0,
        }
        source = self.get_source()
        if source:
            data['source'] = source
        topic_id = self.db.topics.insert(data)
        self.send_notification(content_html, topic_id)
        self.redirect('/topic/%s' % topic_id)

handlers = [
    (r'/', TopicListHandler),
    (r'/topic', TopicListHandler),
    (r'/topic/create', CreateHandler),
    (r'/topic/(\w+)', TopicHandler),
]