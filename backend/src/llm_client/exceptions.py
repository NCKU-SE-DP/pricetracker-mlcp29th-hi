class LLMResponseFormatError(Exception):
    def __init__(self):
        self.message = "Unable to parse LLM response to expected format."
        super().__init__(self.message)