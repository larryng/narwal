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
    def __init__(self, errors):
        plural = 's' if len(errors) > 1 else ''
        super(PostError, self).__init__('error{} returned: {}'.format(plural, ', '.join(errors)))
        self.errors = errors

class BadResponse(AlienException):
    def __init__(self, response):
        super(BadResponse, self).__init__('{} received'.format(response.status_code))
        self.response = response