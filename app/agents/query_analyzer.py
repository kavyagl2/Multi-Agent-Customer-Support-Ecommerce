from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import instructor
from groq import Groq


class QueryIntent(BaseModel):
    query_type: str = Field(description="Type of query (e.g., 'transaction_lookup', 'product_info')")
    required_tables: List[str] = Field(description="List of database tables needed")
    filters: Dict = Field(description="Query filters to apply")
    time_range: Optional[Dict] = Field(description="Time range for the query")

class QueryAnalyzer:
    def __init__(self, groq_api_key: str):
        self.groq_client = Groq(api_key=groq_api_key)
        self.instructor_client = instructor.from_groq(self.groq_client,mode=instructor.Mode.JSON)
    
    def analyze_query(self, query: str, user_context: Dict) -> QueryIntent:
        prompt = f"""Analyze the following user query and context:
        Query: {query}
        Context: {user_context}
        
        Determine:
        1. What type of information they're looking for
        2. Which database tables need to be queried
        3. What filters should be applied
        4. Any time range specifications
        
        Available tables: users, products, transactions, reviews"""
        
        return self.instructor_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_model=QueryIntent,
            messages=[{"role": "user", "content": prompt}]
        )
