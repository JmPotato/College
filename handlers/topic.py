#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

import tornado.web
from tornado import gen
from bson.objectid import ObjectId

from . import BaseHandler
from .utils import make_content

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
    @gen.coroutine
    def get(self, topic_id):
        topic = self.get_topic(topic_id)
        if self.current_user:
            yield self.async_db.notifications.update({
                'topic': ObjectId(topic_id),
                'to': self.current_user['name_lower']
            }, {'$set': {'read': True}}, multi = True)
            if 'read' in topic:
                yield self.async_db.topics.update(
                    {'_id': ObjectId(topic_id)},
                    {'$addToSet': {'read': self.current_user['name_lower']}}
                )
            else:
                yield self.async_db.topics.update(
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
    @gen.coroutine
    def post(self):
        node = self.get_escaped_argument("node", None)
        title = self.get_escaped_argument('title', None)
        content = self.get_escaped_argument('content', None)
        if not (node and title and content):
            self.send_message('请完整填写信息喵')
        if len(title) > 100:
            self.send_message('艾玛标题太长了')
        if len(content) > 20000:
            self.send_message('艾玛内容太多了')
        if not self.get_node(node):
            raise tornado.web.HTTPError(403)
        if self.messages:
            self.render('topic/create.html', node_name=node)
            return
        topic = yield self.async_db.topics.find_one({
            'title': title,
            'content': content,
            'author': self.current_user['name']
        })
        if topic:
            self.send_message('不要发布重复内容！')
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
            'appended_content': [],
            'last_reply_time': time_now,
            'index': 0,
        }
        source = self.get_source()
        if source:
            data['source'] = source
        topic_id = yield self.async_db.topics.insert(data)
        self.send_notification(content_html, topic_id)
        self.redirect('/topic/%s' % topic_id)

class ReplyHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def post(self, topic_id):
        content = self.get_escaped_argument('content', None)
        if not content:
            self.send_message('请完整填写信息喵')
        elif len(content) > 20000:
            self.send_message("艾玛内容太多了")
        if self.messages:
            self.redirect('/topic/%s' % topic_id)
            return
        index = self.db.topics.find_and_modify({'_id': ObjectId(topic_id)},
                                               update={'$inc': {'index': 1}})['index'] + 1
        time_now = time.time()
        content_html = make_content(content)
        self.send_notification(content_html, topic_id)
        source = self.get_source()
        data = {
            'content': content,
            'content_html': content_html,
            'author': self.current_user['name'],
            'topic': topic_id,
            'created': time_now,
            'index': index,
        }
        if source:
            data['source'] = source
        yield self.async_db.replies.insert(data)
        yield self.async_db.topics.update({'_id': ObjectId(topic_id)},
                              {'$set': {'last_reply_time': time_now,
                                        'last_reply_by':
                                        self.current_user['name'],
                                        'read': [self.current_user['name_lower']]}})
        reply_nums = self.db.replies.find({'topic': topic_id}).count()
        last_page = self.get_page_num(reply_nums, 20)
        self.redirect('/topic/%s?p=%s' % (topic_id, last_page))

class LikeHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def get(self, topic_id):
        like = yield self.async_db.users.find_one({'name_lower': self.current_user['name_lower']})
        like = dict(like)['like']
        if ObjectId(topic_id) in like:
            self.send_message('你已收藏过此主题')
            self.redirect('/topic/%s' % topic_id)
            return
        like.append(ObjectId(topic_id))
        yield self.async_db.users.update({'name_lower': self.current_user['name_lower']},
                             {'$set': {'like': like}})
        self.send_message('收藏成功', type='success')
        self.redirect('/topic/%s' % topic_id)

class DisikeHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def get(self, topic_id):
        like = yield self.async_db.users.find_one({'name_lower': self.current_user['name_lower']})
        like = dict(like)['like']
        like.remove(ObjectId(topic_id))
        yield self.async_db.users.update({'name_lower': self.current_user['name_lower']},
                             {'$set': {'like': like}})
        self.send_message('取消收藏成功', type='success')
        self.redirect('/topic/%s' % topic_id)

class AppendHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, topic_id):
        self.render('topic/append.html')

    @tornado.web.authenticated
    @gen.coroutine
    def post(self, topic_id):
        content = self.get_escaped_argument('content', None)
        if not content:
            self.send_message('请完整填写信息喵')
        appended_content = yield self.async_db.topics.find_one({'_id': ObjectId(topic_id)})
        appended_content = dict(appended_content)['appended_content']
        if make_content(content) in appended_content:
            self.send_message('不要发布重复内容！')
            self.redirect('/topic/%s' % topic_id)
            return
        appended_content.append(make_content(content))
        yield self.async_db.topics.update({'_id': ObjectId(topic_id)},
                              {'$set': {'appended': time.time(),
                                        'appended_content': appended_content}})
        self.redirect('/topic/%s' % topic_id)

class RemoveHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def get(self, topic_id):
        self.check_role()
        yield self.async_db.topics.remove({'_id': ObjectId(topic_id)})
        yield self.async_db.replies.remove({'topic': topic_id})
        yield self.async_db.notifications.remove({'topic': topic_id})
        self.send_message('删除成功', type='success')
        self.redirect('/')

class MoveHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, topic_id):
        topic = self.get_topic(topic_id)
        self.render('topic/move.html', topic=topic)

    @tornado.web.authenticated
    @gen.coroutine
    def post(self, topic_id):
        node_name = self.get_argument('to_node', '')
        node = self.get_node(node_name.lower())
        yield self.async_db.topics.update({'_id': ObjectId(topic_id)},
                              {'$set': {'node': node['name']}})
        self.send_message('搬家成功！', type='success')
        self.redirect('/topic/%s' % topic_id)

handlers = [
    (r'/', TopicListHandler),
    (r'/topic', TopicListHandler),
    (r'/topic/create', CreateHandler),
    (r'/topic/(\w+)', TopicHandler),
    (r'/topic/(\w+)/like', LikeHandler),
    (r'/topic/(\w+)/dislike', DisikeHandler),
    (r'/topic/(\w+)/reply', ReplyHandler),
    (r'/topic/(\w+)/move', MoveHandler),
    (r'/topic/(\w+)/append', AppendHandler),
    (r'/topic/(\w+)/remove', RemoveHandler),
]