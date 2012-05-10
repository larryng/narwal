#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'narwal'))
from const import __version__
sys.path.pop()

from setuptools import setup


setup(
    name='narwal',
    packages=['narwal'],
    version=__version__,
    author='Larry Ng',
    author_email='ng.larry@gmail.com',
    url='https://github.com/larryng/narwal',
    description='A thin wrapper for the Reddit API.',
    long_description='See https://github.com/larryng/narwal for more info.',
    keywords=['reddit', 'api', 'wrapper'],
    install_requires=['requests>=0.11.1'],
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Utilities',
        ],
)
