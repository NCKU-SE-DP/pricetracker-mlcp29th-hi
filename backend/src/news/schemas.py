from pydantic import BaseModel, Field

from .constants import AIModel


class SearchRequestSchema(BaseModel):
    prompt: str = Field(min_length=1)


class NewsSummaryRequestSchema(BaseModel):
    content: str = Field(min_length=1)


class NewsSummaryCustomModelRequestSchema(BaseModel):
    content: str = Field(min_length=1)
    ai_model: AIModel