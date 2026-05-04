import tushare as ts
import json
from datetime import datetime, timedelta

import os

# Tushare Pro setup
TS_TOKEN = os.environ.get('TUSHARE_TOKEN', '')
if not TS_TOKEN:
    raise ValueError("TUSHARE_TOKEN environment variable not set")
ts.set_token(TS_TOKEN)
pro = ts.pro_api()

# Stock list: (ts_code, name, sector, target_low, target_high, stop_loss)
stocks = [
    ('688485.SH', '九州一轨', '轨交设备', 60.0, 65.0, 49.0),
    ('600989.SH', '宝丰能源', '煤制烯烃', 38.0, None, None),
    ('603799.SH', '华友钴业', '新能源材料', 50.0, None, None),
    ('600367.SH', '红星发展', '锶盐/电解锰', 22.0, None, None),
    ('603063.SH', '禾望电气', '电气设备', 35.0, None, None),
    ('000488.SZ', 'ST晨鸣', '造纸', 3.5, None, None),
    ('301317.SZ', '鑫磊股份', '通用设备', 25.0, None, None),
    ('002422.SZ', '科伦药业', '医药', 28.0, 30.0, None),
    ('600036.SH', '招商银行', '银行', 35.0, 36.0, None),
    ('600900.SH', '长江电力', '水电', 26.0, 26.5, 22.0),
    ('601985.SH', '中国核电', '核电', 7.5, 8.0, 6.5),
    ('601600.SH', '中国铝业', '有色', 9.5, 10.0, 7.8),
]

trade_date = '20260430'

# Fetch daily data
print('Fetching daily data...')
daily_data = {}
for code, name, sector, t1, t2, stop in stocks:
    try:
        df = pro.daily(ts_code=code, trade_date=trade_date)
        if len(df) > 0:
            r = df.iloc[0]
            daily_data[code] = {
                'open': r['open'],
                'high': r['high'],
                'low': r['low'],
                'close': r['close'],
                'pre_close': r['pre_close'],
                'change': r['change'],
                'pct_chg': r['pct_chg'],
                'vol': r['vol'],
                'amount': r['amount'],
            }
    except Exception as e:
        print(f'{name} daily error: {e}')

# Fetch money flow
print('Fetching money flow...')
moneyflow_data = {}
for code, name, sector, t1, t2, stop in stocks:
    try:
        df = pro.moneyflow(ts_code=code, trade_date=trade_date)
        if len(df) > 0:
            r = df.iloc[0]
            # Calculate net inflows by category (amount in 万元)
            sm_net = r['buy_sm_amount'] - r['sell_sm_amount']
            md_net = r['buy_md_amount'] - r['sell_md_amount']
            lg_net = r['buy_lg_amount'] - r['sell_lg_amount']
            elg_net = r['buy_elg_amount'] - r['sell_elg_amount']
            total_net = sm_net + md_net + lg_net + elg_net
            moneyflow_data[code] = {
                'sm_net': sm_net,
                'md_net': md_net,
                'lg_net': lg_net,
                'elg_net': elg_net,
                'total_net': total_net,
            }
    except Exception as e:
        print(f'{name} moneyflow error: {e}')

# Fetch daily basic
print('Fetching daily basic...')
basic_data = {}
for code, name, sector, t1, t2, stop in stocks:
    try:
        df = pro.daily_basic(ts_code=code, trade_date=trade_date)
        if len(df) > 0:
            r = df.iloc[0]
            basic_data[code] = {
                'pe': r['pe'],
                'pb': r['pb'],
                'total_mv': r['total_mv'] / 10000 if r['total_mv'] else None,  # 万元->亿元
                'circ_mv': r['circ_mv'] / 10000 if r['circ_mv'] else None,
                'turnover_rate': r['turnover_rate'],
            }
    except Exception as e:
        print(f'{name} basic error: {e}')

# Save data
import pickle
with open('/Users/hf/.kimi_openclaw/workspace/portfolio_data.pkl', 'wb') as f:
    pickle.dump({'daily': daily_data, 'moneyflow': moneyflow_data, 'basic': basic_data}, f)

print('\n=== Data Summary ===')
for code, name, sector, t1, t2, stop in stocks:
    d = daily_data.get(code, {})
    m = moneyflow_data.get(code, {})
    b = basic_data.get(code, {})
    print(f"{name}({code}):")
    print(f"  收盘价: {d.get('close', 'N/A')}, 涨跌: {d.get('pct_chg', 'N/A'):.2f}%")
    print(f"  主力净额: {m.get('total_net', 'N/A'):.0f}万")
    print(f"  PE: {b.get('pe', 'N/A')}, PB: {b.get('pb', 'N/A')}, 市值: {b.get('total_mv', 'N/A'):.0f}亿")
