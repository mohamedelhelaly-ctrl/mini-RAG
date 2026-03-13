from helpers.config import get_settings, Settings
import os
import random
import string

class BaseController:
    def __init__(self):
        self.app_settings = get_settings()
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        # self.files_dir = self.base_dir + "/assets/files"
        self.files_dir = os.path.join(self.base_dir, "assets/files")
    
    def generate_random_key(self, length=6):
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        return random_str