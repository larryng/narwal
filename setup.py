#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from narwal import __version__

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
