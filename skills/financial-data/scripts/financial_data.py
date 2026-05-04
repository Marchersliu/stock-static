#!/usr/bin/env python3
"""财报数据抓取 - Tushare/巨潮/东方财富"""
import argparse, json, os, requests

def fetch_tushare_financial(stock, year, quarter):
    """从Tushare获取财报"""
    try:
        import tushare as ts
        token = os.environ.get('TUSHARE_TOKEN', '')
        if not token:
            return {'error': 'TUSHARE_TOKEN not set'}
        ts.set_token(token)
        pro = ts.pro_api()
        
        # 利润表
        df = pro.income(ts_code=stock, period=f'{year}{quarter}')
        if df is not None and not df.empty:
            row = df.iloc[0]
            return {
                'revenue': row.get('total_revenue', 'N/A'),
                'net_profit': row.get('n_income', 'N/A'),
                'source': 'Tushare'
            }
        return {'error': 'No data'}
    except Exception as e:
        return {'error': str(e)}

def main():
    parser = argparse.ArgumentParser(description='Financial Data')
    parser.add_argument('--stock', required=True, help='Stock code e.g. 688485.SH')
    parser.add_argument('--year', type=int, default=2025)
    parser.add_argument('--quarter', default='q1')
    parser.add_argument('--batch', help='Batch file with stock codes')
    parser.add_argument('--output', help='Output CSV/JSON')
    args = parser.parse_args()
    
    q_map = {'q1': '0331', 'q2': '0630', 'q3': '0930', 'q4': '1231'}
    q = q_map.get(args.quarter, '0331')
    
    if args.batch:
        with open(args.batch, 'r') as f:
            stocks = [s.strip() for s in f if s.strip()]
        results = {s: fetch_tushare_financial(s, args.year, q) for s in stocks}
    else:
        results = {args.stock: fetch_tushare_financial(args.stock, args.year, q)}
    
    print(json.dumps(results, ensure_ascii=False, indent=2))
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f'[OK] Saved: {args.output}')

if __name__ == '__main__':
    main()
