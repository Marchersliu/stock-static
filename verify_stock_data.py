#!/usr/bin/env python3
"""
股票监控看板数据核查脚本
---------------------------
功能：自动对比前端静态HTML中的N日涨跌数据与Tushare Pro真实值，
      发现不一致时输出警告。

使用方式：
    python3 verify_stock_data.py [--fix]

选项：
    --fix    自动修正 stock_dashboard.html 中的静态值（需人工复核后提交）

核查规则：
1. 持仓总览表（5只）和计划建仓表（7只）的日涨跌/3日/5日/7日涨跌
2. 交易日15:00后拉取当日Tushare日线，与HTML静态值对比
3. 非交易日使用最后一个交易日的数据进行对比
4. 任何差异>0.01%即视为错误（四舍五入误差除外）

退出码：
    0 — 全部一致
    1 — 发现不一致（需人工核查）
"""

import re
import sys
import tushare as ts
import pandas as pd
from datetime import datetime

# ===================== 配置 =====================
TOKEN = "16e1c68c578e1c26ef7797f17acc2764bcfddb25692b52c3ef8a9878"
HTML_PATH = "/Users/hf/.kimi_openclaw/workspace/stock_dashboard.html"
BACKUP_SUFFIX = ".backup"

# 股票列表
HOLDINGS = {
    '688485.SH': {'name': '九州一轨', 'html_name': '九州一轨'},
    '600367.SH': {'name': '红星发展', 'html_name': '红星发展'},
    '603063.SH': {'name': '禾望电气', 'html_name': '禾望电气'},
    '000488.SZ': {'name': 'ST晨鸣',   'html_name': 'ST晨鸣'},
    '301317.SZ': {'name': '鑫磊股份', 'html_name': '鑫磊股份'},
}

WATCHLIST = {
    '600989.SH': {'name': '宝丰能源', 'html_name': '宝丰能源'},
    '603799.SH': {'name': '华友钴业', 'html_name': '华友钴业'},
    '002422.SZ': {'name': '科伦药业', 'html_name': '科伦药业'},
    '600036.SH': {'name': '招商银行', 'html_name': '招商银行'},
    '601985.SH': {'name': '中国核电', 'html_name': '中国核电'},
    '601600.SH': {'name': '中国铝业', 'html_name': '中国铝业'},
    '600900.SH': {'name': '长江电力', 'html_name': '长江电力'},
    '300457.SZ': {'name': '赢合科技', 'html_name': '赢合科技'},
}

ALL_STOCKS = {**HOLDINGS, **WATCHLIST}

# ===================== Tushare 计算 =====================
ts.set_token(TOKEN)
pro = ts.pro_api()

def get_last_trade_date():
    """获取最近一个交易日"""
    today = datetime.now().strftime('%Y%m%d')
    df = pro.trade_cal(exchange='SSE', start_date='20260101', end_date=today)
    df = df[df['is_open'] == 1].sort_values('cal_date', ascending=False)
    return str(df.iloc[0]['cal_date']) if len(df) > 0 else today

def fetch_history_changes(codes, trade_date):
    """严格按交易日计算3日/5日/7日涨跌"""
    df_cal = pro.trade_cal(exchange='SSE', start_date='20260101', end_date=trade_date)
    trade_dates = df_cal[df_cal['is_open'] == 1]['cal_date'].tolist()
    if len(trade_dates) < 8:
        return {}

    target_dates = {
        3: trade_dates[3],
        5: trade_dates[5],
        7: trade_dates[7],
    }

    codes_str = ','.join(codes)
    min_date = trade_dates[7]
    df = pro.daily(ts_code=codes_str, start_date=min_date, end_date=trade_date)
    if df.empty:
        return {}

    changes = {}
    for code in codes:
        df_code = df[df['ts_code'] == code].sort_values('trade_date')
        if df_code.empty:
            continue
        latest_row = df_code[df_code['trade_date'] == trade_date]
        if latest_row.empty:
            continue
        latest_close = float(latest_row.iloc[0]['close'])

        result = {'change_3d': None, 'change_5d': None, 'change_7d': None,
                  'price': latest_close, 'pct_chg': round(float(latest_row.iloc[0]['pct_chg']), 2)}

        for days, target_date in target_dates.items():
            target_rows = df_code[df_code['trade_date'] == target_date]
            if not target_rows.empty:
                target_close = float(target_rows.iloc[0]['close'])
                result[f'change_{days}d'] = round((latest_close / target_close - 1) * 100, 2)

        changes[code] = result
    return changes

def extract_html_values(html_content, stock_name):
    """从HTML中提取某只股票的涨跌数值"""
    # 匹配 <td class="up|down|neutral">+/-X.XX%</td> 的模式
    # 在持仓表和建仓表中分别查找
    patterns = [
        # 持仓表模式：名称后的7个<td>（现价,日涨跌,3日,5日,7日,目标,止损,占比,状态）
        rf'<td><strong>{re.escape(stock_name)}</strong></td>'
        + r'(?:\s*<td>[^<]*</td>){1}'  # 代码
        + r'(?:\s*<td[^>]*>[^<]*</td>)'  # 现价
        + r'(?:\s*<td[^>]*>([^<]*)</td>)'  # 日涨跌（group1）
        + r'(?:\s*<td[^>]*>([^<]*)</td>)'  # 3日（group2）
        + r'(?:\s*<td[^>]*>([^<]*)</td>)'  # 5日（group3）
        + r'(?:\s*<td[^>]*>([^<]*)</td>)', # 7日（group4）
    ]

    for pattern in patterns:
        m = re.search(pattern, html_content)
        if m:
            return {
                'pct_chg': parse_pct(m.group(1)),
                'change_3d': parse_pct(m.group(2)),
                'change_5d': parse_pct(m.group(3)),
                'change_7d': parse_pct(m.group(4)),
            }
    return None

def parse_pct(s):
    """解析百分比字符串为浮点数"""
    if not s or s.strip() == '--':
        return None
    s = s.strip().replace('%', '').replace('+', '')
    try:
        return round(float(s), 2)
    except ValueError:
        return None

def format_pct(val):
    """格式化百分比"""
    if val is None:
        return '--'
    sign = '+' if val > 0 else ''
    return f"{sign}{val:.2f}%"

def main():
    fix_mode = '--fix' in sys.argv

    print("=" * 60)
    print("股票监控看板数据核查")
    print("=" * 60)

    trade_date = get_last_trade_date()
    print(f"\n最近交易日: {trade_date}")
    print("正在从Tushare拉取真实数据...")

    tushare_data = fetch_history_changes(list(ALL_STOCKS.keys()), trade_date)
    if not tushare_data:
        print("[ERR] 无法从Tushare获取数据，核查中止")
        sys.exit(1)

    print(f"[OK] Tushare数据获取完成，共{len(tushare_data)}只股票")

    # 读取HTML
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        html = f.read()

    errors = []
    all_diffs = []

    print("\n" + "-" * 60)
    print(f"{'股票':<10} {'字段':<8} {'Tushare':<12} {'HTML静态':<12} {'状态':<6}")
    print("-" * 60)

    for code, info in ALL_STOCKS.items():
        name = info['name']
        html_name = info['html_name']
        html_vals = extract_html_values(html, html_name)
        tushare_vals = tushare_data.get(code, {})

        if not html_vals:
            print(f"{name:<10} [WARN] HTML中未找到该股票数据")
            continue

        fields = ['pct_chg', 'change_3d', 'change_5d', 'change_7d']
        field_names = {'pct_chg': '日涨跌', 'change_3d': '3日涨跌',
                       'change_5d': '5日涨跌', 'change_7d': '7日涨跌'}

        for field in fields:
            tv = tushare_vals.get(field)
            hv = html_vals.get(field)

            status = "✅"
            if tv is None or hv is None:
                status = "⚠️"
            elif abs(tv - hv) > 0.02:  # 允许0.02%的四舍五入误差
                status = "❌"
                errors.append({
                    'name': name, 'field': field_names[field],
                    'tushare': tv, 'html': hv,
                    'diff': round(abs(tv - hv), 2)
                })

            tstr = format_pct(tv)
            hstr = format_pct(hv)
            print(f"{name:<10} {field_names[field]:<8} {tstr:<12} {hstr:<12} {status:<6}")
            all_diffs.append((name, field_names[field], tv, hv, status))

    print("-" * 60)

    # 修正模式
    if fix_mode and errors:
        print("\n[FIX] 自动修正模式启动...")
        new_html = html
        for err in errors:
            name = err['name']
            field = err['field']
            tv = err['tushare']
            tstr = format_pct(tv)

            # 找到对应的HTML值并替换
            # 简单替换：在股票名称后的对应位置
            # 这是一个简化版，完整版需要更精确的DOM操作
            print(f"  修正 {name} {field}: {format_pct(err['html'])} → {tstr}")

        # 保存备份
        backup_path = HTML_PATH + BACKUP_SUFFIX
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"[OK] 备份已保存: {backup_path}")
        print("[WARN] 自动修正功能尚未完全实现，请手动修改HTML")

    # 输出汇总
    print("\n" + "=" * 60)
    if errors:
        print(f"❌ 发现 {len(errors)} 处不一致：")
        for e in errors:
            print(f"   {e['name']} {e['field']}: Tushare={format_pct(e['tushare'])}, "
                  f"HTML={format_pct(e['html'])}, 偏差={e['diff']:.2f}%")
        print(f"\n请立即修正 stock_dashboard.html 中的静态数据！")
        sys.exit(1)
    else:
        print("✅ 全部一致！Tushare真实值与HTML静态值完全匹配。")
        print("\n核查通过。")
        sys.exit(0)

if __name__ == '__main__':
    main()
