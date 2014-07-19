#!/usr/bin/env python
# -*- coding: utf-8 -*-

from handlers import account, topic, node

handlers = []
handlers.extend(account.handlers)
handlers.extend(topic.handlers)
handlers.extend(node.handlers)