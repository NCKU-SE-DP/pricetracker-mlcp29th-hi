import abc
from typing import override

import aisuite
from pydantic import ValidationError

from .base import LLMClientBase
from .constants import LLMClientModel, LLMSystemPrompt, RelevanceLevel
from .exceptions import LLMResponseFormatError
from .schemas import NewsSummary


class LLMClientTemplate(LLMClientBase, abc.ABC):

    @staticmethod
    @abc.abstractmethod
    def _model() -> LLMClientModel:
        raise NotImplementedError


    def __init__(self):
        self._client = aisuite.Client()


    @override
    def _ask(self, system_prompt: str, user_prompt: str) -> str:
        completion = self._client.chat.completions.create(
            model=self._model().value,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        content = completion.choices[0].message.content
        return "" if content is None else content


    @override
    def extract_search_keywords(self, news_expectation: str) -> str:
        keywords = self._ask(
            system_prompt=LLMSystemPrompt.SEARCH_KEYWORD_EXTRACTION.value,
            user_prompt=news_expectation
        )
        return keywords


    @override
    def summarize_news(self, content: str) -> NewsSummary:
        summary = self._ask(
            system_prompt=LLMSystemPrompt.NEWS_SUMMARY.value,
            user_prompt=content
        )
        try:
            return NewsSummary.model_validate_json(summary)
        except ValidationError:
            raise LLMResponseFormatError


    @override
    def evaluate_relevance_to_price_changes(self, news_title: str) -> RelevanceLevel:
        relevance = self._ask(
            system_prompt=LLMSystemPrompt.RELEVANCE_EVALUATION.value,
            user_prompt=news_title
        )
        try:
            return RelevanceLevel(relevance)
        except:
            raise LLMResponseFormatError