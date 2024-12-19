class NewsNotFoundError(Exception):
    def __init__(self):
        self.message = "News not found."
        super().__init__(self.message)