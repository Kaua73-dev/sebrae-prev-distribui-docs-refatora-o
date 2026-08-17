class DispatchNotFoundException(Exception):
    def __init__(self, message: str = "Dispatch not found"):
        self.message = message
        super().__init__(self.message)


class DispatchBlockNotFoundException(Exception):
    def __init__(self, message: str = "Dispatch block not found"):
        self.message = message
        super().__init__(self.message)


class DispatchAlreadyRunningException(Exception):
    def __init__(self, message: str = "Dispatch is already running"):
        self.message = message
        super().__init__(self.message)


class DispatchNothingToSendException(Exception):
    def __init__(self, message: str = "Dispatch has no block to send"):
        self.message = message
        super().__init__(self.message)


class DispatchNotReadyException(Exception):
    def __init__(self, message: str = "Dispatch is not ready to be executed"):
        self.message = message
        super().__init__(self.message)
