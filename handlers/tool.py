#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time

import tornado.web
from tornado import gen
from bson.objectid import ObjectId

from . import BaseHandler
from .utils import make_content

class UploadHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('tool/upload_img.html')

    @tornado.web.authenticated
    def post(self):
        try:
            file_metas = self.request.files['img_file'][0]
        except:
            self.send_message('图片半路走丢了，再试一次吧')
            self.render('account/upload.html')
            return
        with open(file_metas['filename'], 'w') as f:
            f.write(file_metas['body'])
        url = self.upload_img(file_metas['filename'], file_metas['filename'])
        if not url:
            os.remove(file_metas['filename'])
            self.send_message('图片上传失败')
            self.render('account/upload.html')
            return
        os.remove(file_metas['filename'])
        self.send_message('图片上传成功，你的图片地址为：%s 把地址复制到主题里即可插入图片' % url, type='success')
        self.render('tool/upload.html')

class NoteListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        p = int(self.get_argument('p', 1))
        notes = self.db.notes.find({'author': self.current_user['name']},
                                     sort=[('created', -1)])
        notes_count = notes.count()
        per_page = 10
        notes = notes[(p - 1) * per_page:p * per_page]
        self.render('tool/note_list.html', notes=notes, notes_count=notes_count, p=p)

class NoteHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, note_id):
        note = self.get_note(note_id)
        self.render('tool/note.html', note=note)

class NewNoteHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('tool/note_new.html')

    @tornado.web.authenticated
    @gen.coroutine
    def post(self):
        title = self.get_escaped_argument('title', None)
        content = self.get_escaped_argument('content', None)
        if not (title and content):
            self.send_message('请完整填写信息喵')
        if self.messages:
            self.render('tool/note_new.html')
            return
        note = yield self.async_db.notes.find_one({
            'title': title,
            'content': content,
            'author': self.current_user['name']
        })
        if note:
            self.send_message('不要发布重复内容！')
            self.redirect('/tool/note/%s' % note['_id'])
            return
        time_now = time.time()
        content_html = make_content(content)
        data = {
            'title': title,
            'content': content,
            'content_html': content_html,
            'author': self.current_user['name'],
            'created': time_now,
            'modify': None,
        }
        yield self.async_db.notes.insert(data)
        self.redirect('/tool/note')

class EditNoteHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, note_id):
        note = self.get_note(note_id)
        self.render('tool/note_edit.html', note=note)

    @tornado.web.authenticated
    @gen.coroutine
    def post(self, note_id):
        note = self.get_note(note_id)
        if not self.current_user['name'] == note['author']:
            self.send_message('无权限！')
            self.redirect('/tool/note')
            return
        title = self.get_escaped_argument('title', None)
        content = self.get_escaped_argument('content', None)
        if not (title and content):
            self.send_message('请完整填写信息喵')
        if self.messages:
            self.render('tool/note_edit.html', note=note)
            return
        time_now = time.time()
        content_html = make_content(content)
        note['title'] = title
        note['content'] = content
        note['content_html'] = content_html
        note['modify'] = time_now
        yield self.async_db.notes.save(note)
        self.send_message('修改成功！', type='success')
        self.redirect('/tool/note/%s' % note_id)

class DelNoteHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def get(self, note_id):
        note = self.get_note(note_id)
        if not self.current_user['name'] == note['author']:
            self.send_message('无权限！')
            self.redirect('/tool/note')
            return
        note_id = ObjectId(note_id)
        yield self.async_db.notes.remove({'_id': note_id})
        self.send_message('删除成功', type='success')
        self.redirect('/tool/note')

handlers = [
    (r'/tool/upload', UploadHandler),
    (r'/tool/note', NoteListHandler),
    (r'/tool/note/new', NewNoteHandler),
    (r'/tool/note/(\w+)', NoteHandler),
    (r'/tool/note/(\w+)/edit', EditNoteHandler),
    (r'/tool/note/(\w+)/delete', DelNoteHandler),
]