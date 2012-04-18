.. _api:

Usage and API
=============


After importing narwal, ::

    >>> import narwal

you'll always be starting with :class:`Reddit`, by invoking either: ::

    >>> session = narwal.Reddit(user_agent='hellonarwal')
    >>> session = narwal.Reddit('username', 'password', user_agent='nice2meetu')

or ::

    >>> session = narwal.connect(user_agent='hellonarwal')
    >>> session = narwal.connect('username', 'password', user_agent='nice2meetu')

But really, :func:`connect` is the same as instantiating :class:`Reddit`.  I
just think :func:`connect` makes more sense intuitively.

narwal defaults to respecting reddit's rules of making at most only 1 request
every 2 seconds and always supplying a useful User-Agent.  That's why if you
try this: ::

    >>> session = narwal.connect()

a :class:`ValueError` will be raised complaining that you need to supply a
``user_agent``.  You can make narwal be disrespectful by setting
``respect=False`` when instantiating a new session: ::

    >>> session = narwal.connect(respect=False)

But c'mon -- be respectful.

Upon receiving a response from GET (and some POST) requests, narwal attempts to
"thingify" the response content.  Thingifying is simply wrapping the useful 
data as a :class:`things.Thing` subclass, as defined by reddit 
`here <https://github.com/reddit/reddit/wiki/thing>`_.  Thingifying works
recursively through the object, such that some data in a Thing may be another
Thing.  For example: ::

    >>> page1 = session.hot()        # Listing
    >>> link = page1[0]              # Link
    
::

    >>> comments = link.comments()   # Listing
    >>> comment = comments[0]        # Comment
    >>> replies = comment.replies    # Listing
    >>> replies[0]                   # Comment 

You can access all of narwal's implemented reddit API calls through 
:class:`narwal.Reddit` methods, but, as you can see in the examples, many of
them are accessible through things' methods for convenience.


narwal
------

.. module:: narwal

.. autofunction:: connect

.. autoclass:: Reddit
   :members:


narwal.things
-------------

.. automodule:: narwal.things
   :members:
   :show-inheritance:


narwal.exceptions
-----------------

.. automodule:: narwal.exceptions
   :members:
   :show-inheritance: