from .BaseController import BaseController
from .ProjectController import ProjectController
import os
from langchain_community.document_loaders import TextLoader, PyMuPDFLoader
from models import ProcessEnum
from langchain_text_splitters import RecursiveCharacterTextSplitter

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

        if ext == ProcessEnum.EXT_TEXT.value:
            return TextLoader(file_path, encoding="utf-8")
        elif ext == ProcessEnum.EXT_PDF.value:
            return PyMuPDFLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
        
    def get_file_content(self, file_id: str):
        loader = self.get_file_loader(file_id)
        return loader.load()
    
    # file_content is a list of Document objects (with page_content and metadata attributes) returned by the loader.load() method
    def process_file_content(self, file_content: list, file_id: str, 
                             chunk_size: int = 100, overlap_size: int = 20):
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=overlap_size, 
            length_function=len)

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
        return chunks

    