class UserEmailAlreadyException(Exception):
    def __init__(self, message: str = "Email already exists"):
        self.message = message
        super().__init__(self.message)


class UserEmailNotFoundException(Exception):
    def __init__(self, message: str = "Email  not found"):
        self.message = message
        super().__init__(self.message)


class UserEmailRequiredException(Exception):
    def __init__(self, message: str = "Email  is required"):
        self.message = message
        super().__init__(self.message)

