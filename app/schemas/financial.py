
from pydantic import BaseModel
from datetime import date
from typing import Optional, List



class FinancialPeriodBase(BaseModel):
   
    source: str
    period_start: date
    period_end: date
    year: int
    month: int
    quarter: int
    total_revenue: float = 0.0
    total_cogs: float = 0.0
    gross_profit: float = 0.0
    total_operating_expenses: float = 0.0
    other_income: float = 0.0
    other_expenses: float = 0.0
    net_income: float = 0.0

class FinancialPeriodResponse(FinancialPeriodBase):
    
    id: int

    class Config:
        from_attributes = True

class AccountDetailBase(BaseModel):
    
    category: str
    account_name: str
    parent_account: Optional[str] = None
    amount: float = 0.0
    account_id: Optional[str] = None

class AccountDetailResponse(AccountDetailBase):
    
    id: int
    period_id: int

    class Config:
        from_attributes = True

class NaturalLanguageQuery(BaseModel):

    question: str

class QueryResponse(BaseModel):
   
    question: str
    answer: str
    sql_query: Optional[str] = None
    data: Optional[List[dict]] = None
    confidence: Optional[float] = None

class FinancialSummary(BaseModel):

    total_revenue: float
    total_expenses: float
    net_income: float
    period_count: int
    source: Optional[str] = None