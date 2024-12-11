from pydantic import BaseModel

from .constants import AIModel


class SearchRequestSchema(BaseModel):
    prompt: str


class NewsSummaryRequestSchema(BaseModel):
    content: str


class NewsSummaryCustomModelRequestSchema(BaseModel):
    content: str
    ai_model: AIModel