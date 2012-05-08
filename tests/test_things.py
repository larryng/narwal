# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.abspath('..'))

from nose.tools import raises, eq_, ok_

from narwal import Reddit
from narwal.things import *

from .common import TEST_AGENT


class test_identify_thing():
    
    def test_empty_dict(self):
        ok_(identify_thing({}) is Blob)
    
    def test_non_thing(self):
        ok_(identify_thing({'hello': 'world'}) is Blob)
    
    def test_normal(self):
        ok_(identify_thing({'kind': 't1'}) is Comment)
        ok_(identify_thing({'kind': 't2_asdf'}) is Account)
        ok_(identify_thing({'kind': 't3_a342kj'}) is Link)
        ok_(identify_thing({'kind': 't4'}) is Message)
        ok_(identify_thing({'kind': 't5'}) is Subreddit)
        ok_(identify_thing({'kind': 't6_adskfj'}) is Link)
        ok_(identify_thing({'kind': 't7_1'}) is Message)
        ok_(identify_thing({'kind': 'listing'}) is Listing)
        ok_(identify_thing({'kind': 'Userlist'}) is Userlist)
        ok_(identify_thing({'kind': 'moRe'}) is More)


class test_blob():
    
    def setup(self):
        self.reddit = Reddit(user_agent=TEST_AGENT)
    
    def test(self):
        b = Blob(self.reddit)
        ok_(b._reddit is self.reddit)


class test_listblob():
    
    def setup(self):
        self.reddit = Reddit(user_agent=TEST_AGENT)
    
    def test(self):
        lb = ListBlob(self.reddit)
        lb.append(1)
        eq_(len(lb), 1)
        lb = ListBlob(self.reddit, items=[1, 2, 3])
        lb[1] = 10
        eq_(lb[1], 10)
        del lb[1]
        eq_(list(lb), [1, 3])
        ok_(3 in lb)
        lb.append(3)
        eq_(lb.count(3), 2)
        eq_(lb.pop(), 3)
        eq_(list(lb), [1, 3])
        lst = []
        for i in lb:
            lst.append(i)
        eq_(lst, [1, 3])
        lb.reverse()
        eq_(list(lb), [3, 1])
        lb.sort()
        eq_(list(lb), [1, 3])
        lb.remove(1)
        eq_(list(lb), [3])


class test_thing():
    
    def setup(self):
        self.reddit = Reddit(user_agent=TEST_AGENT)
    
    def test(self):
        t = Thing(self.reddit)
        ok_(hasattr(t, 'id'))
        ok_(hasattr(t, 'name'))
        eq_(repr(t), '<Thing []>')
        t.name = 'hello'
        eq_(repr(t), '<Thing [hello]>')


class test_created():
    
    def setup(self):
        self.reddit = Reddit(user_agent=TEST_AGENT)
    
    def test(self):
        t = Created(self.reddit)
        ok_(hasattr(t, 'created'))
        ok_(hasattr(t, 'created_utc'))


class test_votable():
    
    # TODO: test methods?  they're just convenience functions...
    
    def setup(self):
        self.reddit = Reddit(user_agent=TEST_AGENT)
    
    def test(self):
        t = Votable(self.reddit)
        ok_(hasattr(t, 'ups'))
        ok_(hasattr(t, 'downs'))
        ok_(hasattr(t, 'likes'))