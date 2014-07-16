#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymongo
import settings

db = pymongo.Connection(host = settings.mongodb_host,
                        port = settings.mongodb_port)[settings.database_name]

db.users.create_index([('created', -1)])
db.topics.create_index([('last_reply_time', -1)])
db.notifications.create_index([('to', 1), ('created', 1)])