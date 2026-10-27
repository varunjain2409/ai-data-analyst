import os
from openai import OpenAI
from database import get_schema
from rule_based_sql import convert_to_sql_rule_based

api_key = os.environ.get("OPENAI_API_KEY", "")
client = OpenAI(api_key=api_key) if api_key else None

SYSTEM_PROMPT = """You are an expert SQL assistant. Convert the user's natural language question into a valid SQLite query.

Database Schema:
{schema}

Rules:
1. Return ONLY the SQL query, no explanation, no markdown formatting
2. Use proper SQLite syntax
3. Only use SELECT statements (no INSERT, UPDATE, DELETE)
4. Use appropriate WHERE clauses, GROUP BY, ORDER BY, JOINs as needed
5. For date comparisons, use the format 'YYYY-MM-DD'
6. Table names: products, customers, orders
7. Column names: id, name, category, price, stock (products); id, name, email, city, country, joined_date (customers); id, customer_id, product_id, quantity, total_amount, order_date, status (orders)

User Question: {question}

SQL Query:"""


def convert_to_sql(question):
    # Try OpenAI first if API key is available
    if client:
        try:
            schema = get_schema()
            prompt = SYSTEM_PROMPT.format(schema=schema, question=question)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=200
            )
            sql = response.choices[0].message.content.strip()
            sql = sql.replace("```sql", "").replace("```", "").strip()
            return {"success": True, "sql": sql, "method": "openai"}
        except Exception:
            pass

    # Fallback to rule-based
    return convert_to_sql_rule_based(question)
