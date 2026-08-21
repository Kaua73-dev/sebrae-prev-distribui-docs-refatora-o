from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.exception.dispatch import (
    DispatchAlreadyRunningException,
    DispatchBlockNotFoundException,
    DispatchNotFoundException,
    DispatchNotReadyException,
    DispatchNothingToSendException,
)
from src.exception.prefix.prefix_exception import (
    PrefixAlreadyExistException,
    PrefixNotFoundException,
    PrefixRequiredException,
)
from src.exception.user import (
    InvalidCredentialsException,
    NotAuthenticatedException,
    NotEnoughPermissionException,
    UserAlreadyExistException,
    UserInactiveException,
)
from src.exception.user_email import (
    UserEmailAlreadyException,
    UserEmailNotFoundException,
    UserEmailRequiredException,
)

UNAUTHORIZED = 401
FORBIDDEN = 403
NOT_FOUND = 404
CONFLICT = 409
UNPROCESSABLE = 422
INTERNAL_ERROR = 500

STATUS_BY_EXCEPTION = {
    InvalidCredentialsException: UNAUTHORIZED,
    NotAuthenticatedException: UNAUTHORIZED,
    NotEnoughPermissionException: FORBIDDEN,
    UserInactiveException: FORBIDDEN,
    UserAlreadyExistException: CONFLICT,
    DispatchNotFoundException: NOT_FOUND,
    DispatchBlockNotFoundException: NOT_FOUND,
    PrefixNotFoundException: NOT_FOUND,
    UserEmailNotFoundException: NOT_FOUND,
    DispatchAlreadyRunningException: CONFLICT,
    PrefixAlreadyExistException: CONFLICT,
    UserEmailAlreadyException: CONFLICT,
    DispatchNotReadyException: UNPROCESSABLE,
    DispatchNothingToSendException: UNPROCESSABLE,
    PrefixRequiredException: UNPROCESSABLE,
    UserEmailRequiredException: UNPROCESSABLE,
}


async def handle_domain_exception(request: Request, exception: Exception) -> JSONResponse:
    status_code = STATUS_BY_EXCEPTION.get(type(exception), INTERNAL_ERROR)

    return JSONResponse(
        status_code=status_code,
        content={"detail": getattr(exception, "message", str(exception))},
        headers={"WWW-Authenticate": "Bearer"} if status_code == UNAUTHORIZED else None,
    )


def register_exception_handlers(app: FastAPI) -> None:
    for exception_type in STATUS_BY_EXCEPTION:
        app.add_exception_handler(exception_type, handle_domain_exception)
