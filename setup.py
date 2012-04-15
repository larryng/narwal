#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name='narwal',
    packages=['narwal'],
    version='0.0.1',
    author='Larry Ng',
    author_email='ng.larry@gmail.com',
    url='',
    description='A thin wrapper for the Reddit API.',
    long_description='',
    keywords=['reddit', 'api', 'wrapper'],
    requires=['requests >= 0.11.1'],
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Internet :: Utilities',
        ],
)