import abc

import aisuite

from .base import LLMClientBase
from .constants import LLMClientModel, LLMSystemPrompt, RelevanceLevel
from .schemas import NewsSummary


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
            system_prompt=LLMSystemPrompt.SEARCH_KEYWORD_EXTRACTION.value,
            user_prompt=news_expectation
        )
        return keywords


    def summarize_news(self, content: str) -> NewsSummary:
        summary = self._ask(
            system_prompt=LLMSystemPrompt.NEWS_SUMMARY.value,
            user_prompt=content
        )
        return NewsSummary.model_validate_json(summary)


    def evaluate_relevance_to_price_changes(self, news_title: str) -> RelevanceLevel:
        relevance = self._ask(
            system_prompt=LLMSystemPrompt.RELEVANCE_EVALUATION.value,
            user_prompt=news_title
        )
        return RelevanceLevel(relevance)