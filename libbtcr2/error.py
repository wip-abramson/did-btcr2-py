class InvalidDidError(Exception):
    def __init__(self, message="invalidDid"):
        super().__init__(message)