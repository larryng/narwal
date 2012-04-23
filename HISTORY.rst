.. :changelog:

Changelog
---------

v0.2.4a (2012-04-23)
++++++++++++++++++++
* automatically un-html-escape unicode chars
* fixed ValueError due to zero length fields when string formatting in older
  versions of Python (thanks staticsafe) 


v0.2.3a (2012-04-21)
++++++++++++++++++++
* hotfix: default Reddit._username to None


v0.2.2a (2012-04-20)
++++++++++++++++++++
* hotfix: /api/delete -> /api/del


v0.2.1a (2012-04-20)
++++++++++++++++++++

* fixed Listing.has_more()
* made util functions more robust
* moved saving of username until successful login
* moved decorators outside of Reddit class for easier testing
* added some tests


v0.2.0a (2012-04-18)
++++++++++++++++++++

* added Reddit.edit() and Commentable.edit()
* added Reddit.distinguish() and Commentable.distinguish()
* refactored .comments(), .remove(), and .delete() into Commentable
* refactored .hide() and .unhide() into Hideable (subclassed by Link, Message)
* refactored .report() into Reportable (subclassed by Link, Comment, Message)
* changed Comment.permalink to return relative path
* added useful __repr__ for Reddit
* removed debugging print statement from Reddit.comment
* changed urljoin and relative_url to return unicode strings