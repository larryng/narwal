# -*- coding: utf-8 -*-

import re

__version__ = '0.3.0'

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
# COMMENTS_PATH_PATTERN = re.compile(r'(?P<start>.*comments)/(?P<link_id>\w+)/(?P<link_title>\w+)/.*')
# POST_ERROR_PATTERN = re.compile(r'\[\d+, \d+, "call", \["\.(error\.[^"]+?)"\]\]')
# SUBMIT_RESPONSE_LINK_PATTERN = re.compile(r'\["({0}/.+?)"\]'.format(BASE_URL))

MAX_REPRSTR = 24

TRUTHY_OBJECTS = ({}, {u'json': {u'errors': []}})