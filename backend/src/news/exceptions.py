from typing import override

from fastapi import status
from fastapi.responses import PlainTextResponse

from ..exception import AppError


class NewsNotFoundError(AppError):
    def __init__(self):
        self.message = "News not found."
        super().__init__(self.message)


    @override
    def generate_http_response(self) ->PlainTextResponse:
        return PlainTextResponse(self.message, status_code=status.HTTP_404_NOT_FOUND)