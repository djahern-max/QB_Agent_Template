from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseAgent(ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    @abstractmethod
    def process_input(self, input_data: Any) -> Dict:
        pass
    
    @abstractmethod
    def generate_response(self, processed_data: Dict) -> Dict:
        pass