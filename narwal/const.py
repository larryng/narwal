import re

API_PERIOD = 2.0
BASE_URL = 'http://www.reddit.com/'
LOGIN_URL = 'https://ssl.reddit.com/api/login.json'
DEFAULT_USER_AGENT = 'python-narwal/0.0.1'

TYPES = {
    '1': 'comment',
    '2': 'account',
    '3': 'link',
    '4': 'message',
    '5': 'subreddit',
}

KIND_PATTERN = re.compile(r't(?P<type>[0-9]+)(?:_(?P<id>[a-z0-9]+))?')
COMMENTS_PATH_PATTERN = re.compile(r'(?P<start>.*comments)/(?P<link_id>\w+)/(?P<link_title>\w+)/.*')
POST_ERROR_PATTERN = re.compile(r'\[\d+, \d+, "call", \["\.(error\.\w+?)"\]\]')

MAX_REPRSTR = 24