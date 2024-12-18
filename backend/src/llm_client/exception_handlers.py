from fastapi import FastAPI, Request, status
from fastapi.responses import PlainTextResponse
from sentry_sdk import capture_exception

from .exceptions import LLMResponseFormatError


def _llm_response_format_error_handler(request: Request, exception: LLMResponseFormatError):
    capture_exception(exception)
    return PlainTextResponse("Something went wrong. Please try again later.", status_code=status.HTTP_502_BAD_GATEWAY)


def attach_to(app: FastAPI):
    app.add_exception_handler(LLMResponseFormatError, _llm_response_format_error_handler)