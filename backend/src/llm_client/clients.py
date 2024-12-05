from .base import LLMClientModel, LLMClientTemplate


class OpenAIClient(LLMClientTemplate):
    
    @staticmethod
    def _model() -> LLMClientModel:
        return LLMClientModel.OPENAI_GPT_4O_MINI
    

class AnthropicClient(LLMClientTemplate):

    @staticmethod
    def _model() -> LLMClientModel:
        return LLMClientModel.ANTHROPIC_CLAUDE_3_HAIKU_20240307