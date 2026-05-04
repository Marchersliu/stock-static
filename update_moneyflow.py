#!/usr/bin/env python3
"""
Tushare 资金流向自动更新脚本
用于更新 投资组合实时监控中心.html 的资金流向数据

运行方式:
    python3 update_moneyflow.py

定时任务（crontab -e）:
    # 工作日 15:35 自动更新（收盘后5分钟）
    35 15 * * 1-5 /usr/bin/python3 /Users/hf/.kimi_openclaw/workspace/update_moneyflow.py
"""

import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
import re
import os

# ============= 配置 =============
TS_TOKEN = 'a9ee0aa6b5d48295c555acee15f3b6e354647267c10981b60da5fa08'

# 持仓股列表 (tushare 格式)
STOCKS = {
    '688485.SH': '九州一轨',
    '600989.SH': '宝丰能源',
    '603799.SH': '华友钴业',
    '600367.SH': '红星发展',
    '603063.SH': '禾望电气',
    '000488.SZ': 'ST晨鸣',
    '301317.SZ': '鑫磊股份',
    '002422.SZ': '科伦药业',
    '600036.SH': '招商银行',
    '600900.SH': '长江电力',
    '601985.SH': '中国核电',
    '601600.SH': '中国铝业',
}

HTML_PATH = '/Users/hf/.kimi_openclaw/workspace/投资组合实时监控中心.html'
ICLOUD_PATH = '/Users/hf/Library/Mobile Documents/com~apple~CloudDocs/下载文件/HF/投资组合实时监控中心.html'


def format_amount(amount):
    """格式化金额：万/亿"""
    if amount is None or pd.isna(amount):
        return '—'
    amount = float(amount)
    if abs(amount) >= 10000:
        return f"{amount/10000:+.2f}亿"
    else:
        return f"{amount:+.0f}万"


def get_trade_date():
    """获取最近交易日（Tushare 格式 YYYYMMDD）"""
    today = datetime.now()
    weekday = today.weekday()
    
    # 节假日回退：五一假期 5/1-5/5
    if today.month == 5 and today.day <= 5:
        return '20260430'
    
    # 周末回退
    if weekday == 5:  # 周六
        today -= timedelta(days=1)
    elif weekday == 6:  # 周日
        today -= timedelta(days=2)
    return today.strftime('%Y%m%d')


def fetch_moneyflow(pro_api, trade_date):
    """抓取所有持仓股的资金流向"""
    results = {}
    for code, name in STOCKS.items():
        try:
            df = pro_api.moneyflow(ts_code=code, start_date=trade_date, end_date=trade_date)
            if len(df) > 0:
                row = df.iloc[0]
                elg_net = row['buy_elg_amount'] - row['sell_elg_amount']  # 超大单净额
                lg_net = row['buy_lg_amount'] - row['sell_lg_amount']    # 大单净额
                md_net = row['buy_md_amount'] - row['sell_md_amount']    # 中单净额
                sm_net = row['buy_sm_amount'] - row['sell_sm_amount']    # 小单净额
                main_net = elg_net + lg_net  # 主力合计（超大单+大单）
                
                results[code] = {
                    'name': name,
                    'trade_date': trade_date,
                    'main_net': main_net,       # 主力净流入
                    'elg_net': elg_net,         # 超大单
                    'lg_net': lg_net,           # 大单
                    'md_net': md_net,           # 中单
                    'sm_net': sm_net,           # 小单
                }
        except Exception as e:
            print(f"[WARN] {code} {name}: {e}")
    return results


def generate_html(results, trade_date):
    """生成资金流向 HTML 片段"""
    
    def row_html(code, data):
        main_color = '#ef4444' if data['main_net'] >= 0 else '#22c55e'
        main_sign = '流入' if data['main_net'] >= 0 else '流出'
        main_bg = '#4a0d0d' if data['main_net'] >= 0 else '#0d4a1a'
        
        elg_color = '#ef4444' if data['elg_net'] >= 0 else '#22c55e'
        lg_color = '#ef4444' if data['lg_net'] >= 0 else '#22c55e'
        md_color = '#ef4444' if data['md_net'] >= 0 else '#22c55e'
        sm_color = '#ef4444' if data['sm_net'] >= 0 else '#22c55e'
        
        return f"""
      <tr>
        <td><strong>{data['name']}</strong><br><span style="font-size:11px;color:#64748b;">{code}</span></td>
        <td style="color:{main_color};font-weight:700;text-align:right;padding:10px 8px;">{format_amount(data['main_net'])}</td>
        <td style="color:{elg_color};text-align:right;padding:10px 8px;">{format_amount(data['elg_net'])}</td>
        <td style="color:{lg_color};text-align:right;padding:10px 8px;">{format_amount(data['lg_net'])}</td>
        <td style="color:{md_color};text-align:right;padding:10px 8px;">{format_amount(data['md_net'])}</td>
        <td style="color:{sm_color};text-align:right;padding:10px 8px;">{format_amount(data['sm_net'])}</td>
        <td style="text-align:center;padding:10px 8px;"><span style="display:inline-block;padding:3px 10px;border-radius:4px;font-size:12px;font-weight:600;background:{main_bg};color:{main_color};">{main_sign}</span></td>
      </tr>"""
    
    rows = ""
    for code in STOCKS.keys():
        if code in results:
            rows += row_html(code, results[code])
    
    date_str = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"
    
    return f"""    <!-- BEGIN_MONEYFLOW -->
    <h3 style="color:#fbbf24;font-size:15px;margin:16px 0 10px;">💰 资金流向 ({date_str})</h3>
    <div style="overflow-x:auto;">
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <thead>
          <tr style="background:#1e293b;color:#94a3b8;font-size:12px;">
            <th style="padding:8px;text-align:left;border-bottom:1px solid #334155;">股票</th>
            <th style="padding:8px;text-align:right;border-bottom:1px solid #334155;">主力净流入</th>
            <th style="padding:8px;text-align:right;border-bottom:1px solid #334155;">超大单</th>
            <th style="padding:8px;text-align:right;border-bottom:1px solid #334155;">大单</th>
            <th style="padding:8px;text-align:right;border-bottom:1px solid #334155;">中单</th>
            <th style="padding:8px;text-align:right;border-bottom:1px solid #334155;">小单</th>
            <th style="padding:8px;text-align:center;border-bottom:1px solid #334155;">方向</th>
          </tr>
        </thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </div>
    <p style="color:#64748b;font-size:11px;margin-top:8px;">数据来源：Tushare | 主力 = 超大单(>100万) + 大单(20-100万) | 更新于 {datetime.now().strftime('%H:%M')}</p>
    <!-- END_MONEYFLOW -->"""


def update_html(html_path, results, trade_date):
    """更新 HTML 文件中的资金流向部分"""
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_section = generate_html(results, trade_date)
    
    # 方法1: 用特殊注释标记定位（推荐）
    begin_marker = '<!-- BEGIN_MONEYFLOW -->'
    end_marker = '<!-- END_MONEYFLOW -->'
    
    if begin_marker in content and end_marker in content:
        # 找到标记之间的内容并替换
        pattern = re.escape(begin_marker) + '.*?' + re.escape(end_marker)
        content = re.sub(pattern, new_section, content, flags=re.DOTALL)
        print(f"[OK] 已替换标记区域")
    else:
        # 方法2: 如果没找到标记，尝试匹配旧版 "资金面信号" 或 "资金流向" 标题
        pattern = r'(\s*<h3 style="color:#fbbf24;font-size:15px;margin:16px 0 10px;">💰 (资金面信号|资金流向).*?</p>\s*</div>)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            content = content[:match.start()] + new_section + content[match.end():]
            print(f"[OK] 已替换旧版资金流向板块")
        else:
            # 方法3: 在 "原材料价格监控" 注释前插入
            insert_marker = '<!-- ==================== 原材料价格监控 ==================== -->'
            if insert_marker in content:
                content = content.replace(insert_marker, new_section + '\n\n  ' + insert_marker)
                print(f"[OK] 已插入新的资金流向板块")
            else:
                print(f"[WARN] 无法定位插入点，未更新")
                return False
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True


def sync_to_icloud():
    """同步到 iCloud"""
    try:
        import shutil
        shutil.copy2(HTML_PATH, ICLOUD_PATH)
        print(f"[OK] 已同步到 iCloud: {ICLOUD_PATH}")
        return True
    except Exception as e:
        print(f"[WARN] iCloud 同步失败: {e}")
        return False


def main():
    print(f"=== Tushare 资金流向更新 ===")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 初始化 Tushare
    ts.set_token(TS_TOKEN)
    pro = ts.pro_api()
    print(f"[OK] Tushare 已连接")
    
    # 获取交易日
    trade_date = get_trade_date()
    print(f"[INFO] 查询日期: {trade_date}")
    
    # 抓取数据
    print(f"[INFO] 正在抓取 {len(STOCKS)} 只股票资金流向...")
    results = fetch_moneyflow(pro, trade_date)
    print(f"[OK] 成功获取 {len(results)} 只股票数据")
    
    # 打印摘要
    print(f"\n摘要:")
    for code, data in results.items():
        direction = '流入' if data['main_net'] >= 0 else '流出'
        print(f"  {data['name']}: 主力{direction} {format_amount(data['main_net'])}")
    
    # 更新 HTML
    if update_html(HTML_PATH, results, trade_date):
        # 同步到 iCloud
        sync_to_icloud()
        print(f"\n[OK] 更新完成!")
    else:
        print(f"\n[ERR] 更新失败")


if __name__ == '__main__':
    main()
