from ..LLMinterface import LLMInterface
from ..LLMEnums import LLMEnums, CohereEnums, EmbeddingDocumentTypeEnums
import cohere
import logging


class CohereProvider(LLMInterface):
    
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
        self.enums = CohereEnums

        self.client = cohere.ClientV2(api_key=self.api_key)
        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id
    
    def set_embedding_model(self, model_id: str, embedding_size: int = None):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self, text: str):
        return text.strip()[:self.default_max_input_characters].strip()
    
    # def generate_text(self, prompt, chat_history:list = [], max_output_tokens = None, temperature = None):
    #     if not self.client:
    #         self.logger.error("Cohere client is not initialized. Cannot generate text.")
    #         return None
        
    #     if not self.generation_model_id:
    #         self.logger.error("Generation model ID is not set. Cannot generate text.")
    #         return None
        
    #     max_output_tokens = max_output_tokens if max_output_tokens else self.default_max_output_tokens
    #     temperature = temperature if temperature else self.default_temperature

    #     response = self.client.chat(
    #         model = self.generation_model_id,
    #         messages = chat_history + [self.construct_prompt(prompt, CohereEnums.ROLE_USER.value)],
    #         max_tokens = max_output_tokens,
    #         temperature = temperature   
    #     )
    #     if not response or not response.choices or len(response.choices) == 0 or not response.choices[0].message:
    #         self.logger.error("No valid response returned from Cohere API.")
    #         return None
        
    #     return response.message.content[0].text

    def generate_text(self, prompt, chat_history: list = [], max_output_tokens=None, temperature=None):
        if not self.client:
            self.logger.error("Cohere client is not initialized.")
            return None

        if not self.generation_model_id:
            self.logger.error("Generation model ID is not set.")
            return None

        max_output_tokens = max_output_tokens if max_output_tokens else self.default_max_output_tokens
        temperature = temperature if temperature else self.default_temperature

        response = self.client.chat(
            model=self.generation_model_id,
            messages=chat_history + [self.construct_prompt(prompt, CohereEnums.ROLE_USER.value)],
            max_tokens=max_output_tokens,
            temperature=temperature
        )

        # ✅ Correct validation and accessor for ClientV2
        if not response or not response.message or not response.message.content:
            self.logger.error("No valid response returned from Cohere API.")
            return None

        return response.message.content[0].text
    
    def embed_text(self, text: str, document_type: str = None):
        if not self.client:
            self.logger.error("Cohere client is not initialized. Cannot embed text.")
            return None
        
        if not self.embedding_model_id:
            self.logger.error("Embedding model ID is not set. Cannot embed text.")
            return None
        
        input_type = CohereEnums.DOCUMENT.value
        if document_type == EmbeddingDocumentTypeEnums.QUERY.value:
            input_type = CohereEnums.QUERY.value
        
        response = self.client.embed(
            model=self.embedding_model_id,
            input_type=input_type,
            texts = [text],
            embedding_types=["float"]
        )

        if not response or not response.embeddings or not response.embeddings.float:
            self.logger.error("No valid embedding returned from Cohere API.")
            return None
        
        return response.embeddings.float[0]
    

    def construct_prompt(self, prompt: str, role: str):
        return {
            "role": role,
            "content": self.process_text(prompt)
        }
    