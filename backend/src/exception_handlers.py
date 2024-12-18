from fastapi import FastAPI, Request, status
from fastapi.responses import PlainTextResponse
from requests.exceptions import RequestException
from sentry_sdk import capture_exception
from sqlalchemy.exc import SQLAlchemyError


def _request_exception_handler(request: Request, exception: RequestException):
    capture_exception(exception)
    return PlainTextResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _sqlalchemy_error_handler(request: Request, exception: SQLAlchemyError):
    capture_exception(exception)
    return PlainTextResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def attach_to(app: FastAPI):
    app.add_exception_handler(RequestException, _request_exception_handler)
    app.add_exception_handler(SQLAlchemyError, _sqlalchemy_error_handler)