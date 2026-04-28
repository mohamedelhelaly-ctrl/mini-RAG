from .BaseController import BaseController
from .ProjectController import ProjectController
import os
from langchain_community.document_loaders import TextLoader, PyMuPDFLoader
from models import ProcessEnum
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from dataclasses import dataclass

# Create dataclass similar to langchain.schema.Document to hold the page_content and metadata for each document returned by the loader.load() method
@dataclass
class Document:
    page_content: str
    metadata: dict

class ProcessController(BaseController):
    
    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
        self.project_path = ProjectController().get_project_path(project_id=project_id)

    def get_file_extention(self, file_id: str):
        return os.path.splitext(file_id)[-1].lower()
    
    def get_file_loader(self, file_id: str):
        ext = self.get_file_extention(file_id)
        file_path = os.path.join(self.project_path, file_id)

        if not os.path.exists(file_path):
            return None

        if ext == ProcessEnum.EXT_TEXT.value:
            return TextLoader(file_path, encoding="utf-8")
        elif ext == ProcessEnum.EXT_PDF.value:
            return PyMuPDFLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
        
    def get_file_content(self, file_id: str):
        loader = self.get_file_loader(file_id)
        if loader:
            return loader.load()
        else:
            return None
    
    # file_content is a list of Document objects (with page_content and metadata attributes) returned by the loader.load() method
    def process_file_content(self, file_content: list, file_id: str, 
                             chunk_size: int = 500, overlap_size: int = 100):
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=overlap_size, 
            length_function=len
        )

        file_content_texts =[
            rec.page_content for rec in file_content
        ]
        file_content_metadata = [
            rec.metadata for rec in file_content
        ]

        chunks = text_splitter.create_documents(
            file_content_texts, 
            metadatas=file_content_metadata
        )
        # chunks = self.process_simple_splitter(
        #     texts=file_content_texts,
        #     metadata=file_content_metadata,
        #     chunk_size=chunk_size
        # )
        return chunks
    
    def process_simple_splitter(self, texts: List[str], metadata: List[dict], chunk_size: int, splitter: str = "\n"):
        full_text = " ".join(texts)

        # Split the full text into chunks based on the specified splitter
        lines = [line.strip() for line in full_text.split(splitter) if line.strip()]
        
        chunks = []
        current_chunk = ""

        for line in lines:
            current_chunk += line + splitter
            if len(current_chunk) >= chunk_size:
                chunks.append(Document(
                    page_content=current_chunk.strip(),
                    metadata={}
                ))
                current_chunk = ""

            if len(current_chunk) > 0:
                chunks.append(Document(
                    page_content=current_chunk.strip(),
                    metadata={}
                ))

        return chunks
