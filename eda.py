
import json
from pathlib import Path
from collections import defaultdict


def load_json(file_path):
    
    print(f"\n {'='*60}")
    print(f"Loading... {file_path}")
    print('='*60)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("Download completed successfully")
        return data
    except Exception as e:
        print(f"Loading error:{e}")
        return None


def analyze_quickbooks(data):
    
    print("\n" + "="*60)
    print("Analysis of the first file (QuickBooks P&L)")
    print("="*60)
    
    
    header = data.get('data', {}).get('Header', {})
    print(f"\n Report information:")
    print(f"Report title: {header.get('ReportName', 'N/A')}")
    print(f"Period: {header.get('StartPeriod', 'N/A')} → {header.get('EndPeriod', 'N/A')}")
    print(f"Currency: {header.get('Currency', 'N/A')}")
    print(f"Assembly: {header.get('SummarizeColumnsBy', 'N/A')}")

    columns = data.get('data', {}).get('Columns', {}).get('Column', [])
    print(f"\n Number of columns (periods): {len(columns)}")
    
    if columns:
        first_col = columns[1] if len(columns) > 1 else columns[0]  
        last_col = columns[-1] if columns else None
        print(f"First period: {first_col.get('ColTitle', 'N/A')}")
        print(f"Last period: {last_col.get('ColTitle', 'N/A')}")
    
    rows = data.get('data', {}).get('Rows', {}).get('Row', [])
    print(f"\n Number of main sections: {len(rows)}")
    
    sections = []
    all_accounts = []
    summaries = []
    
    def extract_accounts(row_list, depth=0):
        for row in row_list:
            if 'Header' in row:
                col_data = row['Header'].get('ColData', [])
                if col_data and col_data[0].get('value'):
                    account_name = col_data[0]['value']
                    account_id = col_data[0].get('id', 'N/A')
                    all_accounts.append({
                        'name': account_name,
                        'id': account_id,
                        'depth': depth
                    })
            
            if 'Summary' in row:
                col_data = row['Summary'].get('ColData', [])
                if col_data and col_data[0].get('value'):
                    summary_name = col_data[0]['value']
                    total_value = col_data[-1].get('value', '0') if col_data else '0'
                    summaries.append({
                        'name': summary_name,
                        'total': total_value
                    })
            
            if 'ColData' in row:
                col_data = row['ColData']
                if col_data and col_data[0].get('value'):
                    account_name = col_data[0]['value']
                    account_id = col_data[0].get('id', 'N/A')
                    all_accounts.append({
                        'name': account_name,
                        'id': account_id,
                        'depth': depth
                    })
            
            if 'Rows' in row:
                sub_rows = row['Rows'].get('Row', [])
                extract_accounts(sub_rows, depth + 1)
    
    extract_accounts(rows)
    
    print(f"\n Main sections")
    main_sections = [acc for acc in all_accounts if acc['depth'] == 0]
    for section in main_sections[:10]:  
        print(f"{section['name']}")
    if len(main_sections) > 10:
        print(f"{len(main_sections) - 10}")
    
    print(f"\n (Summaries):")
    for summary in summaries[:10]:
        print(f"{summary['name']}: ${summary['total']}")
    if len(summaries) > 10:
        print(f"{len(summaries) - 10}")
    
    print(f"\n Statistics:")
    print(f"Total accounts detected: {len(all_accounts)}")
    print(f"Total Summaries:{len(summaries)}")
    
    return {
        'columns_count': len(columns),
        'accounts_count': len(all_accounts),
        'summaries': summaries,
        'accounts': all_accounts
    }


def analyze_rootfi(data):
   
    print("\n" + "="*60)
    print("Analysis of the second file")
    print("="*60)
    
    records = data.get('data', [])
    print(f"\n Number of records (periods): {len(records)}")
    
    if not records:
        print("No data!")
        return None
    
    periods = []
    for record in records:
        period_start = record.get('period_start', 'N/A')
        period_end = record.get('period_end', 'N/A')
        periods.append(f"{period_start} → {period_end}")
    
    print(f"\n Time periods:")
    print(f"First period: {periods[0] if periods else 'N/A'}")
    print(f"Last period:{periods[-1] if periods else 'N/A'}")
    
    sample = records[0]
    
    print(f"\n Fields found in each record:")
    main_fields = ['revenue', 'cost_of_goods_sold', 'gross_profit', 
                   'operating_expenses', 'net_income', 'other_income', 
                   'other_expenses', 'income_before_tax', 'income_tax_expense']
    
    for field in main_fields:
        if field in sample:
            value = sample[field]
            if isinstance(value, list):
                print(f"{field} It contains{len(value)} elements)")
            else:
                print(f"{field}: {value}")
        else:
            print(f"{field} unavailable")
    
    
    print(f"\n Revenue Analysis(Revenue):")
    revenue_categories = set()
    
    def extract_names(items, prefix=""):
        for item in items:
            name = item.get('name', 'Unknown')
            value = item.get('value', 0)
            revenue_categories.add(name)
            if 'line_items' in item and item['line_items']:
                extract_names(item['line_items'], prefix + "  ")
    
    for record in records[:5]:  
        revenue = record.get('revenue', [])
        extract_names(revenue)
    
    print(f"Number of revenue categories: {len(revenue_categories)}")
    for cat in list(revenue_categories)[:5]:
        print(f"     - {cat}")
    
    print(f"\n Expense Analysis(Operating Expenses):")
    expense_categories = set()
    
    for record in records[:5]:
        expenses = record.get('operating_expenses', [])
        extract_names(expenses)
        for exp in expenses:
            expense_categories.add(exp.get('name', 'Unknown'))
            for item in exp.get('line_items', []):
                expense_categories.add(item.get('name', 'Unknown'))
    
    print(f"Number of expense categories: {len(expense_categories)}")
    for cat in list(expense_categories)[:10]:
        print(f"     - {cat}")
    if len(expense_categories) > 10:
        print(f"{len(expense_categories) - 10}")
    
    print(f"\n Summary from the first record):")
    print(f"Gross Profit: ${sample.get('gross_profit', 'N/A'):,}" if isinstance(sample.get('gross_profit'), (int, float)) else f"Gross Profit: {sample.get('gross_profit', 'N/A')}")
    
    if 'net_income' in sample:
        print(f"Net Income: ${sample.get('net_income', 'N/A'):,}" if isinstance(sample.get('net_income'), (int, float)) else f"Net Income: {sample.get('net_income', 'N/A')}")
    
    return {
        'periods_count': len(records),
        'revenue_categories': len(revenue_categories),
        'expense_categories': len(expense_categories),
        'periods': periods
    }


def compare_datasets(qb_analysis, rootfi_analysis):
    
    print("\n" + "="*60)
    print("Compare between two file")
    print("="*60)
    
    print(f"""
    
    {qb_analysis['columns_count']:^15} │ {rootfi_analysis['periods_count']:^15} │
    {qb_analysis['accounts_count']:^15} │ {rootfi_analysis['revenue_categories'] + rootfi_analysis['expense_categories']:^15} │
    
    """)


def main():

    print("Kudwa Financial AI - EDA Script")

    data_dir = Path("data")
    file1 = data_dir / "data_set_1.json"
    file2 = data_dir / "data_set_2.json"
    
    qb_data = load_json(file1)
    qb_analysis = None
    if qb_data:
        qb_analysis = analyze_quickbooks(qb_data)
    
    rootfi_data = load_json(file2)
    rootfi_analysis = None
    if rootfi_data:
        rootfi_analysis = analyze_rootfi(rootfi_data)
    
    if qb_analysis and rootfi_analysis:
        compare_datasets(qb_analysis, rootfi_analysis)
    
    print("\n" + "="*60)
    print("The analysis is complete!")
    print("="*60)


if __name__ == "__main__":
    main()