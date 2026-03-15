from enum import Enum

class ResponseEnum(Enum):
    
    FILE_TYPE_NOT_SUPPORTED = "File type is not supported."
    FILE_SIZE_EXCEEDED = "File size exceeds the maximum limit."
    FILE_UPLOAD_SUCCESS = "File uploaded successfully."
    FILE_UPLOAD_FAILURE = "File upload failed."
    FILE_VALIDATION_SUCCESS = "File validated successfully."
    FILE_PROCESSING_FAILED = "File processing failed."
    FILE_PROCESSING_SUCCESS = "File processed successfully."