import time
import json
import requests
from urlparse import urlparse
from functools import wraps

from .things import Blob, ListBlob, Account, identify_thing
from .util import relative_url, pull_data_dict
from .exceptions import NotLoggedIn, BadResponse, PostError, LoginFail
from .const import DEFAULT_USER_AGENT, LOGIN_URL, POST_ERROR_PATTERN, API_PERIOD, SUBMIT_RESPONSE_LINK_PATTERN


def _limit_rate(f, period=API_PERIOD):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if self._respect and self._last_request_time:
            elapsed = time.time() - self._last_request_time
            diff = period - elapsed
            if diff > 0:
                time.sleep(diff)
        self._last_request_time = time.time()
        return f(self, *args, **kwargs)
    return wrapper


def _login_required(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if self.logged_in:
            return f(self, *args, **kwargs)
        else:
            raise NotLoggedIn()
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
    """A Reddit session.
    
    :param username: (optional) reddit username
    :param password: (optional) reddit password
    :param user_agent: User-Agent
    :param respect: If True, requires user_agent to be specified and limits request rate to 1 every 2 seconds, as per reddit's API rules.
    :type respect: True or False
    """
    def __init__(self, username=None, password=None, user_agent=None, respect=True):
        self._modhash = None
        self._cookies = None
        self._respect = respect
        self._last_request_time = None
        
        if respect and not user_agent:
            raise ValueError('must specify user_agent to respect reddit rules')
        else:
            self._user_agent = user_agent or DEFAULT_USER_AGENT
        
        if username and password:
            self.login(username, password)
    
    def __repr__(self):
        return '<Reddit [{}]>'.format(self._username or '(not logged in)')
    
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
                klass = identify_thing(v)
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
    
    @property
    def logged_in(self):
        """Property.  True if logged in."""
        return bool(self._modhash and self._cookies)
            
    @_limit_rate
    def get(self, *args, **kwargs):
        """Sends a GET request to a reddit path determined by ``args``.  Basically ``.get('foo', 'bar', 'baz')`` will GET http://www.reddit.com/foo/bar/baz/.json.  ``kwargs`` supplied will be passed to :meth:`requests.get` after having ``user_agent`` and ``cookies`` injected.  Injection only occurs if they don't already exist.
        
        Returns :class:`things.Blob` object or a subclass of :class:`things.Blob`, or raises :class:`exceptions.BadResponse` if not a 200 Response.
        
        :param \*args: strings that will form the path to GET
        :param \*\*kwargs: extra keyword arguments to be passed to :meth:`requests.get`
        """
        kwargs = self._inject_request_kwargs(kwargs)
        url = relative_url(*args)
        r = requests.get(url, **kwargs)
        # print r.url
        if r.status_code == 200:
            thing = self._thingify(json.loads(r.content), path=urlparse(r.url).path)
            return thing
        else:
            raise BadResponse(r)
    
    @_limit_rate
    def post(self, *args, **kwargs):
        """Sends a POST request to a reddit path determined by ``args``.  Basically ``.post('foo', 'bar', 'baz')`` will POST http://www.reddit.com/foo/bar/baz/.json.  ``kwargs`` supplied will be passed to ``requests.post`` after having ``modhash`` and ``cookies`` injected, and after having modhash injected into ``kwargs['data']`` if logged in.  Injection only occurs if they don't already exist.
        
        Returns :class:`requests.Response` object, raises :class:`exceptions.BadResponse` if not a 200 Response, or raises :class:`exceptions.POST_ERROR` if a reddit error was returned.
        
        :param \*args: strings that will form the path to POST
        :param \*\*kwargs: extra keyword arguments to be passed to ``requests.POST``
        """
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
        """Logs into reddit with supplied credentials using SSL.  Returns :class:`requests.Response` object, or raises :class:`exceptions.LoginFail` or :class:`exceptions.BadResponse`.
        
        URL: ``https://ssl.reddit.com/api/login``
        
        :param username: reddit username
        :param password: corresponding reddit password
        """
        data = dict(user=username, passwd=password, api_type='json')
        r = requests.post(LOGIN_URL, data=data)
        if r.status_code == 200:
            try:
                j = json.loads(r.content)
                self._cookies = r.cookies
                self._modhash = j['json']['data']['modhash']
                self._username = username
                return r
            except Exception:
                raise LoginFail()
        else:
            raise BadResponse(r)
    
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
        """GETs hot links.  If ``sr`` is ``None``, gets from main.  Returns :class:`things.Listing` object.
        
        URL: ``http://www.reddit.com/[r/<sr>]/?limit=<limit>``
        
        :param sr: subreddit name
        :param limit: max number of submissions to get
        """
        return self._subreddit_get(None, sr, limit)
    
    def new(self, sr=None, limit=None):
        """GETs new links.  If ``sr`` is ``None``, gets from main.  Returns :class:`things.Listing` object.
        
        URL: ``http://www.reddit.com/[r/<sr>/]new/?limit=<limit>``
        
        :param sr: subreddit name
        :param limit: max number of submissions to get
        """
        return self._subreddit_get('new', sr, limit)
    
    def top(self, sr=None, limit=None):
        """GETs top links.  If ``sr`` is ``None``, gets from main.  Returns :class:`things.Listing` object.
        
        URL: ``http://www.reddit.com/[r/<sr>/]top/?limit=<limit>``
        
        :param sr: subreddit name
        :param limit: max number of submissions to get
        """
        return self._subreddit_get('top', sr, limit)
    
    def controversial(self, sr=None, limit=None):
        """GETs controversial links.  If ``sr`` is ``None``, gets from main.  Returns :class:`things.Listing` object.
        
        URL: ``http://www.reddit.com/[r/<sr>/]controversial/?limit=<limit>``
        
        :param sr: subreddit name
        :param limit: max number of submissions to get
        """
        return self._subreddit_get('controversial', sr, limit)
    
    def comments(self, sr=None, limit=None):
        """GETs newest comments.  If ``sr`` is ``None``, gets all.  Returns :class:`things.Listing` object.
        
        URL: ``http://www.reddit.com/[r/<sr>/]comments/?limit=<limit>``
        
        :param sr: subreddit name
        :param limit: max number of comments to get
        """
        return self._subreddit_get('comments', sr, limit)
    
    def user(self, username):
        """GETs user info.  Returns :class:`things.Account` object.
        
        URL: ``http://www.reddit.com/user/<username>/about/``
        
        :param username: username of user to get info
        """
        return self.get('user', username, 'about')
    
    def subreddit(self, sr):
        """GETs subreddit info.  Returns :class:`things.Subreddit` object.
        
        URL: ``http://www.reddit.com/r/<sr>/about/``
        
        :param sr: subreddit name
        """
        return self.get('r', sr, 'about')
    
    def info(self, url):
        """GETs info about ``url``.  See https://github.com/reddit/reddit/wiki/API%3A-info.json.
        
        URL: ``http://www.reddit.com/api/info/?url=<url>``
        
        :param url: url
        """
        return self.get('api', 'info', params=dict(url=url))
    
    def search(self, query, limit=None):
        """Use reddit's search function.  Returns :class:`things.Listing` object.
        
        URL: ``http://www.reddit.com/search/?q=<query>&limit=<limit>``
        
        :param query: query string
        :param limit: max number of results to get
        """
        return self._limit_get('search', params=dict(q=query), limit=limit)
    
    def domain(self, domain_, limit=None):
        """GETs links from ``domain_``.  Returns :class:`things.Listing` object.
        
        URL: ``http://www.reddit.com/domain/?domain=<domain_>&limit=<limit>``
        
        :param domain: the domain, e.g. ``google.com``
        :param limit: max number of links to get
        """
        return self._limit_get('domain', domain_, limit=limit)
    
    def user_comments(self, user, limit=None):
        """GETs a user's posted comments.  Returns :class:`things.Listing` object.
        
        :param user: reddit username
        :param limit: max number of comments to return
        """
        return self._limit_get('user', user, 'comments', limit=limit)
    
    def user_submitted(self, user, limit=None):
        """GETs a user's submissions.  Returns :class:`things.Listing` object.
        
        :param user: reddit username
        :param limit: max number of submissions to return
        """
        return self._limit_get('user', user, 'submitted', limit=limit)
    
    def moderators(self, sr):
        """GETs moderators of subreddit ``sr``.  Returns :class:`things.ListBlob` object.
        
        **NOTE**: The :class:`things.Account` objects in the returned ListBlob *only* have ``id`` and ``name`` set.  This is because that's all reddit returns.  If you need full info on each moderator, you must individually GET them using :meth:`user` or :meth:`things.Account.about`.
        
        URL: ``http://www.reddit.com/r/<sr>/about/moderators/``
        
        :param sr: name of subreddit
        """
        userlist = self.get('r', sr, 'about', 'moderators')
        return _process_userlist(userlist)
    
    @_login_required
    def me(self):
        """Login required.  GETs info about logged in user.  Returns :class`things.Account` object.
        
        See https://github.com/reddit/reddit/wiki/API%3A-mine.json.
        
        URL: ``http://www.reddit.com/api/me/``
        """
        return self.get('api', 'me')
    
    @_login_required
    def mine(self, limit=None):
        """Login required.  GETs logged in user's subscribed subreddits.  Returns :class:`things.Listing` object.
        
        See https://github.com/reddit/reddit/wiki/API%3A-mine.json.
        
        URL: ``http://www.reddit.com/reddits/mine?limit=<limit>``
        
        :param limit: max number of subreddits to get
        """
        return self._limit_get('reddits', 'mine', limit=limit)
    
    @_login_required
    def saved(self, limit=None):
        """Login required.  GETs logged in user's saved submissions.  Returns :class:`things.Listing` object.
        
        URL: ``http://www.reddit.com/saved/``
        
        :param limit: max number of submissions to get
        """
        return self._limit_get('saved', limit=limit)
    
    @_login_required
    def vote(self, id_, dir_):
        """Login required.  POSTs a vote.  Returns :class:`requests.Response` object.
        
        See https://github.com/reddit/reddit/wiki/API%3A-vote.
        
        URL: ``http://www.reddit.com/api/vote/``
        
        :param id\_: full id of object voting on
        :param dir\_: direction of vote (1, 0, or -1)
        """
        data = dict(id=id_, dir=dir_)
        return self.post('api', 'vote', data=data)
    
    @_login_required
    def upvote(self, id_):
        """Login required.  POSTs an upvote (1).  Returns :class:`requests.Response` object.
        
        See https://github.com/reddit/reddit/wiki/API%3A-vote.
        
        URL: ``http://www.reddit.com/api/vote/``
        
        :param id\_: full id of object voting on
        """
        return self.vote(id_, 1)
    
    @_login_required
    def downvote(self, id_):
        """Login required.  POSTs a downvote (-1).  Returns :class:`requests.Response` object.
        
        See https://github.com/reddit/reddit/wiki/API%3A-vote.
        
        URL: ``http://www.reddit.com/api/vote/``
        
        :param id\_: full id of object voting on
        """
        return self.vote(id_, -1)
    
    @_login_required
    def unvote(self, id_):
        """Login required.  POSTs a null vote (0).  Returns :class:`requests.Response` object.
        
        See https://github.com/reddit/reddit/wiki/API%3A-vote.
        
        URL: ``http://www.reddit.com/api/vote/``
        
        :param id\_: full id of object voting on
        """
        return self.vote(id_, 0)
    
    @_login_required
    def comment(self, parent, text):
        """Login required.  POSTs a comment in response to ``parent``.  Returns :class:`things.Comment` object.
        
        See https://github.com/reddit/reddit/wiki/API%3A-comment.
        
        URL: ``http://www.reddit.com/api/comment/``
        
        :param parent: full id of thing commenting on
        :param text: comment text
        """
        data = dict(parent=parent, text=text)
        r = self.post('api', 'comment', data=data)
        try:
            j = json.loads(r.content)
            data_dict = pull_data_dict(j['jquery'])
            return self._thingify(data_dict)
        except Exception:
            raise BadResponse(r)
    
    @_login_required
    def edit(self, id_, text):
        """Login required.  Sends POST to change selftext or comment text to ``text``.  Returns :class:`things.Comment` or :class:`things.Link` object depending on what's being edited.
        
        URL: ``http://www.reddit.com/api/editusertext/``
        
        :param id\_: full id of link or comment to edit
        :param text: new self or comment text
        """
        data = dict(thing_id=id_, text=text)
        r = self.post('api', 'editusertext', data=data)
        try:
            j = json.loads(r.content)
            data_dict = pull_data_dict(j['jquery'])
            return self._thingify(data_dict)
        except Exception:
            raise BadResponse(r)
    
    @_login_required
    def _submit(self, sr, title, kind, url=None, text=None, follow=True):
        data = dict(title=title, sr=sr, kind=kind)
        if kind == 'link':
            data['url'] = url
        elif kind == 'self':
            data['text'] = text
        r = self.post('api', 'submit', data=data)
        try:
            m = SUBMIT_RESPONSE_LINK_PATTERN.search(r.content)
            if follow:
                r2 = self.get(urlparse(m.group(1)).path)
                link = r2[0][0]
                return link
            else:
                return m.group(1)
        except Exception:
            raise BadResponse(r)
    
    @_login_required
    def submit_link(self, sr, title, url, follow=True):
        """Login required.  POSTs a link submission.  Returns :class:`things.Link` object if ``follow=True`` (default), or the string permalink of the new submission otherwise.
        
        Argument ``follow`` exists because reddit only returns the permalink after POSTing a submission.  In order to get detailed info on the new submission, we need to make another request.  If you don't want to make that additional request, just set ``follow=False``.
        
        See https://github.com/reddit/reddit/wiki/API%3A-submit.
        
        URL: ``http://www.reddit.com/api/submit/``
        
        :param sr: name of subreddit to submit to
        :param title: title of submission
        :param url: submission link
        :param follow: set to ``True`` to follow retrieved permalink to return detailed :class:`things.Link` object.  ``False`` to just return permalink.
        :type follow: bool
        """
        return self._submit(sr, title, 'link', url=url, follow=follow)
    
    @_login_required
    def submit_text(self, sr, title, text, follow=True):
        """Login required.  POSTs a text submission.  Returns :class:`things.Link` object if ``follow=True`` (default), or the string permalink of the new submission otherwise.
        
        Argument ``follow`` exists because reddit only returns the permalink after POSTing a submission.  In order to get detailed info on the new submission, we need to make another request.  If you don't want to make that additional request, set ``follow=False``.
        
        See https://github.com/reddit/reddit/wiki/API%3A-submit.
        
        URL: ``http://www.reddit.com/api/submit/``
        
        :param sr: name of subreddit to submit to
        :param title: title of submission
        :param text: submission self text
        :param follow: set to ``True`` to follow retrieved permalink to return detailed :class:`things.Link` object.  ``False`` to just return permalink.
        :type follow: bool
        """
        return self._submit(sr, title, 'self', text=text, follow=follow)
    
    @_login_required
    def delete(self, id_):
        """Login required.  Send POST to delete an object.  Returns :class:`requests.Response` object.
        
        URL: ``http://www.reddit.com/api/del/``
        
        :param sr: full id of object to delete   
        """
        data = dict(id=id_)
        return self.post('api', 'del', data=data)
    
    @_login_required
    def save(self, id_):
        """Login required.  Sends POST to save a link.  Returns :class:`requests.Response` object.
        
        See https://github.com/reddit/reddit/wiki/API%3A-save.
        
        URL: ``http://www.reddit.com/api/save/``
        
        :param id\_: full id of link to save
        """
        data = dict(id=id_)
        return self.post('api', 'save', data=data)
    
    @_login_required
    def unsave(self, id_):
        """Login required.  Sends POST to unsave a link.  Returns :class:`requests.Response` object.
        
        See https://github.com/reddit/reddit/wiki/API%3A-unsave.
        
        URL: ``http://www.reddit.com/api/unsave/``
        
        :param id\_: full id of link to unsave
        """
        data = dict(id=id_)
        return self.post('api', 'unsave', data=data)
    
    @_login_required
    def hide(self, id_):
        """Login required.  Sends POST to hide a link.  Returns :class:`requests.Response` object.
        
        See https://github.com/reddit/reddit/wiki/API%3A-hide.
        
        URL: ``http://www.reddit.com/api/hide/``
        
        :param id\_: full id of link to hide
        """
        data = dict(id=id_)
        return self.post('api', 'hide', data=data)
    
    @_login_required
    def unhide(self, id_):
        """Login required.  Sends POST to unhide a link.  Returns :class:`requests.Response` object.
        
        See https://github.com/reddit/reddit/wiki/API%3A-unhide.
        
        URL: ``http://www.reddit.com/api/unhide/``
        
        :param id\_: full id of link to unhide
        """
        data = dict(id=id_)
        return self.post('api', 'unhide', data=data)
    
    @_login_required
    def marknsfw(self, id_):
        """Login required.  Sends POST to mark link as NSFW.  Returns :class:`requests.Response` object.
        
        URL: ``http://www.reddit.com/api/marknsfw/``
        
        :param id\_: full id of link to mark
        """
        data = dict(id=id_)
        return self.post('api', 'marknsfw', data=data)
    
    @_login_required
    def unmarknsfw(self, id_):
        """Login required.  Sends POST to unmark link as NSFW.  Returns :class:`requests.Response` object.
        
        URL: ``http://www.reddit.com/api/unmarknsfw/``
        
        :param id\_: full id of link to unmark
        """
        data = dict(id=id_)
        return self.post('api', 'unmarknsfw', data=data)
    
    @_login_required
    def report(self, id_):
        """Login required.  Sends POST to report a link.  Returns :class:`requests.Response` object.
        
        URL: ``http://www.reddit.com/api/report/``
        
        :param id\_: full id of link to report
        """
        data = dict(id=id_)
        return self.post('api', 'report', data=data)
    
    # reddit seems to block bots from sharing, so this doesnt work :(
    @_login_required
    def share(self, parent, share_from, replyto, share_to, message):
        data = dict(parent=parent, share_from=share_from, replyto=replyto, share_to=share_to, message=message)
        return self.post('api', 'share', data=data)
    
    @_login_required
    def message(self, to, subject, text):
        """Alias for :meth:`compose`."""
        return self.compose(to, subject, text)
    
    @_login_required
    def compose(self, to, subject, text):
        """Login required.  Sends POST to send a message to a user.  Returns :class:`requests.Response` object.
        
        URL: ``http://www.reddit.com/api/compose/``
        
        :param to: username or :class`things.Account` of user to send to
        :param subject: subject of message
        :param text: message body text
        """
        if isinstance(to, Account):
            to = to.name
        data = dict(to=to, subject=subject, text=text)
        return self.post('api', 'compose', data=data)
    
    @_login_required
    def read_message(self, id_):
        """Login required.  Send POST to mark a message as read.  Returns :class:`requests.Response` object.
        
        URL: ``http://www.reddit.com/api/read_message/``
        
        :param id\_: full id of message to mark
        """
        data = dict(id=id_)
        return self.post('api', 'read_message', data=data)
    
    @_login_required
    def unread_message(self, id_):
        """Login required.  Send POST to unmark a message as read.  Returns :class:`requests.Response` object.
        
        URL: ``http://www.reddit.com/api/unread_message/``
        
        :param id\_: full id of message to unmark
        """
        data = dict(id=id_)
        return self.post('api', 'unread_message', data=data)
    
    @_login_required
    def hide_message(self, id_):
        """Login required.  Send POST to hide a message.  Returns :class:`requests.Response` object.
        
        URL: ``http://www.reddit.com/api/hide_message/``
        
        :param id\_: full id of message to hide
        """
        data = dict(id=id_)
        return self.post('api', 'hide_message', data=data)
    
    @_login_required
    def unhide_message(self, id_):
        """Login required.  Send POST to unhide a message.  Returns :class:`requests.Response` object.
        
        URL: ``http://www.reddit.com/api/unhide_message/``
        
        :param id\_: full id of message to unhide
        """
        data = dict(id=id_)
        return self.post('api', 'unhide_message', data=data)
    
    @_login_required
    def subscribe(self, sr):
        """Login required.  Send POST to subscribe to a subreddit.  If ``sr`` is the name of the subreddit, a GET request is sent to retrieve the full id of the subreddit, which is necessary for this API call.  Returns :class:`requests.Response` object.
        
        URL: ``http://www.reddit.com/api/subscribe/``
        
        :param sr: full id of subreddit or name of subreddit (full id is preferred)
        """
        if not sr.startswith('t5_'):
            sr = self.subreddit(sr).name
        data = dict(action='sub', sr=sr)
        return self.post('api', 'subscribe', data=data)
    
    @_login_required
    def unsubscribe(self, sr):
        """Login required.  Send POST to unsubscribe to a subreddit.  If ``sr`` is the name of the subreddit, a GET request is sent to retrieve the full id of the subreddit, which is necessary for this API call.  Returns :class:`requests.Response` object.
        
        URL: ``http://www.reddit.com/api/unsubscribe/``
        
        :param sr: full id of subreddit or name of subreddit (full id is preferred)   
        """
        if not sr.startswith('t5_'):
            sr = self.subreddit(sr).name
        data = dict(action='unsub', sr=sr)
        return self.post('api', 'subscribe', data=data)
    
    @_login_required
    def inbox(self, limit=None):
        """Login required.  GETs logged in user's inbox. Returns :class:`things.Listing` object.
        
        URL: ``http://www.reddit.com/message/inbox/``
        
        :param limit: max number of objects to get
        """
        return self._limit_get('message', 'inbox', limit=limit)
    
    @_login_required
    def unread(self, limit=None):
        """Login required.  GETs logged in user's unread. Returns :class:`things.Listing` object.
        
        URL: ``http://www.reddit.com/message/unread/``
        
        :param limit: max number of objects to get
        """
        return self._limit_get('message', 'unread', limit=limit)
    
    @_login_required
    def messages(self, limit=None):
        """Login required.  GETs logged in user's messages. Returns :class:`things.Listing` object.
        
        URL: ``http://www.reddit.com/message/messages/``
        
        :param limit: max number of messages to get
        """
        return self._limit_get('message', 'messages', limit=limit)
    
    @_login_required
    def commentreplies(self, limit=None):
        """Login required.  GETs logged in user's comment replies. Returns :class:`things.Listing` object.
        
        URL: ``http://www.reddit.com/message/comments/``
        
        :param limit: max number of comment replies to get
        """
        return self._limit_get('message', 'comments', limit=limit)
    
    @_login_required
    def postreplies(self, limit=None):
        """Login required.  GETs logged in user's post replies. Returns :class:`things.Listing` object.
        
        URL: ``http://www.reddit.com/message/selfreply/``
        
        :param limit: max number of post replies to get
        """
        return self._limit_get('message', 'selfreply', limit=limit)
    
    @_login_required
    def sent(self, limit=None):
        """Login required.  GETs logged in user's sent messages. Returns :class:`things.Listing` object.
        
        URL: ``http://www.reddit.com/message/sent/``
        
        :param limit: max number of messages to get
        """
        return self._limit_get('message', 'sent', limit=limit)
    
    @_login_required
    def modmail(self, limit=None):
        """Login required.  GETs logged in user's modmail. Returns :class:`things.Listing` object.
        
        URL: ``http://www.reddit.com/message/moderator/``
        
        :param limit: max number of messages to get
        """
        return self._limit_get('message', 'moderator', limit=limit)
    
    @_login_required
    def liked(self, limit=None):
        """GETs logged-in user's liked submissions.  Returns :class:`things.Listing` object.
        
        :param limit: max number of submissions to get 
        """
        return self._limit_get('user', self._username, 'liked', limit=limit)
    
    @_login_required
    def disliked(self, limit=None):
        """GETs logged-in user's disliked submissions.  Returns :class:`things.Listing` object.
        
        :param limit: max number of submissions to get 
        """
        return self._limit_get('user', self._username, 'disliked', limit=limit)
    
    @_login_required
    def hidden(self, limit=None):
        """GETs logged-in user's hidden submissions.  Returns :class:`things.Listing` object.
        
        :param limit: max number of submissions to get 
        """
        return self._limit_get('user', self._username, 'hidden', limit=limit)
    
    @_login_required
    def approve(self, id_):
        """Login required.  Sends POST to approve a submission. Returns :class:`things.Listing` object.
        
        URL: ``http://www.reddit.com/api/approve/``
        
        :param limit: full id of submission to approve
        """
        data = dict(id=id_)
        return self.post('api', 'approve', data=data)
    
    @_login_required
    def remove(self, id_):
        """Login required.  Sends POST to remove a submission or comment. Returns :class:`things.Listing` object.
        
        URL: ``http://www.reddit.com/api/remove/``
        
        :param limit: full id of object to remove
        """
        data = dict(id=id_)
        return self.post('api', 'remove', data=data)
    
    @_login_required
    def distinguish(self, id_, how):
        """Login required.  Sends POST to distinguish a submission or comment. Returns :class:`requests.Response` object.
        
        URL: ``http://www.reddit.com/api/distinguish/``
        
        :param id\_: full id of object to distinguish
        :param how: either True, False, or 'admin'
        """
        if how not in (True, False, 'admin'):
            raise ValueError("how must be either True, False, or 'admin'")
        data = dict(id=id_, how=how)
        return self.post('api', 'distinguish', data=data)
    
    @_login_required
    def flairlist(self, r, limit=1000, after=None, before=None):
        """Login required.  See https://github.com/reddit/reddit/wiki/API%3A-flairlist.  Returns :class:`requests.Response` object.
        
        URL: ``http://www.reddit.com/api/flairlist``
        
        :param r: name of subreddit
        :param limit: max number of items to return
        :param after: full id of user to return entries after
        :param before: full id of user to return entries *before* 
        """
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
        """Login required.  See https://github.com/reddit/reddit/wiki/API%3A-flair.  Returns :class:`requests.Response` object.
        
        URL: ``http://www.reddit.com/api/flair``
        
        :param r: name of subreddit
        :param name: name of the user
        :param text: flair text to assign
        :param css_class: CSS class to assign to flair text
        """
        data = dict(r=r, name=name, text=text, css_class=css_class)
        return self.post('api', 'flair', data=data)

    @_login_required
    def flaircsv(self, r, flair_csv):
        """Login required.  See https://github.com/reddit/reddit/wiki/API%3A-flaircsv.  Returns :class:`requests.Response` object.
        
        URL: ``http://www.reddit.com/api/flaircsv``
        
        :param r: name of subreddit
        :param flair_csv: csv file contents
        """
        data = dict(r=r, flair_csv=flair_csv)
        return self.post('api', 'flaircsv', data=data)
    
    @_login_required
    def contributors(self, sr):
        """Login required.  GETs list of contributors to subreddit ``sr``. Returns :class:`things.ListBlob` object.
        
        **NOTE**: The :class:`things.Account` objects in the returned ListBlob *only* have ``id`` and ``name`` set.  This is because that's all reddit returns.  If you need full info on each contributor, you must individually GET them using :meth:`user` or :meth:`things.Account.about`.
        
        URL: ``http://www.reddit.com/r/<sr>/about/contributors/``
        
        :param sr: name of subreddit
        """
        userlist = self.get('r', sr, 'about', 'contributors')
        return _process_userlist(userlist)


def connect(*args, **kwargs):
    """Just an alias to instantiate :class:`Reddit`, really."""
    return Reddit(*args, **kwargs)