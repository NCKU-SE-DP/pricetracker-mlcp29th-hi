from fastapi import FastAPI, Request, status
from fastapi.responses import PlainTextResponse
from sentry_sdk import capture_exception

from .exceptions import DomainMismatchException


def _domain_mismatch_exception_handler(request: Request, exception: DomainMismatchException):
    capture_exception(exception)
    return PlainTextResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def attach_to(app: FastAPI):
    app.add_exception_handler(DomainMismatchException, _domain_mismatch_exception_handler)