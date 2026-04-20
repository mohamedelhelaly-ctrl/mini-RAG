import os

class TemplateParser:
    def __init__(self, language: str, default_language: str = "en"):
        self.language = None
        self.default_language = default_language
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.set_language(language)

    def set_language(self, language: str):
        language_file_path = os.path.join(self.current_path, "locales", language)
        if language and os.path.exists(language_file_path):
            self.language = language
        else:
            self.language = self.default_language

    def get_prompt(self, group: str, key: str, vars: dict = {}):
        if not group or not key:
            return None
        
        current_language = self.language
        group_file_path = os.path.join(self.current_path, "locales", self.language, f"{group}.py")
        if not os.path.exists(group_file_path):
            current_language = self.default_language
            group_file_path = os.path.join(self.current_path, "locales", self.default_language, f"{group}.py")
        if not os.path.exists(group_file_path):
            return None
        
        module = __import__(f"stores.llm.templates.locales.{current_language}.{group}", fromlist=[group])
        if not module:
            return None
        
        key_attribute = getattr(module, key)
        return key_attribute.substitute(vars)
        

 