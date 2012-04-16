narwal
======

narwal (sic) is a Python wrapper for reddit's API made to be simple, intuitive,
and concise.

The goal is to make using narwal as easy as navigating reddit on a browser.



Installation
------------

To install: ::

    $ pip install narwal



Examples (until better docs are written)
----------------------------------------


Start a session: ::

    >>> import narwal
    >>> session = narwal.connect(user_agent='narwal demo')


Start a logged in session: ::

    >>> session = narwal.connect('narwal_bot', 'password', user_agent='narwal demo')


Get the front page: ::

    >>> page1 = session.hot()
    >>> for link in page1:
    ...   print link
    ... 
    (1775) Well, there's one futuristic utopia (NSFW)
    (1830) I'm no longer a 23 year old virgin! Awww Yeah!!!
    (2086) The Most Irritating Software in the World
    ...


Get the next page: ::

    >>> page2 = page1.more()
    >>> print page2
    [<Link [(966) Please tell me ...]>, <Link [(1100) Chubby arctic ...]>, ...]


Get the fourth link's comments: ::
    
    >>> comments = page1[3].comments()
    >>> for c in comments[:3]:
    ...   print c
    ... 
    (378) Perryn: [I think he's trying to say something.](http://i.imgur.com/Dq6yJ.jpg)
    (111) averageUsername123: [WHY ARE THEY SO VIOLENT?!](http://3.bp.blogspot.com/-bhdVeis6-FE/Tb-95L2yRzI/AAAAAAAAAOQ/xlkwBsESdVU/s1600/come-at-me-bro-i-will-turtle-slap-the-shit-out-of-you.jpg)
    (27) ZoidbergTheThird: That's the cutest fucking turtle I've ever seen.


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


Plus a whole lot more, as most of the reddit API has been implemented.  Please
see the source for more info while I'm working on the docs.