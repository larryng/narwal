# -*- coding: utf-8 -*-

import random
import string
import time

import sys
import os
sys.path.insert(0, os.path.abspath('..'))

import requests
from nose.tools import raises, eq_, ok_

from narwal.reddit import Reddit, _limit_rate, _login_required
from narwal.const import DEFAULT_USER_AGENT, API_PERIOD
from narwal.exceptions import LoginFail, NotLoggedIn, BadResponse
from narwal import things

from .common import TEST_AGENT 


def genstr(length=16):
    return ''.join([random.choice(string.ascii_letters) for _ in xrange(length)]) 


def setup():
    global USERNAME, PASSWORD, reddit
    path = os.path.join(os.path.dirname(__file__), os.path.pardir, 'LOGIN')
    with open(path, 'r') as f:
        USERNAME, PASSWORD = f.read().split(' ')


class test_login():
    
    def setup(self):
        self.reddit = Reddit(user_agent=TEST_AGENT)
    
    '''
    # if we run this test too many times, reddit blocks us, so i'm leaving it
    # commented out.
    @raises(LoginFail)
    def test_fail(self):
        self.reddit.login(genstr(), genstr())
    '''
    
    def test_success(self):
        r = self.reddit.login(USERNAME, PASSWORD)
        eq_(r.status_code, 200)
        ok_('reddit_session' in self.reddit._cookies)
        ok_(self.reddit._modhash)
        eq_(self.reddit._username, USERNAME)


class test_logged_in():
    
    def setup(self):
        self.reddit = Reddit(user_agent=TEST_AGENT)
    
    def test(self):
        eq_(self.reddit.logged_in, False)
        self.reddit.login(USERNAME, PASSWORD)
        eq_(self.reddit.logged_in, True)


class test_reddit___init__():
    
    @raises(ValueError)
    def test_respect_and_no_user_agent(self):
        Reddit()
    
    def test_no_respect_and_no_user_agent(self):
        r = Reddit(respect=False)
        eq_(r._user_agent, DEFAULT_USER_AGENT)
    
    def test_normal(self):
        r = Reddit(user_agent=TEST_AGENT)
        eq_(r._respect, True)
        eq_(r._user_agent, TEST_AGENT)
    
    def test_auto_login(self):
        r = Reddit(USERNAME, PASSWORD, user_agent=TEST_AGENT)
        eq_(r.logged_in, True)


class test__inject_request_kwargs():
    
    def test_not_logged_in(self):
        r = Reddit(user_agent=TEST_AGENT)
        
        result = r._inject_request_kwargs({})
        eq_(result, {'headers': {'User-Agent': TEST_AGENT}})
        
        result = r._inject_request_kwargs({'headers': {'User-Agent': 'dummy'}})
        eq_(result['headers'], {'User-Agent': 'dummy'})
        
        result = r._inject_request_kwargs({'other': 'other', 'headers': {'stuff': 'stuff'}})
        eq_(result['other'], 'other')
        eq_(result['headers']['stuff'], 'stuff')
        eq_(result['headers']['User-Agent'], TEST_AGENT)

    def test_logged_in(self):
        r = Reddit(USERNAME, PASSWORD, user_agent=TEST_AGENT)
        
        result = r._inject_request_kwargs({})
        eq_(result['cookies'], r._cookies)
        eq_(result['headers']['User-Agent'], TEST_AGENT)


class test__limit_rate():
    
    def test(self):
        
        class RedditTester(Reddit):
            @_limit_rate
            def _test_function(inner):
                self.dummy += 1
        
        self.dummy = 0
        
        r = RedditTester(user_agent=TEST_AGENT)
        ok_(r._last_request_time is None)
        
        t0 = time.time()
        
        r._test_function()
        elapsed = time.time() - t0
        eq_(self.dummy, 1)
        ok_(elapsed <= .01)
        
        r._test_function()
        elapsed = time.time() - t0
        eq_(self.dummy, 2)
        ok_(API_PERIOD-.01 <= elapsed <= API_PERIOD+.01)


class test__login_required():
    
    def setup(self):
        
        class RedditTester(Reddit):
            @_login_required
            def _test_function(inner):
                self.dummy += 1
        
        self.dummy = 0
        self.reddit = RedditTester(user_agent=TEST_AGENT)
    
    @raises(NotLoggedIn)
    def test_fail(self):
        self.reddit._test_function()
    
    def test_normal(self):
        self.reddit.login(USERNAME, PASSWORD)
        self.reddit._test_function()
        eq_(self.dummy, 1)


class test__thingify():
    def setup(self):
        self.reddit = Reddit(user_agent=TEST_AGENT)
    
    def test_atoms(self):
        for i in [42, 'foobar', True]:
            eq_(self.reddit._thingify(i), i)
    
    def test_unescape_unicode(self):
        eq_(self.reddit._thingify(u'&amp;#34; &amp;#229;'), u'" å')
    
    def test_empty_dict(self):
        ok_(isinstance(self.reddit._thingify({}), things.Blob))
    
    def test_empty_list(self):
        ok_(isinstance(self.reddit._thingify([]), things.ListBlob))
    
    def test_dict_non_thing(self):
        v = self.reddit._thingify({'foo': 'bar'})
        ok_(isinstance(v, things.Blob))
        eq_(v.foo, 'bar')
    
    def test_dict_basic(self):
        v = self.reddit._thingify({'kind': 't1',
                                   'data': {'foo': 'bar'}})
        ok_(isinstance(v, things.Comment))
        eq_(v.foo, 'bar')
    
    def test_list_basic(self):
        v = self.reddit._thingify([{'kind': 't1',
                                    'data': {'foo': 'bar'}},
                                   {'baz': 'bam'}])
        ok_(isinstance(v, things.ListBlob))
        ok_(isinstance(v[0], things.Comment))
        ok_(isinstance(v[1], things.Blob))
        eq_(v[0].foo, 'bar')
        eq_(v[1].baz, 'bam')
    
    def test_nested(self):
        path = "/some/path"
        v = self.reddit._thingify(
            [{'foo': 'bar'},
             [{'kind': 't2',
               'data': {'hello': 'world',
                        'last': [{'one': 1}]}}]],
            path=path
        )
        
        ok_(isinstance(v, things.ListBlob))
        ok_(isinstance(v[0], things.Blob))
        ok_(isinstance(v[1], things.ListBlob))
        ok_(isinstance(v[1][0], things.Account))
        ok_(isinstance(v[1][0].last, things.ListBlob))
        ok_(isinstance(v[1][0].last[0], things.Blob))
        
        eq_(v[0].foo, 'bar')
        eq_(v[1][0].hello, 'world')
        eq_(v[1][0].last[0].one, 1)
        
        eq_(v._path, path)
        eq_(v[0]._path, path)
        eq_(v[1]._path, path)
        eq_(v[1][0]._path, path)
        eq_(v[1][0].last._path, path)
        eq_(v[1][0].last[0]._path, path)


class test_get():
    
    def setup(self):
        self.reddit = Reddit(user_agent=TEST_AGENT)
    
    def test_basic(self):
        r = self.reddit.get()
        ok_(isinstance(r, things.Listing))
        
        r = self.reddit.get('r', 'test')
        ok_(isinstance(r, things.Listing))

        r = self.reddit.get('comments', params={'limit': 3})
        ok_(isinstance(r, things.Listing))
        eq_(len(r), 3)
    
    def test_badresponse(self):
        try:
            self.reddit.get(genstr(), genstr())
        except Exception as e:
            ok_(isinstance(e, BadResponse))
            ok_(isinstance(e.response, requests.Response))
            ok_(e.response.status_code != 200)


class test__limit_get():
    
    def setup(self):
        self.reddit = Reddit(user_agent=TEST_AGENT)
    
    def test_no_limit(self):
        r = self.reddit._limit_get()
        s = self.reddit.get()
        ok_(isinstance(r, things.Listing))
        eq_(len(r), len(s))
        ok_(r._limit is None)
    
    def test_limit_normal(self):
        r = self.reddit._limit_get(limit=10)
        ok_(isinstance(r, things.Listing))
        eq_(len(r), 10)
        eq_(r._limit, 10)
    
    def test_limit_already_params(self):
        r = self.reddit._limit_get(params={}, limit=10)
        ok_(isinstance(r, things.Listing))
        eq_(len(r), 10)
        eq_(r._limit, 10)
    
    def test_limit_already_limit_in_params(self):
        r = self.reddit._limit_get(params={'limit': 5}, limit=10)
        ok_(isinstance(r, things.Listing))
        eq_(len(r), 10)
        eq_(r._limit, 10)


class test__subreddit_get():
    
    def setup(self):
        self.reddit = Reddit(user_agent=TEST_AGENT)
    
    def test(self):
        r = self.reddit._subreddit_get('pics', None)
        ok_(all([i.subreddit == 'pics' and isinstance(i, things.Link) for i in r]))
        
        r = self.reddit._subreddit_get('funny', 'comments', limit=7)
        ok_(all([i.subreddit == 'funny' and isinstance(i, things.Comment) for i in r]))
        eq_(len(r), 7)


class test_basic_getters():
    
    def setup(self):
        self.reddit = Reddit(user_agent=TEST_AGENT)
    
    def test_hot(self):
        ok_(isinstance(self.reddit.hot(), things.Listing))
    
    def test_new(self):
        ok_(isinstance(self.reddit.new(), things.Listing))
    
    def test_top(self):
        ok_(isinstance(self.reddit.top(), things.Listing))
    
    def test_controversial(self):
        ok_(isinstance(self.reddit.controversial(), things.Listing))
    
    def test_comments(self):
        ok_(isinstance(self.reddit.comments(), things.Listing))
    
    def test_user(self):
        ok_(isinstance(self.reddit.user('kn0thing'), things.Account))
    
    def test_subreddit(self):
        ok_(isinstance(self.reddit.subreddit('pics'), things.Subreddit))
    
    def test_info(self):
        ok_(isinstance(self.reddit.info('http://www.reddit.com/'), things.Listing))
    
    def test_search(self):
        ok_(isinstance(self.reddit.search('test post'), things.Listing))
    
    def test_domain(self):
        ok_(isinstance(self.reddit.domain('reddit.com'), things.Listing))
    
    def test_user_comments(self):
        ok_(isinstance(self.reddit.user_comments('alienth'), things.Listing))
    
    def test_user_submitted(self):
        ok_(isinstance(self.reddit.user_comments('chromakode'), things.Listing))
    
    def test_moderators(self):
        ok_(isinstance(self.reddit.moderators('politics'), things.ListBlob))