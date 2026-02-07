
import json
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models import FinancialPeriod, AccountDetail
from app.database import SessionLocal, init_db


class DataProcessor:
  
    def __init__(self):
        self.quickbooks_data = None
        self.rootfi_data = None
    
    def load_json(self, file_path: str) -> Optional[Dict]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Downloaded: {file_path}")
            return data
        except Exception as e:
            print(f"Loading error{file_path}: {e}")
            return None
    
    def load_all_data(self, data_dir: str = "data"):
        data_path = Path(data_dir)
        
        self.quickbooks_data = self.load_json(data_path / "data_set_1.json")
        self.rootfi_data = self.load_json(data_path / "data_set_2.json")
        
        return self.quickbooks_data is not None and self.rootfi_data is not None
    
    def get_quarter(self, month: int) -> int:
    
        return (month - 1) // 3 + 1
    
    def parse_month_year(self, col_title: str) -> Optional[tuple]:
       
        try:
            month_map = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
                'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
                'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }
            parts = col_title.split()
            if len(parts) == 2:
                month = month_map.get(parts[0])
                year = int(parts[1])
                if month:
                    return (month, year)
        except:
            pass
        return None
    
    def safe_float(self, value: Any) -> float:
    
        if value is None or value == "" or value == " ":
            return 0.0
        try:
            return float(str(value).replace(",", ""))
        except:
            return 0.0
    
    def process_quickbooks(self, db: Session) -> int:
        
        if not self.quickbooks_data:
            print("No QuickBooks data")
            return 0
        
        print("\n QuickBooks processing...")
        
        data = self.quickbooks_data.get('data', {})
        columns = data.get('Columns', {}).get('Column', [])
        rows = data.get('Rows', {}).get('Row', [])
        
        months_info = []
        for i, col in enumerate(columns):
            title = col.get('ColTitle', '')
            parsed = self.parse_month_year(title)
            if parsed:
                month, year = parsed
                months_info.append({
                    'index': i,
                    'month': month,
                    'year': year,
                    'title': title
                })
        
        print(f"Number of months: {len(months_info)}")
        
        sections_data = self._extract_quickbooks_sections(rows)
        
        records_created = 0
        
        for month_info in months_info:
            idx = month_info['index']
            month = month_info['month']
            year = month_info['year']
            
            total_income = self._get_section_value(sections_data, 'Total Income', idx)
            total_cogs = self._get_section_value(sections_data, 'Total Cost of Goods Sold', idx)
            gross_profit = self._get_section_value(sections_data, 'Gross Profit', idx)
            total_expenses = self._get_section_value(sections_data, 'Total Expenses', idx)
            net_income = self._get_section_value(sections_data, 'Net Income', idx)
            other_income = self._get_section_value(sections_data, 'Total Other Income', idx)
            other_expenses = self._get_section_value(sections_data, 'Total Other Expenses', idx)
            
            if net_income == 0 and (gross_profit != 0 or total_expenses != 0):
                net_income = gross_profit - total_expenses + other_income - other_expenses
            
            period = FinancialPeriod(
                source="quickbooks",
                period_start=date(year, month, 1),
                period_end=date(year, month, 28),  
                year=year,
                month=month,
                quarter=self.get_quarter(month),
                total_revenue=total_income,
                total_cogs=total_cogs,
                gross_profit=gross_profit,
                total_operating_expenses=total_expenses,
                other_income=other_income,
                other_expenses=other_expenses,
                net_income=net_income
            )
            
            db.add(period)
            records_created += 1
        
        db.commit()
        print(f" Created {records_created}")
        return records_created
    
    def _extract_quickbooks_sections(self, rows: List) -> Dict:
    
        sections = {}
        
        def extract_summaries(row_list):
            for row in row_list:
                if 'Summary' in row:
                    col_data = row['Summary'].get('ColData', [])
                    if col_data:
                        name = col_data[0].get('value', '')
                        values = [self.safe_float(c.get('value', 0)) for c in col_data[1:]]
                        sections[name] = values
                
                if 'Rows' in row:
                    extract_summaries(row['Rows'].get('Row', []))
                
                if row.get('type') == 'Section' and 'Summary' in row:
                    col_data = row['Summary'].get('ColData', [])
                    if col_data:
                        name = col_data[0].get('value', '')
                        values = [self.safe_float(c.get('value', 0)) for c in col_data[1:]]
                        sections[name] = values
        
        extract_summaries(rows)
        
        for row in rows:
            if 'Summary' in row:
                col_data = row['Summary'].get('ColData', [])
                if col_data:
                    name = col_data[0].get('value', '')
                    values = [self.safe_float(c.get('value', 0)) for c in col_data[1:]]
                    sections[name] = values
            
            if 'ColData' in row and row.get('type') != 'Section':
                col_data = row['ColData']
                if col_data:
                    name = col_data[0].get('value', '')
                    if 'Gross Profit' in name or 'Net Income' in name or 'Net Operating' in name:
                        values = [self.safe_float(c.get('value', 0)) for c in col_data[1:]]
                        sections[name] = values
        
        return sections
    
    def _get_section_value(self, sections: Dict, name: str, index: int) -> float:
        
        for key, values in sections.items():
            if name in key:
                if index < len(values):
                    return values[index]
        return 0.0
    
    def process_rootfi(self, db: Session) -> int:
       
        if not self.rootfi_data:
            print("No Rootfi data")
            return 0
        
        print("\n Rootfi processing in progress...")
        
        records = self.rootfi_data.get('data', [])
        print(f" Number of periods:{len(records)}")
        
        records_created = 0
        
        for record in records:
            period_start_str = record.get('period_start', '')
            period_end_str = record.get('period_end', '')
            
            try:
                period_start = datetime.strptime(period_start_str, '%Y-%m-%d').date()
                period_end = datetime.strptime(period_end_str, '%Y-%m-%d').date()
            except:
                continue
            
            year = period_start.year
            month = period_start.month
            
            total_revenue = self._extract_rootfi_total(record.get('revenue', []))
            
            total_cogs = self._extract_rootfi_total(record.get('cost_of_goods_sold', []))
            
            gross_profit = record.get('gross_profit', 0) or (total_revenue - total_cogs)
            
            total_expenses = self._extract_rootfi_total(record.get('operating_expenses', []))
            
            other_income = self._extract_rootfi_total(record.get('other_income', []))
            other_expenses = self._extract_rootfi_total(record.get('other_expenses', []))
            
            net_income = record.get('net_income')
            if net_income is None:
                net_income = gross_profit - total_expenses + other_income - other_expenses
            
            period = FinancialPeriod(
                source="rootfi",
                period_start=period_start,
                period_end=period_end,
                year=year,
                month=month,
                quarter=self.get_quarter(month),
                total_revenue=self.safe_float(total_revenue),
                total_cogs=self.safe_float(total_cogs),
                gross_profit=self.safe_float(gross_profit),
                total_operating_expenses=self.safe_float(total_expenses),
                other_income=self.safe_float(other_income),
                other_expenses=self.safe_float(other_expenses),
                net_income=self.safe_float(net_income)
            )
            
            db.add(period)
            db.flush()  
            records_created += 1
            
            self._add_rootfi_account_details(db, period, record)
        
        db.commit()
        print(f" Created {records_created}")
        return records_created
    
    def _extract_rootfi_total(self, items: List) -> float:
        total = 0.0
        for item in items:
            value = item.get('value', 0)
            total += self.safe_float(value)
        return total
    
    def _add_rootfi_account_details(self, db: Session, period: FinancialPeriod, record: Dict):
        
        for item in record.get('revenue', []):
            self._add_account_recursive(db, period, item, 'income', None)
        
        for item in record.get('cost_of_goods_sold', []):
            self._add_account_recursive(db, period, item, 'cogs', None)
        
        for item in record.get('operating_expenses', []):
            self._add_account_recursive(db, period, item, 'expense', None)
    
    def _add_account_recursive(self, db: Session, period: FinancialPeriod, 
                                item: Dict, category: str, parent: Optional[str]):
        
        name = item.get('name', 'Unknown')
        value = self.safe_float(item.get('value', 0))
        account_id = item.get('account_id')
        
        detail = AccountDetail(
            period_id=period.id,
            category=category,
            account_name=name,
            parent_account=parent,
            amount=value,
            account_id=account_id
        )
        db.add(detail)
        
        for sub_item in item.get('line_items', []):
            self._add_account_recursive(db, period, sub_item, category, name)
    
    
    def process_all(self, data_dir: str = "data") -> Dict:
        
        print("\n" + "="*60)
        print("Starting data processing")
        print("="*60)
        
        if not self.load_all_data(data_dir):
            return {"success": False, "error": "Data loading failed"}
        
        
        init_db()
        
        db = SessionLocal()
        
        try:
            db.query(AccountDetail).delete()
            db.query(FinancialPeriod).delete()
            db.commit()
            print("\n Old data has been deleted")
            
            qb_count = self.process_quickbooks(db)
            
            rootfi_count = self.process_rootfi(db)
            
            print("\n" + "="*60)
            print("Processing complete!")
            print(f" QuickBooks: {qb_count} ")
            print(f" Rootfi: {rootfi_count} ")
            print(f" Sum: {qb_count + rootfi_count} ")
            print("="*60)
            
            return {
                "success": True,
                "quickbooks_records": qb_count,
                "rootfi_records": rootfi_count,
                "total_records": qb_count + rootfi_count
            }
            
        except Exception as e:
            db.rollback()
            print(f"\n Error {e}")
            return {"success": False, "error": str(e)}
        
        finally:
            db.close()



if __name__ == "__main__":
    processor = DataProcessor()
    result = processor.process_all()
    print(f"\n The Result {result}")