class InvalidCredentialsException(Exception):
    def __init__(self, message: str = "Email or password is invalid"):
        self.message = message
        super().__init__(self.message)


class UserAlreadyExistException(Exception):
    def __init__(self, message: str = "User already exists"):
        self.message = message
        super().__init__(self.message)


class UserInactiveException(Exception):
    def __init__(self, message: str = "User is inactive"):
        self.message = message
        super().__init__(self.message)


class NotAuthenticatedException(Exception):
    def __init__(self, message: str = "Not authenticated"):
        self.message = message
        super().__init__(self.message)


class NotEnoughPermissionException(Exception):
    def __init__(self, message: str = "Not enough permission"):
        self.message = message
        super().__init__(self.message)
