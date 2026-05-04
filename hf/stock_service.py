#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票实时监控后台服务
- HTTP服务端口 8888，局域网可访问
- /stock-dashboard.html -> 看板页面
- /api/data -> JSON数据接口
- 后台线程：交易日每2分钟抓取Tushare数据
- 开机自启配置见 com.openclaw.stockdashboard.plist
"""

import http.server
import socketserver
import json
import threading
import time
import datetime
import os
import sys
import socket

# Tushare
import tushare as ts
import pandas as pd

TOKEN = os.environ.get('TUSHARE_TOKEN', '')
if not TOKEN:
    raise ValueError("TUSHARE_TOKEN environment variable not set")
ts.set_token(TOKEN)
pro = ts.pro_api()

PORT = 8888
WORKSPACE = "/Users/hf/.kimi_openclaw/workspace"
HTML_FILE = os.path.join(WORKSPACE, "stock_dashboard.html")

# ===================== 股票配置 =====================
HOLDINGS = [
    {"code": "688485.SH", "name": "九州一轨", "shares": 23480, "cost": 46.70, "target": "60/65", "stop": 49.0, "hero": True},
    {"code": "600367.SH", "name": "红星发展", "shares": 1600, "cost": 21.20, "target": "22", "stop": None, "hero": False},
    {"code": "603063.SH", "name": "禾望电气", "shares": 300, "cost": 44.31, "target": "35", "stop": 37.0, "hero": False},
    {"code": "000488.SZ", "name": "ST晨鸣", "shares": 48200, "cost": 3.10, "target": "3.5", "stop": None, "hero": False},
    {"code": "301317.SZ", "name": "鑫磊股份", "shares": 500, "cost": 60.21, "target": "25", "stop": None, "hero": False},
]

WATCHLIST = [
    {"code": "600989.SH", "name": "宝丰能源", "target": "38", "stop": None, "rec": 28.00},
    {"code": "603799.SH", "name": "华友钴业", "target": "50", "stop": None, "rec": 58.00},
    {"code": "002422.SZ", "name": "科伦药业", "target": "28-30", "stop": None, "rec": 32.00},
    {"code": "600036.SH", "name": "招商银行", "target": "35-36", "stop": None, "rec": 35.00},
    {"code": "601985.SH", "name": "中国核电", "target": "7.5-8.0", "stop": 6.5, "rec": 8.50},
    {"code": "601600.SH", "name": "中国铝业", "target": "9.5-10.0", "stop": 7.8, "rec": 10.50},
    {"code": "600900.SH", "name": "长江电力", "target": "26-26.5", "stop": 22, "rec": 26.00},
]

CYB_STOCKS = [
    {"code": "300750.SZ", "name": "宁德时代"},
    {"code": "300308.SZ", "name": "中际旭创"},
    {"code": "300502.SZ", "name": "新易盛"},
    {"code": "300059.SZ", "name": "东方财富"},
    {"code": "300274.SZ", "name": "阳光电源"},
    {"code": "300476.SZ", "name": "胜宏科技"},
    {"code": "300394.SZ", "name": "天孚通信"},
    {"code": "300124.SZ", "name": "汇川技术"},
    {"code": "300760.SZ", "name": "迈瑞医疗"},
    {"code": "300014.SZ", "name": "亿纬锂能"},
]

ALL_STOCKS = HOLDINGS + WATCHLIST + CYB_STOCKS
ALL_CODES = [s["code"] for s in ALL_STOCKS]

# ===================== 数据缓存 =====================
class DataCache:
    def __init__(self):
        self.data = {"stocks": {}, "indices": {}, "commodities": {}, "market_status": "初始化中", "timestamp": None}
        self.lock = threading.Lock()
    
    def update(self, new_data):
        with self.lock:
            self.data = new_data
    
    def get(self):
        with self.lock:
            return dict(self.data)

cache = DataCache()

# ===================== 交易时间判断 =====================
def is_trading_time():
    """A股交易时段：工作日 9:30-11:30, 13:00-15:00"""
    now = datetime.datetime.now()
    if now.weekday() >= 5:
        return False
    t = now.time()
    morning = datetime.time(9, 30) <= t <= datetime.time(11, 30)
    afternoon = datetime.time(13, 0) <= t <= datetime.time(15, 0)
    return morning or afternoon

def get_last_trade_date():
    """获取最近一个交易日"""
    today = datetime.datetime.now().strftime('%Y%m%d')
    try:
        df = pro.trade_cal(exchange='SSE', start_date='20260101', end_date=today)
        df = df[df['is_open'] == 1]
        if len(df) > 0:
            return df.iloc[-1]['cal_date']
    except Exception as e:
        print(f"[WARN] trade_cal failed: {e}")
    return today

# ===================== Tushare数据抓取 =====================
def fetch_stock_data(trade_date=None):
    """抓取所有股票数据"""
    if trade_date is None:
        trade_date = get_last_trade_date()
    
    result = {code: {
        "price": None, "open": None, "high": None, "low": None,
        "pre_close": None, "pct_chg": None, "volume": None, "amount": None,
        "main_net": None, "xl_net": None, "l_net": None, "m_net": None, "s_net": None,
        "pe": None, "pb": None, "total_mv": None, "circ_mv": None,
        "turnover_rate": None, "volume_ratio": None,
    } for code in ALL_CODES}
    
    # 1. 日线行情
    try:
        df_daily = pro.daily(trade_date=trade_date)
        df_daily = df_daily[df_daily["ts_code"].isin(ALL_CODES)]
        for _, row in df_daily.iterrows():
            c = row["ts_code"]
            if c in result:
                result[c].update({
                    "price": round(float(row["close"]), 2),
                    "open": round(float(row["open"]), 2),
                    "high": round(float(row["high"]), 2),
                    "low": round(float(row["low"]), 2),
                    "pre_close": round(float(row["pre_close"]), 2),
                    "pct_chg": round(float(row["pct_chg"]), 2),
                    "volume": int(row["vol"]),
                    "amount": round(float(row["amount"]), 2),
                })
        print(f"[OK] daily: {len(df_daily)} stocks")
    except Exception as e:
        print(f"[ERR] daily: {e}")
    
    # 2. 资金流向
    try:
        df_money = pro.moneyflow(trade_date=trade_date)
        df_money = df_money[df_money["ts_code"].isin(ALL_CODES)]
        for _, row in df_money.iterrows():
            c = row["ts_code"]
            if c in result:
                # 单位：万元
                result[c].update({
                    "main_net": round(float(row.get("net_mf_amount", 0)), 2),
                    "xl_net": round(float(row.get("buy_elg_amount", 0)) - float(row.get("sell_elg_amount", 0)), 2),
                    "l_net": round(float(row.get("buy_lg_amount", 0)) - float(row.get("sell_lg_amount", 0)), 2),
                    "m_net": round(float(row.get("buy_md_amount", 0)) - float(row.get("sell_md_amount", 0)), 2),
                    "s_net": round(float(row.get("buy_sm_amount", 0)) - float(row.get("sell_sm_amount", 0)), 2),
                })
        print(f"[OK] moneyflow: {len(df_money)} stocks")
    except Exception as e:
        print(f"[ERR] moneyflow: {e}")
    
    # 3. 每日指标（PE/PB/市值）
    try:
        df_basic = pro.daily_basic(trade_date=trade_date)
        df_basic = df_basic[df_basic["ts_code"].isin(ALL_CODES)]
        for _, row in df_basic.iterrows():
            c = row["ts_code"]
            if c in result:
                pe = row.get("pe")
                pb = row.get("pb")
                total_mv = row.get("total_mv")  # 万元
                circ_mv = row.get("circ_mv")
                turnover_rate = row.get("turnover_rate")
                volume_ratio = row.get("volume_ratio")
                result[c].update({
                    "pe": round(float(pe), 2) if pd.notna(pe) else None,
                    "pb": round(float(pb), 2) if pd.notna(pb) else None,
                    "total_mv": round(float(total_mv), 2) if pd.notna(total_mv) else None,
                    "circ_mv": round(float(circ_mv), 2) if pd.notna(circ_mv) else None,
                    "turnover_rate": round(float(turnover_rate), 2) if pd.notna(turnover_rate) else None,
                    "volume_ratio": round(float(volume_ratio), 2) if pd.notna(volume_ratio) else None,
                })
        print(f"[OK] daily_basic: {len(df_basic)} stocks")
    except Exception as e:
        print(f"[ERR] daily_basic: {e}")
    
    # 4. 大盘指数
    indices = {}
    try:
        for idx_code, idx_name in [("000001.SH", "上证指数"), ("399001.SZ", "深证成指"), ("399006.SZ", "创业板指")]:
            df_idx = pro.index_daily(ts_code=idx_code, trade_date=trade_date)
            if len(df_idx) > 0:
                row = df_idx.iloc[0]
                indices[idx_name] = {
                    "close": round(float(row["close"]), 2),
                    "open": round(float(row["open"]), 2),
                    "high": round(float(row["high"]), 2),
                    "low": round(float(row["low"]), 2),
                    "pct_chg": round(float(row["pct_chg"]), 2),
                }
        print(f"[OK] indices: {list(indices.keys())}")
    except Exception as e:
        print(f"[ERR] indices: {e}")
    
    # 5. 融资融券（仅持仓股）
    holding_codes = [s["code"] for s in HOLDINGS]
    margin_data = {}
    try:
        df_margin = pro.margin(trade_date=trade_date)
        df_margin = df_margin[df_margin["ts_code"].isin(holding_codes)]
        for _, row in df_margin.iterrows():
            c = row["ts_code"]
            margin_data[c] = {
                "rzye": round(float(row.get("rzye", 0)), 2),      # 融资余额（元）
                "rqye": round(float(row.get("rqye", 0)), 2),      # 融券余额（元）
                "rzmr": round(float(row.get("rzmr", 0)), 2),      # 融资买入额
                "rzcj": round(float(row.get("rzcj", 0)), 2),      # 融资偿还额
            }
        print(f"[OK] margin: {len(df_margin)} stocks")
    except Exception as e:
        print(f"[ERR] margin: {e}")
    
    return {
        "stocks": result,
        "indices": indices,
        "margin": margin_data,
        "market_status": "交易中" if is_trading_time() else "休市",
        "trade_date": trade_date,
        "timestamp": datetime.datetime.now().isoformat(),
    }

# ===================== 后台数据刷新线程 =====================
def data_fetcher_loop():
    """交易日每2分钟抓取数据"""
    # 首次抓取
    try:
        print(f"[{datetime.datetime.now()}] 初始数据抓取...")
        data = fetch_stock_data()
        cache.update(data)
        print(f"[{datetime.datetime.now()}] 初始数据完成")
    except Exception as e:
        print(f"[{datetime.datetime.now()}] 初始抓取失败: {e}")
    
    while True:
        try:
            if is_trading_time():
                print(f"[{datetime.datetime.now()}] 交易时段，抓取数据...")
                data = fetch_stock_data()
                cache.update(data)
                print(f"[{datetime.datetime.now()}] 数据更新完成")
            else:
                # 非交易时段，每30分钟检查一次是否有新数据（收盘后可能有补录）
                now = datetime.datetime.now()
                # 只在上午9点后、下午3点后尝试补抓
                if now.time() >= datetime.time(9, 0):
                    print(f"[{datetime.datetime.now()}] 非交易时段，检查补录数据...")
                    data = fetch_stock_data()
                    cache.update(data)
            
            time.sleep(120)  # 2分钟
        except Exception as e:
            print(f"[{datetime.datetime.now()}] 抓取异常: {e}")
            time.sleep(120)

# ===================== HTTP服务 =====================
class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WORKSPACE, **kwargs)
    
    def log_message(self, fmt, *args):
        # 减少日志噪音
        pass
    
    def do_GET(self):
        if self.path == "/api/data":
            self._send_json()
        elif self.path == "/api/health":
            self._send_health()
        elif self.path == "/" or self.path == "/stock-dashboard" or self.path == "/index.html":
            self.path = "/stock_dashboard.html"
            super().do_GET()
        else:
            super().do_GET()
    
    def _send_json(self):
        data = cache.get()
        body = json.dumps(data, ensure_ascii=False, default=str)
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))
    
    def _send_health(self):
        data = cache.get()
        status = {
            "status": "ok",
            "market_status": data.get("market_status"),
            "last_update": data.get("timestamp"),
            "trading_time": is_trading_time(),
        }
        body = json.dumps(status, ensure_ascii=False)
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

class ReuseAddrTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def start_server():
    with ReuseAddrTCPServer(("0.0.0.0", PORT), DashboardHandler) as httpd:
        print(f"=" * 60)
        print(f"股票监控服务已启动")
        print(f"本地访问: http://localhost:{PORT}/")
        print(f"局域网访问: http://{socket.gethostname()}.local:{PORT}/")
        print(f"API接口: http://localhost:{PORT}/api/data")
        print(f"=" * 60)
        httpd.serve_forever()

# ===================== 启动 =====================
if __name__ == "__main__":
    # 启动数据抓取后台线程
    fetcher = threading.Thread(target=data_fetcher_loop, daemon=True, name="DataFetcher")
    fetcher.start()
    
    # 启动HTTP服务（主线程）
    start_server()
