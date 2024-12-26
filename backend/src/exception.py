import abc

from fastapi.responses import PlainTextResponse


class AppError(Exception, abc.ABC):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


    @abc.abstractmethod
    def generate_http_response(self) -> PlainTextResponse:
        raise NotImplementedError