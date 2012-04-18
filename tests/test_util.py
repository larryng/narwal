import sys
import os
sys.path.insert(0, os.path.abspath('..'))

from nose.tools import raises, eq_, ok_

from narwal.util import limstr, urljoin, relative_url, kind, pull_data_dict
from narwal.const import BASE_URL, TYPES


class test_limstr():

    @raises(ValueError)
    def test_negative_max_length(self):
        limstr('', -1)
    
    def test_blanks(self):
        eq_(limstr('', 0), '')
        eq_(limstr('', 1), '')
    
    def test_normal(self):
        s = 'hello world'
        eq_(limstr(s, 0), '')
        eq_(limstr(s, 5), 'he...')
        eq_(limstr(s, 11), 'hello world')
        eq_(limstr(s, 12), 'hello world')
    
    def test_same_type(self):
        ok_(isinstance(limstr('hello world', 5), str))
        ok_(isinstance(limstr(u'hello world', 5), unicode))


class test_urljoin():
    
    def test_blank(self):
        eq_(urljoin(), u'')
    
    def test_normal(self):
        eq_(urljoin('a'), u'a')
        eq_(urljoin('a', 'bc', 'def'), u'a/bc/def')
    
    def test_types(self):
        eq_(urljoin(123, 'abc', u'def'), u'123/abc/def')
    
    def test_slashes(self):
        eq_(urljoin('/a/', '/b', 'c///'), u'a/b/c')


class test_relative_url():
    
    def setup(self):
        self.url = BASE_URL.rstrip('/')
    
    def test_normal(self):
        eq_(relative_url(), self.url + u'/.json')
        eq_(relative_url('a'), self.url + u'/a/.json')
        eq_(relative_url('a', 'b'), self.url + u'/a/b/.json')
    
    def test_ends_with_json(self):
        eq_(relative_url('a/b/.json'), self.url + u'/a/b/.json')
        eq_(relative_url('a', '/b.json'), self.url + u'/a/b.json')


class test_kind():
    
    @raises(TypeError)
    def test_typeerror(self):
        kind(123)
    
    def test_else(self):
        eq_(kind(''), '')
        eq_(kind('notatype'), 'notatype')
    
    def test_normal(self):
        for i in TYPES:
            eq_(kind('t{}'.format(i)), TYPES[i])
            eq_(kind('t{}_a'.format(i)), TYPES[i])
            eq_(kind('t{}_1'.format(i)), TYPES[i])
            eq_(kind('t{}_a123jkl'.format(i)), TYPES[i])


class test_pull_data_dict():
    
    @raises(TypeError)
    def test_error(self):
        pull_data_dict('asdf')
    
    def test_none(self):
        eq_(pull_data_dict([]), None)
        eq_(pull_data_dict([1, 3]), None)
    
    def test_normal(self):
        d = {'data': 1}
        eq_(pull_data_dict([d]), d)
        eq_(pull_data_dict([3, d]), d)
        eq_(pull_data_dict(['as', [2, d]]), d)
        eq_(pull_data_dict([1, ['f', 3], d, '4']), d)