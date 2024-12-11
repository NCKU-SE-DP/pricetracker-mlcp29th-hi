import abc

import aisuite

from .constants import LLMClientModel, LLMSystemPrompt, RelevanceLevel
from .schemas import NewsSummary


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