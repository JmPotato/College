#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymongo
import settings

db = pymongo.Connection(host = settings.mongodb_host,
                        port = settings.mongodb_port)[settings.database_name]

db.members.create_index([('created', -1)])
