#!/usr/bin/env python3
"""
报告生成主脚本 - 自动生成持仓日报/周报/月报

用法:
    python3 generate_report.py --type daily --output ~/Desktop/持仓日报.html
    python3 generate_report.py --type weekly --output ~/Desktop/持仓周报.html
    python3 generate_report.py --type daily --format markdown

类型:
    daily    - 日报（当日行情+新闻+原料）
    weekly   - 周报（5日走势+板块+技术分析）
    monthly  - 月报（月度回顾+策略建议）

格式:
    html      - 带CSS样式的完整页面（默认）
    markdown  - 纯文本摘要
    json      - 结构化数据
"""
import argparse
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from datetime import datetime, timedelta
from utils import (
    ALL_STOCK_CODES, HOLDINGS, WATCHLIST, STOCK_KEYWORDS,
    get_tushare_token, format_change, print_section
)
from fetch_data import init_tushare, fetch_price, fetch_moneyflow, fetch_sector_moneyflow, fetch_commodity_prices, fetch_index_data


def generate_daily_report(pro, fmt='html'):
    """生成日报"""
    today = datetime.now().strftime('%Y-%m-%d')
    trade_date = datetime.now().strftime('%Y%m%d')
    
    # 抓取数据
    price = fetch_price(pro, HOLDINGS + WATCHLIST, trade_date)
    moneyflow = fetch_moneyflow(pro, HOLDINGS + WATCHLIST, trade_date)
    sectors = fetch_sector_moneyflow(pro)
    commodities = fetch_commodity_prices(pro)
    indices = fetch_index_data()
    
    if fmt == 'json':
        return {
            'type': 'daily', 'date': today,
            'price': price, 'moneyflow': moneyflow,
            'sectors': sectors, 'commodities': commodities, 'indices': indices
        }
    
    # HTML 报告
    if fmt == 'html':
        return _generate_html_report(today, price, moneyflow, sectors, commodities, indices, '日报')
    
    # Markdown 报告
    return _generate_markdown_report(today, price, moneyflow, sectors, commodities, indices, '日报')


def _generate_html_report(date, price, moneyflow, sectors, commodities, indices, report_type):
    """生成HTML格式报告"""
    # 持仓表格
    holdings_rows = []
    for code in HOLDINGS:
        p = price.get(code, {})
        mf = moneyflow.get(code, {})
        info = STOCK_KEYWORDS.get(code, {})
        if p:
            holdings_rows.append(f"""
            <tr>
                <td>{info.get('name', code)}</td>
                <td>{code}</td>
                <td>{p.get('close', '—')}</td>
                <td style="color:{'var(--green)' if p.get('pct_chg', 0) > 0 else 'var(--red)'}">{format_change(p.get('pct_chg'))}</td>
                <td>{format_change(mf.get('main_net'), '万') if mf else '—'}</td>
                <td>{info.get('target', '—')}</td>
            </tr>""")
    
    # 原料表格
    commodity_rows = []
    for c in commodities[:10]:
        color = 'var(--green)' if (c.get('change') or 0) > 0 else 'var(--red)'
        commodity_rows.append(f"""
        <tr>
            <td>{c.get('name')}</td>
            <td>{c.get('price', '—')} {c.get('unit')}</td>
            <td style="color:{color}">{format_change(c.get('change'))}</td>
        </tr>""")
    
    # 指数
    index_str = ' | '.join([f"{k}: {v.get('close', '—')} ({format_change(v.get('pct'))})" for k, v in indices.items()])
    
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>持仓{report_type} - {date}</title>
<style>
body {{ font-family: -apple-system, system-ui; background: #0d1b2a; color: #c8d6e0; padding: 20px; }}
table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #1a2b3d; }}
th {{ background: rgba(74,158,255,0.15); color: #4a9eff; }}
h2 {{ color: #4a9eff; border-left: 3px solid #4a9eff; padding-left: 10px; }}
.green {{ color: #00d084; }} .red {{ color: #ff4757; }}
.header {{ font-size: 24px; font-weight: bold; margin-bottom: 20px; }}
.summary {{ background: rgba(74,158,255,0.08); padding: 15px; border-radius: 8px; margin: 10px 0; }}
</style>
</head>
<body>
<div class="header">📊 持仓{report_type} · {date}</div>
<div class="summary">{index_str}</div>

<h2>🔴 持仓总览（{len(HOLDINGS)}只）</h2>
<table>
<tr><th>名称</th><th>代码</th><th>现价</th><th>日涨跌</th><th>主力流向</th><th>目标价</th></tr>
{''.join(holdings_rows)}
</table>

<h2>🏭 原料期货（前10种）</h2>
<table>
<tr><th>原料</th><th>价格</th><th>涨跌</th></tr>
{''.join(commodity_rows)}
</table>

<div style="color:var(--text2); font-size:12px; margin-top:30px;">
  生成时间: {datetime.now().strftime('%H:%M:%S')} | 
  数据来源: Tushare Pro / 腾讯接口
</div>
</body>
</html>"""
    return html


def _generate_markdown_report(date, price, moneyflow, sectors, commodities, indices, report_type):
    """生成Markdown格式报告"""
    lines = [f"# 📊 持仓{report_type} · {date}", ""]
    
    # 指数
    lines.append("## 📈 指数概览")
    for k, v in indices.items():
        lines.append(f"- **{k}**: {v.get('close', '—')} ({format_change(v.get('pct'))})")
    lines.append("")
    
    # 持仓
    lines.append(f"## 🔴 持仓总览（{len(HOLDINGS)}只）")
    lines.append("| 名称 | 代码 | 现价 | 涨跌 | 主力 | 目标价 |")
    lines.append("|------|------|------|------|------|--------|")
    for code in HOLDINGS:
        p = price.get(code, {})
        mf = moneyflow.get(code, {})
        info = STOCK_KEYWORDS.get(code, {})
        if p:
            lines.append(f"| {info.get('name')} | {code} | {p.get('close')} | {format_change(p.get('pct_chg'))} | {format_change(mf.get('main_net'), '万') if mf else '—'} | {info.get('target', '—')} |")
    lines.append("")
    
    # 原料
    lines.append("## 🏭 原料期货（前10种）")
    for c in commodities[:10]:
        lines.append(f"- **{c.get('name')}**: {c.get('price', '—')} {c.get('unit')} ({format_change(c.get('change'))})")
    lines.append("")
    
    lines.append(f"_生成时间: {datetime.now().strftime('%H:%M:%S')}_")
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Stock Report Generator')
    parser.add_argument('--type', choices=['daily', 'weekly', 'monthly'],
                        default='daily', help='Report type')
    parser.add_argument('--format', choices=['html', 'markdown', 'json'],
                        default='html', help='Output format')
    parser.add_argument('--output', '-o', help='Output file path')
    
    args = parser.parse_args()
    
    pro = init_tushare()
    
    if args.type == 'daily':
        report = generate_daily_report(pro, args.format)
    else:
        print(f"[WARN] {args.type} report not yet implemented, falling back to daily")
        report = generate_daily_report(pro, args.format)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report if isinstance(report, str) else json.dumps(report, ensure_ascii=False, indent=2))
        print(f"[OK] Report saved to {args.output}")
    else:
        print(report if isinstance(report, str) else json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
