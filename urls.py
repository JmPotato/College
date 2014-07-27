#!/usr/bin/env python
# -*- coding: utf-8 -*-

from handlers import account, topic, node, member, tool

handlers = []
handlers.extend(account.handlers)
handlers.extend(topic.handlers)
handlers.extend(node.handlers)
handlers.extend(member.handlers)
handlers.extend(tool.handlers)