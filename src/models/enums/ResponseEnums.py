from enum import Enum

class ResponseEnum(Enum):
    
    FILE_TYPE_NOT_SUPPORTED = "File type is not supported."
    FILE_SIZE_EXCEEDED = "File size exceeds the maximum limit."
    FILE_UPLOAD_SUCCESS = "File uploaded successfully."
    FILE_UPLOAD_FAILURE = "File upload failed."
    FILE_VALIDATION_SUCCESS = "File validated successfully."
    FILE_PROCESSING_FAILED = "File processing failed."
    FILE_PROCESSING_SUCCESS = "File processed successfully."
    NO_FILES_TO_PROCESS = "No files available to process for this project."
    FILE_NOT_FOUND = "File not found for the given project and file ID."
    PROJECT_NOT_FOUND = "Project not found."
    VECTORDB_INSERTION_FAILED = "Failed to insert data into vector database."
    VECTORDB_INSERTION_SUCCESS = "Data inserted into vector database successfully."
    VECTORDB_COLLECTION_INFO_RETRIEVED = "Vector database collection information retrieved successfully."
    VECTORDB_SEARCH_SUCCESS = "Vector database search completed successfully."
    VECTORDB_SEARCH_ERROR = "An error occurred during vector database search."
    RAG_ANSWER_ERROR = "An error occurred while generating the answer for the query."
    RAG_ANSWER_SUCCESS = "Answer generated successfully for the query."