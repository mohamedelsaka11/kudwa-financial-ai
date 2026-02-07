
import os
import re
from typing import Optional, Dict, Any, List
from groq import Groq
from sqlalchemy import text
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from app.database import SessionLocal
from datetime import datetime


load_dotenv()

class AIService:
   
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        
        self.conversation_history = []
        self.max_history = 10
        
        self.db_schema = """
        Table: financial_periods
        Columns:
        - id: INTEGER (Primary Key)
        - source: TEXT ('quickbooks' or 'rootfi')
        - period_start: DATE
        - period_end: DATE
        - year: INTEGER (e.g., 2024)
        - month: INTEGER (1-12)
        - quarter: INTEGER (1-4, where Q1=1, Q2=2, Q3=3, Q4=4)
        - total_revenue: REAL (total income/revenue for the period)
        - total_cogs: REAL (cost of goods sold)
        - gross_profit: REAL (revenue - cogs)
        - total_operating_expenses: REAL (operating expenses)
        - other_income: REAL
        - other_expenses: REAL
        - net_income: REAL (final profit/loss)
        
        Table: account_details
        Columns:
        - id: INTEGER (Primary Key)
        - period_id: INTEGER (Foreign Key to financial_periods)
        - category: TEXT ('income', 'expense', 'cogs')
        - account_name: TEXT
        - parent_account: TEXT
        - amount: REAL
        - account_id: TEXT
        
        Notes:
        - Data spans from 2020 to 2025
        - QuickBooks has 68 monthly records
        - Rootfi has 36 monthly records
        - Total: 104 records
        - All monetary values are in USD
        """
    def add_to_history(self, role: str, content: str):
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
    
    def get_conversation_context(self) -> str:
        if not self.conversation_history:
            return ""
        
        context = "PREVIOUS CONVERSATION:\n"
        for msg in self.conversation_history[-6:]:  
            role = "User" if msg["role"] == "user" else "Assistant"
            context += f"{role}: {msg['content']}\n"
        
        return context
    
    def clear_history(self):
        self.conversation_history = []
    
    
    
    def generate_sql(self, question: str) -> str:
        
        conversation_context = self.get_conversation_context()
        
        prompt = f"""You are a SQL expert. Convert the following natural language question to a SQLite SQL query.

DATABASE SCHEMA:
{self.db_schema}

{conversation_context}

IMPORTANT RULES:
1. Return ONLY the SQL query, no explanations
2. Use SQLite syntax
3. For quarters: Q1=1, Q2=2, Q3=3, Q4=4
4. For profit questions, use net_income column
5. For revenue questions, use total_revenue column
6. For expenses, use total_operating_expenses + total_cogs
7. Always include year in results when relevant
8. Use SUM() for aggregations across multiple periods
9. Round monetary values to 2 decimal places using ROUND()
10. If question asks about "profit", use net_income
11. If question asks about comparison, use appropriate GROUP BY
12. If the question refers to previous context (like "and Q2?" or "what about 2023?"), use the context to understand what metric is being asked about

CURRENT QUESTION: {question}

SQL QUERY:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a SQL expert. Return only valid SQLite SQL queries, nothing else. Use conversation context to understand follow-up questions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,
                max_tokens=500
            )
            
            sql = response.choices[0].message.content.strip()
            
            sql = self._clean_sql(sql)
            
            return sql
            
        except Exception as e:
            print(f"Error generating SQL: {e}")
            return None
    
    def _clean_sql(self, sql: str) -> str:
        
        sql = re.sub(r'```sql\s*', '', sql)
        sql = re.sub(r'```\s*', '', sql)
        
        if 'SELECT' in sql.upper():
            start = sql.upper().find('SELECT')
            sql = sql[start:]
        
        if ';' in sql:
            sql = sql.split(';')[0] + ';'
        
        return sql.strip()
    
    def execute_sql(self, sql: str, db: Session) -> List[Dict]:
        
        if not self._is_safe_sql(sql):
            print("Blocked unsafe SQL query!")
            return None
        
        try:
            result = db.execute(text(sql))
            columns = result.keys()
            rows = result.fetchall()
            
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))
            
            return data
            
        except Exception as e:
            print(f"Error executing SQL: {e}")
            return None
    
    def _is_safe_sql(self, sql: str) -> bool:
        
        sql_clean = sql.replace('\n', ' ').replace('\r', ' ').strip()
        sql_upper = sql_clean.upper()
        
        dangerous_keywords = [
            'DROP ', 'DELETE ', 'INSERT ', 'UPDATE ', 
            'ALTER ', 'CREATE ', 'TRUNCATE ', 'REPLACE ',
            'EXEC ', 'EXECUTE ', 'GRANT ', 'REVOKE ',
            ' -- ', ';--', '/*', '*/', 'XP_'
        ]
        
        if not sql_upper.startswith('SELECT'):
            print(f"Query must start with SELECT")
            return False
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                print(f"Dangerous keyword detected: {keyword}")
                return False
        
        sql_without_end = sql_clean.rstrip(';')
        if ';' in sql_without_end:
            print("Multiple statements not allowed")
            return False
        
        print("SQL query is safe")
        return True
    
    def generate_answer(self, question: str, sql: str, data: List[Dict]) -> str:
        
        prompt = f"""Based on the following data, provide a clear and concise answer to the user's question.

QUESTION: {question}

SQL QUERY USED: {sql}

DATA RESULTS:
{data}

INSTRUCTIONS:
1. Provide a direct, clear answer
2. Include specific numbers from the data
3. Format currency values with $ and commas (e.g., $1,234,567.89)
4. If comparing periods, mention the trend (increase/decrease)
5. Keep the answer concise but informative
6. Add a brief insight if relevant

ANSWER:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analyst providing clear, data-driven insights. Be concise and professional."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating answer: {e}")
            return f"The query returned: {data}"
    
       
    
    def comparative_analysis(self, period1: str, period2: str, year: int = None) -> Dict[str, Any]:
        
        db = SessionLocal()
        
        try:
           
            if period1.startswith('Q') and period2.startswith('Q'):
                
                q1 = int(period1[1])
                q2 = int(period2[1])
                
                if not year:
                    year = 2024  
                
                sql = f"""
                SELECT 
                    quarter,
                    ROUND(SUM(total_revenue), 2) as revenue,
                    ROUND(SUM(total_operating_expenses + total_cogs), 2) as expenses,
                    ROUND(SUM(gross_profit), 2) as gross_profit,
                    ROUND(SUM(net_income), 2) as net_income
                FROM financial_periods
                WHERE year = {year} AND quarter IN ({q1}, {q2})
                GROUP BY quarter
                ORDER BY quarter
                """
                comparison_type = "quarterly"
                
            else:
                
                year1 = int(period1)
                year2 = int(period2)
                
                sql = f"""
                SELECT 
                    year,
                    ROUND(SUM(total_revenue), 2) as revenue,
                    ROUND(SUM(total_operating_expenses + total_cogs), 2) as expenses,
                    ROUND(SUM(gross_profit), 2) as gross_profit,
                    ROUND(SUM(net_income), 2) as net_income
                FROM financial_periods
                WHERE year IN ({year1}, {year2})
                GROUP BY year
                ORDER BY year
                """
                comparison_type = "yearly"
            
            
            data = self.execute_sql(sql, db)
            
            if not data or len(data) < 2:
                return {
                    "success": False,
                    "error": "Not enough data for comparison"
                }
            
            
            period1_data = data[0]
            period2_data = data[1]
            
            changes = {}
            for key in ['revenue', 'expenses', 'gross_profit', 'net_income']:
                val1 = period1_data.get(key, 0) or 0
                val2 = period2_data.get(key, 0) or 0
                
                change = val2 - val1
                change_pct = (change / val1 * 100) if val1 != 0 else 0
                
                changes[key] = {
                    "period1_value": val1,
                    "period2_value": val2,
                    "change": round(change, 2),
                    "change_percentage": round(change_pct, 2)
                }
            
            analysis = self._generate_comparative_insight(
                period1, period2, changes, comparison_type, year
            )
            
            return {
                "success": True,
                "comparison_type": comparison_type,
                "period1": period1,
                "period2": period2,
                "year": year if comparison_type == "quarterly" else None,
                "data": {
                    "period1": period1_data,
                    "period2": period2_data
                },
                "changes": changes,
                "analysis": analysis
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        
        finally:
            db.close()
    
    def _generate_comparative_insight(self, period1: str, period2: str, 
                                       changes: Dict, comparison_type: str,
                                       year: int = None) -> str:
        
        year_text = f" in {year}" if year else ""
        
        prompt = f"""Analyze this financial comparison between {period1} and {period2}{year_text}:

CHANGES:
- Revenue: ${changes['revenue']['period1_value']:,.2f} → ${changes['revenue']['period2_value']:,.2f} ({changes['revenue']['change_percentage']:+.1f}%)
- Expenses: ${changes['expenses']['period1_value']:,.2f} → ${changes['expenses']['period2_value']:,.2f} ({changes['expenses']['change_percentage']:+.1f}%)
- Gross Profit: ${changes['gross_profit']['period1_value']:,.2f} → ${changes['gross_profit']['period2_value']:,.2f} ({changes['gross_profit']['change_percentage']:+.1f}%)
- Net Income: ${changes['net_income']['period1_value']:,.2f} → ${changes['net_income']['period2_value']:,.2f} ({changes['net_income']['change_percentage']:+.1f}%)

Provide a brief, insightful analysis (3-4 sentences) highlighting:
1. The most significant change
2. Whether performance improved or declined
3. Any concerns or positive trends"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analyst providing clear, concise insights."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Revenue changed by {changes['revenue']['change_percentage']:+.1f}%, Net Income changed by {changes['net_income']['change_percentage']:+.1f}%"
    
    def query(self, question: str) -> Dict[str, Any]:
        
        print(f"\n{'='*50}")
        print(f"Question ? {question}")
        print('='*50)
        
        self.add_to_history("user", question)
        
        print(" Generation Loading SQL...")
        sql = self.generate_sql(question)
        
        if not sql:
            error_response = {
                "success": False,
                "question": question,
                "error": "Failed to generate SQL query",
                "answer": "I couldn't understand the question. Please try rephrasing."
            }
            return error_response
        
        print(f"SQL: {sql}")
        
        
        print("Query Loading...")
        db = SessionLocal()
        
        try:
            data = self.execute_sql(sql, db)
            
            if data is None:
                error_response = {
                    "success": False,
                    "question": question,
                    "sql_query": sql,
                    "error": "Failed to execute SQL query",
                    "answer": "There was an error executing the query. The SQL might be invalid."
                }
                return error_response
            
            print(f" Results {len(data)} ")
            
            print("Generation Loading result...")
            answer = self.generate_answer(question, sql, data)
            
            self.add_to_history("assistant", answer)
            
            print(f"Result {answer[:100]}...")
            
            return {
                "success": True,
                "question": question,
                "sql_query": sql,
                "data": data,
                "answer": answer,
                "rows_returned": len(data)
            }
            
        except Exception as e:
            error_response = {
                "success": False,
                "question": question,
                "sql_query": sql,
                "error": str(e),
                "answer": f"An error occurred: {str(e)}"
            }
            return error_response
        
        finally:
            db.close()
    
    def get_sample_questions(self) -> List[str]:
        
        return [
            "What was the total profit in Q1 2024?",
            "Show me revenue trends for 2024",
            "Which quarter had the highest revenue in 2024?",
            "Compare Q1 and Q2 performance in 2024",
            "What was the total revenue in 2023?",
            "What are the total expenses for 2024?",
            "Show me the net income by quarter for 2024",
            "What was the gross profit in Q4 2024?",
            "Which year had the highest revenue?",
            "What is the average monthly revenue in 2024?"
        ]


if __name__ == "__main__":
    print("\n" + "-"*25)
    print(" Kudwa Financial AI - Test Mode")
    print("-"*25)
    
   
    ai = AIService()
    
    test_question = "What was the total profit in Q1 2024?"
    
    result = ai.query(test_question)
    
    print("\n" + "="*50)
    print("Complete Result")
    print("="*50)
    print(f"Success: {result['success']}")
    print(f"Question: {result['question']}")
    print(f"SQL: {result.get('sql_query', 'N/A')}")
    print(f"Data: {result.get('data', 'N/A')}")
    print(f"Answer: {result.get('answer', 'N/A')}")