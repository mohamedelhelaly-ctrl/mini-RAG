from .BaseController import BaseController
from fastapi import UploadFile
from models import ResponseEnum
from .ProjectController import ProjectController
import re
import os

class DataController(BaseController):
    
    def __init__(self):
        super().__init__()
        self.size_scale = 1024 * 1024  # Convert bytes to MB
    
    def validate_file(self, file: UploadFile):
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False, ResponseEnum.FILE_TYPE_NOT_SUPPORTED.value
        
        if file.size > self.app_settings.FILE_MAX_SIZE * self.size_scale:
            return False, ResponseEnum.FILE_SIZE_EXCEEDED.value
        
        return True, ResponseEnum.FILE_VALIDATION_SUCCESS.value
    
    def generate_unique_filename(self, original_filename: str, project_id: str):
        
        project_path = ProjectController().get_project_path(project_id=project_id)
        random_key = self.generate_random_key()
        cleaned_filename = self.clean_filename(original_filename=original_filename)

        new_file_path = os.path.join(project_path, random_key + "_" + cleaned_filename)

        while(os.path.exists(new_file_path)):
            random_key = self.generate_random_key()
            new_file_path = os.path.join(project_path, random_key + "_" + cleaned_filename)
        
        return new_file_path


    def clean_filename(self, original_filename: str):
        #remove any special characters except _ and .
        cleaned_filename = re.sub(r'[^\w\.-]', '_', original_filename)
        
        #replace any space with underscore
        cleaned_filename = cleaned_filename.replace(' ', '_')
        
        return cleaned_filename
    