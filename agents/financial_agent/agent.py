from app.core.base_agent import BaseAgent
from typing import Any, Dict

class FinancialAgent(BaseAgent):
    def process_input(self, input_data: Any) -> Dict:
        # Add your document processing logic here
        return {"processed": input_data}
    
    def generate_response(self, processed_data: Dict) -> Dict:
        # Add your AI analysis logic here
        return {
            "analysis": "Sample analysis",
            "recommendations": ["Sample recommendation"]
        }