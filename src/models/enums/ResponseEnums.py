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