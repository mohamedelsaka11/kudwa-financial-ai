
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.database import get_db
from app.models import FinancialPeriod, AccountDetail
from app.schemas.financial import (
    FinancialPeriodResponse,
    FinancialSummary,
    NaturalLanguageQuery,
    QueryResponse
)
from app.services.ai_service import AIService


ai_service = AIService()
router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "healthy", "message": "Kudwa Financial AI is running!"}


@router.get("/periods", response_model=List[FinancialPeriodResponse])
def get_all_periods(
    source: Optional[str] = Query(None, description="Filter by source: quickbooks or rootfi"),
    year: Optional[int] = Query(None, description="Filter by year"),
    quarter: Optional[int] = Query(None, description="Filter by quarter (1-4)"),
    db: Session = Depends(get_db)
):
    query = db.query(FinancialPeriod)
    
    if source:
        query = query.filter(FinancialPeriod.source == source)
    if year:
        query = query.filter(FinancialPeriod.year == year)
    if quarter:
        query = query.filter(FinancialPeriod.quarter == quarter)
    
    return query.order_by(FinancialPeriod.year, FinancialPeriod.month).all()


@router.get("/periods/{period_id}", response_model=FinancialPeriodResponse)
def get_period(period_id: int, db: Session = Depends(get_db)):
    
    period = db.query(FinancialPeriod).filter(FinancialPeriod.id == period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")
    return period


@router.get("/summary", response_model=FinancialSummary)
def get_financial_summary(
    source: Optional[str] = Query(None, description="Filter by source"),
    year: Optional[int] = Query(None, description="Filter by year"),
    db: Session = Depends(get_db)
):
    query = db.query(FinancialPeriod)
    
    if source:
        query = query.filter(FinancialPeriod.source == source)
    if year:
        query = query.filter(FinancialPeriod.year == year)
    
    periods = query.all()
    
    if not periods:
        raise HTTPException(status_code=404, detail="No data found")
    
    total_revenue = sum(p.total_revenue for p in periods)
    total_expenses = sum(p.total_operating_expenses + p.total_cogs for p in periods)
    net_income = sum(p.net_income for p in periods)
    
    return FinancialSummary(
        total_revenue=total_revenue,
        total_expenses=total_expenses,
        net_income=net_income,
        period_count=len(periods),
        source=source
    )


@router.get("/quarterly/{year}")
def get_quarterly_analysis(year: int, db: Session = Depends(get_db)):
    
    periods = db.query(FinancialPeriod).filter(
        FinancialPeriod.year == year
    ).all()
    
    if not periods:
        raise HTTPException(status_code=404, detail=f"No data found for year {year}")
    
    quarters = {}
    for q in [1, 2, 3, 4]:
        q_periods = [p for p in periods if p.quarter == q]
        if q_periods:
            quarters[f"Q{q}"] = {
                "revenue": sum(p.total_revenue for p in q_periods),
                "expenses": sum(p.total_operating_expenses for p in q_periods),
                "gross_profit": sum(p.gross_profit for p in q_periods),
                "net_income": sum(p.net_income for p in q_periods),
                "months": len(q_periods)
            }
    
    return {
        "year": year,
        "quarters": quarters,
        "total_periods": len(periods)
    }


@router.get("/trends/revenue")
def get_revenue_trends(
    year: Optional[int] = Query(None),
    source: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(FinancialPeriod)
    
    if year:
        query = query.filter(FinancialPeriod.year == year)
    if source:
        query = query.filter(FinancialPeriod.source == source)
    
    periods = query.order_by(FinancialPeriod.year, FinancialPeriod.month).all()
    
    return {
        "trends": [
            {
                "year": p.year,
                "month": p.month,
                "revenue": p.total_revenue,
                "source": p.source
            }
            for p in periods
        ],
        "total_periods": len(periods)
    }


@router.get("/expenses/breakdown")
def get_expense_breakdown(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(AccountDetail).filter(AccountDetail.category == "expense")
    
    if year or month:
        period_query = db.query(FinancialPeriod.id)
        if year:
            period_query = period_query.filter(FinancialPeriod.year == year)
        if month:
            period_query = period_query.filter(FinancialPeriod.month == month)
        period_ids = [p[0] for p in period_query.all()]
        query = query.filter(AccountDetail.period_id.in_(period_ids))
    
    expenses = query.all()
    
    breakdown = {}
    for exp in expenses:
        name = exp.account_name
        if name not in breakdown:
            breakdown[name] = 0
        breakdown[name] += exp.amount
    
    sorted_breakdown = dict(sorted(breakdown.items(), key=lambda x: x[1], reverse=True))
    
    return {
        "breakdown": sorted_breakdown,
        "total": sum(breakdown.values()),
        "categories_count": len(breakdown)
    }
    

@router.post("/ai/query", response_model=QueryResponse)
def ai_query(query: NaturalLanguageQuery):
    
    result = ai_service.query(query.question)
    
    return QueryResponse(
        question=result["question"],
        answer=result.get("answer", "Could not generate answer"),
        sql_query=result.get("sql_query"),
        data=result.get("data"),
        confidence=1.0 if result["success"] else 0.0
    )


@router.get("/ai/sample-questions")
def get_sample_questions():
    
    return {
        "sample_questions": ai_service.get_sample_questions()
    }
    
    
@router.post("/ai/clear-history")
def clear_conversation_history():
   
    ai_service.clear_history()
    return {
        "success": True,
        "message": "Conversation history cleared. You can start a new conversation."
    }


@router.get("/ai/history")
def get_conversation_history():
   
    return {
        "history": ai_service.conversation_history,
        "total_messages": len(ai_service.conversation_history)
    }
    
@router.get("/ai/compare")
def compare_periods(
    period1: str = Query(..., description="First period (e.g., Q1 or 2023)"),
    period2: str = Query(..., description="Second period (e.g., Q2 or 2024)"),
    year: Optional[int] = Query(None, description="Year for quarterly comparison")
):
    result = ai_service.comparative_analysis(period1, period2, year)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Comparison failed"))
    
    return result