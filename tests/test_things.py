import sys
import os
sys.path.insert(0, os.path.abspath('..'))

from nose.tools import raises, eq_, ok_

from narwal.things import *

'''
TYPES = {
    '1': 'comment',
    '2': 'account',
    '3': 'link',
    '4': 'message',
    '5': 'subreddit',
}
'''

class test_identify_class():
    
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
        ok_(identify_thing({'kind': 'listing'}) is Listing)
        ok_(identify_thing({'kind': 'Userlist'}) is Userlist)
        ok_(identify_thing({'kind': 'moRe'}) is More)