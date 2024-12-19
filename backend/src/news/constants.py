from enum import Enum


class AIModel(str, Enum):
    OPENAI    = "openai"
    ANTHROPIC = "anthropic"