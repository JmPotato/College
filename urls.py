#!/usr/bin/env python
# -*- coding: utf-8 -*-

from handlers import account, topic

handlers = []
handlers.extend(account.handlers)
handlers.extend(topic.handlers)