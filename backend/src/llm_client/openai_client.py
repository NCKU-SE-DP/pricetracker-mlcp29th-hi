from enum import Enum

from openai import OpenAI
from pydantic import BaseModel, Field

from ..news.config import Configuration


class NewsSummary(BaseModel):
    summary: str = Field(validation_alias="影響")
    reason: str = Field(validation_alias="原因")


class RelevanceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class OpenAIClient:
    __shared_instance = None


    def __new__(cls, *args, **kwargs):
        if cls.__shared_instance is None:
            cls.__shared_instance = super().__new__(cls)
        return cls.__shared_instance
    

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
    

    def extract_search_keywords(self, news_expectation: str) -> str | None:
        keywords = self._ask(
            system_prompt="你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
            user_prompt=news_expectation
        )
        return keywords
    

    def summarize_news(self, content: str) -> NewsSummary:
        summary = self._ask(
            system_prompt="你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
            user_prompt=content
        )
        return NewsSummary.model_validate_json(summary)
    
    
    def evaluate_relevance_to_price_changes(self, news_title: str) -> RelevanceLevel:
        relevance = self._ask(
            system_prompt="你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
            user_prompt=news_title
        )
        return RelevanceLevel(relevance)