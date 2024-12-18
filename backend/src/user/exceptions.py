class InvalidAccessTokenError(Exception):
    def __init__(self):
        self.message = "Invalid user access token."
        super().__init__(self.message)


class InvalidCredentialsError(Exception):
    def __init__(self):
        self.message = "Incorrect username or password."
        super().__init__(self.message)