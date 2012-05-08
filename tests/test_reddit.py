# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.abspath('..'))

import time
import random
import requests
from functools import partial 
from nose.tools import raises, eq_, ok_

from narwal.reddit import Reddit, _limit_rate, _login_required
from narwal.const import DEFAULT_USER_AGENT, API_PERIOD
from narwal.exceptions import LoginFail, NotLoggedIn, BadResponse
from narwal import things

from .common import TEST_AGENT, genstr  


USERNAME = 'reddit'
PASSWORD = 'password'
USERNAME2 = 'larry'
PASSWORD2 = 'password'
TEST_SR = 'reddit_test1'
CREATED_SR = 'myreddit'

# TODO: document prerequisites for running these tests

class test_login():
    
    def setup(self):
        self.reddit = Reddit(user_agent=TEST_AGENT, respect=False)
    
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
        self.reddit = Reddit(user_agent=TEST_AGENT, respect=False)
    
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


def _opposite_pair_test_helper(link, attr, ftrue, ffalse):
    def testval():
        return getattr(link, attr)
    
    if testval():
        ok_(ftrue(link))
        link = link.refresh()
        ok_(not testval())
        
        ok_(ffalse(link))
        link = link.refresh()
        ok_(testval())
    else:
        ok_(ffalse(link))
        link = link.refresh()
        ok_(testval())
        
        ok_(ftrue(link))
        link = link.refresh()
        ok_(not testval())


def _limit_getter_test_helper(f):
    ok_(isinstance(f(), things.Listing))
    ok_(isinstance(f(limit=random.randint(1, 100)), things.Listing))


class test__inject_post_data():
    
    def test_not_logged_in(self):
        r = Reddit(user_agent=TEST_AGENT)
        
        result = r._inject_post_data({})
        eq_(result, {'data': {'api_type': 'json'}})
        
        result = r._inject_post_data({'a': 1})
        eq_(result['a'], 1)
        eq_(result['data']['api_type'], 'json')
        
        result = r._inject_post_data({'data': {'api_type': 'not'}})
        eq_(result['data']['api_type'], 'not')

    def test_logged_in(self):
        r = Reddit(USERNAME, PASSWORD, user_agent=TEST_AGENT)
        
        result = r._inject_post_data({})
        eq_(result['data']['uh'], r._modhash)


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
        self.reddit = RedditTester(user_agent=TEST_AGENT, respect=False)
    
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
        self.reddit = Reddit(user_agent=TEST_AGENT, respect=False)
    
    def test_basic(self):
        r = self.reddit.get()
        ok_(isinstance(r, things.Listing))
        
        r = self.reddit.get('r', TEST_SR)
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
        self.reddit = Reddit(user_agent=TEST_AGENT, respect=False)
    
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
        self.reddit = Reddit(user_agent=TEST_AGENT, respect=False)
    
    def test(self):
        r = self.reddit._subreddit_get(TEST_SR, None)
        ok_(all([i.subreddit == TEST_SR and isinstance(i, things.Link) for i in r]))
        
        r = self.reddit._subreddit_get(TEST_SR, 'comments', limit=4)
        ok_(all([i.subreddit == TEST_SR and isinstance(i, things.Comment) for i in r]))
        eq_(len(r), 4)


class test_getters():
    
    def setup(self):
        self.reddit = Reddit(user_agent=TEST_AGENT, respect=False)
    
    def test_hot(self):
        _limit_getter_test_helper(self.reddit.hot)
    
    def test_new(self):
        _limit_getter_test_helper(self.reddit.new)
    
    def test_top(self):
        _limit_getter_test_helper(self.reddit.top)
    
    def test_controversial(self):
        _limit_getter_test_helper(self.reddit.controversial)
    
    def test_comments(self):
        _limit_getter_test_helper(self.reddit.comments)
    
    def test_user(self):
        ok_(isinstance(self.reddit.user('reddit'), things.Account))
    
    def test_subreddit(self):
        ok_(isinstance(self.reddit.subreddit(TEST_SR), things.Subreddit))
    
    def test_info(self):
        f = partial(self.reddit.info, 'http://www.google.com/')
        _limit_getter_test_helper(f)
    
    def test_search(self):
        f = partial(self.reddit.search, 'test post')
        _limit_getter_test_helper(f)
    
    def test_domain(self):
        f = partial(self.reddit.domain, 'google.com')
        _limit_getter_test_helper(f)
    
    def test_user_comments(self):
        f = partial(self.reddit.user_comments, 'reddit')
        _limit_getter_test_helper(f)
    
    def test_user_submitted(self):
        f = partial(self.reddit.user_submitted, 'reddit')
        _limit_getter_test_helper(f)
    
    def test_moderators(self):
        ok_(isinstance(self.reddit.moderators(TEST_SR), things.ListBlob))
        ok_(isinstance(self.reddit.moderators(TEST_SR, limit=random.randint(1, 100)), things.ListBlob))
    

class test_logged_in_getters():
    
    def setup(self):
        self.reddit = Reddit(USERNAME, PASSWORD, user_agent=TEST_AGENT, respect=False)
    
    def test_me(self):
        a = self.reddit.me()
        ok_(isinstance(a, things.Account))
        eq_(a.name, USERNAME)
    
    def test_mine(self):
        _limit_getter_test_helper(self.reddit.mine)
        _limit_getter_test_helper(partial(self.reddit.mine, 'contributor'))
        _limit_getter_test_helper(partial(self.reddit.mine, 'moderator'))
    
    def test_inbox(self):
        _limit_getter_test_helper(self.reddit.inbox)
    
    def test_unread(self):
        _limit_getter_test_helper(self.reddit.unread)
    
    def test_messages(self):
        _limit_getter_test_helper(self.reddit.messages)
    
    def test_commentreplies(self):                                                                                   
        _limit_getter_test_helper(self.reddit.commentreplies)                                                         
                                                                                                                     
    def test_postreplies(self):                                                                                      
        _limit_getter_test_helper(self.reddit.postreplies)                                                            
                                                                                                                     
    def test_sent(self):                                                                                             
        _limit_getter_test_helper(self.reddit.sent)                                                                   
                                                                                                                     
    def test_modmail(self):                                                                                          
        _limit_getter_test_helper(self.reddit.modmail)                                                                

    def test_liked(self):
        _limit_getter_test_helper(self.reddit.liked)

    def test_disliked(self):
        _limit_getter_test_helper(self.reddit.disliked)

    def test_hidden(self):
        _limit_getter_test_helper(self.reddit.hidden)
    
    def test_contributors(self):
        ok_(isinstance(self.reddit.contributors(CREATED_SR), things.ListBlob))
        ok_(isinstance(self.reddit.contributors(CREATED_SR, limit=random.randint(1, 100)), things.ListBlob))


class test_posters():
    
    def setup(self):
        self.reddit = Reddit(USERNAME, PASSWORD, user_agent=TEST_AGENT, respect=False)
        self.link = self.reddit.hot()[0]
        self.created = []
    
    def test_vote(self):
        l = self.link
        ok_(self.reddit.vote(l.name, 1))
        l = l.refresh()
        eq_(l.likes, True)
        
        ok_(self.reddit.vote(l.name, 0))
        l = l.refresh()
        eq_(l.likes, None)
        
        ok_(self.reddit.vote(l.name, -1))
        l = l.refresh()
        eq_(l.likes, False)
    
    def test_upvote(self):
        l = self.link
        ok_(self.reddit.upvote(l.name))
        l = l.refresh()
        eq_(l.likes, True)
    
    def test_downvote(self):
        l = self.link
        ok_(self.reddit.downvote(l.name))
        l = l.refresh()
        eq_(l.likes, False)
    
    def test_unvote(self):
        l = self.link
        ok_(self.reddit.unvote(l.name))
        l = l.refresh()
        eq_(l.likes, None)
    
    def test_comment_and_edit(self):
        s = genstr()
        c = self.link.comment(s)
        if c:
            self.created.append(c)
            
        eq_(c.author, USERNAME)
        eq_(c.parent_id, self.link.name)
        eq_(c.body, s)
        
        s = genstr()
        c = c.edit(s)
        eq_(c.body, s)
    
    def test_submit_link(self):
        t = genstr()
        u = 'http://www.google.com/?t={0}'.format(t)
        l = self.reddit.submit_link(TEST_SR, t, u)
        if l:
            self.created.append(l)
        
        eq_(l.subreddit, TEST_SR)
        eq_(l.author, USERNAME)
        eq_(l.title, t)
        eq_(l.url, u)
    
    def test_submit_text_and_edit(self):
        t = genstr()
        b = genstr()
        l = self.reddit.submit_text(TEST_SR, t, b)
        if l:
            self.created.append(l)
            
        eq_(l.subreddit, TEST_SR)
        eq_(l.author, USERNAME)
        eq_(l.title, t)
        eq_(l.selftext, b)
        
        b = genstr()
        l = l.edit(b)
        eq_(l.selftext, b)
    
    # TODO: test delete
    
    def test_save_and_unsave(self):
        _opposite_pair_test_helper(
            self.link,
            'saved',
            lambda l: self.reddit.unsave(l.name),
            lambda l: self.reddit.save(l.name)
        )
    
    def test_hide_and_unhide(self):
        _opposite_pair_test_helper(
            self.link,
            'hidden',
            lambda l: self.reddit.unhide(l.name),
            lambda l: self.reddit.hide(l.name)
        )
    
    def test_marknsfw_and_unmarknsfw(self):
        link = self.reddit.submit_text(TEST_SR, 'foo', 'bar')
        if link:
            self.created.append(link)
        _opposite_pair_test_helper(
            link,
            'over_18',
            lambda l: self.reddit.unmarknsfw(l.name),
            lambda l: self.reddit.marknsfw(l.name)
        )
    
    def test_report(self):
        link = self.reddit.submit_text(CREATED_SR, 'foo', 'bar')
        if link:
            self.created.append(link)
        ok_(self.reddit.report(link.name))
        link = link.refresh()
        eq_(link.num_reports, 1)
        # need to test it was actually reported
    
    def test_compose_read_and_unread_message(self):
        r2 = Reddit(USERNAME2, PASSWORD2, user_agent=TEST_AGENT, respect=False)
        ok_(self.reddit.compose(USERNAME2, 'foo', 'bar'))
        m = r2.unread()[0]
        ok_(m.new)
        eq_(m.author, USERNAME)
        eq_(m.subject, 'foo')
        eq_(m.body, 'bar')
        
        ok_(r2.read_message(m.name))
        l = r2.unread()
        ok_(len(l) <= 0 or l[0].name != m.name)
        
        ok_(r2.unread_message(m.name))
        n = r2.unread()[0]
        eq_(m.name, n.name)
    
    def test_subscribe_and_unsubscribe(self):
        sr = self.reddit.subreddit(TEST_SR).name
        ok_(self.reddit.subscribe(sr))
        ok_(TEST_SR in [r.display_name for r in self.reddit.mine()])
        ok_(self.reddit.unsubscribe(sr))
        ok_(TEST_SR not in [r.display_name for r in self.reddit.mine()])
        
        ok_(self.reddit.subscribe(TEST_SR))
        ok_(TEST_SR in [r.display_name for r in self.reddit.mine()])
        ok_(self.reddit.unsubscribe(TEST_SR))
        ok_(TEST_SR not in [r.display_name for r in self.reddit.mine()])
    
    def test_approve(self):
        l = self.reddit.submit_text(CREATED_SR, 'foo', 'bar')
        if l:
            self.created.append(l)
        
        ok_(self.reddit.approve(l.name))
        l = l.refresh()
        eq_(l.approved_by, USERNAME)
    
    def test_remove(self):
        l = self.reddit.submit_text(CREATED_SR, 'foo', 'bar')
        if l:
            self.created.append(l)
        
        ok_(self.reddit.remove(l.name))
        l = l.refresh()
        eq_(l.banned_by, USERNAME)
    
    def test_distinguish(self):
        l = self.reddit.submit_text(CREATED_SR, 'foo', 'bar')
        if l:
            self.created.append(l)
        
        ok_(self.reddit.distinguish(l.name))
        # TODO: check if this actually distinguished.  don't know how
    
    def test_flair_flairlist_flaircsv(self):
        ok_(self.reddit.flair(CREATED_SR, USERNAME2, 'sometext', 'someclass'))
        l = self.reddit.flairlist(CREATED_SR)
        ok_((USERNAME2, 'sometext', 'someclass') in
            [(a.user, a.flair_text, a.flair_css_class) for a in l])
        ok_(self.reddit.flaircsv(CREATED_SR, '{0},,'.format(USERNAME2)))
        l = self.reddit.flairlist(CREATED_SR)
        ok_(USERNAME2 not in [a.user for a in l])
    
    def teardown(self):
        for i in self.created:
            i.delete()