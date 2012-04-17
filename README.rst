narwal
======

narwal (sic) is a Python wrapper for reddit's API made to be simple, intuitive,
and concise, i.e. *pythonic*. ::

    >>> import narwal
    >>> session = narwal.connect('narwal_bot', 'hunter2', user_agent='i'm a narw(h)al!')
    >>> frontpage = session.hot()
    >>> for link in frontpage[:3]:
        ...   print link
        ... 
        (3088) Words can not describe how much I love this pic of Obama and Clinton
        (1697) Rough day for a mom at the airport.
        (1370) I felt awful when this happened.
    >>> frontpage[1].upvote()
    <Response [200]>
    >>> frontpage[1].comment('cool story bro')
    <Comment [narwal_bot: cool story bro]>

See the docs at http://narwal.readthedocs.org/.

Works with Python 2.7.


Installation
------------

To install, just do the usual: ::

    $ pip install narwal


Examples
--------

Start a session: ::

    >>> import narwal
    >>> session = narwal.connect(user_agent='narwal demo')

Start a logged in session: ::

    >>> session = narwal.connect('narwal_bot', 'password', user_agent='narwal demo')

Get the front page: ::

    >>> page1 = session.hot()

Get the next page: ::

    >>> page2 = page1.more()

Get the fourth link's comments: ::
    
    >>> comments = page1[3].comments()

Get the second link of r/test/top: ::

    >>> link = session.top('test')[1]

Submit a comment to it: ::

    >>> comment = link.comment('the narwhal ba--')

Downvote the comment we just submitted: ::

    >>> comment.downvote()
    <Response [200]>
    
And reply to it: ::

    >>> comment.reply('NO! *slap*')
    <Comment [(1) narwal_bot: NO! *slap*]>

Check our inbox: ::

    >>> inbox = session.inbox()

Read the first message: ::

    >>> print inbox[0]
    larryng: hi there

Get the sender's account info and submissions: ::

    >>> user = session.user(message.author)
    >>> user.submitted()
    [<Link [(1) test post please ...]>]

Plus a whole lot more, since most of the reddit API has been implemented.  See
the API docs (or the source) for more features.