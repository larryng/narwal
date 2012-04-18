.. :changelog:

History
-------


0.2.0a (2012-04-18)
+++++++++++++++++++

* added Reddit.edit() and Commentable.edit()
* added Reddit.distinguish() and Commentable.distinguish()
* refactored .comments(), .remove(), and .delete() into Commentable
* refactored .hide() and .unhide() into Hideable (subclassed by Link, Message)
* refactored .report() into Reportable (subclassed by Link, Comment, Message)
* changed Comment.permalink to return relative path
* added useful __repr__ for Reddit
* removed debugging print statement from Reddit.comment
* changed urljoin and relative_url to return unicode strings