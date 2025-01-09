from pydantic import BaseModel, Field
from typing import Dict
import instructor
from langchain_groq import ChatGroq
from .query_analyzer import QueryIntent

class SQLQuery(BaseModel):
    query: str = Field(description="SQL query to execute")
    parameters: Dict = Field(description="Query parameters")

class SQLGenerator:
    def __init__(self, groq_api_key: str):
        self.groq_client = ChatGroq(api_key=groq_api_key)
        self.instructor_client = instructor.patch(self.groq_client)
    
    def generate_sql(self, query_intent: QueryIntent, user_id: int) -> SQLQuery:
        table_schemas = {
            "users": ["id", "email", "name", "created_at"],
            "products": ["id", "name", "description", "price", "stock"],
            "transactions": ["id", "user_id", "product_id", "quantity", "total_amount", "status", "timestamp"],
            "reviews": ["id", "user_id", "product_id", "rating", "comment", "timestamp"]
        }
        
        prompt = f"""Generate a SQL query based on the following intent:
        Query Type: {query_intent.query_type}
        Required Tables: {query_intent.required_tables}
        Filters: {query_intent.filters}
        Time Range: {query_intent.time_range}
        User ID: {user_id}
        
        Table Schemas:
        {table_schemas}
        
        Requirements:
        1. Always include user_id filter for security
        2. Use proper JOIN syntax
        3. Return relevant columns only
        4. Use parameterized queries
        """
        
        return self.instructor_client(
            model="mixtral-8x7b-32768",
            response_model=SQLQuery,
            messages=[{"role": "user", "content": prompt}]
        )