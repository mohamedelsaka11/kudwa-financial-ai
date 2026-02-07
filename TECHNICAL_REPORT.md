# Technical Report: Kudwa Financial AI

## 1. Project Overview

### 1.1 Objective

Build an intelligent financial data processing system that integrates diverse financial data sources and provides AI-powered natural language querying capabilities.

### 1.2 Key Requirements

- Integrate data from QuickBooks and Rootfi sources
- Enable natural language queries on financial data
- Provide RESTful APIs for data access
- Ensure data security and query safety

---

## 2. Architecture Design

### 2.1 System Architecture

```text
+----------------+      +----------------+      +----------------+
|                |      |                |      |                |
|     Client     |----->|    FastAPI     |----->|    SQLite      |
|   (API Call)   |      |    Backend     |      |   Database     |
|                |      |                |      |                |
+----------------+      +-------+--------+      +----------------+
                                |
                                v
                        +----------------+
                        |                |
                        |   Groq LLM     |
                        |  (Llama 3.3)   |
                        |                |
                        +----------------+
```

### 2.2 Data Flow

1. User sends natural language question
2. AI Service converts question to SQL
3. SQL executes against SQLite database
4. Results processed and returned with AI-generated insights

---

## 3. Technology Choices

### 3.1 Backend Framework: FastAPI

Why FastAPI?

- High performance (async support)
- Automatic API documentation (Swagger/OpenAPI)
- Built-in data validation with Pydantic
- Easy to learn and maintain

Alternatives Considered:

- Flask: Simpler but lacks async and auto-docs
- Django: Too heavy for this use case

### 3.2 Database: SQLite

Why SQLite?

- Zero configuration required
- Perfect for demo/assessment projects
- Easy deployment (single file)
- Sufficient for the data volume (104 records)

For Production:

- Would migrate to PostgreSQL for scalability
- Add connection pooling and proper indexing

### 3.3 LLM: Groq (Llama 3.3 70B)

Why Groq?

- Extremely fast inference (~200ms)
- Free tier available
- High-quality SQL generation
- Good understanding of financial context

Alternatives Considered:

- OpenAI GPT-4: Better quality but slower and costs money
- Local LLM: Too slow for real-time queries

### 3.4 ORM: SQLAlchemy

Why SQLAlchemy?

- Industry standard for Python
- Supports multiple databases
- Easy migration if needed
- Good integration with FastAPI

---

## 4. Data Processing Approach

### 4.1 Challenge: Different Data Formats

QuickBooks Format:

- Nested JSON structure
- Column-based (one column per month)
- 68 monthly periods

Rootfi Format:

- Record-based JSON
- One record per month
- 36 monthly periods

### 4.2 Solution: Unified Schema

Created a normalized database schema that accepts data from both sources:

| Field                | Description                        |
| -------------------- | ---------------------------------- |
| source               | Origin of data (quickbooks/rootfi) |
| period_start         | Start date of period               |
| year, month, quarter | Time dimensions                    |
| total_revenue        | Total income                       |
| net_income           | Final profit/loss                  |

### 4.3 Data Transformation

- QuickBooks: Parsed nested structure, extracted values by column index
- Rootfi: Iterated through records, calculated missing net_income
- Both: Normalized to same schema, stored in unified table

---

## 5. AI Integration

### 5.1 Text-to-SQL Approach

Why Text-to-SQL instead of RAG?

- Financial data requires precise calculations
- SQL provides exact numerical results
- Easier to validate and debug
- Better for aggregations (SUM, AVG, etc.)

### 5.2 Implementation

1. Schema Injection: Database schema included in every prompt
2. SQL Generation: LLM converts question to SQL
3. Safety Validation: Check for dangerous keywords
4. Execution: Run validated SQL query
5. Answer Generation: LLM creates human-readable response

### 5.3 Conversation Memory

Implemented conversation history to support follow-up questions:

- Stores last 10 messages
- Includes context in SQL generation prompt
- Enables queries like "And Q2?" after asking about Q1

---

## 6. Security Measures

### 6.1 SQL Injection Protection

Blocked Keywords:

- DROP, DELETE, INSERT, UPDATE
- ALTER, CREATE, TRUNCATE

Protection Methods:

- Only SELECT queries allowed
- Dangerous keywords blocked
- Multiple statements prevented

### 6.2 Input Validation

- All API inputs validated with Pydantic
- Type checking enforced
- Invalid requests rejected with clear errors

---

## 7. API Design

### 7.1 RESTful Principles

- Resource-based URLs (/periods, /summary)
- HTTP methods used correctly (GET, POST)
- Consistent response format

### 7.2 Versioning

- API versioned (/api/v1/)
- Allows future updates without breaking changes

---

## 8. Known Limitations

### 8.1 Current Limitations

- SQLite not suitable for high concurrency
- Conversation memory not persisted (in-memory only)
- No user authentication
- Limited to English queries

### 8.2 Future Improvements

- Add PostgreSQL for production
- Implement Redis for session storage
- Add JWT authentication
- Support multiple languages
- Add query caching for performance
- Implement rate limiting

---

## 9. Testing

### 9.1 Manual Testing Performed

- All API endpoints tested via Swagger UI
- AI queries tested with various question types
- SQL injection attempts blocked successfully
- Comparative analysis verified with known data

### 9.2 Sample Test Cases

| Test            | Input               | Expected         | Result |
| --------------- | ------------------- | ---------------- | ------ |
| Revenue Query   | Total revenue 2024? | 53.28M           | Pass   |
| Quarter Compare | Q1 vs Q2 2024       | Shows difference | Pass   |
| SQL Injection   | DROP TABLE          | Blocked          | Pass   |
| Follow-up       | And Q2?             | Uses context     | Pass   |

---

## 10. Conclusion

This project successfully demonstrates:

- Integration of multiple financial data sources
- AI-powered natural language querying
- Clean API design with proper documentation
- Security-first approach to data access

The system is production-ready for demo purposes and provides a solid foundation for future enhancements.

---

Author: [Mohamed Elsaka]
