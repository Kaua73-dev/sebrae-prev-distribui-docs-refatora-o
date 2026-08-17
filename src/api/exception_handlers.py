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
from src.exception.user_email import (
    UserEmailAlreadyException,
    UserEmailNotFoundException,
    UserEmailRequiredException,
)

NOT_FOUND = 404
CONFLICT = 409
UNPROCESSABLE = 422
INTERNAL_ERROR = 500

STATUS_BY_EXCEPTION = {
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
    return JSONResponse(
        status_code=STATUS_BY_EXCEPTION.get(type(exception), INTERNAL_ERROR),
        content={"detail": getattr(exception, "message", str(exception))},
    )


def register_exception_handlers(app: FastAPI) -> None:
    for exception_type in STATUS_BY_EXCEPTION:
        app.add_exception_handler(exception_type, handle_domain_exception)
