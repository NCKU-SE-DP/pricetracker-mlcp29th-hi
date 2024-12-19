from fastapi import FastAPI, Request, status
from fastapi.responses import PlainTextResponse
from sentry_sdk import capture_exception

from .exceptions import NewsNotFoundError
from ..logger import Logger


def _news_not_found_error_handler(request: Request, exception: NewsNotFoundError):
    capture_exception(exception)
    Logger().log_error(exception)
    return PlainTextResponse(exception.message, status_code=status.HTTP_404_NOT_FOUND)


def attach_to(app: FastAPI):
    app.add_exception_handler(NewsNotFoundError, _news_not_found_error_handler)