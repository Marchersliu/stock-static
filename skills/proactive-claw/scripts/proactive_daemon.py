#!/usr/bin/env python3
"""
主动监控守护进程 - 盘中股票异动自动提醒

用法:
    python3 proactive_daemon.py --mode stock        # 只监控股票
    python3 proactive_daemon.py --mode all          # 全功能监控
    python3 proactive_daemon.py --once              # 单次检查

配置:
    ~/.proactive-claw.json
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta

CONFIG_PATH = os.path.expanduser('~/.proactive-claw.json')

def load_config():
    """加载配置"""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return {
        'stock': {'enabled': True, 'alert_threshold': 7, 'moneyflow_threshold': 5000},
        'quiet_hours': {'start': '23:00', 'end': '08:00'}
    }


def is_quiet_hours():
    """判断是否在静默时段"""
    now = datetime.now()
    config = load_config()
    quiet = config.get('quiet_hours', {})
    start = quiet.get('start', '23:00')
    end = quiet.get('end', '08:00')
    
    start_h, start_m = map(int, start.split(':'))
    end_h, end_m = map(int, end.split(':'))
    
    start_time = now.replace(hour=start_h, minute=start_m, second=0)
    end_time = now.replace(hour=end_h, minute=end_m, second=0)
    
    if start_time <= now or now <= end_time:
        return True
    return False


def check_stock_alerts():
    """检查股票异动（调用stock-monitor技能脚本）"""
    stock_dir = '/Users/hf/.kimi_openclaw/workspace/skills/stock-monitor/scripts'
    if not os.path.exists(stock_dir):
        print("[WARN] stock-monitor not found, skipping stock alerts")
        return []
    
    # 导入并运行alert_system
    sys.path.insert(0, stock_dir)
    try:
        from alert_system import init_tushare, check_price_alerts, check_moneyflow_alerts
        pro = init_tushare()
        alerts = []
        alerts.extend(check_price_alerts(pro, threshold=7))
        alerts.extend(check_moneyflow_alerts(pro))
        return alerts
    except Exception as e:
        print(f"[WARN] Stock check failed: {e}")
        return []


def run_once():
    """单次检查"""
    print(f"\n{'='*50}")
    print(f"  主动监控检查 {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*50}")
    
    if is_quiet_hours():
        print("  🌙 静默时段，跳过")
        return
    
    config = load_config()
    
    if config.get('stock', {}).get('enabled', False):
        alerts = check_stock_alerts()
        if alerts:
            print(f"\n🚨 发现 {len(alerts)} 条股票提醒:")
            for alert in alerts[:5]:
                print(f"  • {alert.get('message', '')}")
        else:
            print("  ✅ 股票无异常")
    
    print(f"\n  下次检查: {(datetime.now() + timedelta(minutes=30)).strftime('%H:%M')}")


def run_daemon(interval=1800):
    """守护进程模式"""
    print(f'[Daemon] Proactive-claw started, interval={interval}s')
    while True:
        try:
            run_once()
        except Exception as e:
            print(f'[ERR] Check failed: {e}')
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description='Proactive Monitoring Daemon')
    parser.add_argument('--mode', choices=['stock', 'all'], default='stock',
                        help='Monitoring mode')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--interval', type=int, default=1800,
                        help='Check interval in seconds (default: 1800=30min)')
    
    args = parser.parse_args()
    
    if args.once:
        run_once()
    else:
        run_daemon(args.interval)


if __name__ == '__main__':
    main()
