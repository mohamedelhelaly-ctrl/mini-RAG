from enum import Enum

class LLMEnums(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"

class OpenAIEnums(Enum):
    ROLE_SYSTEM = "system"
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"

class CohereEnums(Enum):
    ROLE_SYSTEM = "system"
    ROLE_USER = "user"
    ROLE_ASSISTANT = "chatbot" 

    DOCUMENT = "search_document"
    QUERY = "search_query"

class AnthropicEnums(Enum):
    ROLE_SYSTEM = "system"
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"


class EmbeddingDocumentTypeEnums(Enum):
    DOCUMENT = "document"
    QUERY = "query"
