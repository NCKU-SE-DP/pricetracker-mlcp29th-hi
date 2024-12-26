from typing import override

from fastapi import status
from fastapi.responses import PlainTextResponse

from ..exception import AppError


class DomainMismatchException(AppError):
    """Exception raised for URLs whose domain does not match the news website's domain."""

    def __init__(
        self,
        url: str,
        message: str = "URL's domain does not match the news website's domain",
    ):
        self.url = url
        self.message = message
        super().__init__(self.message)
    

    @override
    def generate_http_response(self) ->PlainTextResponse:
        return PlainTextResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NewsExtractionError(Exception):
    def __init__(self):
        self.message = "Unable to extract the news from the html."
        super().__init__(self.message)