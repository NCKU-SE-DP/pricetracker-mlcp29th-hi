from typing import override

from fastapi import status
from fastapi.responses import PlainTextResponse

from ..exception import AppError


class LLMResponseFormatError(AppError):
    def __init__(self):
        self.message = "Unable to parse LLM response to expected format."
        super().__init__(self.message)
    

    @override
    def generate_http_response(self) -> PlainTextResponse:
        return PlainTextResponse("Something went wrong. Please try again later.", status_code=status.HTTP_502_BAD_GATEWAY)