# 🏦 Kudwa Financial AI

An intelligent financial data processing system with AI-powered natural language querying capabilities.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [AI Capabilities](#ai-capabilities)
- [Project Structure](#project-structure)
- [Technologies Used](#technologies-used)

---

## 🎯 Overview

Kudwa Financial AI is a backend system that integrates diverse financial data sources (QuickBooks and Rootfi) into a unified database, enabling users to query financial data using natural language. The system leverages Large Language Models (LLMs) to convert natural language questions into SQL queries and provide insightful answers.

### Problem Solved

- **Data Fragmentation:** Unifies data from multiple financial sources
- **Technical Barriers:** Enables non-technical users to query data naturally
- **Time Savings:** Instant insights instead of manual spreadsheet analysis

---

## ✨ Features

### Core Features

- ✅ Multi-Source Data Integration: QuickBooks and Rootfi data unified
- ✅ Natural Language Querying: Ask questions in plain English
- ✅ Text-to-SQL Conversion: AI-powered SQL generation
- ✅ RESTful API: Clean, documented endpoints
- ✅ Conversation Memory: Context-aware follow-up questions

### AI Analytics

- ✅ Comparative Analysis: Compare quarters or years
- ✅ Trend Analysis: Revenue and expense trends
- ✅ Automated Insights: AI-generated financial insights

### Security

- ✅ SQL Injection Protection: Only SELECT queries allowed
- ✅ Input Validation: Pydantic schema validation

---

## 🚀 Installation

### Prerequisites

- Python 3.11 or higher
- Groq API Key from https://console.groq.com/keys

### Step 1: Download or Clone the Repository

Download the project files and navigate to the project directory:

cd kudwa-financial-ai

### Step 2: Create Virtual Environment

python -m venv venv

Windows:
venv\Scripts\activate

macOS/Linux:
source venv/bin/activate

### Step 3: Install Dependencies

pip install -r requirements.txt

### Step 4: Configure Environment

Create .env file in the root directory with:

GROQ_API_KEY=your_api_key_here

DATABASE_URL=sqlite:///./kudwa_financial.db

APP_NAME=Kudwa Financial AI
DEBUG=True

### Step 5: Load Data

python -m app.services.data_processor

### Step 6: Run the Server

uvicorn app.main:app --reload

### Step 7: Access the API

- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

---

## 📖 Usage

### Natural Language Query Example

POST http://localhost:8000/api/v1/ai/query

Body: {"question": "What was the total revenue in 2024?"}

Response:
{
"question": "What was the total revenue in 2024?",
"answer": "The total revenue in 2024 was ,281,944.86.",
"confidence": 1.0
}

### Comparative Analysis Example

GET http://localhost:8000/api/v1/ai/compare?period1=Q1&period2=Q2&year=2024

---

## 🔌 API Endpoints

### Financial Data Endpoints

| Method | Endpoint                   | Description               |
| ------ | -------------------------- | ------------------------- |
| GET    | /api/v1/health             | Health check              |
| GET    | /api/v1/periods            | Get all financial periods |
| GET    | /api/v1/summary            | Get financial summary     |
| GET    | /api/v1/quarterly/{year}   | Quarterly analysis        |
| GET    | /api/v1/trends/revenue     | Revenue trends            |
| GET    | /api/v1/expenses/breakdown | Expense breakdown         |

### AI Endpoints

| Method | Endpoint                    | Description               |
| ------ | --------------------------- | ------------------------- |
| POST   | /api/v1/ai/query            | Natural language query    |
| GET    | /api/v1/ai/compare          | Comparative analysis      |
| GET    | /api/v1/ai/sample-questions | Sample questions          |
| POST   | /api/v1/ai/clear-history    | Clear conversation        |
| GET    | /api/v1/ai/history          | View conversation history |

---

## 🤖 AI Capabilities

### Sample Questions

- What was the total profit in Q1 2024?
- Show me revenue trends for 2024
- Which quarter had the highest revenue?
- Compare Q1 and Q2 performance in 2024
- What were the total expenses in 2023?

### Follow-up Questions

- The system supports context-aware conversations:

- User: What was revenue in Q1 2024?
  - AI: The revenue was .78M

- User: And Q2?
  - AI: The revenue was .24M (understands context)

---

## 📁 Project Structure

```text
kudwa-financial-ai/
|
|-- app/
|   |-- __init__.py
|   |-- main.py                  # FastAPI application
|   |-- database.py              # Database configuration
|   |-- models.py                # SQLAlchemy models
|   |
|   |-- api/
|   |   |-- __init__.py
|   |   |-- routes.py            # API endpoints
|   |
|   |-- services/
|   |   |-- __init__.py
|   |   |-- data_processor.py    # Data processing
|   |   |-- ai_service.py        # AI/LLM integration
|   |
|   |-- schemas/
|       |-- __init__.py
|       |-- financial.py         # Pydantic schemas
|
|-- data/
|   |-- data_set_1.json          # QuickBooks data
|   |-- data_set_2.json          # Rootfi data
|
|-- .env                         # Environment variables
|-- requirements.txt             # Dependencies
|-- README.md                    # Documentation

```

---

## 🛠️ Technologies Used

| Technology     | Purpose               |
| -------------- | --------------------- |
| FastAPI        | Web framework         |
| SQLAlchemy     | ORM and Database      |
| SQLite         | Database storage      |
| Groq Llama 3.3 | LLM for NL processing |
| Pydantic       | Data validation       |
| Uvicorn        | ASGI server           |

---

## 📊 Data Sources

### QuickBooks (data_set_1.json)

- Period: Jan 2020 - Aug 2025
- Records: 68 monthly periods
- Type: Profit and Loss Report

### Rootfi (data_set_2.json)

- Period: Aug 2022 - Jul 2025
- Records: 36 monthly periods
- Type: Profit and Loss Report

---

## 🔒 Security Features

- SQL Injection Protection: Only SELECT queries allowed
- Dangerous Keywords Blocked: DROP, DELETE, INSERT, UPDATE, etc.
- Input Validation: All inputs validated with Pydantic

---

## 👤 Author

Moamed Elsaka

- GitHub: https://github.com/mohamedelsaka11
- LinkedIn: https://www.linkedin.com/in/mohamed-elsaka-75078021a/
