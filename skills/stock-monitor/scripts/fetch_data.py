#!/usr/bin/env python3
"""
数据抓取主脚本 - 从Tushare Pro和腾讯接口获取A股实时数据

用法:
    python3 fetch_data.py --type all --output /tmp/stock_data.json
    python3 fetch_data.py --type price --codes 688485.SH,600989.SH
    python3 fetch_data.py --type commodity --output /tmp/commodities.json
    python3 fetch_data.py --type sector --output /tmp/sectors.json

类型:
    all         - 抓取所有类型数据
    price       - 个股行情（开/高/低/收/量/额）
    moneyflow   - 资金流向（主力净流入）
    sector      - 板块资金流向聚合
    commodity   - 20种原料期货价格
    index       - 指数行情（上证/深成指/创业板/恒指）
"""
import argparse
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tushare as ts
import requests
import json
from datetime import datetime
from utils import (
    ALL_STOCK_CODES, HOLDINGS, WATCHLIST, STOCK_KEYWORDS,
    COMMODITY_CONFIG, get_tushare_token, get_main_contract,
    is_trading_time, format_change, save_json
)


def init_tushare():
    """初始化 Tushare Pro"""
    token = get_tushare_token()
    if not token:
        print("[ERR] Tushare Token not found. Set TUSHARE_TOKEN env var or create .env file")
        sys.exit(1)
    ts.set_token(token)
    return ts.pro_api()


def fetch_price(pro, codes=None, trade_date=None):
    """抓取个股行情"""
    if not trade_date:
        trade_date = datetime.now().strftime('%Y%m%d')
    if not codes:
        codes = ALL_STOCK_CODES
    
    results = {}
    for code in codes:
        try:
            df = pro.daily(ts_code=code, trade_date=trade_date)
            if df is not None and not df.empty:
                row = df.iloc[0]
                results[code] = {
                    'name': STOCK_KEYWORDS.get(code, {}).get('name', code),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'pre_close': float(row['pre_close']),
                    'change': float(row['change']),
                    'pct_chg': float(row['pct_chg']),
                    'vol': float(row['vol']),
                    'amount': float(row['amount']),
                    'trade_date': trade_date
                }
        except Exception as e:
            print(f"[WARN] {code} price fetch failed: {e}")
    return results


def fetch_moneyflow(pro, codes=None, trade_date=None):
    """抓取资金流向"""
    if not trade_date:
        trade_date = datetime.now().strftime('%Y%m%d')
    if not codes:
        codes = ALL_STOCK_CODES
    
    results = {}
    for code in codes:
        try:
            df = pro.moneyflow(ts_code=code, trade_date=trade_date)
            if df is not None and not df.empty:
                row = df.iloc[0]
                results[code] = {
                    'name': STOCK_KEYWORDS.get(code, {}).get('name', code),
                    'main_net': float(row.get('net_mf_amount', 0)),  # 主力净流入
                    'retail_net': float(row.get('net_mf_amount', 0)) - float(row.get('buy_elg_amount', 0)),
                    'trade_date': trade_date
                }
        except Exception as e:
            print(f"[WARN] {code} moneyflow fetch failed: {e}")
    return results


def fetch_sector_moneyflow(pro):
    """抓取板块资金流向（按行业聚合）"""
    trade_date = datetime.now().strftime('%Y%m%d')
    all_sectors = {}
    
    for code, info in STOCK_KEYWORDS.items():
        sector = info.get('sector', '其他')
        try:
            df = pro.moneyflow(ts_code=code, trade_date=trade_date)
            if df is not None and not df.empty:
                row = df.iloc[0]
                main_net = float(row.get('net_mf_amount', 0))
                if sector not in all_sectors:
                    all_sectors[sector] = {'total_net': 0, 'stocks': [], 'up': 0, 'down': 0}
                all_sectors[sector]['total_net'] += main_net
                all_sectors[sector]['stocks'].append(info['name'])
        except Exception as e:
            pass
    
    # 格式化输出
    sectors = []
    for sector, data in sorted(all_sectors.items(), key=lambda x: x[1]['total_net'], reverse=True):
        sectors.append({
            'name': sector,
            'total_net': round(data['total_net'], 2),
            'stocks': data['stocks']
        })
    return {'sectors': sectors, 'timestamp': datetime.now().isoformat()}


def fetch_commodity_prices(pro):
    """抓取原料期货价格（20种）"""
    results = []
    today = datetime.now().strftime('%Y%m%d')
    
    for cfg in COMMODITY_CONFIG:
        try:
            contract = get_main_contract(cfg['symbol'], cfg['exchange'])
            df = pro.fut_daily(ts_code=contract, trade_date=today)
            if df is not None and not df.empty:
                row = df.iloc[0]
                close = float(row['close']) if 'close' in row else None
                pre_close = float(row['pre_close']) if 'pre_close' in row else close
                change = ((close - pre_close) / pre_close * 100) if close and pre_close else None
                
                results.append({
                    'name': cfg['name'],
                    'symbol': cfg['symbol'],
                    'exchange': cfg['exchange'],
                    'unit': cfg['unit'],
                    'price': close,
                    'pre_close': pre_close,
                    'change': round(change, 2) if change else None,
                    'contract': contract,
                    'date': today
                })
        except Exception as e:
            print(f"[WARN] {cfg['name']} fetch failed: {e}")
    
    return results


def fetch_index_data():
    """抓取指数行情（含恒指）"""
    indices = {}
    today = datetime.now().strftime('%Y%m%d')
    
    # A股指数
    try:
        pro = init_tushare()
        for idx_code in ['000001.SH', '399001.SZ', '399006.SZ']:
            df = pro.index_daily(ts_code=idx_code, trade_date=today)
            if df is not None and not df.empty:
                row = df.iloc[0]
                name_map = {'000001.SH': '上证指数', '399001.SZ': '深成指', '399006.SZ': '创业板指'}
                indices[name_map[idx_code]] = {
                    'close': float(row['close']),
                    'pct': float(row['pct_chg']),
                    'change': float(row['change'])
                }
    except Exception as e:
        print(f"[WARN] A股指数 fetch failed: {e}")
    
    # 恒指（腾讯接口）
    try:
        resp = requests.get('https://qt.gtimg.cn/q=hkHSI', timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        text = resp.text
        m = __import__('re').search(r'v_hkHSI="([^"]+)"', text)
        if m:
            parts = m.group(1).split('~')
            if len(parts) >= 35:
                indices['恒生指数'] = {
                    'close': float(parts[3]),
                    'change': float(parts[31]),
                    'pct': float(parts[32]),
                    'date_time': parts[30]
                }
    except Exception as e:
        print(f"[WARN] HSI fetch failed: {e}")
    
    return indices


def fetch_all(pro):
    """抓取所有类型数据"""
    print("[Fetch] Starting full data fetch...")
    data = {
        'timestamp': datetime.now().isoformat(),
        'trading': is_trading_time()
    }
    
    print("  → Price...")
    data['price'] = fetch_price(pro)
    
    print("  → Moneyflow...")
    data['moneyflow'] = fetch_moneyflow(pro)
    
    print("  → Sector...")
    data['sector'] = fetch_sector_moneyflow(pro)
    
    print("  → Commodity...")
    data['commodity'] = fetch_commodity_prices(pro)
    
    print("  → Index...")
    data['index'] = fetch_index_data()
    
    print("[Fetch] All done!")
    return data


def main():
    parser = argparse.ArgumentParser(description='Stock Data Fetcher')
    parser.add_argument('--type', choices=['all', 'price', 'moneyflow', 'sector', 'commodity', 'index'],
                        default='all', help='Data type to fetch')
    parser.add_argument('--codes', help='Comma-separated stock codes (for price/moneyflow)')
    parser.add_argument('--output', '-o', help='Output JSON file path')
    parser.add_argument('--date', help='Trade date (YYYYMMDD), default today')
    
    args = parser.parse_args()
    
    # 初始化
    pro = init_tushare()
    trade_date = args.date or datetime.now().strftime('%Y%m%d')
    codes = args.codes.split(',') if args.codes else None
    
    # 执行抓取
    if args.type == 'all':
        data = fetch_all(pro)
    elif args.type == 'price':
        data = fetch_price(pro, codes, trade_date)
    elif args.type == 'moneyflow':
        data = fetch_moneyflow(pro, codes, trade_date)
    elif args.type == 'sector':
        data = fetch_sector_moneyflow(pro)
    elif args.type == 'commodity':
        data = fetch_commodity_prices(pro)
    elif args.type == 'index':
        data = fetch_index_data()
    
    # 输出
    if args.output:
        save_json(data, args.output)
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
