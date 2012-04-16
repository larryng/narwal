class AlienException(Exception):
    '''Generic exception'''

class LoginFail(AlienException):
    '''Unable to login for whatever reason (bad user/password combo, no response, etc.)'''

class NotLoggedIn(AlienException):
    '''Need to be logged in to call'''

class NoMoreError(AlienException):
    '''Can't get next/prev items of a Listing'''

class UnsupportedError(AlienException):
    '''Currently unsupported API feature'''

class PostError(AlienException):
    """Response contained reddit errors in response."""
    def __init__(self, errors):
        plural = 's' if len(errors) > 1 else ''
        super(PostError, self).__init__('error{} returned: {}'.format(plural, ', '.join(errors)))
        
        #: list of string reddit errors received in response
        self.errors = errors

class BadResponse(AlienException):
    """A non-200 response, or a 200 response with non-OK content received.""" 
    def __init__(self, response):
        super(BadResponse, self).__init__('{} received'.format(response.status_code))
        
        #: the :class:`requests.Response` object returned
        self.response = response