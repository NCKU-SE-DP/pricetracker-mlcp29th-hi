import abc
from enum import Enum

import aisuite
from pydantic import BaseModel, Field


class NewsSummary(BaseModel):
    summary: str = Field(validation_alias="影響")
    reason:  str = Field(validation_alias="原因")


class RelevanceLevel(Enum):
    HIGH   = "high"
    MEDIUM = "medium"
    LOW    = "low"


class LLMClientModel(Enum):
    OPENAI_GPT_4O_MINI                = "openai:gpt-4o-mini"
    ANTHROPIC_CLAUDE_3_HAIKU_20240307 = "anthropic:claude-3-haiku-20240307"


class LLMClientBase(metaclass=abc.ABCMeta):
    __shared_instance = None


    def __new__(cls, *args, **kwargs):
        if cls.__shared_instance is None:
            cls.__shared_instance = super().__new__(cls)
        return cls.__shared_instance


    @abc.abstractmethod
    def _ask(self, system_prompt: str, user_prompt: str) -> str | None:
        """
        Abstract method for interacting with the language model (LLM).

        Subclasses must implement this method to define how to query the LLM
        given a system prompt and user prompt. The method should return the
        response from the LLM as a string, or None if no response is generated
        or there is an error.

        Args:
            system_prompt (str):
                A predefined prompt providing context or instructions for the
                LLM to follow.
            user_prompt (str): The input or query provided by the user to the
                LLM.

        Returns:
            str | None: The response from the LLM as a string, or None if there
            is no valid response.
        
        Note:
            This is an abstract method and must be implemented in subclasses of
            `LLMClientBase`.
        """
        raise NotImplementedError


    @abc.abstractmethod
    def extract_search_keywords(self, news_expectation: str) -> str | None:
        raise NotImplementedError


    @abc.abstractmethod
    def summarize_news(self, content: str) -> NewsSummary:
        raise NotImplementedError


    @abc.abstractmethod
    def evaluate_relevance_to_price_changes(self, news_title: str) -> RelevanceLevel:
        raise NotImplementedError


class LLMClientTemplate(LLMClientBase, abc.ABC):

    @staticmethod
    @abc.abstractmethod
    def _model() -> LLMClientModel:
        raise NotImplementedError


    def __init__(self):
        self._client = aisuite.Client()


    def _ask(self, system_prompt: str, user_prompt: str) -> str | None:
        completion = self._client.chat.completions.create(
            model=self._model().value,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return completion.choices[0].message.content


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