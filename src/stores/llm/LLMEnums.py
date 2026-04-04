from enum import Enum

class LLMEnums(Enum):

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"

class OpenAIEnums(Enum):
    ROLE_SYSTEM = "system"
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"

