from typing import Literal

from pydantic import BaseModel


class SearchRequestSchema(BaseModel):
    prompt: str


class NewsSummaryRequestSchema(BaseModel):
    content: str


class NewsSummaryCustomModelRequestSchema(BaseModel):
    content: str
    ai_model: Literal["openai", "anthropic"]