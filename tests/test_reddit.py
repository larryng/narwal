import random
import string
import time

import sys
import os
sys.path.insert(0, os.path.abspath('..'))

from nose.tools import raises, eq_, ok_, timed

from narwal.reddit import Reddit, _limit_rate, _login_required
from narwal.const import DEFAULT_USER_AGENT, API_PERIOD
from narwal.exceptions import LoginFail, NotLoggedIn


TEST_AGENT = 'narwal (goo.gl/IBenG) testing' 


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
    pass