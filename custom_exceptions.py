'''Custom exceptions for the app.'''

class UsernameAlreadyExistsError(Exception):
    '''Exception raised when user tries to signup with a username that has already been registered.'''

    def __init__(self, username):
        self.message = f"Username {username} is taken."
        super().__init__(self.message)

class EmailAlreadyExistsError(Exception):
    '''Exception raised when user tries to signup with an email that has already been registered.'''

    def __init__(self, email):
        self.message = f"Email {email} is taken."
        super().__init__(self.message)