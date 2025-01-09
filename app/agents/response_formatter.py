from pydantic import BaseModel, Field
from typing import Dict, Any
import instructor
from langchain_groq import ChatGroq

class FormattedResponse(BaseModel):
    message: str = Field(description="Natural language response")
    data: Dict[str, Any] = Field(description="Structured data")

class ResponseFormatter:
    def __init__(self, groq_api_key: str):
        self.groq_client = ChatGroq(api_key=groq_api_key)
        self.instructor_client = instructor.patch(self.groq_client)
    
    def format_response(self, query: str, results: Dict[str, Any], user_context: Dict) -> FormattedResponse:
        prompt = f"""Format a response for:
        Original Query: {query}
        Query Results: {results}
        User Context: {user_context}
        
        Requirements:
        1. Natural language response
        2. Highlight key information
        3. Include relevant numbers/stats
        4. Keep original data in structured format
        """
        
        return self.instructor_client(
            model="mixtral-8x7b-32768",
            response_model=FormattedResponse,
            messages=[{"role": "user", "content": prompt}]
        )