from .const import BASE_URL, KIND_PATTERN, TYPES


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

def relative_url(*args):
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
    if not isinstance(lst, list):
        raise TypeError('lst must be a list')
    for i in lst:
        if isinstance(i, list):
            v = pull_data_dict(i)
            if v:
                return v
        elif isinstance(i, dict) and 'data' in i:
            return i
    return None