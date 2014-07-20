#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.web
from . import BaseHandler

class NodeListHandler(BaseHandler):
    def get(self):
        nodes = self.db.nodes.find()
        self.render('node/list.html', nodes = nodes)

class NodeHandler(BaseHandler):
    def get(self, node_name):
        node = self.get_node(node_name)
        topics = self.db.topics.find({'node': node['name']},
                                     sort=[('last_reply_time', -1)])
        topics_count = topics.count()
        p = int(self.get_argument('p', 1))
        self.render('node/node.html', node=node, topics=topics,
                    topics_count=topics_count, p=p)

class AddHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.check_role()
        self.render('node/add.html')

    @tornado.web.authenticated
    def post(self):
        self.check_role()
        node_name = self.get_argument('node_name', None)
        node_title = self.get_argument('node_title', None)
        description = self.get_argument('description', '')
        html = self.get_argument('html', '')
        if not node_title:
            node_title = node_name
        if not (node_title and node_name):
            self.send_message('请完整填写信息喵')
        if self.db.nodes.find_one({'name_lower': node_name.lower()}):
            self.send_message('该节点已存在！')
        if self.db.nodes.find_one({'title': node_title}):
            self.send_message('节点标题有冲突！')
        if self.messages:
            self.render('node/add.html')
            return
        self.db.nodes.insert({
            'name': node_name,
            'name_lower': node_name.lower(),
            'title': node_title,
            'description': description,
            'html': html,
        })
        self.redirect(self.get_argument('next', '/node/' + node_name))


class EditHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, node_name):
        self.check_role()
        node = self.get_node(node_name)
        self.render('node/edit.html', node = node)

    @tornado.web.authenticated
    def post(self, node_name):
        self.check_role()
        node = self.get_node(node_name)
        node_name = self.get_argument('node_name', None)
        node_title = self.get_argument('node_title', None)
        description = self.get_argument('description', '')
        if not node_name:
            self.send_message('请完整填写信息喵')
        if node_name != node['name'] and self.db.nodes.find_one({'name_lower': node_name.lower()}):
            self.send_message('该节点已存在！')
        if node_title != node['title'] and self.db.nodes.find_one({'title': node_title}):
            self.send_message('节点标题有冲突！')
        if self.messages:
            self.render('node/edit.html', node = node)
            return
        self.db.topics.update({'node': node['name']},
                              {'$set': {'node': node_name}}, multi=True)
        node['name'] = node_name
        node['name_lower'] = node_name.lower()
        node['title'] = node_title
        node['description'] = description
        self.db.nodes.save(node)

        self.send_message('修改成功！', type='success')
        self.redirect(self.get_argument('next', '/node/' + node['name']))

class RemoveHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, node_name):
        self.check_role()
        node = self.get_node(node_name)
        self.render('node/remove.html', node = node)

    @tornado.web.authenticated
    def post(self, node_name):
        self.check_role()
        from_node = self.get_node(node_name)
        node_name = self.get_argument('to_node')
        to_node = self.get_node(node_name)
        users = self.db.users.find({'favorite': from_node['name']})
        for user in users:
            user['favorite'].remove(from_node['name'])
            self.db.users.save(user)
        self.db.nodes.remove(from_node)
        self.db.topics.update({'node': from_node['name']},
                              {'$set': {'node': to_node['name']}}, multi=True)
        self.send_message('删除成功！', type='success')
        self.redirect('/')

handlers = [
    (r'/node', NodeListHandler),
    (r'/node/add', AddHandler),
    (r'/node/([%A-Za-z0-9.-]+)', NodeHandler),
    (r'/node/([%A-Za-z0-9.-]+)/edit', EditHandler),
    (r'/node/([%A-Za-z0-9.-]+)/remove', RemoveHandler),
]