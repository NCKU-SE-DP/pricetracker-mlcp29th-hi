from typing import override

from fastapi import status
from fastapi.responses import PlainTextResponse

from ..exception import AppError


class AuthenticationError(AppError):
    @override
    def generate_http_response(self) -> PlainTextResponse:
        return PlainTextResponse(self.message, status_code=status.HTTP_401_UNAUTHORIZED)


class RegistrationError(AppError):
    @override
    def generate_http_response(self) -> PlainTextResponse:
        return PlainTextResponse(self.message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class InvalidAccessTokenError(AuthenticationError):
    def __init__(self):
        self.message = "Invalid user access token."
        super().__init__(self.message)


class InvalidCredentialsError(AuthenticationError):
    def __init__(self):
        self.message = "Incorrect username or password."
        super().__init__(self.message)


class UsernameNotAvailableError(RegistrationError):
    def __init__(self, username: str):
        self.message = f"The username '{username}' is not available."
        super().__init__(self.message)