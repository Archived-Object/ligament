class TaskExecutionException(Exception):

    def __init__(self, header, *args, **vargs):
        """ header : str
                a short description of the error message

            (kwarg) payload : (any)
                A value to return in place of a normal return value
        """

        self.header = header
        """the header for the error (short error message)"""

        if "payload" in vargs:
            self.payload = vargs["payload"]
            del vargs["payload"]
        else:
            self.payload = Nones
            """The value this exception should default to"""

        Exception.__init__(self, *args, **vargs)
