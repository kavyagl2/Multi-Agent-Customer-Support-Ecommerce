from pydantic import BaseModel, Field
from typing import Dict
import instructor
from groq import Groq
from .query_analyzer import QueryIntent

from sqlalchemy import text
from pydantic import BaseModel, Field
from typing import Dict


class SQLQuery(BaseModel):
    query: str = Field(description="SQL query to execute")
    parameters: Dict = Field(description="Query parameters")

    def to_sqlalchemy(self):
        """Convert to SQLAlchemy-compatible text query."""
        return text(self.query), self.parameters  # Return both query and parameters for SQLAlchemy

class SQLGenerator:
    def __init__(self, groq_api_key: str):
        self.groq_client = Groq(api_key=groq_api_key)
        self.instructor_client = instructor.from_groq(self.groq_client, mode=instructor.Mode.JSON)

    def generate_sql(self, query_intent: QueryIntent, user_id: int) -> SQLQuery:
        table_schemas = {
            "users": ["id", "email", "name", "created_at"],
            "products": ["id", "name", "description", "price", "stock"],
            "transactions": ["id", "user_id", "product_id", "quantity", "total_amount", "status", "timestamp"],
            "reviews": ["id", "user_id", "product_id", "rating", "comment", "timestamp"]
        }

        prompt = f"""
                ### Task: Generate a secure, optimized SQL query based on user intent, dynamically handling different user requests.

                #### **User Query Details:**
                - **Query Type:** {query_intent.query_type}  
                - **Required Tables:** {query_intent.required_tables}  
                - **Filters:** {query_intent.filters}  
                - **Time Range:** {query_intent.time_range}  
                - **User ID:** {user_id}

                #### **Database Schema:**
                The database contains the following tables and columns:

                1. **users**  
                - `id` (Primary Key)  
                - `email`  
                - `name`  
                - `created_at`  

                2. **products**  
                - `id` (Primary Key)  
                - `name`  
                - `description`  
                - `price`  
                - `stock`  

                3. **transactions**  
                - `id` (Primary Key)  
                - `user_id` (Foreign Key → users.id)  
                - `product_id` (Foreign Key → products.id)  
                - `quantity`  
                - `total_amount`  
                - `status`  
                - `timestamp`  

                4. **reviews**  
                - `id` (Primary Key)  
                - `user_id` (Foreign Key → users.id)  
                - `product_id` (Foreign Key → products.id)  
                - `rating`  
                - `comment`  
                - `timestamp`  

                ---

                ### **SQL Query Requirements**
                1. **Use Explicit Table Aliases**  
                - Use clear aliases (e.g., `u` for users, `t` for transactions).
                - Example: `FROM transactions AS t JOIN users AS u ON t.user_id = u.id`.

                2. **Include the Required Tables in the FROM Clause**  
                - Ensure all tables referenced in the query are included in the `FROM` and `JOIN` clauses.
                - Example:
                    ```sql
                    SELECT t.id, t.total_amount, u.name
                    FROM transactions t
                    JOIN users u ON t.user_id = u.id
                    WHERE t.user_id = :user_id
                    ```

                3. **Always Use Parameterized Queries (No Hardcoded Values)**  
                - Use placeholders for dynamic values, such as `:user_id` or `:start_date`, instead of hardcoding values.

                4. **Handle Filters Dynamically**  
                - Incorporate filters provided by the user into the `WHERE` clause. If the user specifies multiple filters, combine them logically (e.g., `AND`/`OR`).
                - Example:
                    ```sql
                    WHERE t.user_id = :user_id AND t.timestamp >= :start_date
                    ```

                5. **Support Sorting and Limiting Results**  
                - If sorting is required, ensure that the model generates an `ORDER BY` clause with proper sorting direction (`ASC` or `DESC`).
                - Always include a `LIMIT` clause when necessary.
                - Example:
                    ```sql
                    ORDER BY t.timestamp DESC LIMIT :limit
                    ```

                6. **Handle Dynamic Joins**  
                - If multiple tables are involved, generate the necessary `JOIN` clauses based on the user query.
                - Example:
                    ```sql
                    SELECT t.id, t.quantity, p.name
                    FROM transactions t
                    JOIN products p ON t.product_id = p.id
                    WHERE t.user_id = :user_id
                    ```

                7. **Dynamic Query Construction Based on User Input**  
                - Based on the user's query, adapt the query to fit the user's intent. Consider scenarios where the user requests:
                    - Information from a single table (e.g., users or transactions).
                    - Joins across multiple tables (e.g., transactions, products, and reviews).
                    - Filtering by various fields, such as `user_id`, `timestamp`, `status`, etc.
                    - Time-range-based filtering, such as recent transactions or reviews.

                8. **Ensure Query Optimization**  
                - Generate efficient queries that avoid `SELECT *`, ensuring only the required columns are fetched.
                - Limit the number of rows returned using `LIMIT` where applicable.

                ---

                ### **Examples of Dynamic Query Generation:**

                #### **Example 1: "Show me the last reviewed transaction."**
                **Generated SQL:**
                ```sql
                SELECT t.id, t.user_id, t.product_id, t.quantity, t.total_amount, t.status, t.timestamp, 
                    r.id AS review_id, r.rating, r.comment, r.timestamp AS review_timestamp
                FROM transactions t
                JOIN reviews r ON t.id = r.product_id
                WHERE t.user_id = :user_id
                ORDER BY r.timestamp DESC
                LIMIT 1
                ```
                """

        response = self.instructor_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_model=SQLQuery,
            messages=[{"role": "user", "content": prompt}]
        )

        return response  # This will return SQLQuery with query and parameters

