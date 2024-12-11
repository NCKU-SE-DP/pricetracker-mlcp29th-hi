from pydantic import BaseModel, Field


class NewsSummary(BaseModel):
    summary: str = Field(validation_alias="影響")
    reason:  str = Field(validation_alias="原因")