#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

import tornado.web

from . import BaseHandler

class TopicListHandler(BaseHandler):
    def get(self):
        if not self.get_current_user():
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
        if self.get_current_user():
            self.db.notifications.update({
                'topic': ObjectId(topic_id),
                'to': self.get_current_user()['name_lower']
            }, {'$set': {'read': True}}, multi = True)
            if 'read' in topic:
                self.db.topics.update(
                    {'_id': ObjectId(topic_id)},
                    {'$addToSet': {'read': self.self.get_current_user()['name_lower']}}
                )
            else:
                self.db.topics.update(
                    {'_id': ObjectId(topic_id)},
                    {'$set': {'read': [self.self.get_current_user()['name_lower']]}}
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
                    p = p
        )


handlers = [
    (r'/', TopicListHandler),
    (r'/topic', TopicListHandler),
    (r'/topic/(\w+)', TopicHandler),
]