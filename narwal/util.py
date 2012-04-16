from .const import BASE_URL, KIND_PATTERN, TYPES


def urljoin(*args):
    return '/'.join(a.strip('/') for a in args)

def limstr(s, max_length):
    if len(s) > max_length:
        type_ = type(s)
        return s[:max_length-3] + type_('...')
    else:
        return s

def relative_url(*args):
    url = urljoin(BASE_URL, *args)
    if not url.endswith('.json'):
        url += '/.json'
    return url

def kind(s):
    try:
        m = KIND_PATTERN.match(s)
        return TYPES[m.group('type')]
    except:
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