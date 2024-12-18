from fastapi import FastAPI, Request, status
from fastapi.responses import PlainTextResponse
from sentry_sdk import capture_exception

from .exceptions import AuthenticationError


def _authentication_error_handler(request: Request, exception: AuthenticationError):
    capture_exception(exception)
    return PlainTextResponse(exception.message, status_code=status.HTTP_401_UNAUTHORIZED)


def attach_to(app: FastAPI):
    app.add_exception_handler(AuthenticationError, _authentication_error_handler)