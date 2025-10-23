class RequestsException(Exception):
    """
    Exception while making Http Requests/Response
    """
    def __init__(self, errors, exception_id):
        # Call the base class constructor with the parameters it needs
        self.exception_id = exception_id
        self.errors = errors
        super().__init__(errors)

    def __str__(self):
        if self.exception_id is None:
            return self.errors
        return '{} - {}'.format(str(self.exception_id), self.errors)