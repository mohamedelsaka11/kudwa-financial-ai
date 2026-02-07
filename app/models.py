
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class FinancialPeriod(Base):
    
    __tablename__ = "financial_periods"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)  
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False) 
    total_revenue = Column(Float, default=0.0)
    total_cogs = Column(Float, default=0.0) 
    gross_profit = Column(Float, default=0.0)
    total_operating_expenses = Column(Float, default=0.0)
    other_income = Column(Float, default=0.0)
    other_expenses = Column(Float, default=0.0)
    net_income = Column(Float, default=0.0)
    
    account_details = relationship("AccountDetail", back_populates="period")

    def __repr__(self):
        return f"<FinancialPeriod {self.source} {self.year}-{self.month}>"


class AccountDetail(Base):
    
    __tablename__ = "account_details"

    id = Column(Integer, primary_key=True, index=True)
    
    period_id = Column(Integer, ForeignKey("financial_periods.id"), nullable=False)
    period = relationship("FinancialPeriod", back_populates="account_details")
    
    category = Column(String, nullable=False) 
    account_name = Column(String, nullable=False)
    parent_account = Column(String, nullable=True) 
    amount = Column(Float, default=0.0)
    
    account_id = Column(String, nullable=True) 

    def __repr__(self):
        return f"<AccountDetail {self.account_name}: {self.amount}>"