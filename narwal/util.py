# -*- coding: utf-8 -*-

import re
from .const import BASE_URL, KIND_PATTERN, TYPES, TRUTHY_OBJECTS
from .exceptions import UnexpectedResponse


def limstr(s, max_length):
    if max_length < 0:
        raise ValueError('max_length must be at least 0')
    type_ = type(s)
    if len(s) > max_length:
        if max_length <= 3:
            return type_('.') * max_length
        else:
            return s[:max_length-3] + type_('...')
    else:
        return s


def urljoin(*args):
    return u'/'.join(unicode(a).strip('/') for a in args)


def reddit_url(*args):
    if len(args) > 0 and args[0].startswith(BASE_URL):
        url = urljoin(*args)
    else:
        url = urljoin(BASE_URL, *args)
    if not url.endswith(u'.json'):
        url += u'/.json'
    return url


def kind(s):
    m = KIND_PATTERN.match(s)
    if m:
        return TYPES[m.group('type')]
    else:
        return s


def pull_data_dict(lst):
    for i in lst:
        if isinstance(i, list):
            v = pull_data_dict(i)
            if v:
                return v
        elif isinstance(i, dict) and 'data' in i:
            return i
    return None


def html_unicode_unescape(s):
    def f(matchobj):
        return unichr(int(matchobj.group(1)))
    return re.sub(r'&amp;#(\d+);', f, s)


def assert_truthy(d):
    if d in TRUTHY_OBJECTS:
        return True
    else:
        raise UnexpectedResponse(d)