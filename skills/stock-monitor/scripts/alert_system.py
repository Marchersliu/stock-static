#!/usr/bin/env python3
"""
异常提醒主脚本 - 涨跌停/±7%/大单异动自动监控

用法:
    python3 alert_system.py --watch --threshold 7
    python3 alert_system.py --check --codes 688485.SH,600989.SH
    python3 alert_system.py --alert-all  # 检查所有监控条件

监控条件:
    涨跌幅 >= ±7%       → 异动提醒
    触及目标价          → 建仓/止盈提醒
    触及止损线          → 止损提醒
    主力净流入 ±5000万+ → 资金异动
    原材料价格 ±5%+     → 成本变动提醒

提醒方式:
    console     - 终端彩色输出（默认）
    log         - 写入 /tmp/stock_alerts.log
    notify      - Mac通知（需配置）
"""
import argparse
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tushare as ts
import json
from datetime import datetime
from utils import (
    ALL_STOCK_CODES, HOLDINGS, STOCK_KEYWORDS, COMMODITY_CONFIG,
    get_tushare_token, get_main_contract, format_change, print_section
)
from fetch_data import fetch_price, fetch_moneyflow, fetch_commodity_prices


def init_tushare():
    token = get_tushare_token()
    if not token:
        print("[ERR] Tushare Token not found")
        sys.exit(1)
    ts.set_token(token)
    return ts.pro_api()


ALERT_LOG = '/tmp/stock_alerts.log'


def log_alert(message):
    """记录提醒日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {message}\n"
    with open(ALERT_LOG, 'a', encoding='utf-8') as f:
        f.write(line)
    print(f"🚨 {message}")


def check_price_alerts(pro, codes=None, threshold=7):
    """检查涨跌幅异常"""
    if not codes:
        codes = HOLDINGS
    
    alerts = []
    trade_date = datetime.now().strftime('%Y%m%d')
    price_data = fetch_price(pro, codes, trade_date)
    
    for code in codes:
        p = price_data.get(code, {})
        if not p:
            continue
        
        pct = p.get('pct_chg', 0)
        name = STOCK_KEYWORDS.get(code, {}).get('name', code)
        close = p.get('close', 0)
        
        # ±7% 异动
        if abs(pct) >= threshold:
            direction = "📈 大涨" if pct > 0 else "📉 大跌"
            msg = f"{direction} {name}({code}) {close} ({format_change(pct)})"
            log_alert(msg)
            alerts.append({'type': 'price_move', 'code': code, 'message': msg})
        
        # 涨停/跌停
        if pct >= 9.5:
            msg = f"🔴 涨停 {name}({code}) {close}"
            log_alert(msg)
            alerts.append({'type': 'limit_up', 'code': code, 'message': msg})
        elif pct <= -9.5:
            msg = f"🟢 跌停 {name}({code}) {close}"
            log_alert(msg)
            alerts.append({'type': 'limit_down', 'code': code, 'message': msg})
        
        # 目标价检查
        target_str = STOCK_KEYWORDS.get(code, {}).get('target')
        if target_str:
            targets = [float(t) for t in target_str.replace('/', '-').split('-')]
            for target in targets:
                if close >= target * 0.98 and close <= target * 1.02:
                    msg = f"🎯 触及目标价 {name}({code}) 目标{target} 当前{close}"
                    log_alert(msg)
                    alerts.append({'type': 'target', 'code': code, 'message': msg})
        
        # 止损检查
        stop = STOCK_KEYWORDS.get(code, {}).get('stop')
        if stop and close <= float(stop):
            msg = f"⚠️ 跌破止损线 {name}({code}) 止损{stop} 当前{close}"
            log_alert(msg)
            alerts.append({'type': 'stop_loss', 'code': code, 'message': msg})
    
    return alerts


def check_moneyflow_alerts(pro, codes=None, threshold=5000):
    """检查资金流向异常"""
    if not codes:
        codes = HOLDINGS
    
    alerts = []
    trade_date = datetime.now().strftime('%Y%m%d')
    mf_data = fetch_moneyflow(pro, codes, trade_date)
    
    for code in codes:
        mf = mf_data.get(code, {})
        if not mf:
            continue
        
        main_net = mf.get('main_net', 0)
        name = STOCK_KEYWORDS.get(code, {}).get('name', code)
        
        if abs(main_net) >= threshold * 10000:  # 万→元
            direction = "🟢 主力大幅流入" if main_net > 0 else "🔴 主力大幅流出"
            msg = f"{direction} {name}({code}) {format_change(main_net/10000, '万')}"
            log_alert(msg)
            alerts.append({'type': 'moneyflow', 'code': code, 'message': msg})
    
    return alerts


def check_commodity_alerts(pro, threshold=5):
    """检查原材料价格异常"""
    alerts = []
    commodities = fetch_commodity_prices(pro)
    
    for c in commodities:
        change = c.get('change') or 0
        if abs(change) >= threshold:
            direction = "📈 大涨" if change > 0 else "📉 大跌"
            msg = f"{direction} {c.get('name')} {c.get('price')} {c.get('unit')} ({format_change(change)})"
            log_alert(msg)
            alerts.append({'type': 'commodity', 'commodity': c.get('name'), 'message': msg})
    
    return alerts


def watch_mode(pro, interval=300, threshold=7):
    """持续监控模式（每5分钟检查一次）"""
    import time
    
    print(f"[Alert] Watch mode started, interval={interval}s, threshold=±{threshold}%")
    print(f"[Alert] Log file: {ALERT_LOG}")
    
    try:
        while True:
            print(f"\n{'='*50}")
            print(f"  检查时间: {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*50}")
            
            all_alerts = []
            all_alerts.extend(check_price_alerts(pro, threshold=threshold))
            all_alerts.extend(check_moneyflow_alerts(pro))
            all_alerts.extend(check_commodity_alerts(pro))
            
            if not all_alerts:
                print("  ✅ 无异常")
            else:
                print(f"  🚨 共{len(all_alerts)}条提醒")
            
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[Alert] Watch mode stopped")


def main():
    parser = argparse.ArgumentParser(description='Stock Alert System')
    parser.add_argument('--watch', action='store_true', help='Watch mode (continuous monitoring)')
    parser.add_argument('--check', action='store_true', help='Single check')
    parser.add_argument('--alert-all', action='store_true', help='Check all alert conditions')
    parser.add_argument('--codes', help='Comma-separated stock codes to check')
    parser.add_argument('--threshold', type=float, default=7, help='Price movement threshold (%)')
    parser.add_argument('--interval', type=int, default=300, help='Watch interval (seconds)')
    parser.add_argument('--output', help='Output JSON file')
    
    args = parser.parse_args()
    
    pro = init_tushare()
    codes = args.codes.split(',') if args.codes else None
    
    if args.watch:
        watch_mode(pro, args.interval, args.threshold)
    elif args.check or args.alert_all:
        print_section("异常检查")
        all_alerts = []
        all_alerts.extend(check_price_alerts(pro, codes, args.threshold))
        all_alerts.extend(check_moneyflow_alerts(pro, codes))
        all_alerts.extend(check_commodity_alerts(pro, args.threshold))
        
        if not all_alerts:
            print("\n✅ 所有监控条件正常，无异常")
        else:
            print(f"\n🚨 共发现 {len(all_alerts)} 条提醒")
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(all_alerts, f, ensure_ascii=False, indent=2)
            print(f"[OK] Saved to {args.output}")
    else:
        print("[ERR] Specify --watch, --check, or --alert-all")
        sys.exit(1)


if __name__ == '__main__':
    main()
