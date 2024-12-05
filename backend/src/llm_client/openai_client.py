from openai import OpenAI

from .base import LLMClientBase
from ..news.config import Configuration


class OpenAIClient(LLMClientBase):   

    def __init__(self):
        configuration = Configuration()
        self._openai = OpenAI(api_key=configuration.open_ai_api_key)
        self.ai_model = configuration.open_ai_model
    

    def _ask(self, system_prompt: str, user_prompt: str) -> str | None:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        completion = self._openai.chat.completions.create(
            model=self.ai_model,
            messages=messages
        )
        response = completion.choices[0].message.content
        return response