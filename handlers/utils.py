import re
import requests
import settings

from tornado.escape import xhtml_escape, _unicode, _URL_RE
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, TextLexer

_MENTION_RE = re.compile(r'((?:^|\W)@\w+)')
_FLOOR_RE = re.compile(r'((?:^|\W)#\d+)')
_TOPIC_RE = re.compile(r'((?:^|\W)t[a-z0-9]{24})')
_EMAIL_RE = re.compile(r'([A-Za-z0-9-+.]+@[A-Za-z0-9-.]+)(\s|$)')

formatter = HtmlFormatter()


def make_content(text, extra_params='rel="nofollow"'):
    """https://github.com/facebook/tornado/blob/master/tornado/escape.py#L238
    """
    if extra_params:
        extra_params = " " + extra_params.strip()

    def make_link(m):
        url = m.group(1)
        proto = m.group(2)

        href = m.group(1)
        if not proto:
            href = "http://" + href

        params = extra_params

        if '.' in href:
            name_extension = href.split('.')[-1].lower()
            if name_extension in ('jpg', 'png', 'git', 'jpeg'):
                return u'<img src="%s" />' % href

        return u'<a href="%s"%s>%s</a>' % (href, params, url)

    def cover_email(m):
        data = {'mail': m.group(1),
                'end': m.group(2)}
        return u'<a href="mailto:%(mail)s">%(mail)s</a>%(end)s' % data

    def convert_mention(m):
        data = {}
        data['begin'], data['user'] = m.group(1).split('@')
        t = u'%(begin)s<a href="/member/%(user)s" class="mention">' \
            u'@%(user)s</a>'
        return t % data

    def convert_floor(m):
        data = {}
        data['begin'], data['floor'] = m.group(1).split('#')
        t = u'%(begin)s<a href="#reply%(floor)s"' \
            ' class="mention mention_floor">#%(floor)s</a>'
        return t % data

    def convert_topic(m):
        data = {}
        data['begin'], data['topic_link'] = m.group(1).split('t')
        data['topic_link_short'] = data['topic_link'][:6]
        t = u"""%(begin)s<a href="%(topic_link)s"
            class="mention mention_topic"
            _id=%(topic_link)s>t%(topic_link_short)s</a>"""
        return t % data

    text = _unicode(xhtml_escape(text)).replace(' ', '&nbsp;')
    text = _EMAIL_RE.sub(cover_email, text)
    text = _MENTION_RE.sub(convert_mention, text)
    text = _FLOOR_RE.sub(convert_floor, text)
    text = _TOPIC_RE.sub(convert_topic, text)
    return _URL_RE.sub(make_link, text)
