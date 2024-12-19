from fastapi import FastAPI, Request, status
from fastapi.responses import PlainTextResponse
from sentry_sdk import capture_exception

from .exceptions import AuthenticationError, RegistrationError
from ..logger import Logger


def _authentication_error_handler(request: Request, exception: AuthenticationError):
    capture_exception(exception)
    Logger().log_error(exception)
    return PlainTextResponse(exception.message, status_code=status.HTTP_401_UNAUTHORIZED)


def _registration_error_handler(request: Request, exception: RegistrationError):
    capture_exception(exception)
    Logger().log_error(exception)
    return PlainTextResponse(exception.message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


def attach_to(app: FastAPI):
    app.add_exception_handler(AuthenticationError, _authentication_error_handler)
    app.add_exception_handler(RegistrationError, _registration_error_handler)