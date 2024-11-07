from pydantic import BaseModel


class SearchRequestSchema(BaseModel):
    prompt: str


class NewsSummaryRequestSchema(BaseModel):
    content: str