import time
import json
import requests
from urlparse import urlparse
from functools import wraps

from .things import Blob, ListBlob, Account, identify_class
from .util import relative_url
from .exceptions import NotLoggedIn, BadResponse, PostError
from .const import DEFAULT_USER_AGENT, LOGIN_URL, POST_ERROR_PATTERN, API_PERIOD


def _login_required(f):
    '''Decorator which requires to proceed'''
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if self.logged_in:
            return f(self, *args, **kwargs)
        else:
            raise NotLoggedIn()
    return wrapper

    
def _limit_rate(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if self._respect and self._last_request_time:
            elapsed = time.time() - self._last_request_time
            diff = API_PERIOD - elapsed
            if diff > 0:
                time.sleep(diff)
        self._last_request_time = time.time()
        return f(self, *args, **kwargs)
    return wrapper


def _process_userlist(userlist):
    r = userlist.children
    items = []
    for u in r:
        a = Account(userlist._reddit)
        a.id = u.id
        a.name = u.name
        items.append(a)
    r._items = items
    return r


class Reddit(object):
    def __init__(self, username=None, password=None, user_agent=None, respect=True):
        self._modhash = None
        self._cookies = None
        self._respect = respect
        self._last_request_time = None
        self._me = None
        
        if respect and not user_agent:
            raise ValueError('must specify user_agent to respect reddit rules')
        else:
            self._user_agent = user_agent or DEFAULT_USER_AGENT
        
        if username and password:
            self.login(username, password)
    
    @property
    def logged_in(self):
        return bool(self._modhash and self._cookies)
    
    
    def _inject_request_kwargs(self, kwargs):
        if self._cookies:
            kwargs.setdefault('cookies', self._cookies)
        if 'headers' in kwargs:
            kwargs['headers'].setdefault('User-Agent', self._user_agent)
        else:
            kwargs.setdefault('headers', {'User-Agent': self._user_agent})
        return kwargs
    
    
    def _thingify(self, obj, path=None):
        def helper(obj_, dict_):
            for k, v in dict_.items():
                value = recur(v)
                setattr(obj_, k, value)
            return obj_
        
        def recur(v):
            if isinstance(v, dict):
                klass = identify_class(v)
                tmp = klass(self)
                tmp._path = path
                retval = helper(tmp, v if klass is Blob else v['data'])
            elif isinstance(v, list):
                retval = ListBlob(self, items=[self._thingify(o, path) for o in v])
                retval._path = path
            else:
                retval = v
            return retval
        
        return recur(obj)
            
    @_limit_rate
    def get(self, *args, **kwargs):
        kwargs = self._inject_request_kwargs(kwargs)
        url = relative_url(*args)
        r = requests.get(url, **kwargs)
        print r.url
        if r.status_code == 200:
            thing = self._thingify(json.loads(r.content), path=urlparse(r.url).path)
            return thing
        else:
            raise BadResponse(r)
    
    @_limit_rate
    def post(self, *args, **kwargs):
        kwargs = self._inject_request_kwargs(kwargs)
        if self._modhash:
            if 'data' in kwargs:
                data = kwargs['data'].copy()
                data.setdefault('uh', self._modhash)
                kwargs['data'] = data
            else:
                kwargs['data'] = dict(uh=self._modhash)
        url = relative_url(*args)
        r = requests.post(url, **kwargs)
        if r.status_code == 200:
            errors = POST_ERROR_PATTERN.findall(r.content)
            if errors:
                raise PostError(errors)
            else:
                return r
        else:
            raise BadResponse(r)

    def login(self, username, password):
        data = dict(user=username, passwd=password, api_type='json')
        r = requests.post(LOGIN_URL, data=data)
        try:
            j = json.loads(r.content)
            self._cookies = r.cookies
            self._modhash = j['json']['data']['modhash']
            return r
        except Exception:
            raise BadResponse(r)
    
    # START: Basic getting
    
    def _limit_get(self, *args, **kwargs):
        limit = kwargs.pop('limit') if 'limit' in kwargs else None
        if limit is not None:
            kwargs.setdefault('params', {})['limit'] = limit
        r = self.get(*args, **kwargs)
        if issubclass(type(r), Blob):
            r._limit = limit
        return r
    
    def _subreddit_get(self, child=None, sr=None, limit=None):
        args = (child,) if child else ()
        if sr:
            args = ('r', sr) + args
        return self._limit_get(*args, limit=limit)
    
    def hot(self, sr=None, limit=None):
        return self._subreddit_get(None, sr, limit)
    
    def new(self, sr=None, limit=None):
        return self._subreddit_get('new', sr, limit)
    
    def top(self, sr=None, limit=None):
        return self._subreddit_get('top', sr, limit)
    
    def controversial(self, sr=None, limit=None):
        return self._subreddit_get('controversial', sr, limit)
    
    def comments(self, sr=None, limit=None):
        return self._subreddit_get('comments', sr, limit)
    
    def user(self, username):
        return self.get('user', username, 'about')
    
    def subreddit(self, name):
        return self.get('r', name, 'about')
    
    def info(self, url):
        return self.get('api', 'info', params=dict(url=url))
    
    def search(self, query, limit=None):
        return self._limit_get('search', params=dict(q=query), limit=limit)
    
    def domain(self, domain_, limit=None):
        return self._limit_get('domain', domain_, limit=limit)
    
    @_login_required
    def me(self, refresh=False):
        if not self._me or refresh:
            r = self.get('api', 'me')
            if issubclass(type(r), Blob):
                self._me = r
                self._modhash = r.modhash
            else:
                raise BadResponse(r)
        return self._me
    
    @_login_required
    def mine(self, limit=None):
        return self._limit_get('reddits', 'mine', limit=limit)
    
    def moderators(self, sr):
        userlist = self.get('r', sr, 'about', 'moderators')
        return _process_userlist(userlist)
    
    # END: Basic getting
    
    # START: Logged-in user's basic actions
    
    @_login_required
    def saved(self, limit=None):
        return self._limit_get('saved', limit=limit)
    
    @_login_required
    def vote(self, id_, dir_):
        data = dict(id=id_, dir=dir_)
        return self.post('api', 'vote', data=data)
    
    @_login_required
    def upvote(self, id_):
        return self.vote(id_, 1)
    
    @_login_required
    def downvote(self, id_):
        return self.vote(id_, -1)
    
    @_login_required
    def unvote(self, id_):
        return self.vote(id_, 0)
    
    @_login_required
    def comment(self, parent, text):
        data = dict(parent=parent, text=text)
        return self.post('api', 'comment', data=data)
    
    @_login_required
    def submit_link(self, sr, title, url):
        data = dict(title=title, url=url, sr=sr, kind='link')
        return self.post('api', 'submit', data=data)
    
    @_login_required
    def submit_text(self, sr, title, text):
        data = dict(title=title, text=text, sr=sr, kind='self')
        return self.post('api', 'submit', data=data)
    
    @_login_required
    def save(self, id_):
        data = dict(id=id_)
        return self.post('api', 'save', data=data)
    
    @_login_required
    def unsave(self, id_):
        data = dict(id=id_)
        return self.post('api', 'unsave', data=data)
    
    @_login_required
    def hide(self, id_):
        data = dict(id=id_)
        return self.post('api', 'hide', data=data)
    
    @_login_required
    def unhide(self, id_):
        data = dict(id=id_)
        return self.post('api', 'unhide', data=data)
    
    @_login_required
    def marknsfw(self, id_):
        data = dict(id=id_)
        return self.post('api', 'marknsfw', data=data)
    
    @_login_required
    def unmarknsfw(self, id_):
        data = dict(id=id_)
        return self.post('api', 'unmarknsfw', data=data)
    
    @_login_required
    def report(self, id_):
        data = dict(id=id_)
        return self.post('api', 'report', data=data)
    
    # reddit seems to block bots from sharing, so this doesnt work :(
    @_login_required
    def share(self, parent, share_from, replyto, share_to, message):
        data = dict(parent=parent, share_from=share_from, replyto=replyto, share_to=share_to, message=message)
        return self.post('api', 'share', data=data)
    
    @_login_required
    def compose(self, to, subject, text):
        if isinstance(to, Account):
            to = to.name
        data = dict(to=to, subject=subject, text=text)
        return self.post('api', 'compose', data=data)
    
    @_login_required
    def read_message(self, id_):
        data = dict(id=id_)
        return self.post('api', 'read_message', data=data)
    
    @_login_required
    def unread_message(self, id_):
        data = dict(id=id_)
        return self.post('api', 'unread_message', data=data)
    
    @_login_required
    def hide_message(self, id_):
        data = dict(id=id_)
        return self.post('api', 'hide_message', data=data)
    
    @_login_required
    def unhide_message(self, id_):
        data = dict(id=id_)
        return self.post('api', 'unhide_message', data=data)
    
    @_login_required
    def subscribe(self, sr):
        if not sr.startswith('t5_'):
            sr = self.subreddit(sr).name
        data = dict(action='sub', sr=sr)
        return self.post('api', 'subscribe', data=data)
    
    @_login_required
    def unsubscribe(self, sr):
        if not sr.startswith('t5_'):
            sr = self.subreddit(sr).name
        data = dict(action='unsub', sr=sr)
        return self.post('api', 'subscribe', data=data)
    
    @_login_required
    def delete(self, id_):
        data = dict(id=id_)
        return self.post('api', 'delete', data=data)
    
    # END: Logged-in user's basic actions
    
    # START: Logged-in user's messages and comments
    
    @_login_required
    def inbox(self, limit=None):
        return self._limit_get('message', 'inbox', limit=limit)
    
    @_login_required
    def unread(self, limit=None):
        return self._limit_get('message', 'unread', limit=limit)
    
    @_login_required
    def messages(self, limit=None):
        return self._limit_get('message', 'messages', limit=limit)
    
    @_login_required
    def commentreplies(self, limit=None):
        return self._limit_get('message', 'comments', limit=limit)
    
    @_login_required
    def postreplies(self, limit=None):
        return self._limit_get('message', 'selfreply', limit=limit)
    
    @_login_required
    def sent(self, limit=None):
        return self._limit_get('message', 'sent', limit=limit)
    
    @_login_required
    def modmail(self, limit=None):
        return self._limit_get('message', 'moderator', limit=limit)
    
    # END: Logged-in user's messages and comments
    
    # START: Mod actions
    
    @_login_required
    def approve(self, id_):
        data = dict(id=id_)
        return self.post('api', 'approve', data=data)
    
    @_login_required
    def remove(self, id_):
        data = dict(id=id_)
        return self.post('api', 'remove', data=data)
    
    @_login_required
    def flairlist(self, r, limit=100, after=None, before=None):
        data = dict(r=r, limit=limit)
        if after:
            data['after'] = after
        elif before:
            data['before'] = before
        else:
            raise ValueError('after or before must be a non-empty string')
        return self.post('api', 'flairlist', data=data)
    
    @_login_required
    def flair(self, r, name, text, css_class):
        data = dict(r=r, name=name, text=text, css_class=css_class)
        return self.post('api', 'flair', data=data)

    @_login_required
    def flaircsv(self, r, flair_csv):
        data = dict(r=r, flair_csv=flair_csv)
        return self.post('api', 'flaircsv', data=data)
    
    @_login_required
    def contributors(self, sr):
        userlist = self.get('r', sr, 'about', 'contributors')
        return _process_userlist(userlist)
    
    # END: Mod actions
    

def connect(*args, **kwargs):
    return Reddit(*args, **kwargs)