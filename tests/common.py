# -*- coding: utf-8 -*-

import random
import string

TEST_AGENT = 'narwal (goo.gl/IBenG) testing'

def genstr(length=16):
    return ''.join(random.choice(string.ascii_letters) for _ in xrange(length))