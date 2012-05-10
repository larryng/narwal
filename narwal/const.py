# -*- coding: utf-8 -*-

import re

__version__ = '0.3.0b'

API_PERIOD = 2.0
BASE_URL = 'http://www.reddit.com'
LOGIN_URL = 'https://ssl.reddit.com/api/login.json'
#BASE_URL = 'http://reddit.local:8888'
#LOGIN_URL = 'http://reddit.local:8888/api/login.json'
DEFAULT_USER_AGENT = 'python-narwal/{0}'.format(__version__)

TYPES = {
    '1': 'comment',
    '2': 'account',
    '3': 'link',
    '4': 'message',
    '5': 'subreddit',
    '6': 'link',
    '7': 'message'
}

KIND_PATTERN = re.compile(r't(?P<type>[0-9]+)(?:_(?P<id>[a-z0-9]+))?')

MAX_REPRSTR = 24

TRUTHY_OBJECTS = ({}, {u'json': {u'errors': []}})