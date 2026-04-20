from ..LLMinterface import LLMInterface
from ..LLMEnums import LLMEnums, AnthropicEnums, EmbeddingDocumentTypeEnums
import anthropic
import logging


class AnthropicProvider(LLMInterface):
    
    def __init__(self, api_key: str, 
                 default_max_input_characters: int = 1000, 
                 default_max_output_tokens: int = 1000, 
                 default_temperature: float = 0.2):
        
        self.api_key = api_key
        self.default_max_input_characters = default_max_input_characters
        self.default_max_output_tokens = default_max_output_tokens
        self.default_temperature = default_temperature
        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None
        self.enums = AnthropicEnums

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id
    
    def set_embedding_model(self, model_id: str, embedding_size: int = None):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self, text: str):
        return text.strip()[:self.default_max_input_characters].strip()
    

    def generate_text(self, prompt, chat_history: list = [], max_output_tokens=None, temperature=None):
        if not self.client:
            self.logger.error("Anthropic client is not initialized.")
            return None

        if not self.generation_model_id:
            self.logger.error("Generation model ID is not set.")
            return None

        max_output_tokens = max_output_tokens if max_output_tokens else self.default_max_output_tokens
        temperature = temperature if temperature else self.default_temperature

        system_prompt = None
        filtered_messages = []
        for msg in chat_history:
            if msg.get("role") == self.enums.ROLE_SYSTEM.value:
                system_prompt = msg.get("content", "")
            else:
                filtered_messages.append(msg)

        response = self.client.messages.create(
            model=self.generation_model_id,
            system=system_prompt,
            messages=filtered_messages + [self.construct_prompt(prompt, AnthropicEnums.ROLE_USER.value)],
            max_tokens=max_output_tokens,
            temperature=temperature
        )

        
        if not response or not response.content or len(response.content) == 0:
            self.logger.error("No valid response returned from Anthropic API.")
            return None

        return response.content[0].text
    
    # Anthropic does not currently support embeddings, so this method is a no-op for now
    def embed_text(self, text: str, document_type: str = None):
        raise NotImplementedError("Text embedding is not implemented yet for AnthropicProvider.")
        

    def construct_prompt(self, prompt: str, role: str):
        return {
            "role": role,
            "content": self.process_text(prompt)
        }
    