import unittest
import os
from unittest.mock import patch
from src.llm_client.clients import AnthropicClient, OpenAIClient
from src.llm_client.constants import LLMSystemPrompt, RelevanceLevel
from src.llm_client.exceptions import LLMResponseFormatError
from src.llm_client.schemas import NewsSummary

# 除非確認要使用真實的API進行測試(當然會因此擁有額外的開銷)，否則將RUN_REAL_API_TESTS設置為False
RUN_REAL_API_TESTS = os.getenv("RUN_REAL_API_TESTS", "false").lower() == "true"


class TestLLMClientBase(unittest.TestCase):
    __test__ = False
    client_class = None
    mock_path = None


    @classmethod
    def setUpClass(cls):
        cls.client = cls.client_class()


    @unittest.skipIf(not RUN_REAL_API_TESTS, "模擬 API 呼叫，跳過真實測試")
    def test_evaluate_relevance_to_price_changes_real(self):
        result = self.client.evaluate_relevance_to_price_changes("食品價格上漲")
        self.assertIn(result, RelevanceLevel)


    @unittest.skipIf(not RUN_REAL_API_TESTS, "模擬 API 呼叫，跳過真實測試")
    def test_summarize_news_real(self):
        result = self.client.summarize_news("一篇有關食品價格的新聞內容").model_dump()
        self.assertIn("summary", result)
        self.assertIn("reason", result)


    @unittest.skipIf(not RUN_REAL_API_TESTS, "模擬 API 呼叫，跳過真實測試")
    def test_extract_search_keywords_real(self):
        result = self.client.extract_search_keywords("這篇新聞提到食品價格的波動以及市場的供應鏈問題")
        self.assertGreater(len(result.split()), 0)


    def test_evaluate_relevance_to_price_changes(self):
        with patch(self.mock_path) as mock_generate_text:
            mock_generate_text.return_value = 'high'

            result = self.client.evaluate_relevance_to_price_changes("食品價格上漲")

            self.assertEqual(result, RelevanceLevel.HIGH)

            mock_generate_text.assert_called_once_with(
                system_prompt=LLMSystemPrompt.RELEVANCE_EVALUATION.value,
                user_prompt="食品價格上漲"
            )


    def test_evaluate_relevance_to_price_changes_invalid_llm(self):
        with patch(self.mock_path) as mock_generate_text:
            mock_generate_text.return_value = 'invalid_case'

            with self.assertRaises(LLMResponseFormatError):
                self.client.evaluate_relevance_to_price_changes("食品價格上漲")


    def test_summarize_news(self):
        with patch(self.mock_path) as mock_generate_text:
            mock_generate_text.return_value = '{"影響": "影響描述", "原因": "原因描述"}'

            result = self.client.summarize_news("一篇新聞內容")

            self.assertEqual(result, NewsSummary.model_validate_json('{"影響": "影響描述", "原因": "原因描述"}'))

            mock_generate_text.assert_called_once_with(
                system_prompt=LLMSystemPrompt.NEWS_SUMMARY.value,
                user_prompt="一篇新聞內容"
            )


    def test_summarize_news_failed(self):
        with patch(self.mock_path) as mock_generate_text:
            mock_generate_text.return_value = 'Invalid json'
            with self.assertRaises(LLMResponseFormatError):
                self.client.summarize_news("一篇新聞內容")


    def test_extract_search_keywords(self):
        with patch(self.mock_path) as mock_generate_text:
            mock_generate_text.return_value = '食品 價格'

            result = self.client.extract_search_keywords("一段希望看到的新聞文字")

            self.assertEqual(result, '食品 價格')

            mock_generate_text.assert_called_once_with(
                system_prompt=LLMSystemPrompt.SEARCH_KEYWORD_EXTRACTION.value,
                user_prompt="一段希望看到的新聞文字"
            )


    def test_extract_search_keywords_failed(self):
        with patch(self.mock_path) as mock_generate_text:
            mock_generate_text.return_value = '食品 價格'

            result = self.client.extract_search_keywords("一段希望看到的新聞文字")

            self.assertEqual(result, '食品 價格')

            mock_generate_text.assert_called_once_with(
                system_prompt=LLMSystemPrompt.SEARCH_KEYWORD_EXTRACTION.value,
                user_prompt="一段希望看到的新聞文字"
            )


    def test_singleton_pattern(self):
        client1 = self.client_class()
        client2 = self.client_class()
        assert client1 is client2


class TestOpenAIClient(TestLLMClientBase):
    __test__ = True
    client_class = OpenAIClient
    mock_path = "src.llm_client.clients.OpenAIClient._ask"


class TestAnthropicClient(TestLLMClientBase):
    __test__ = True
    client_class = AnthropicClient
    mock_path = "src.llm_client.clients.AnthropicClient._ask"


if __name__ == '__main__':
    unittest.main()