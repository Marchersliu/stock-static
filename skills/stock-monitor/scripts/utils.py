import os
import json
import time
import re
from datetime import datetime, timedelta

# ========== 股票代码映射 ==========
ALL_STOCK_CODES = [
    '688485.SH', '600989.SH', '603799.SH', '600367.SH',
    '603063.SH', '000488.SZ', '301317.SZ', '002422.SZ',
    '600036.SH', '600900.SH', '601985.SH', '601600.SH'
]

HOLDINGS = ['688485.SH', '600989.SH', '603799.SH', '600367.SH',
            '603063.SH', '000488.SZ', '301317.SZ', '002422.SZ']

WATCHLIST = ['600036.SH', '600900.SH', '601985.SH', '601600.SH']

STOCK_KEYWORDS = {
    '688485.SH': {'name': '九州一轨', 'sector': '轨交设备', 'target': '60/65', 'stop': '49'},
    '600989.SH': {'name': '宝丰能源', 'sector': '煤化工·烯烃', 'target': '38', 'stop': None},
    '603799.SH': {'name': '华友钴业', 'sector': '新能源材料', 'target': '50', 'stop': None},
    '600367.SH': {'name': '红星发展', 'sector': '有色·锶锰', 'target': '22', 'stop': None},
    '603063.SH': {'name': '禾望电气', 'sector': '电气设备', 'target': '35', 'stop': None},
    '000488.SZ': {'name': 'ST晨鸣', 'sector': '造纸', 'target': '3.5', 'stop': None},
    '301317.SZ': {'name': '鑫磊股份', 'sector': '通用设备', 'target': '25', 'stop': None},
    '002422.SZ': {'name': '科伦药业', 'sector': '医药', 'target': '28-30', 'stop': None},
    '600036.SH': {'name': '招商银行', 'sector': '银行', 'target': '35-36', 'stop': None},
    '600900.SH': {'name': '长江电力', 'sector': '电力·水电', 'target': '26-26.5', 'stop': '22'},
    '601985.SH': {'name': '中国核电', 'sector': '核电', 'target': '7.5-8.0', 'stop': '6.5'},
    '601600.SH': {'name': '中国铝业', 'sector': '铝·有色', 'target': '9.5-10.0', 'stop': '7.8'}
}

# ========== 期货配置 ==========
COMMODITY_CONFIG = [
    {'name': '碳酸锂', 'symbol': 'LC', 'exchange': 'GFE', 'unit': '元/吨'},
    {'name': '镍', 'symbol': 'NI', 'exchange': 'SHF', 'unit': '元/吨'},
    {'name': '铝锭', 'symbol': 'AL', 'exchange': 'SHF', 'unit': '元/吨'},
    {'name': '氧化铝', 'symbol': 'AO', 'exchange': 'SHF', 'unit': '元/吨'},
    {'name': '铜', 'symbol': 'CU', 'exchange': 'SHF', 'unit': '元/吨'},
    {'name': '锌', 'symbol': 'ZN', 'exchange': 'SHF', 'unit': '元/吨'},
    {'name': '锰硅', 'symbol': 'SM', 'exchange': 'ZCE', 'unit': '元/吨'},
    {'name': '铅', 'symbol': 'PB', 'exchange': 'SHF', 'unit': '元/吨'},
    {'name': '锡', 'symbol': 'SN', 'exchange': 'SHF', 'unit': '元/吨'},
    {'name': '聚丙烯', 'symbol': 'PP', 'exchange': 'DCE', 'unit': '元/吨'},
    {'name': '甲醇', 'symbol': 'MA', 'exchange': 'ZCE', 'unit': '元/吨'},
    {'name': '焦煤', 'symbol': 'JM', 'exchange': 'DCE', 'unit': '元/吨'},
    {'name': '焦炭', 'symbol': 'J', 'exchange': 'DCE', 'unit': '元/吨'},
    {'name': '原油', 'symbol': 'SC', 'exchange': 'SHF', 'unit': '元/桶'},
    {'name': '纸浆', 'symbol': 'SP', 'exchange': 'SHF', 'unit': '元/吨'},
    {'name': '螺纹钢', 'symbol': 'RB', 'exchange': 'SHF', 'unit': '元/吨'},
    {'name': '纯碱', 'symbol': 'SA', 'exchange': 'ZCE', 'unit': '元/吨'},
    {'name': '玻璃', 'symbol': 'FG', 'exchange': 'ZCE', 'unit': '元/吨'},
    {'name': 'PVC', 'symbol': 'V', 'exchange': 'DCE', 'unit': '元/吨'},
]

# ========== 工具函数 ==========
def get_tushare_token():
    """从环境变量或 .env 文件读取 Tushare Token"""
    token = os.environ.get('TUSHARE_TOKEN')
    if token:
        return token
    # 尝试读取 .env 文件
    env_paths = ['.env', '../.env', '../../.env']
    for path in env_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                for line in f:
                    if line.startswith('TUSHARE_TOKEN='):
                        return line.strip().split('=', 1)[1].strip().strip('"').strip("'")
    return None


def get_main_contract(symbol, exchange):
    """推导期货主力合约代码"""
    now = datetime.now()
    # 取当前年月后第2个月
    if now.month <= 10:
        contract_month = now.month + 2
        contract_year = now.year % 100
    else:
        contract_month = (now.month + 2) % 12
        contract_year = (now.year + 1) % 100
    month_str = f"{contract_month:02d}"
    return f"{symbol}{month_str}.{exchange}"


def is_trading_time():
    """判断是否A股交易时间"""
    now = datetime.now()
    weekday = now.weekday()
    if weekday >= 5:
        return False
    hour, minute = now.hour, now.minute
    return (9 <= hour < 11 or (hour == 11 and minute <= 30) or
            13 <= hour < 15 or (hour == 15 and minute == 0))


def format_change(value, unit='%'):
    """格式化涨跌幅，带颜色"""
    if value is None:
        return '—'
    if unit == '%':
        prefix = '+' if value > 0 else ''
        return f"{prefix}{value:.2f}%"
    else:
        prefix = '+' if value > 0 else ''
        return f"{prefix}{value:.2f}"


def safe_float(val, default=None):
    """安全转换为 float"""
    if val is None or val == '' or (isinstance(val, float) and val != val):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def print_section(title):
    """打印带分隔线的标题"""
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


def save_json(data, filepath):
    """保存数据到 JSON 文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] Saved to {filepath}")


def load_json(filepath):
    """从 JSON 文件读取数据"""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)
