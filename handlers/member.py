#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.web
from tornado import gen

from . import BaseHandler


class MemberListHandler(BaseHandler):
    def get(self):
        per_page = 22
        members = self.db.users.find(sort=[('created', -1)])
        count = members.count()
        p = int(self.get_argument('p', 1))
        members = members[(p - 1) * per_page:p * per_page]
        self.render('member/list.html', per_page=per_page, members=members,
                    count=count, p=p)

class MemberPageHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, name):
        member = self.get_user(name)
        topics = self.db.topics.find({'author': member['name']},
                                     sort=[('last_reply_time', -1)])
        topics = topics[:10]
        replies = self.db.replies.find({'author': member['name']},
                                       sort=[('created', -1)])
        replies = replies[:10]
        if member['like']:
            liked_topics = [self.get_topic(x) for x in member['like'][:10]]
        else:
            liked_topics = []
        self.render('member/member.html', member=member, topics=topics,
                    replies=replies, liked_topics=liked_topics)

class FavoriteHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, name):
        if not self.current_user['name'] == name:
            self.redirect('/member/' + name)
        member = self.get_user(name)
        topics = [self.get_topic(x) for x in member['like']]
        topics_count = len(topics)
        p = int(self.get_argument('p', 1))
        topics = topics[(p - 1) * 10:p*10]
        self.render('member/topics.html', member=member,
                    topics=topics, topics_count=topics_count, p=p, base_url = "/member/%s/favorite" % member['name'])

class MemberTopicsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, name):
        member = self.get_user(name)
        topics = self.db.topics.find(
            {'author': member['name']},
            sort=[('last_reply_time', -1)]
        )
        topics_count = topics.count()
        p = int(self.get_argument('p', 1))
        topics = topics[(p - 1) * 10:p*10]
        self.render('member/topics.html', member=member,
                    topics=topics, topics_count=topics_count, p=p, base_url = "/member/%s/topics" % member['name'])

class ChangeRoleHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def post(self, name):
        role = int(self.get_argument('role', 100))
        if self.current_user['role'] < 3:
            self.check_role(role_min=role + 1)
        name = name.lower()
        yield self.async_db.users.update({'name_lower': name},
                               {'$set': {'role': role}})
        self.redirect('/member/' + name)

handlers = [
    (r'/member', MemberListHandler),
    (r'/member/([A-Za-z][A-Za-z0-9._]{0,9})', MemberPageHandler),
    (r'/member/([A-Za-z][A-Za-z0-9._]{0,9})/favorite', FavoriteHandler),
    (r'/member/([A-Za-z][A-Za-z0-9._]{0,9})/topics', MemberTopicsHandler),
    (r'/member/([A-Za-z][A-Za-z0-9._]{0,9})/role', ChangeRoleHandler),
]