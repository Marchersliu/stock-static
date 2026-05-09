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
import xml.etree.ElementTree as ET

# Tushare
import tushare as ts
import pandas as pd

# 尝试加载 .env 文件（如果存在）
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ.setdefault(key, val)

TOKEN = os.environ.get('TUSHARE_TOKEN', '')
if not TOKEN:
    raise ValueError("TUSHARE_TOKEN environment variable not set")
ts.set_token(TOKEN)
pro = ts.pro_api()

PORT = 8888
WORKSPACE = "/Users/hf/.kimi_openclaw/workspace"
HTML_FILE = os.path.join(WORKSPACE, "dashboard.html")

import requests
import urllib.parse
import re
import concurrent.futures

# akshare（免费数据源，作为 Tushare/新浪的备选）
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
    print("[OK] akshare 已加载")
except ImportError:
    AKSHARE_AVAILABLE = False
    print("[WARN] akshare 未安装，运行: pip3 install akshare")

# ===================== 交易日检测 =====================
TRADING_DAY_CACHE = {'is_open': None, 'date': None}

def is_trading_day():
    """自动检测A股是否交易日，非交易日静默"""
    today = datetime.datetime.now().strftime('%Y%m%d')
    if TRADING_DAY_CACHE['date'] == today and TRADING_DAY_CACHE['is_open'] is not None:
        return TRADING_DAY_CACHE['is_open']
    try:
        df = pro.trade_cal(exchange='SSE', start_date=today, end_date=today)
        if len(df) > 0:
            is_open = bool(df.iloc[0]['is_open'])
            TRADING_DAY_CACHE['date'] = today
            TRADING_DAY_CACHE['is_open'] = is_open
            if not is_open:
                print(f"[休市] {today} 非交易日，服务静默")
            else:
                print(f"[开市] {today} 交易日，正常运作")
            return is_open
    except Exception as e:
        print(f"[WARN] 交易日检测失败: {e}")
    # 默认静默（出错时不推送）
    return False

# ===================== 股票配置 =====================
# 2026-05-09 更新：聚焦7只核心标的（2持仓+5关注）
HOLDINGS = [
    {"code": "688485.SH", "name": "九州一轨", "shares": 19569, "cost": 46.70, "target": "80/100", "stop": 52.0, "hero": True},
    {"code": "002158.SZ", "name": "汉钟精机", "shares": 13100, "cost": 32.00, "target": "35-40", "stop": 28.0, "hero": False},
]

WATCHLIST = [
    {"code": "002364.SZ", "name": "中恒电气", "target": "12-13", "stop": 9.5, "rec": 10.5},
    {"code": "002484.SZ", "name": "江海股份", "target": "48-52", "stop": 38.0, "rec": 43.0},
    {"code": "002439.SZ", "name": "启明星辰", "target": "25-30", "stop": 18.0, "rec": 20.00},
]

MONITOR_STOCKS = HOLDINGS + WATCHLIST
ALL_STOCK_CODES = [s['code'] for s in MONITOR_STOCKS]

# 板块映射（用于板块资金流向监控）
# 2026-05-09 全面梳理：5只核心标的 + 产业链映射
STOCK_SECTORS = {
    '688485.SH': {'sector': '轨交设备', 'sector_code': None, 'related': ['半导体/芯片', 'AI芯片散热', '国产替代']},
    '002158.SZ': {'sector': '通用设备', 'sector_code': None, 'related': ['半导体/芯片', '半导体设备', '国产替代', '数据中心']},
    '002364.SZ': {'sector': 'AI算力·电源', 'sector_code': None, 'related': ['数据中心', '储能', '算电协同', '新能源超充']},
    '002484.SZ': {'sector': 'AI算力·电容', 'sector_code': None, 'related': ['电子元件', '英伟达供应链', '国产替代']},
    '002439.SZ': {'sector': '网络安全', 'sector_code': None, 'related': ['AI安全', '国产替代', '信创']},
}

# ===================== 价格提醒配置 =====================
# 九州一轨价格提醒：达到指定价格时触发iMessage提醒
PRICE_ALERTS = {
    "688485.SH": {
        "name": "九州一轨",
        "alerts": [
            {"price": 57.0, "label": "57", "sent": False, "msg": "🔔 九州一轨 达到 57元！+22%浮盈，半导体概念火热，关注能否继续上冲60目标。建议：观察，不追"},
            {"price": 59.0, "label": "59", "sent": False, "msg": "📈 九州一轨 达到 59元！+26.3%浮盈，接近第一目标60元。建议：准备减仓，锁定利润"},
            {"price": 60.0, "label": "60", "sent": False, "msg": "🎯 九州一轨 达到第一目标 60元！+28.5%浮盈，建议减仓30%（卖7,044股）"},
            {"price": 62.0, "label": "62", "sent": False, "msg": "📈 九州一轨 达到 62元！+32.7%浮盈，突破第一目标区间。建议：继续减仓20%（卖4,696股）"},
            {"price": 65.0, "label": "65", "sent": False, "msg": "🎯🎯 九州一轨 达到第二目标 65元！+39%浮盈，建议再减仓30%（卖7,044股）"},
            {"price": 67.0, "label": "67", "sent": False, "msg": "⚠️ 九州一轨 达到 67元！+43.5%浮盈，超目标区间，建议再减20%（卖4,696股）"},
            {"price": 70.0, "label": "70", "sent": False, "msg": "🚨 九州一轨 达到 70元！+50%浮盈，强烈建议清仓或仅留底仓！半导体炒作过热风险极高"},
        ]
    }
}

ALERT_STATE_FILE = os.path.join(WORKSPACE, "price_alert_state.json")

def load_alert_state():
    """加载已发送提醒的状态"""
    try:
        with open(ALERT_STATE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_alert_state(state):
    """保存提醒状态"""
    with open(ALERT_STATE_FILE, 'w') as f:
        json.dump(state, f, ensure_ascii=False)

def check_price_alerts(stocks_data):
    """检查价格是否达到提醒阈值，写入待发送队列"""
    state = load_alert_state()
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # 重置每日状态（新的一天可以重新提醒）
    if state.get('date') != today:
        state = {'date': today}
    
    pending_alerts = []
    
    for code, cfg in PRICE_ALERTS.items():
        if code not in stocks_data:
            continue
        price = stocks_data[code].get('close', 0)
        if price <= 0:
            continue
            
        for alert in cfg['alerts']:
            key = f"{code}_{alert['label']}"
            if state.get(key):
                continue  # 已发送过
                
            if price >= alert['price']:
                # 价格达到阈值，标记为待发送
                pending_alerts.append({
                    'code': code,
                    'name': cfg['name'],
                    'price': price,
                    'label': alert['label'],
                    'msg': alert['msg'],
                    'key': key
                })
    
    # 写入待发送队列文件
    if pending_alerts:
        queue_file = os.path.join(WORKSPACE, "price_alert_queue.json")
        with open(queue_file, 'w') as f:
            json.dump(pending_alerts, f, ensure_ascii=False)
        print(f"[ALERT] {len(pending_alerts)} 条价格提醒待发送: {[a['label'] for a in pending_alerts]}")
    
    return pending_alerts

def mark_alert_sent(key):
    """标记提醒已发送"""
    state = load_alert_state()
    state[key] = True
    save_alert_state(state)

# ===================== 持仓股/计划标的关键词池（新闻关联分析用）=====================
# 2026-05-09 更新：聚焦7只核心标的
STOCK_KEYWORDS = {
    # 持仓股
    '688485.SH': {
        'name': '九州一轨',
        'keywords': ['九州一轨', '688485', '轨交', '轨道交通', '减振', '降噪', '半导体', '晶禧', '并购', '收购', '金刚石'],
        'industry': ['轨交设备', '半导体'],
        'level': 'hero'
    },
    '002158.SZ': {
        'name': '汉钟精机',
        'keywords': ['汉钟精机', '汉钟', '002158', '压缩机', '真空泵', '制冷', '数据中心', '半导体', '磁悬浮', 'SEMI', '液冷'],
        'industry': ['通用设备', '半导体设备'],
        'level': 'holding'
    },
    # 关注股（前5只）
    '002364.SZ': {
        'name': '中恒电气',
        'keywords': ['中恒电气', '002364', '中恒', 'HVDC', '高压直流', '算电协同', '数据中心电源', '储能', '超充', '宁德时代', '英伟达电源'],
        'industry': ['电源设备', '储能', '数据中心'],
        'level': 'watchlist'
    },
    '002484.SZ': {
        'name': '江海股份',
        'keywords': ['江海股份', '002484', '江海', '超级电容', 'MLPC', '固态电容', 'GB300', '英伟达电容', 'Cerebus', '服务器电容'],
        'industry': ['电子元件', '半导体材料'],
        'level': 'watchlist'
    },
    '002439.SZ': {
        'name': '启明星辰',
        'keywords': ['启明星辰', '002439', '启明', '网络安全', '信息安全', 'AI安全', '数据安全', '中国移动', '国资云'],
        'industry': ['网络安全', 'AI安全'],
        'level': 'watchlist'
    },
}

# 通用行业关键词（当新闻标题含这些词时，标记为行业关联）
# 2026-05-09 精简：只保留前5只核心标的相关行业
INDUSTRY_KEYWORDS = {
    '新能源': ['新能源', '锂电', '电动车', '动力电池', '储能', '光伏', '风电', '氢能'],
    '半导体': ['半导体', '芯片', '晶圆', '光刻', 'IC', '集成电路', 'EDA', '先进制程'],
    'AI算力': ['AI', '人工智能', '算力', '数据中心', '光模块', '英伟达', 'NVIDIA', 'Blackwell', 'GB300', '液冷', '服务器', '推理', 'Agentic AI', 'HVDC', '高压直流'],
    '国产替代': ['国产替代', '自主可控', '卡脖子', '制裁', '管制', '脱钩', '华为', '海思', '鸿蒙'],
    '有色': ['铝', '铜', '镍', '钴', '锂', '稀土', '钨', '钼', '锌', '锡', '锑', '有色'],
    '化工': ['化工', '烯烃', '甲醇', '尿素', 'PVC', 'MDI', '钛白粉', '醋酸'],
    '医药': ['医药', '创新药', '仿制药', '集采', 'CXO', '医疗器械', '生物药'],
    '金融': ['银行', '保险', '券商', 'LPR', '降准', '降息', '信贷', '社融', 'M2'],
    '能源': ['核电', '水电', '火电', '煤炭', '天然气', '石油', '原油', '页岩油'],
    '基建': ['轨交', '高铁', '铁路', '地铁', '轨道交通', '新基建', '设备更新'],
    '消费': ['白酒', '啤酒', '食品', '家电', '汽车', '零售', '旅游'],
    '科技': ['AI', '人工智能', '算力', '数据中心', '光模块', '机器人', '具身智能'],
    '原材料': ['纸浆', '造纸', '木材', '棉花', '白糖', '大豆', '玉米'],
    '电子材料': ['电子布', '玻纤', 'PCB', '低介电', '基材', '覆铜板', 'CCL'],
    '功率半导体': ['SiC', '碳化硅', 'MOSFET', 'IGBT', '功率器件', '第三代半导体'],
}

# ===================== 新闻关联分析 =====================
def analyze_news_relevance(item):
    """
    分析单条新闻与持仓股/计划标的的关联度。
    返回 (related_stocks, relevance_level, reason)
    - related_stocks: 关联的股票代码列表
    - relevance_level: 'direct'(直接提及) / 'industry'(行业关联) / 'none'
    - reason: 关联原因描述
    """
    title = item.get('title', '')
    summary = item.get('summary', '') or item.get('content', '')
    text = title + ' ' + summary
    
    related = []
    reasons = []
    
    # 1. 直接匹配：股票名或代码出现在新闻中
    for code, info in STOCK_KEYWORDS.items():
        for kw in info['keywords']:
            if kw in text:
                related.append(code)
                reasons.append(f"提及{info['name']}({kw})")
                break
    
    # 2. 行业关联：新闻含行业关键词，且该行业对应某持仓股
    if not related:
        for industry, kws in INDUSTRY_KEYWORDS.items():
            for kw in kws:
                if kw in text:
                    # 找到该行业对应的持仓股
                    for code, info in STOCK_KEYWORDS.items():
                        if industry in info['industry'] or kw in info['keywords']:
                            if code not in related:
                                related.append(code)
                                reasons.append(f"行业关联:{industry}")
                    break
    
    # 去重
    related = list(dict.fromkeys(related))
    
    if related:
        # 判断关联级别
        has_direct = any(
            any(kw in text for kw in STOCK_KEYWORDS[c]['keywords'][:3])  # 前3个关键词含股票名/代码
            for c in related
        )
        level = 'direct' if has_direct else 'industry'
        return related, level, '；'.join(reasons[:3])
    
    return [], 'none', ''


def mark_news_relevance(items):
    """为新闻列表批量标记关联度 + 多分类标签"""
    for item in items:
        related, level, reason = analyze_news_relevance(item)
        item['related_stocks'] = related
        item['relevance_level'] = level
        item['relevance_reason'] = reason
        item['relevance_score'] = {'direct': 3, 'industry': 2, 'none': 0}.get(level, 0)
        # 多分类标签
        title = item.get('title', '')
        content = item.get('content', '') or item.get('summary', '')
        item['catTags'] = classify_multi_tags(title, content)
        # 生成前端展示的关联标签
        if related:
            tags = []
            for code in related:
                info = STOCK_KEYWORDS.get(code, {})
                level_badge = '⭐' if info.get('level') == 'hero' else ('🔵' if info.get('level') == 'holding' else '⚪')
                tags.append(f"{level_badge}{info.get('name', code)}")
            item['stock_tags'] = tags
        else:
            item['stock_tags'] = []
    return items


# ===================== Tushare 新闻抓取（已购买新闻权限，无限制）=====================
# 新闻策略优先级：
# 1. Tushare news/major_news/cctv_news（已购买权限，每分钟400次，主力）
# 2. kimi_search（网页搜索，降级替代方案）
# 3. RSS（人民网、中国新闻网，辅助）
# 4. Brave Search API（Token已配置但国内网络暂不可用，待后续验证）
# 2026-05-03 HF已购买 Tushare Pro 新闻资讯独立权限（1000元/年）
# 文档：https://tushare.pro/document/2?doc_id=143
# 权限：每分钟400次，总量不限
# 现状（三个板块全部可用）：
# - news 接口（长篇新闻）：9来源全覆盖，单次最大1500条，字段 datetime/content/title
# - major_news 接口（快讯）：财联社/新浪财经/华尔街见闻/同花顺等，字段 pub_time/title/url
# - cctv_news 接口（新闻联播）：字段 date/title/content
# 
# 策略：
# 1. 1小时缓存：减少重复API调用（性能优化，非频率限制）
# 2. news 接口为主力：9个来源全部抓取
# 3. major_news 补充：4个来源快讯补充
# 4. cctv_news 补充：官方新闻联播文字稿（政策权威来源）
# 5. 无频次计数器：已购买权限，无需限制

TUSHARE_NEWS_CACHE = {
    'data': None,
    'timestamp': None,
}

def fetch_tushare_all_news(max_per_source=10):
    """
    已购买新闻权限版：
    - news 接口（快讯）：9来源全抓，单次1500条
    - major_news（长篇）：4来源补充
    - 1小时缓存作为性能优化
    """
    # 检查缓存
    now = datetime.datetime.now()
    if TUSHARE_NEWS_CACHE['timestamp'] and TUSHARE_NEWS_CACHE['data']:
        cache_age = (now - TUSHARE_NEWS_CACHE['timestamp']).total_seconds()
        if cache_age < 3600:  # 1小时缓存
            print(f"[CACHE] Tushare新闻缓存命中，{int(cache_age)}秒前更新")
            return TUSHARE_NEWS_CACHE['data']
    
    items = []
    today = now.strftime('%Y-%m-%d')
    start_dt = f"{today} 00:00:00"
    end_dt = f"{today} 23:59:59"
    
    # ========== 主力：news 接口（9来源快讯）==========
    news_sources = {
        'sina': {'name': '新浪财经', 'sourceClass': 'sina', 'defaultCat': 'finance'},
        'wallstreetcn': {'name': '华尔街见闻', 'sourceClass': 'wscn', 'defaultCat': 'finance'},
        '10jqka': {'name': '同花顺', 'sourceClass': 'ths', 'defaultCat': 'finance'},
        'eastmoney': {'name': '东方财富', 'sourceClass': 'eastmoney', 'defaultCat': 'finance'},
        'yuncaijing': {'name': '云财经', 'sourceClass': 'yuncaijing', 'defaultCat': 'finance'},
        'fenghuang': {'name': '凤凰新闻', 'sourceClass': 'fenghuang', 'defaultCat': 'finance'},
        'jinrongjie': {'name': '金融界', 'sourceClass': 'jinrongjie', 'defaultCat': 'finance'},
        'cls': {'name': '财联社', 'sourceClass': 'cls', 'defaultCat': 'company'},
        'yicai': {'name': '第一财经', 'sourceClass': 'yicai', 'defaultCat': 'finance'},
    }
    
    for src_id, cfg in news_sources.items():
        try:
            df = pro.news(src=src_id, start_date=start_dt, end_date=end_dt, limit=max_per_source)
            if df is None or df.empty:
                continue
            for _, row in df.iterrows():
                title = str(row.get('title', '')).strip()
                content = str(row.get('content', '')).strip()
                # 如果 title 为空，用 content 前50字
                if not title and content:
                    title = content[:50]
                dt = str(row.get('datetime', '')).strip()
                if not title:
                    continue
                date_str = dt[:10] if dt else today
                time_str = dt[11:16] if dt and len(dt) >= 16 else ''
                cat = classify_event(title + ' ' + content)
                if cat == 'company':
                    cat = cfg['defaultCat']
                # Tushare news接口不提供原始url，构建来源站搜索链接
                # 财联社 → use cls.cn search, 新浪财经 → sina search, etc.
                src_url_map = {
                    'sina': f'https://search.sina.com.cn/?q={urllib.parse.quote(title)}&c=news',
                    'wallstreetcn': f'https://wallstreetcn.com/search?q={urllib.parse.quote(title)}',
                    '10jqka': f'https://www.10jqka.com.cn/stockpage/search/?keyword={urllib.parse.quote(title)}',
                    'eastmoney': f'https://search.eastmoney.com/search/web?q={urllib.parse.quote(title)}',
                    'yuncaijing': f'https://www.yuncaijing.com/search?keyword={urllib.parse.quote(title)}',
                    'fenghuang': f'https://search.ifeng.com/sofeng/search.action?c=1&q={urllib.parse.quote(title)}',
                    'jinrongjie': f'https://search.jrj.com.cn/search?keyword={urllib.parse.quote(title)}',
                    'cls': f'https://www.cls.cn/searchPage?keyword={urllib.parse.quote(title)}',
                    'yicai': f'https://www.yicai.com.cn/search?keys={urllib.parse.quote(title)}',
                }
                fallback_url = src_url_map.get(src_id, f'https://www.baidu.com/s?wd={urllib.parse.quote(title)}')
                items.append({
                    'date': date_str,
                    'time': time_str,
                    'title': title,
                    'url': fallback_url,
                    'category': cat,
                    'source': f'Tushare·{cfg["name"]}',
                    'sourceClass': cfg['sourceClass'],
                })
            print(f"[OK] Tushare·{cfg['name']}(news): {len(df)} 条")
        except Exception as e:
            err = str(e)
            if '频率' in err or '超限' in err:
                print(f"[WARN] Tushare·{cfg['name']}: 频率限制")
            elif '权限' in err:
                print(f"[ERR] Tushare·{cfg['name']}: 无权限")
            else:
                print(f"[ERR] Tushare·{cfg['name']}: {err[:80]}")
    
    # ========== 补充：major_news（4来源长篇新闻）==========
    major_sources = {
        '财联社': {'sourceClass': 'cls', 'defaultCat': 'company'},
        '新浪财经': {'sourceClass': 'sina', 'defaultCat': 'finance'},
        '华尔街见闻': {'sourceClass': 'wscn', 'defaultCat': 'finance'},
        '同花顺': {'sourceClass': 'ths', 'defaultCat': 'finance'},
    }
    
    for src_name, cfg in major_sources.items():
        try:
            df = pro.major_news(src=src_name, start_date=start_dt, end_date=end_dt, limit=max_per_source)
            if df is None or df.empty:
                continue
            for _, row in df.iterrows():
                title = str(row.get('title', '')).strip()
                pub_time = str(row.get('pub_time', '')).strip()
                url = str(row.get('url', '')).strip()
                if not title:
                    continue
                date_str = pub_time[:10] if pub_time else today
                time_str = pub_time[11:16] if pub_time and len(pub_time) >= 16 else ''
                cat = classify_event(title)
                if cat == 'company':
                    cat = cfg['defaultCat']
                items.append({
                    'date': date_str,
                    'time': time_str,
                    'title': title,
                    'url': url or f'https://search.eastmoney.com/search/web?q={urllib.parse.quote(title)}',
                    'category': cat,
                    'source': f'Tushare·{src_name}',
                    'sourceClass': cfg['sourceClass'],
                })
            print(f"[OK] Tushare·{src_name}(major): {len(df)} 条")
        except Exception as e:
            err = str(e)
            if '频率' in err or '超限' in err:
                print(f"[WARN] Tushare·{src_name}(major): 频率限制")
            elif '权限' in err:
                print(f"[ERR] Tushare·{src_name}(major): 无权限")
            else:
                print(f"[ERR] Tushare·{src_name}(major): {err[:80]}")
    
    # ========== 补充：cctv_news（新闻联播文字稿）==========
    try:
        yesterday = (now - datetime.timedelta(days=1)).strftime('%Y%m%d')
        today_ymd = now.strftime('%Y%m%d')
        # 抓取昨天+今天的新闻联播
        for cctv_date in [yesterday, today_ymd]:
            try:
                df = pro.cctv_news(date=cctv_date)
                if df is None or df.empty:
                    continue
                for _, row in df.iterrows():
                    title = str(row.get('title', '')).strip()
                    content = str(row.get('content', '')).strip()
                    if not title:
                        continue
                    # 新闻联播内容通常很长，摘要取前80字
                    summary = content[:80] + '...' if len(content) > 80 else content
                    # 新闻联播归类为政策
                    cat = classify_event(title + ' ' + content)
                    if cat not in ['policy', 'finance', 'material']:
                        cat = 'policy'
                    date_str = f"{cctv_date[:4]}-{cctv_date[4:6]}-{cctv_date[6:]}"
                    items.append({
                        'date': date_str,
                        'time': '19:00',
                        'title': f'[新闻联播] {title}',
                        'url': '',
                        'category': cat,
                        'source': 'Tushare·新闻联播',
                        'sourceClass': 'cctv',
                        'content': summary,
                    })
                print(f"[OK] Tushare·新闻联播(cctv): {len(df)} 条 ({cctv_date})")
            except Exception as e:
                print(f"[ERR] Tushare·新闻联播({cctv_date}): {e[:80]}")
    except Exception as e:
        print(f"[ERR] Tushare·新闻联播: {e[:80]}")
    
    # 写入缓存
    TUSHARE_NEWS_CACHE['data'] = items
    TUSHARE_NEWS_CACHE['timestamp'] = now
    
    return items


# ===================== 新浪个股新闻抓取 =====================
SINA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def ts_code_to_sina_symbol(ts_code):
    """688485.SH -> sh688485, 002158.SZ -> sz002158"""
    code, market = ts_code.split('.')
    return f'sh{code}' if market == 'SH' else f'sz{code}'

def classify_event(title):
    """根据标题自动分类"""
    t = title.lower()
    policy_kw = ['降准', '降息', '央行', '政治局', '证监会', '国务院', '财政部', '外汇局', '监管', '改革', '制度']
    finance_kw = ['利率', '非农', '就业', 'PMI', 'CPI', 'GDP', '港股', '美股', 'A股', '沪指', '深成指', '创业板', '恒指', '纳指', '标普']
    material_kw = ['镍', '钴', '锂', '铝', '铜', '钢', '煤', '油', '天然气', '硫磺', '碳酸锂', '氧化铝', '氢氧化锂', '电解镍', '原油', 'WTI', '布伦特', 'LME', '期货', '现货', '原料', '材料']
    if any(k in t for k in policy_kw):
        return 'policy'
    if any(k in t for k in finance_kw):
        return 'finance'
    if any(k in t for k in material_kw):
        return 'material'
    return 'company'

def classify_multi_tags(title, content=''):
    """
    给新闻打多个分类标签。
    返回标签列表，每条新闻可同时属于多个分类。
    标签: portfolio(持仓直击), chain(产业链), policy(政策宏观), geo(地缘国际), market(市场资金)
    """
    t = (title + ' ' + content).lower()
    tags = []
    
    # 1. 持仓直击：标题含持仓/建仓股名或代码
    portfolio_kw = [
        '九州一轨', '688485', '红星发展', '600367', '禾望电气', '603063',
        '汉钟精机', '002158', '鑫磊股份', '301317', '宝丰能源', '600989',
        '招商银行', '600036', '长江电力', '600900', '中国核电', '601985',
        'ST利达', '603828', '通源环境', '688679', '华蓝集团', '301027',
        '腾亚精工', '301125',
    ]
    if any(k in t for k in portfolio_kw):
        tags.append('portfolio')
    
    # 2. 产业链：原材料、行业上下游
    chain_kw = [
        '碳酸锂', '氢氧化锂', '钴', '镍', '铝', '铜', '锶', '锰', '电解锰',
        '氧化铝', '电解铝', '铝锭', '铝价', '纸浆', '文化纸', '白卡纸',
        '甲醇', '聚烯烃', '煤化工', '煤制烯烃', '电气设备', '变流器',
        '风电', '光伏', '储能', '核电', '水电', '大坝', '核燃料', '铀',
        '轨交', '高铁', '铁路', '地铁', '轨道交通', '减震', '降噪',
        '创新药', '大输液', '抗生素', 'adc药物', '仿制药', '原料药',
        '压缩机', '风机', '水泵', '真空泵',
        'wti', '布伦特', '原油', 'opec', 'lme', '期货', '现货',
    ]
    if any(k in t for k in chain_kw):
        tags.append('chain')
    
    # 3. 政策宏观：央行、财政、监管
    policy_kw = [
        '降准', '降息', '央行', '政治局', '证监会', '国务院', '财政部',
        '外汇局', '监管', '改革', '制度', 'lpr', 'mlf', '逆回购',
        '社融', 'm2', 'cpi', 'ppi', 'pmi', 'gdp', '财政', '货币政策',
    ]
    if any(k in t for k in policy_kw):
        tags.append('policy')
    
    # 4. 地缘国际：战争、制裁、中美、原油、黄金
    geo_kw = [
        '伊朗', '以色列', '加沙', '黎巴嫩', '真主党', '哈马斯', '巴以',
        '也门', '胡塞', '红海', '曼德海峡', '霍尔木兹', '沙特', '海湾',
        '朝鲜', '金正恩', '朝鲜半岛', '韩朝', '朝核',
        '俄罗斯', '俄乌', '乌克兰', '北约', '欧盟', '欧洲',
        '特朗普', '拜登', '美国', '中美', '美中', '台海', '台湾', '赖清德',
        '菲律宾', '南海', '越南', '印度', '印巴', '克什米尔', '巴基斯坦',
        '关税', '贸易战', '制裁', '禁运', '脱钩', '供应链',
        '中东', '叙利亚', '伊拉克', '阿富汗', '土耳其', '埃尔多安',
        '石油', '原油', '黄金', '白银', '避险',
        '冲突', '战争', '军事', '导弹', '核', '空袭', '轰炸', '停火', '维和',
    ]
    if any(k in t for k in geo_kw):
        tags.append('geo')
    
    # 5. 市场资金：大盘、板块、主力、IPO
    market_kw = [
        'a股', '沪指', '深成指', '创业板', '科创板', '北交所',
        '涨停', '跌停', '大涨', '大跌', '暴跌', '飙升',
        '主力资金', '北向资金', '南向资金', '外资', '机构',
        'ipo', '上市', '退市', '停牌', '复牌', '并购',
        '财报', '年报', '季报', '业绩预告', '营收', '净利润',
        '分红', '股息', '增持', '减持', '回购',
        '牛市', '熊市', '反弹', '回调',
        '板块', '概念股', '龙头股', '妖股',
        '股价', '市盈率', '市净率', '估值',
        '港股', '美股', '恒指', '纳指', '标普',
    ]
    if any(k in t for k in market_kw):
        tags.append('market')
    
    # 兜底：如果没有打到任何标签，给 market（最宽泛）
    if not tags:
        tags.append('market')
    
    return tags


def fetch_sina_stock_news(ts_code, max_items=8):
    """从新浪财经抓取个股最新新闻"""
    symbol = ts_code_to_sina_symbol(ts_code)
    url = f'http://vip.stock.finance.sina.com.cn/corp/go.php/vCB_AllNewsStock/symbol/{symbol}.phtml'
    try:
        resp = requests.get(url, headers=SINA_HEADERS, timeout=5)
        resp.encoding = 'gbk'
        text = resp.text.replace('&nbsp;', ' ')
        
        # Extract date, time, url, title
        pattern = r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s+<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.+?)</a>'
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        results = []
        for m in matches[:max_items]:
            date, time_str, href, title = m
            title = re.sub(r'<[^>]+>', '', title).strip()
            if not title:
                continue
            # Fix relative URLs
            if href.startswith('/'):
                href = f'http://vip.stock.finance.sina.com.cn{href}'
            elif href and not href.startswith('http'):
                href = f'http://vip.stock.finance.sina.com.cn/corp/go.php/{href}'
            
            results.append({
                'date': date,
                'time': time_str,
                'title': title,
                'url': href,
                'code': ts_code,
                'category': classify_event(title),
                'source': '新浪财经',
                'sourceClass': 'sina'
            })
        return results
    except Exception as e:
        print(f"[WARN] fetch_sina_stock_news {ts_code} failed: {e}")
        return []


# ===================== 巨潮资讯公告抓取 =====================
def fetch_cninfo_announcements(ts_code, page_size=5):
    """从巨潮资讯抓取公司公告"""
    try:
        code = ts_code.split('.')[0]
        # 根据交易所确定 column
        if ts_code.endswith('.SH'):
            column = 'sse'
            plate = 'sh'
        elif ts_code.endswith('.SZ'):
            column = 'szse'
            plate = 'sz'
        else:
            column = 'bjse'
            plate = 'bj'
        
        url = 'https://www.cninfo.com.cn/new/hisAnnouncement/query'
        payload = {
            'pageNum': 1,
            'pageSize': page_size,
            'tabName': 'fulltext',
            'column': column,
            'stock': f'{code},{plate}{code}',
            'searchkey': '',
            'secids': '',
            'sortType': '',
            'sortName': '',
            'limit': page_size
        }
        resp = requests.post(url, data=payload, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        data = resp.json()
        announcements = data.get('announcements', []) or []
        
        results = []
        for ann in announcements[:page_size]:
            title = ann.get('announcementTitle', '')
            time_str = ann.get('announcementTime', '')
            # 解析时间
            if time_str:
                try:
                    dt = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                    date = dt.strftime('%Y-%m-%d')
                    time_only = dt.strftime('%H:%M')
                except:
                    date = time_str[:10]
                    time_only = ''
            else:
                date = datetime.datetime.now().strftime('%Y-%m-%d')
                time_only = ''
            
            # 分类
            cat = 'company'
            if any(k in title for k in ['重组', '收购', '并购', '合并']):
                cat = 'company'
            elif any(k in title for k in ['年报', '季报', '半年报', '业绩', '净利润']):
                cat = 'finance'
            
            adj_url = ann.get('adjunctUrl', '')
            url_full = f'https://www.cninfo.com.cn/new/disclosure/detail?plate={plate}&stockCode={code}&announcementId={ann.get("announcementId", "")}&announcementTime={date}' if not adj_url else f'https://static.cninfo.com.cn/{adj_url}'
            
            results.append({
                'date': date,
                'time': time_only,
                'title': title,
                'url': url_full,
                'code': ts_code,
                'category': cat,
                'source': '巨潮资讯',
                'sourceClass': 'cninfo'
            })
        print(f"[OK] 巨潮资讯 {ts_code}: {len(results)} 条公告")
        return results
    except Exception as e:
        print(f"[ERR] 巨潮资讯 {ts_code}: {e}")
        return []


# ===================== 东方财富新闻抓取 =====================
def fetch_eastmoney_news(ts_code, max_items=3):
    """从东方财富抓取个股新闻"""
    try:
        code_pure = ts_code.split('.')[0]
        # 使用搜索API获取InnerCode后查新闻
        url = f'https://searchapi.eastmoney.com/api/suggest/get?input={code_pure}&type=14&count=1'
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        data = resp.json()
        
        inner_code = None
        if data and isinstance(data, dict):
            qt = data.get('QuotationCodeTable', {})
            if isinstance(qt, dict):
                data_list = qt.get('Data', [])
                if data_list and len(data_list) > 0:
                    inner_code = data_list[0].get('InnerCode')
        
        if inner_code:
            guba_url = f'https://searchapi.eastmoney.com/api/bksearch/web/getesbnews?keyword={code_pure}&pageindex=1&pagesize={max_items}'
            resp2 = requests.get(guba_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            if resp2.status_code == 200:
                news_data = resp2.json()
                if news_data and isinstance(news_data, dict):
                    news_list = news_data.get('Data', [])
                    results = []
                    for n in news_list[:max_items]:
                        title = n.get('Title', '')
                        time_str = n.get('ShowTime', '')
                        if time_str:
                            try:
                                dt = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                                date = dt.strftime('%Y-%m-%d')
                                time_only = dt.strftime('%H:%M')
                            except:
                                date = time_str[:10]
                                time_only = ''
                        else:
                            date = datetime.datetime.now().strftime('%Y-%m-%d')
                            time_only = ''
                        
                        content = n.get('Content', '')
                        content_text = re.sub(r'<[^>]+>', '', content).strip()[:200]
                        
                        results.append({
                            'date': date,
                            'time': time_only,
                            'title': title,
                            'summary': content_text,
                            'url': n.get('Url', ''),
                            'code': ts_code,
                            'category': classify_event(title),
                            'source': '东方财富',
                            'sourceClass': 'eastmoney'
                        })
                    print(f"[OK] 东方财富 {ts_code}: {len(results)} 条")
                    return results
        print(f"[OK] 东方财富 {ts_code}: 0 条")
        return []
    except Exception as e:
        print(f"[ERR] 东方财富 {ts_code}: {e}")
        return []


# ===================== 政策/宏观新闻抓取 =====================
def fetch_policy_news():
    """抓取央行、财政部、商务部等宏观政策新闻"""
    items = []
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # 1. 央行新闻
    try:
        url = 'http://www.pbc.gov.cn/goutongjiaoliu/113456/113469/index.html'
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        if resp.status_code == 200:
            titles = re.findall(r'<a[^>]*>([^<]{10,60})</a>', resp.text)
            for t in titles[:5]:
                if any(k in t for k in ['降准', '降息', '利率', 'MLF', 'LPR', '货币政策', '流动性']):
                    items.append({
                        'date': today,
                        'time': '',
                        'title': t,
                        'url': 'http://www.pbc.gov.cn/zhengcehuobisi/11140/index.html',
                        'category': 'policy',
                        'source': '央行',
                        'sourceClass': 'pbc'
                    })
            print(f"[OK] 央行政策: {len(items)} 条")
    except Exception as e:
        print(f"[ERR] 央行政策: {e}")
    
    # 2. 财政部新闻
    try:
        url = 'http://www.mof.gov.cn/zhengwuxinxi/zhengcefabu/'
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        if resp.status_code == 200:
            titles = re.findall(r'<a[^>]*>([^<]{10,80})</a>', resp.text)
            for t in titles[:3]:
                if any(k in t for k in ['财政', '税收', '预算', '国债', '专项债', '减税']):
                    items.append({
                        'date': today,
                        'time': '',
                        'title': t,
                        'url': 'http://www.mof.gov.cn/zhengwuxinxi/zhengcefabu/',
                        'category': 'policy',
                        'source': '财政部',
                        'sourceClass': 'pbc'
                    })
            print(f"[OK] 财政部: {len([i for i in items if i['source']=='财政部'])} 条")
    except Exception as e:
        print(f"[ERR] 财政部: {e}")
    
    return items


# ===================== RSS 新闻抓取 =====================
def fetch_people_rss(max_items=8):
    """抓取人民网时政要闻 RSS"""
    try:
        url = 'http://www.people.com.cn/rss/politics.xml'
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        root = ET.fromstring(resp.text)
        items = []
        for item in root.findall('.//item')[:max_items]:
            title = item.findtext('title', '')
            pub = item.findtext('pubDate', '')
            link = item.findtext('link', '')
            # 解析日期
            if pub:
                try:
                    dt = datetime.datetime.strptime(pub, '%a, %d %b %Y %H:%M:%S %z')
                    date = dt.strftime('%Y-%m-%d')
                    time_only = dt.strftime('%H:%M')
                except:
                    date = pub[:10]
                    time_only = ''
            else:
                date = datetime.datetime.now().strftime('%Y-%m-%d')
                time_only = ''
            
            items.append({
                'date': date,
                'time': time_only,
                'title': title,
                'url': link,
                'category': 'policy',
                'source': '人民网',
                'sourceClass': 'people'
            })
        print(f"[OK] 人民网RSS: {len(items)} 条")
        return items
    except Exception as e:
        print(f"[ERR] 人民网RSS: {e}")
        return []


def fetch_huanqiu_rss(max_items=8):
    """抓取中国新闻网即时新闻 RSS（替代失效的环球时报）"""
    try:
        url = 'http://www.chinanews.com.cn/rss/scroll-news.xml'
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        root = ET.fromstring(resp.content)  # 用 content 避免编码问题
        items = []
        for item in root.findall('.//item')[:max_items]:
            title = item.findtext('title', '')
            pub = item.findtext('pubDate', '')
            link = item.findtext('link', '')
            if pub:
                try:
                    dt = datetime.datetime.strptime(pub, '%a, %d %b %Y %H:%M:%S %z')
                    date = dt.strftime('%Y-%m-%d')
                    time_only = dt.strftime('%H:%M')
                except:
                    date = pub[:10]
                    time_only = ''
            else:
                date = datetime.datetime.now().strftime('%Y-%m-%d')
                time_only = ''
            
            items.append({
                'date': date,
                'time': time_only,
                'title': title,
                'url': link,
                'category': 'policy',
                'source': '中国新闻网',
                'sourceClass': 'chinanews'
            })
        print(f"[OK] 中国新闻网RSS: {len(items)} 条")
        return items
    except Exception as e:
        print(f"[ERR] 中国新闻网RSS: {e}")
        return []


# ===================== 统一盘前新闻候选抓取 =====================
# 候选池结果缓存（10分钟），避免每次API调用都重新抓取
PREMARKET_CACHE = {
    'data': None,
    'timestamp': None,
}

NEWS_SOURCE_STATUS = {
    '新浪财经': '✅ 已接入',
    '巨潮资讯': '✅ 已接入',
    '东方财富': '✅ 已接入',
    '央行/财政部': '✅ 已接入',
    '人民网': '✅ 已接入',
    '环球时报': '❌ 已失效，替换为中国新闻网RSS',
    'Tushare·财联社': '✅ 已接入',
    'Tushare·新浪财经': '✅ 已接入',
    'Tushare·华尔街见闻': '✅ 已接入',
    'Tushare·同花顺': '✅ 已接入',
    'Tushare·东方财富': '✅ 已接入',
    'Tushare·云财经': '✅ 已接入',
    'Tushare·凤凰新闻': '✅ 已接入',
    'Tushare·金融界': '✅ 已接入',
    'Tushare·第一财经': '✅ 已接入',
    'Tushare·新闻联播': '✅ 已接入',
    '金十数据': '⏳ 待接入（反爬）',
    '雪球': '⏳ 待接入（需认证）',
    '路透社': '⏳ 待接入（付费墙）',
    '彭博社': '⏳ 待接入（付费墙）',
}

# ===================== 交易日判断与盘中缓存策略 =====================
_TRADE_CAL_CACHE = {'date': None, 'is_open': False}

def _is_trade_day():
    """查Tushare trade_cal判断今天是否开市（缓存一天）"""
    global _TRADE_CAL_CACHE
    today = datetime.datetime.now().strftime('%Y%m%d')
    if _TRADE_CAL_CACHE['date'] == today:
        return _TRADE_CAL_CACHE['is_open']
    try:
        df = pro.trade_cal(exchange='SSE', start_date=today, end_date=today)
        is_open = bool(df[df['is_open'] == 1].shape[0] > 0)
        _TRADE_CAL_CACHE = {'date': today, 'is_open': is_open}
        return is_open
    except Exception as e:
        print(f"[WARN] trade_cal查询失败: {e}")
        # 降级：周末休市，其他默认开市
        weekday = datetime.datetime.now().weekday()
        is_open = weekday < 5
        _TRADE_CAL_CACHE = {'date': today, 'is_open': is_open}
        return is_open

def is_trading_time():
    """
    判断当前是否在盘中时段（交易日 9:15-15:30）。
    用于决定缓存时长：盘中2分钟，休市10分钟。
    """
    # 先查是否交易日（考虑法定节假日）
    if not _is_trade_day():
        return False
    now = datetime.datetime.now()
    hour, minute = now.hour, now.minute
    start = 9 * 60 + 15   # 9:15
    end = 15 * 60 + 30    # 15:30
    current = hour * 60 + minute
    return start <= current <= end

def get_cache_ttl():
    """返回当前时段的缓存秒数：盘中2分钟，休市10分钟"""
    return 120 if is_trading_time() else 600


def fetch_premarket_candidates():
    """
    抓取盘前新闻候选池。
    聚合多来源新闻（持仓股+建仓股+宏观政策），去重+分类+排序+关联分析。
    结果缓存10分钟，避免重复慢请求。
    """
    # 检查缓存（盘中2分钟，休市10分钟）
    now = datetime.datetime.now()
    ttl = get_cache_ttl()
    if PREMARKET_CACHE['timestamp'] and PREMARKET_CACHE['data']:
        cache_age = (now - PREMARKET_CACHE['timestamp']).total_seconds()
        if cache_age < ttl:
            print(f"[CACHE] 候选池缓存命中，{int(cache_age)}秒前更新（盘中2min/休市10min）")
            return PREMARKET_CACHE['data']
    
    all_items = []
    source_counts = {}
    
    # 持仓股 + 关注股 统一抓取
    all_stocks = HOLDINGS + WATCHLIST
    
    def fetch_one_stock(stock):
        """抓取单只股票的2个来源新闻（精简版）"""
        items_local = []
        counts_local = {}
        
        # 只抓新浪财经，减少超时
        try:
            sina_items = fetch_sina_stock_news(stock['code'], max_items=3)
            for item in sina_items:
                item['stock_name'] = stock['name']
                item['stock_code'] = stock['code']
            items_local.extend(sina_items)
            counts_local['新浪财经'] = len(sina_items)
        except Exception as e:
            print(f"[WARN] 新浪财经 {stock['code']}: {e}")
        
        # 巨潮资讯公告（快速，不超时）
        try:
            cninfo_items = fetch_cninfo_announcements(stock['code'], page_size=3)
            for item in cninfo_items:
                item['stock_name'] = stock['name']
                item['stock_code'] = stock['code']
            items_local.extend(cninfo_items)
            counts_local['巨潮资讯'] = len(cninfo_items)
        except Exception as e:
            print(f"[WARN] 巨潮资讯 {stock['code']}: {e}")
        
        return items_local, counts_local
    
    # 并行抓取13只股票（最多6线程）
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(fetch_one_stock, s): s for s in all_stocks}
        for future in concurrent.futures.as_completed(futures):
            items_local, counts_local = future.result()
            all_items.extend(items_local)
            for src, cnt in counts_local.items():
                source_counts[src] = source_counts.get(src, 0) + cnt
    
    # ⚠️ 政策/RSS/Tushare 新闻抓取已禁用（API超时问题），仅保留持仓股新闻
    # 如需恢复，需给每个函数加 timeout 参数
    #
    # 政策/宏观新闻（已禁用）
    # try:
    #     policy_items = fetch_policy_news()
    #     all_items.extend(policy_items)
    # except Exception as e:
    #     print(f"[WARN] fetch_policy_news: {e}")
    
    # RSS时政/国际新闻（已禁用）
    # try:
    #     people_items = fetch_people_rss(max_items=8)
    #     all_items.extend(people_items)
    # except Exception as e:
    #     print(f"[WARN] fetch_people_rss: {e}")
    #
    # try:
    #     huanqiu_items = fetch_huanqiu_rss(max_items=8)
    #     all_items.extend(huanqiu_items)
    # except Exception as e:
    #     print(f"[WARN] fetch_huanqiu_rss: {e}")
    
    # Tushare 全来源新闻（精简版，只抓20条，加超时）
    try:
        tushare_items = fetch_tushare_all_news(max_per_source=3)
        all_items.extend(tushare_items)
        for item in tushare_items:
            src = item.get('source', 'Tushare')
            source_counts[src] = source_counts.get(src, 0) + 1
        print(f"[OK] Tushare新闻: {len(tushare_items)} 条")
    except Exception as e:
        print(f"[WARN] fetch_tushare_all_news: {e}")
    
    # ===================== 财经相关性过滤 =====================
    # 策略：只保留与用户股票池真正相关的新闻，过滤掉社会/娱乐/旅游等杂讯
    # 保留条件（满足任一即可）：
    # 1. 与持仓/建仓股直接关联（relevance=direct）
    # 2. 与持仓/建仓股行业关联（relevance=industry）
    # 3. 标题含用户持仓相关行业关键词（锂电、半导体、核电、轨交、医药、银行、有色、水电等）
    # 4. 标题含重要地缘/宏观关键词（伊朗、制裁、关税、冲突、战争、原油、黄金、LPR、降准等）
    # 5. 来源为宏观政策类（央行、财政部、证监会、国务院金融等）且标题含财经关键词
    
    # 用户持仓相关核心行业关键词（精准匹配）
    # 2026-05-09 更新：聚焦7只核心标的
    USER_INDUSTRY_KWS = [
        # 九州一轨
        '轨交', '高铁', '铁路', '地铁', '轨道交通', '减震', '降噪',
        # 汉钟精机
        '通用设备', '压缩机', '风机', '水泵', '真空泵', '制冷', '磁悬浮',
        # 启明星辰
        '网络安全', '信息安全', 'AI安全', '数据安全', '国资云', '网安',
        # 通源环境
        '液冷', '散热', '数据中心', '浸没式液冷', '温控', 'IDC',
        # ST柯利达
        '建筑装饰', '装修', '幕墙', 'ST', '重组', '借壳', '摘帽',
        # 华蓝集团
        '设计院', '工程咨询', '算电协同', '元禾控股',
        # 腾亚精工
        '电动工具', '园林机械', '割草机', '泳池机器人', '机器人关节',
        # 半导体（九州、汉钟相关）
        '半导体', '芯片', '晶圆', '光刻', 'IC', '集成电路',
        # 算力/AI（启明、通源、华蓝相关）
        'AI', '人工智能', '算力', '光模块', '大模型', 'Agent',
    ]
    
    # 重要地缘/宏观关键词
    MACRO_KWS = [
        '伊朗', '霍尔木兹', '制裁', '关税', '贸易战', '中美', '特朗普', '拜登',
        '欧盟', '俄罗斯', '俄乌', '中东', '海湾', '石油', '原油', 'OPEC', 'WTI', '布伦特',
        '黄金', '白银', '铜价', '镍价', '铝价', '钴价', '锂价', '锶',
        '降准', '降息', 'LPR', 'MLF', '逆回购', '社融', 'M2', 'CPI', 'PPI', 'PMI',
        'GDP', '财政', '货币政策', '政治局', '证监会', '国务院', '央行',
    ]
    
    # 通用财经关键词（需配合排除词使用，避免社会新闻混入）
    # ⚠️ 必须精准，宽泛词（如"突破"）会导致社会新闻混入
    GENERAL_FINANCE_KWS = [
        'A股', '沪指', '深成指', '创业板', '科创板', '北交所',
        '涨停', '跌停', '涨停潮', '跌停潮', '大涨', '大跌', '暴跌', '飙升',
        '主力资金', '北向资金', '南向资金', '外资', '机构', '公募', '私募',
        'IPO', '上市', '退市', '停牌', '复牌', '并购重组', '借壳', '定增',
        '财报', '年报', '季报', '业绩预告', '业绩快报', '营收', '净利润', '毛利率',
        '分红', '股息', '送转', '配股', '增持', '减持', '回购', '股权激励',
        '牛市', '熊市', '反弹', '回调', '支撑位', '压力位',
        '板块', '概念股', '龙头股', '妖股', '白马股', '蓝筹股', '成长股',
        '股价', '市盈率', '市净率', '估值', 'PE', 'PB',
    ]
    
    # 排除词：含这些词的新闻大概率是无关社会新闻
    EXCLUDE_KWS = [
        '景区', '旅游', '游客', '景点', '门票', '导游', '旅行社',
        '水獭', '动物', '宠物', '野生动物',
        '网红', '打卡', '拍照', '美食', '小吃', '民宿',
        '离婚', '结婚', '出轨', '绯闻', ' celebrity', '明星',
        '车祸', '交通事故', '火灾', '地震', '台风', '暴雨', '天气',
        '小学', '中学', '大学', '高考', '中考', '招生', '录取',
        '广场舞', '马拉松', '演唱会', '音乐节', '电影节',
        '钓鱼', '露营', '徒步', '骑行', '瑜伽', '健身',
        # 影视/娱乐/社会杂讯
        '票房', '五一', '国庆', '春节档', '暑期档', '电影', '影片', '首映',
        '民警', '巡逻', '交警', '消防', '城管', '执法', '查获', '缴获',
        '救助', '救援', '捐款', '公益', '慈善', '志愿',
        '寻亲', '失踪', '找回', '团聚', '感人',
        # 纯地方新闻
        '地名：红旗渠', '地名：黄山', '地名：泰山', '地名：故宫',  # 仅示例，实际用更通用方式
    ]
    
    filtered_items = []
    dropped = 0
    for item in all_items:
        title = item.get('title', '')
        level = item.get('relevance_level', 'none')
        source = item.get('source', '')
        
        # 优先条件1-2：与持仓/建仓股有关联
        if level in ('direct', 'industry'):
            filtered_items.append(item)
            continue
        
        # 排除词检查：含排除词的直接丢弃
        if any(kw in title for kw in EXCLUDE_KWS):
            dropped += 1
            continue
        
        # 条件3：用户持仓相关行业
        if any(kw in title for kw in USER_INDUSTRY_KWS):
            filtered_items.append(item)
            continue
        
        # 条件4：重要地缘/宏观
        if any(kw in title for kw in MACRO_KWS):
            filtered_items.append(item)
            continue
        
        # 条件5：通用财经关键词（严格匹配）
        if any(kw in title for kw in GENERAL_FINANCE_KWS):
            filtered_items.append(item)
            continue
        
        # 其余丢弃
        dropped += 1
    
    print(f"[Filter] 财经过滤前: {len(all_items)} 条 → 过滤后: {len(filtered_items)} 条（丢弃 {dropped} 条无关新闻）")
    
    # 去重 + 同源合并（相同新闻合并来源，如：Tushare·华尔街见闻 / 第一财经 / 同花顺）
    def normalize_title(title):
        """归一化标题用于去重：去空格、标点、大小写"""
        import re
        return re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', str(title)).lower()
    
    title_groups = {}
    for item in filtered_items:
        norm = normalize_title(item.get('title', ''))
        if not norm:
            continue
        if norm not in title_groups:
            title_groups[norm] = []
        title_groups[norm].append(item)
    
    merged = []
    for norm, group in title_groups.items():
        if len(group) == 1:
            merged.append(group[0])
            continue
        # 合并相同标题的新闻
        base = group[0].copy()
        sources = []
        source_classes = []
        latest_time = base.get('time', '')
        latest_date = base.get('date', '')
        for g in group:
            src = g.get('source', '')
            if src and src not in sources:
                sources.append(src)
            src_cls = g.get('sourceClass', '')
            if src_cls and src_cls not in source_classes:
                source_classes.append(src_cls)
            # 保留最新时间
            t = g.get('time', '')
            d = g.get('date', '')
            if d + t > latest_date + latest_time:
                latest_time = t
                latest_date = d
        # 合并来源显示
        base['source'] = ' / '.join(sources)
        base['sourceClass'] = source_classes[0] if source_classes else 'sina'
        base['time'] = latest_time
        base['date'] = latest_date
        # 标记为合并来源
        base['merged_sources'] = sources
        merged.append(base)
    
    unique = merged
    
    # 关联度分析：给每条新闻标记与持仓/建仓股的关联度
    unique = mark_news_relevance(unique)
    
    # 先按日期时间倒序，再按关联度降序（稳定排序保留时间顺序）
    unique.sort(key=lambda x: x.get('date', '') + x.get('time', ''), reverse=True)
    unique.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    # 分类
    categories = {
        'policy': {'name': '🏛️ 政策/宏观', 'items': []},
        'company': {'name': '🏢 公司公告', 'items': []},
        'material': {'name': '🛢️ 原料/行业', 'items': []},
        'finance': {'name': '🏦 金融/市场', 'items': []},
    }
    for item in unique:
        cat = item.get('category', 'company')
        if cat not in categories:
            cat = 'company'
        categories[cat]['items'].append(item)
    
    result = {
        'categories': categories,
        'total': len(unique),
        'source_counts': source_counts,
        'source_status': NEWS_SOURCE_STATUS,
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'ok',
    }
    
    # 保存缓存
    PREMARKET_CACHE['data'] = result
    PREMARKET_CACHE['timestamp'] = datetime.datetime.now()
    
    return result


# ===================== 重大事件监控（持仓关联过滤）=====================
# 重大事件缓存（10分钟）
EVENTS_CACHE = {
    'data': None,
    'timestamp': None,
}

def fetch_all_events():
    """
    重大事件监控：只抓取与持仓股/计划标的公司直接相关的新闻和公告。
    基于关键词匹配过滤，确保每条新闻都与用户的股票池相关。
    """
    # 检查缓存（盘中2分钟，休市10分钟）
    now = datetime.datetime.now()
    ttl = get_cache_ttl()
    if EVENTS_CACHE['timestamp'] and EVENTS_CACHE['data']:
        cache_age = (now - EVENTS_CACHE['timestamp']).total_seconds()
        if cache_age < ttl:
            print(f"[CACHE] 事件缓存命中，{int(cache_age)}秒前更新（盘中2min/休市10min）")
            return EVENTS_CACHE['data']
    
    all_news = []
    
    # 1. 持仓股+计划标的新闻（直接相关）
    def fetch_stock_events(stock):
        items_local = []
        try:
            news = fetch_sina_stock_news(stock['code'], max_items=5)
            for n in news:
                n['stock_name'] = stock['name']
                n['stock_code'] = stock['code']
                n['relevance_level'] = 'direct'
                n['related_stocks'] = [stock['code']]
            items_local.extend(news)
        except Exception as e:
            print(f"[WARN] sina {stock['code']}: {e}")
        
        try:
            cninfo = fetch_cninfo_announcements(stock['code'], page_size=3)
            for n in cninfo:
                n['stock_name'] = stock['name']
                n['stock_code'] = stock['code']
                n['relevance_level'] = 'direct'
                n['related_stocks'] = [stock['code']]
            items_local.extend(cninfo)
        except Exception as e:
            print(f"[WARN] cninfo {stock['code']}: {e}")
        
        try:
            em = fetch_eastmoney_news(stock['code'], max_items=3)
            for n in em:
                n['stock_name'] = stock['name']
                n['stock_code'] = stock['code']
                n['relevance_level'] = 'direct'
                n['related_stocks'] = [stock['code']]
            items_local.extend(em)
        except Exception as e:
            print(f"[WARN] eastmoney {stock['code']}: {e}")
        
        return items_local
    
    # 并行抓取
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(fetch_stock_events, s): s for s in MONITOR_STOCKS}
        for future in concurrent.futures.as_completed(futures):
            items_local = future.result()
            all_news.extend(items_local)
    
    # 2. Tushare 全渠道新闻 → 只保留与持仓/计划标的关联的
    try:
        tushare_items = fetch_tushare_all_news(max_per_source=15)
        tushare_items = mark_news_relevance(tushare_items)
        # 过滤：只保留直接关联或行业关联的新闻
        filtered = [n for n in tushare_items if n.get('relevance_level') in ('direct', 'industry')]
        for n in filtered:
            n['stock_name'] = '关联持仓'
        all_news.extend(filtered)
        print(f"[OK] Tushare关联新闻: {len(filtered)} 条")
    except Exception as e:
        print(f"[WARN] Tushare关联: {e}")
    
    # 3. 宏观政策新闻 → 只保留与持仓/建仓股行业相关的
    try:
        policy_news = fetch_policy_news() + fetch_people_rss(max_items=5) + fetch_huanqiu_rss(max_items=5)
        policy_news = mark_news_relevance(policy_news)
        filtered = [n for n in policy_news if n.get('relevance_level') in ('direct', 'industry')]
        for n in filtered:
            n['stock_name'] = '宏观关联'
        all_news.extend(filtered)
        print(f"[OK] 宏观关联: {len(filtered)} 条")
    except Exception as e:
        print(f"[WARN] 宏观关联: {e}")
    
    # 去重 + 同源合并
    def normalize_title(title):
        import re
        return re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', str(title)).lower()
    
    title_groups = {}
    for n in all_news:
        norm = normalize_title(n.get('title', ''))
        if not norm:
            continue
        if norm not in title_groups:
            title_groups[norm] = []
        title_groups[norm].append(n)
    
    merged = []
    for norm, group in title_groups.items():
        if len(group) == 1:
            merged.append(group[0])
            continue
        base = group[0].copy()
        sources = []
        source_classes = []
        latest_time = base.get('time', '')
        latest_date = base.get('date', '')
        for g in group:
            src = g.get('source', '')
            if src and src not in sources:
                sources.append(src)
            src_cls = g.get('sourceClass', '')
            if src_cls and src_cls not in source_classes:
                source_classes.append(src_cls)
            t = g.get('time', '')
            d = g.get('date', '')
            if d + t > latest_date + latest_time:
                latest_time = t
                latest_date = d
        base['source'] = ' / '.join(sources)
        base['sourceClass'] = source_classes[0] if source_classes else 'sina'
        base['time'] = latest_time
        base['date'] = latest_date
        base['merged_sources'] = sources
        merged.append(base)
    
    unique = merged
    
    # 重大事件定义：5日内 + 直接相关
    today = datetime.datetime.now().date()
    def is_within_5_days(date_str):
        try:
            d = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            return (today - d).days <= 5
        except:
            return True  # 日期解析失败时保留
    
    unique = [n for n in unique if n.get('relevance_level') == 'direct' and is_within_5_days(n.get('date', ''))]
    
    # 先按日期时间倒序，再按关联度降序（稳定排序保留时间顺序）
    unique.sort(key=lambda x: x.get('date', '') + x.get('time', ''), reverse=True)
    unique.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    # 分类
    categories = {
        'policy': {'name': '🏛️ 政策', 'items': []},
        'finance': {'name': '🏦 金融', 'items': []},
        'company': {'name': '🏢 公司', 'items': []},
        'material': {'name': '🛢️ 原料', 'items': []},
    }
    for n in unique:
        cat = n.get('category', 'company')
        if cat not in categories:
            cat = 'company'
        categories[cat]['items'].append(n)
    
    result = {
        'categories': categories,
        'total': len(unique),
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'filter': '5日内直接相关'
    }
    
    # 保存缓存
    EVENTS_CACHE['data'] = result
    EVENTS_CACHE['timestamp'] = datetime.datetime.now()
    
    return result


# ===================== 数据缓存 =====================
class DataCache:
    def __init__(self):
        self.data = {"stocks": {}, "indices": {}, "commodities": {}, "events": {}, "market_status": "初始化中", "timestamp": None}
        self.lock = threading.Lock()
    
    def update(self, new_data):
        with self.lock:
            self.data = new_data
    
    def get(self):
        with self.lock:
            return dict(self.data)

cache = DataCache()


# ===================== 交易时间判断 =====================
# 注意：is_trading_time() 已在上文定义（含 trade_cal 法定节假日判断）
# 此处不再重复定义，避免覆盖

def get_last_trade_date():
    """获取最近一个交易日日期"""
    today = datetime.datetime.now()
    # 从最近3天往前找
    for i in range(7):
        d = today - datetime.timedelta(days=i)
        date_str = d.strftime('%Y%m%d')
        try:
            df = pro.trade_cal(exchange='SSE', start_date=date_str, end_date=date_str)
            if not df.empty and df.iloc[0]['is_open'] == 1:
                return date_str
        except:
            # 降级：周末判断
            if d.weekday() < 5:
                return date_str
    return today.strftime('%Y%m%d')

def fetch_commodity_prices():
    """通过Tushare期货接口抓取原材料期货价格（20种原料全覆盖）"""
    commodity_futures = {
        # ===== 锂电/新能源材料 =====
        '碳酸锂': {'code': 'LC2605.GFE', 'unit': '元/吨', 'source': '广期所碳酸锂'},
        '镍': {'code': 'NI2605.SHF', 'unit': '元/吨', 'source': '沪镍期货'},
        # 电解钴: 国内无期货，保留占位
        '电解钴': {'code': None, 'unit': '元/吨', 'source': '暂无免费API'},
        
        # ===== 有色/稀有金属 =====
        '铝锭': {'code': 'AL2605.SHF', 'unit': '元/吨', 'source': '沪铝期货'},
        '氧化铝': {'code': 'AO2605.SHF', 'unit': '元/吨', 'source': '氧化铝期货'},
        '铜': {'code': 'CU2605.SHF', 'unit': '元/吨', 'source': '沪铜期货'},
        '锌': {'code': 'ZN2605.SHF', 'unit': '元/吨', 'source': '沪锌期货'},
        '铅': {'code': 'PB2605.SHF', 'unit': '元/吨', 'source': '沪铅期货'},
        '锡': {'code': 'SN2605.SHF', 'unit': '元/吨', 'source': '沪锡期货'},
        '锰硅（电解锰代理）': {'code': 'SM2605.ZCE', 'unit': '元/吨', 'source': '郑商所锰硅'},
        # 碳酸锶: 国内无期货，保留占位
        '碳酸锶（锶盐）': {'code': None, 'unit': '元/吨', 'source': '暂无免费API'},
        
        # ===== 煤化工/烯烃 =====
        '聚丙烯': {'code': 'PP2605.DCE', 'unit': '元/吨', 'source': 'PP期货'},
        '甲醇': {'code': 'MA2605.ZCE', 'unit': '元/吨', 'source': '甲醇期货'},
        '焦煤': {'code': 'JM2605.DCE', 'unit': '元/吨', 'source': '焦煤期货'},
        '焦炭': {'code': 'J2605.DCE', 'unit': '元/吨', 'source': '焦炭期货'},
        '原油': {'code': 'SC2606.INE', 'unit': '元/桶', 'source': '原油期货'},
        
        # ===== 钢铁/建材 =====
        '螺纹钢（钢材代理）': {'code': 'RB2605.SHF', 'unit': '元/吨', 'source': '螺纹钢期货'},
        '纯碱': {'code': 'SA2605.ZCE', 'unit': '元/吨', 'source': '纯碱期货'},
        
        # ===== 造纸 =====
        '纸浆': {'code': 'SP2605.SHF', 'unit': '元/吨', 'source': '纸浆期货'},
        
        # ===== 化工基础原料（暂无期货） =====
        '硫酸': {'code': None, 'unit': '元/吨', 'source': '暂无免费API'},
    }
    
    prices = {}
    for name, info in commodity_futures.items():
        # 无期货合约的原料，返回"现货查询"模式（带直达链接）
        if info['code'] is None:
            # 映射到用户提供的现货查询入口
            spot_urls = {
                '电解钴': {
                    'url': 'https://www.smm.cn/price/metal/Co',
                    'alt': 'https://www.ccmn.cn/price/xiaojinshu/',
                    'freq': '工作日10:00',
                    'spec': 'Co≥99.8% 国产/金川',
                },
                '碳酸锶（锶盐）': {
                    'url': 'https://www.smm.cn/price/metal/StrontiumCarbonate',
                    'alt': 'https://www.100ppi.com/price/110000/',
                    'freq': '周/半月更新',
                    'spec': 'SrCO₃≥97%/98% 工业级',
                },
                '硫酸': {
                    'url': 'https://www.100ppi.com/price/60000/',
                    'alt': 'https://www.smm.cn/price/chemical',
                    'freq': '工作日更新',
                    'spec': '工业级98% 浓硫酸',
                },
            }
            meta = spot_urls.get(name, {})
            prices[name] = {
                'latest': 0,
                'change_pct': 0,
                'unit': info['unit'],
                'source': info['source'],
                'trade_date': '现货查询',
                'spot_url': meta.get('url', ''),
                'spot_alt': meta.get('alt', ''),
                'spot_freq': meta.get('freq', ''),
                'spot_spec': meta.get('spec', ''),
            }
            continue
        try:
            df = pro.fut_daily(ts_code=info['code'])
            if df is not None and not df.empty:
                row = df.iloc[0]
                pre_close = float(row['pre_close']) if row['pre_close'] else 0
                change1 = float(row['change1']) if row['change1'] else 0
                pct = round(change1 / pre_close * 100, 2) if pre_close else 0
                prices[name] = {
                    'latest': round(float(row['close']), 2),
                    'change_pct': pct,
                    'unit': info['unit'],
                    'source': info['source'],
                    'trade_date': str(row['trade_date']),
                }
        except Exception as e:
            print(f"[ERR] 期货 {name} ({info['code']}): {e}")
    
    return prices
    """获取最近一个交易日"""
    today = datetime.datetime.now().strftime('%Y%m%d')
    try:
        df = pro.trade_cal(exchange='SSE', start_date='20260101', end_date=today)
        trade_dates = df[df['is_open'] == 1]['cal_date'].tolist()
        return trade_dates[-1] if trade_dates else today
    except:
        return today


# ===================== Tushare 数据抓取 =====================
def fetch_sina_realtime():
    """盘中 fallback：akshare 新浪实时行情（替代直接请求）"""
    if not AKSHARE_AVAILABLE:
        print("[WARN] akshare 不可用，使用 legacy 新浪接口")
        return _fetch_sina_realtime_legacy()
    
    stocks = {}
    try:
        # 使用 akshare 获取全市场实时数据（新浪接口）
        df = ak.stock_zh_a_spot()
        
        # 构建代码映射表
        target_codes = set()
        for code in ALL_STOCK_CODES:
            if code.endswith('.SH'):
                target_codes.add('sh' + code.replace('.SH', ''))
            elif code.endswith('.SZ'):
                target_codes.add('sz' + code.replace('.SZ', ''))
        
        # 筛选持仓股票
        result = df[df['代码'].isin(target_codes)].copy()
        
        for _, row in result.iterrows():
            sina_code = row['代码']
            if sina_code.startswith('sh'):
                ts_code = sina_code[2:] + '.SH'
            elif sina_code.startswith('sz'):
                ts_code = sina_code[2:] + '.SZ'
            else:
                continue
            
            # 字段映射（akshare 列名 → 统一格式）
            price = float(row['最新价']) if pd.notna(row['最新价']) else 0
            pre_close = float(row['昨收']) if pd.notna(row['昨收']) else 0
            open_p = float(row['今开']) if pd.notna(row['今开']) else 0
            high = float(row['最高']) if pd.notna(row['最高']) else 0
            low = float(row['最低']) if pd.notna(row['最低']) else 0
            volume = int(row['成交量']) if pd.notna(row['成交量']) else 0
            amount = float(row['成交额']) if pd.notna(row['成交额']) else 0
            change = float(row['涨跌额']) if pd.notna(row['涨跌额']) else 0
            pct = float(row['涨跌幅']) if pd.notna(row['涨跌幅']) else 0
            name = row['名称'] if pd.notna(row['名称']) else ''
            
            stocks[ts_code] = {
                'price': round(price, 2),
                'change': round(change, 2),
                'pct': round(pct, 2),
                'open': round(open_p, 2),
                'high': round(round(high, 2), 2),
                'low': round(low, 2),
                'volume': volume,
                'amount': round(amount / 10000, 2),  # 万元
                'name': name,
            }
        
        if stocks:
            print(f"[OK] akshare 新浪实时数据: {len(stocks)} 只股票")
    except Exception as e:
        print(f"[ERR] fetch_sina_realtime (akshare): {e}")
        # 降级到原始新浪直接请求
        stocks = _fetch_sina_realtime_legacy()
    
    return stocks


def _fetch_sina_realtime_legacy():
    """原始新浪直接请求（降级备用）"""
    stocks = {}
    try:
        sina_codes = []
        for code in ALL_STOCK_CODES:
            if code.endswith('.SH'):
                sina_codes.append('sh' + code.replace('.SH', ''))
            elif code.endswith('.SZ'):
                sina_codes.append('sz' + code.replace('.SZ', ''))
        
        url = 'https://hq.sinajs.cn/list=' + ','.join(sina_codes)
        req = requests.get(url, headers={'Referer': 'https://finance.sina.com.cn'}, timeout=10)
        req.encoding = 'gbk'
        text = req.text
        
        for line in text.split('\n'):
            if not line.strip() or 'hq_str_' not in line:
                continue
            prefix = 'var hq_str_'
            start = line.find(prefix)
            if start == -1:
                continue
            eq = line.find('="', start)
            end = line.find('";', eq)
            if eq == -1 or end == -1:
                continue
            
            sina_code = line[start + len(prefix):eq]
            data_str = line[eq + 2:end]
            parts = data_str.split(',')
            if len(parts) < 10:
                continue
            
            if sina_code.startswith('sh'):
                ts_code = sina_code[2:] + '.SH'
            elif sina_code.startswith('sz'):
                ts_code = sina_code[2:] + '.SZ'
            else:
                continue
            
            name = parts[0]
            pre_close = float(parts[1])
            open_p = float(parts[2])
            current = float(parts[3])
            high = float(parts[4])
            low = float(parts[5])
            volume = int(parts[8])
            amount = float(parts[9])
            change = current - pre_close
            pct = round((change / pre_close) * 100, 2) if pre_close else 0
            
            stocks[ts_code] = {
                'price': round(current, 2),
                'change': round(change, 2),
                'pct': pct,
                'open': round(open_p, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'volume': volume,
                'amount': round(amount / 10000, 2),
                'name': name,
            }
        
        if stocks:
            print(f"[OK] 新浪实时数据(legacy): {len(stocks)} 只股票")
    except Exception as e:
        print(f"[ERR] fetch_sina_realtime legacy: {e}")
    
    return stocks


def fetch_daily_data():
    """抓取日线行情数据 — 盘中 fallback 新浪实时"""
    trade_date = get_last_trade_date()
    stocks = {}
    
    try:
        # 优先 Tushare 日线
        codes = ','.join(ALL_STOCK_CODES)
        df = pro.daily(ts_code=codes, trade_date=trade_date)
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                code = row['ts_code']
                stocks[code] = {
                    'price': round(row['close'], 2),
                    'change': round(row['change'], 2),
                    'pct': round(row['pct_chg'], 2),
                    'open': round(row['open'], 2),
                    'high': round(row['high'], 2),
                    'low': round(row['low'], 2),
                    'volume': int(row['vol']),
                    'amount': round(row['amount'], 2),
                }
            print(f"[OK] Tushare 日线数据: {len(stocks)} 只")
        else:
            print("[WARN] Tushare 日线为空，尝试新浪实时...")
            stocks = fetch_sina_realtime()
            # 用当前日期作为 trade_date（新浪数据没有日期字段，取今天）
            trade_date = datetime.datetime.now().strftime('%Y%m%d')
    except Exception as e:
        print(f"[ERR] fetch_daily_data: {e}, fallback 新浪实时...")
        stocks = fetch_sina_realtime()
        trade_date = datetime.datetime.now().strftime('%Y%m%d')
    
    return stocks, trade_date


def fetch_moneyflow():
    """抓取资金流向数据"""
    trade_date = get_last_trade_date()
    flows = {}
    
    try:
        for code in ALL_STOCK_CODES:
            df = pro.moneyflow(ts_code=code, trade_date=trade_date)
            if df is not None and not df.empty:
                row = df.iloc[0]
                flows[code] = {
                    'main_net': round(row.get('net_mf_amount', 0), 2),  # net_mf_amount 单位已经是万元
                    'main_pct': round(row.get('net_mf_rate', 0), 2),
                }
    except Exception as e:
        print(f"[ERR] fetch_moneyflow: {e}")
    
    return flows


def fetch_daily_basic():
    """抓取每日基本面指标（PE/PB/市值等）"""
    trade_date = get_last_trade_date()
    basics = {}
    
    try:
        codes = ','.join(ALL_STOCK_CODES)
        df = pro.daily_basic(ts_code=codes, trade_date=trade_date)
        for _, row in df.iterrows():
            code = row['ts_code']
            basics[code] = {
                'turnover': round(row.get('turnover_rate', 0), 2),
                'pe': round(row.get('pe', 0), 2),
                'pb': round(row.get('pb', 0), 2),
                'mv': round(row.get('total_mv', 0), 2),  # 总市值（万元）
                'circ_mv': round(row.get('circ_mv', 0), 2),
            }
    except Exception as e:
        print(f"[ERR] fetch_daily_basic: {e}")
    
    return basics


def fetch_hsi_data():
    """获取恒生指数实时数据（腾讯接口）"""
    try:
        import urllib.request
        req = urllib.request.Request(
            'https://qt.gtimg.cn/q=hkHSI',
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            text = resp.read().decode('gbk', errors='ignore')
        
        # 解析: v_hkHSI="100~恒生指数~HSI~26169.100~25776.530~..."
        if 'v_hkHSI="' not in text:
            return None
        
        start = text.find('v_hkHSI="') + len('v_hkHSI="')
        end = text.find('"', start)
        data_str = text[start:end]
        parts = data_str.split('~')
        
        if len(parts) < 35:
            return None
        
        # 字段映射（腾讯接口格式）— 78字段格式
        close = float(parts[3])      # 当前价
        pre_close = float(parts[4])  # 昨收
        change = float(parts[31])    # 涨跌额
        pct = float(parts[32])       # 涨跌幅%
        date_time = parts[30]        # 日期时间
        
        # 解析日期
        trade_date = date_time.split()[0].replace('/', '') if date_time else None
        
        return {
            'name': '恒生指数',
            'price': round(close, 2),
            'change': round(change, 2),
            'pct': round(pct, 2),
            'region': 'hk',
            'trade_date': trade_date,
        }
    except Exception as e:
        print(f"[ERR] fetch_hsi_data: {e}")
        return None

def fetch_index_data():
    """抓取主要指数数据 — 腾讯qt.gtimg.cn实时接口"""
    indices = {}
    index_codes = {
        'sh000001': ('000001.SH', '上证指数'),
        'sz399001': ('399001.SZ', '深证成指'),
        'sz399006': ('399006.SZ', '创业板指'),
        'sh000016': ('000016.SH', '上证50'),
        'sh000300': ('000300.SH', '沪深300'),
    }
    
    try:
        codes_str = ','.join(index_codes.keys())
        url = f'https://qt.gtimg.cn/q={codes_str}'
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            try:
                text = raw.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text = raw.decode('gb2312')
                except UnicodeDecodeError:
                    text = raw.decode('gbk', errors='replace')
        
        for tcode, (std_code, name) in index_codes.items():
            pattern = rf'v_{tcode}="([^"]+)"'
            m = re.search(pattern, text)
            if m:
                parts = m.group(1).split('~')
                if len(parts) > 4:
                    price = float(parts[3])
                    preclose = float(parts[4])
                    change = round(price - preclose, 2)
                    pct = round(change / preclose * 100, 2)
                    indices[std_code] = {
                        'name': name,
                        'price': price,
                        'change': change,
                        'pct': pct,
                    }
                    
    except Exception as e:
        print(f"[ERR] fetch_index_data: {e}")
    
    return indices


def fetch_margin_data():
    """抓取融资融券数据"""
    trade_date = get_last_trade_date()
    margins = {}
    
    try:
        for code in ALL_STOCK_CODES:
            # 上交所/深交所分开查询
            exchange = 'SSE' if code.endswith('.SH') else 'SZSE'
            df = pro.margin_detail(exchange_id=exchange, trade_date=trade_date, ts_code=code)
            if df is not None and not df.empty:
                row = df.iloc[0]
                margins[code] = {
                    'rzye': round(row.get('rzye', 0) / 10000, 2),  # 融资余额（万元）
                    'rqye': round(row.get('rqye', 0) / 10000, 2),  # 融券余额（万元）
                    'rz_buy': round(row.get('rzmre', 0) / 10000, 2),  # 融资买入额
                }
    except Exception as e:
        print(f"[ERR] fetch_margin_data: {e}")
    
    return margins


def fetch_history_changes():
    """计算3日/5日/7日涨跌"""
    try:
        end_date = get_last_trade_date()
        # 获取最近10个交易日
        df = pro.trade_cal(exchange='SSE', start_date='20260101', end_date=end_date)
        trade_dates = df[df['is_open'] == 1]['cal_date'].tolist()
        
        changes = {}
        for code in ALL_STOCK_CODES:
            if len(trade_dates) >= 8:
                # 获取最近8个交易日数据
                start = trade_dates[-8]
                hist = pro.daily(ts_code=code, start_date=start, end_date=end_date)
                if hist is not None and len(hist) >= 2:
                    closes = hist['close'].tolist()
                    changes[code] = {
                        '3d': round((closes[-1] / closes[-4] - 1) * 100, 2) if len(closes) >= 4 else None,
                        '5d': round((closes[-1] / closes[-6] - 1) * 100, 2) if len(closes) >= 6 else None,
                        '7d': round((closes[-1] / closes[-8] - 1) * 100, 2) if len(closes) >= 8 else None,
                    }
        return changes
    except Exception as e:
        print(f"[ERR] fetch_history_changes: {e}")
        return {}


def fetch_moving_averages():
    """计算MA5/MA10/MA20"""
    try:
        end_date = get_last_trade_date()
        df = pro.trade_cal(exchange='SSE', start_date='20260101', end_date=end_date)
        trade_dates = df[df['is_open'] == 1]['cal_date'].tolist()
        
        mas = {}
        for code in ALL_STOCK_CODES:
            if len(trade_dates) >= 20:
                start = trade_dates[-22]  # 多取几天保险
                hist = pro.daily(ts_code=code, start_date=start, end_date=end_date)
                if hist is not None and len(hist) >= 5:
                    closes = hist['close'].tolist()
                    mas[code] = {
                        'ma5': round(sum(closes[-5:]) / 5, 2) if len(closes) >= 5 else None,
                        'ma10': round(sum(closes[-10:]) / 10, 2) if len(closes) >= 10 else None,
                        'ma20': round(sum(closes[-20:]) / 20, 2) if len(closes) >= 20 else None,
                    }
        return mas
    except Exception as e:
        print(f"[ERR] fetch_moving_averages: {e}")
        return {}


# ===================== 后台数据抓取线程 =====================
def fetch_sector_fund_flow_akshare():
    """用 akshare 获取板块资金流向（5分钟/次），覆盖全行业"""
    sectors = []
    
    if not AKSHARE_AVAILABLE:
        print("[WARN] akshare 不可用，跳过板块资金")
        return []
    
    # 尝试1: akshare 行业资金流排名
    try:
        df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")
        if df is not None and len(df) > 0:
            # 列名映射（不同版本列名可能不同）
            name_col = '名称' if '名称' in df.columns else df.columns[0]
            
            # 找主力净流入列
            net_col = None
            for c in df.columns:
                c_str = str(c)
                if '主力净流入' in c_str or '主力净流入额' in c_str:
                    net_col = c
                    break
            
            # 找涨跌幅或主力净占比列
            pct_col = None
            for c in df.columns:
                c_str = str(c)
                if '涨跌幅' in c_str or '主力净占比' in c_str or '净占比' in c_str:
                    pct_col = c
                    break
            
            for _, row in df.iterrows():
                name = str(row.get(name_col, ''))
                if not name:
                    continue
                
                # 解析主力净流入（可能是万元或亿元，统一为万元）
                net_val = row.get(net_col, 0) if net_col else 0
                try:
                    net = float(net_val) if pd.notna(net_val) else 0
                except:
                    net = 0
                
                # 解析涨跌幅
                pct_val = row.get(pct_col, 0) if pct_col else 0
                try:
                    pct = float(pct_val) if pd.notna(pct_val) else 0
                except:
                    pct = 0
                
                # 如果数值过大（亿元级别），转为万元
                if abs(net) > 1000000:
                    net = net / 10000
                
                sectors.append({
                    'name': name,
                    'main_net': round(net, 2),
                    'avg_pct': round(pct, 2),
                    'stocks': [],  # 全市场板块不返回成分股列表
                })
            
            if sectors:
                # 按主力净流入降序排列
                sectors.sort(key=lambda x: x['main_net'], reverse=True)
                print(f"[OK] akshare 行业板块资金: {len(sectors)} 个")
                return sectors
    except Exception as e:
        print(f"[WARN] akshare 行业板块资金失败: {e}")
    
    # Fallback: 用 stock_zh_a_spot 手动聚合持仓相关行业
    try:
        df = ak.stock_zh_a_spot()
        if df is None or len(df) == 0:
            return []
        
        # 持仓相关行业关键词映射
        # 2026-05-09 全面梳理：5只核心标的 + 产业链映射
        SECTOR_KEYWORDS = {
            # 个股所属板块
            '轨交设备': ['轨交', '铁路', '车辆', '交通设备'],
            '通用设备': ['通用设备', '机械', '压缩机', '真空泵'],
            'AI算力·电源': ['电源', '电气', 'HVDC', '高压直流', '储能', '超充'],
            'AI算力·电容': ['电容', '电子元件', '被动元件'],
            '网络安全': ['网络安全', '信息安全', '软件', 'IT服务'],
            # 产业链映射
            '半导体/芯片': ['半导体', '芯片', '集成电路', '金刚石', '散热', '真空泵'],
            'AI芯片散热': ['散热', '金刚石', '基板', 'SDBG', 'DLC'],
            '半导体设备': ['真空泵', '半导体设备', '晶圆'],
            '数据中心': ['数据中心', '服务器', '算力', '机房'],
            '储能': ['储能', '电池', 'PCS', '逆变器'],
            '算电协同': ['算电协同', '虚拟电厂', '能源互联网'],
            '新能源超充': ['超充', '快充', '充电桩', '新能源'],
            '电子元件': ['电子元件', '被动元件', 'MLCC', '电阻', '电感'],
            '英伟达供应链': ['英伟达', 'NVIDIA', 'GB300', 'Blackwell'],
            'AI安全': ['AI安全', '人工智能安全', '大模型安全'],
            '国产替代': ['国产替代', '自主可控', '卡脖子'],
            '信创': ['信创', '国产软件', '国产化'],
        }
        
        for sector_name, keywords in SECTOR_KEYWORDS.items():
            total_amount = 0
            total_pct = 0
            count = 0
            
            for _, row in df.iterrows():
                name = str(row.get('名称', ''))
                if any(kw in name for kw in keywords):
                    try:
                        pct = float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else 0
                        amount = float(row.get('成交额', 0)) if pd.notna(row.get('成交额')) else 0
                        total_pct += pct
                        total_amount += amount
                        count += 1
                    except:
                        pass
            
            if count > 0:
                sectors.append({
                    'name': sector_name,
                    'main_net': round(total_amount / 10000, 2),
                    'avg_pct': round(total_pct / count, 2),
                    'stocks': [],
                })
        
        if sectors:
            sectors.sort(key=lambda x: x['main_net'], reverse=True)
            print(f"[OK] 手动聚合板块资金: {len(sectors)} 个板块")
        return sectors
        
    except Exception as e2:
        print(f"[ERR] 板块资金fallback也失败: {e2}")
        return []


def aggregate_sector_moneyflow(stocks):
    """
    [已弃用] 基于个股 moneyflow 数据，按行业聚合板块资金流向。
    保留为 fallback，当 akshare 不可用时使用。
    """
    # 板块定义：名称 -> [股票代码列表]
    # 2026-05-09 全面梳理：5只核心标的 + 产业链映射
    SECTORS = {
        # 个股所属板块
        '轨交设备': ['688485.SH'],
        '通用设备': ['002158.SZ'],
        'AI算力·电源': ['002364.SZ'],
        'AI算力·电容': ['002484.SZ'],
        '网络安全': ['002439.SZ'],
        # 产业链映射（一只股票可出现在多个板块）
        '半导体/芯片': ['688485.SH', '002158.SZ'],
        'AI芯片散热': ['688485.SH'],
        '半导体设备': ['002158.SZ'],
        '数据中心': ['002364.SZ', '002484.SZ'],
        '储能': ['002364.SZ'],
        '算电协同': ['002364.SZ'],
        '新能源超充': ['002364.SZ'],
        '电子元件': ['002484.SZ'],
        '英伟达供应链': ['002484.SZ'],
        'AI安全': ['002439.SZ'],
        '国产替代': ['688485.SH', '002158.SZ', '002484.SZ', '002439.SZ'],
        '信创': ['002439.SZ'],
    }
    
    sector_data = []
    for sector_name, codes in SECTORS.items():
        total_net = 0
        stock_details = []
        for code in codes:
            s = stocks.get(code, {})
            mn = s.get('main_net', 0)
            if mn:
                total_net += mn
                stock_name = STOCK_KEYWORDS.get(code, {}).get('name', code)
                stock_details.append({
                    'name': stock_name,
                    'code': code.split('.')[0],
                    'main_net': mn,
                })
        
        if stock_details:
            total_pct = 0
            count = 0
            for code in codes:
                s = stocks.get(code, {})
                pct = s.get('pct')  # fix: 字段名是 pct 不是 pct_chg
                if pct is not None:
                    total_pct += pct
                    count += 1
            avg_pct = round(total_pct / count, 2) if count > 0 else 0
            
            sector_data.append({
                'name': sector_name,
                'main_net': round(total_net, 2),
                'avg_pct': avg_pct,
                'stocks': stock_details,
            })
    
    sector_data.sort(key=lambda x: x['main_net'], reverse=True)
    return sector_data


# 原材料价格监控配置
COMMODITY_FETCH_INTERVAL = 7200  # 2小时（秒）
commodity_cache_info = {
    'last_fetch': 0,  # 上次抓取时间戳
    'data': {},       # 缓存数据
    'timestamp': '',  # 缓存时间字符串
}

# 全球指数抓取配置
GLOBAL_INDEX_CODES = {
    'sh000001': ('000001.SH', '上证指数', 'CN'),
    'sz399001': ('399001.SZ', '深证成指', 'CN'),
    'sz399006': ('399006.SZ', '创业板指', 'CN'),
    'sh000016': ('000016.SH', '上证50', 'CN'),
    'sh000300': ('000300.SH', '沪深300', 'CN'),
    'sh000688': ('000688.SH', '科创50', 'CN'),
}

# 美股/港股/全球指数（使用腾讯接口）
GLOBAL_QT_CODES = {
    'hkHSI': ('HSI', '恒生指数', 'HK'),
    'usDJI': ('DJI', '道琼斯', 'US'),
    'usIXIC': ('IXIC', '纳斯达克', 'US'),
    'usSPX': ('SPX', '标普500', 'US'),
    'gbFTSE': ('FTSE', '英国富时', 'UK'),
    'deDAX': ('DAX', '德国DAX', 'DE'),
    'jpNI225': ('NI225', '日经225', 'JP'),
}

def fetch_global_indices():
    """抓取全球主要股市指数 — 腾讯qt.gtimg.cn接口"""
    indices = {}
    
    # A股指数
    try:
        codes_str = ','.join(GLOBAL_INDEX_CODES.keys())
        url = f'https://qt.gtimg.cn/q={codes_str}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            try:
                text = raw.decode('utf-8')
            except UnicodeDecodeError:
                text = raw.decode('gb2312', errors='replace')
        
        for qt_code, (ts_code, name, region) in GLOBAL_INDEX_CODES.items():
            pattern = f'v_{qt_code}="([^"]+)"'
            match = re.search(pattern, text)
            if match:
                parts = match.group(1).split('~')
                if len(parts) >= 35:
                    close = float(parts[3]) if parts[3] else 0
                    pre = float(parts[4]) if parts[4] else 0
                    change = float(parts[31]) if parts[31] else 0
                    pct = float(parts[32]) if parts[32] else 0
                    indices[ts_code] = {
                        'name': name,
                        'price': round(close, 2),
                        'pre_close': round(pre, 2),
                        'change': round(change, 2),
                        'pct': round(pct, 2),
                        'region': region,
                    }
    except Exception as e:
        print(f"[ERR] A股指数: {e}")
    
    # 港股/美股/全球
    try:
        codes_str = ','.join(GLOBAL_QT_CODES.keys())
        url = f'https://qt.gtimg.cn/q={codes_str}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            try:
                text = raw.decode('utf-8')
            except UnicodeDecodeError:
                text = raw.decode('gb2312', errors='replace')
        
        for qt_code, (symbol, name, region) in GLOBAL_QT_CODES.items():
            pattern = f'v_{qt_code}="([^"]+)"'
            match = re.search(pattern, text)
            if match:
                parts = match.group(1).split('~')
                if len(parts) >= 35:
                    close = float(parts[3]) if parts[3] else 0
                    pre = float(parts[4]) if parts[4] else 0
                    change = float(parts[31]) if parts[31] else 0
                    pct = float(parts[32]) if parts[32] else 0
                    indices[symbol] = {
                        'name': name,
                        'price': round(close, 2),
                        'pre_close': round(pre, 2),
                        'change': round(change, 2),
                        'pct': round(pct, 2),
                        'region': region,
                    }
    except Exception as e:
        print(f"[ERR] 全球指数: {e}")
    
    print(f"[OK] 全球指数: {len(indices)} 个")
    return indices


# 板块资金流向监控配置（akshare，每5分钟）
SECTOR_FETCH_INTERVAL = 300  # 5分钟（秒）
sector_cache_info = {
    'last_fetch': 0,
    'data': [],
}

def background_fetch():
    """后台定时抓取Tushare数据 — 非交易日自动静默"""
    while True:
        # 自动检测交易日，非交易日静默不推送
        if not is_trading_day():
            time.sleep(600)  # 非交易日10分钟检查一次
            continue
        
        try:
            print(f"[{datetime.datetime.now()}] 开始抓取数据...")
            
            stocks, trade_date = fetch_daily_data()
            moneyflow = fetch_moneyflow()
            basics = fetch_daily_basic()
            indices = fetch_global_indices()  # 全球指数
            
            margins = fetch_margin_data()
            history = fetch_history_changes()
            mas = fetch_moving_averages()
            
            # 合并数据
            for code in stocks:
                if code in moneyflow:
                    stocks[code].update(moneyflow[code])
                if code in basics:
                    stocks[code].update(basics[code])
                if code in history:
                    stocks[code].update(history[code])
                if code in mas:
                    stocks[code].update(mas[code])
                if code in margins:
                    stocks[code].update(margins[code])
            
            # 市场状态
            market_status = "交易中" if is_trading_time() else "休市"
            
            # 板块资金：直接聚合持仓个股
            try:
                sector_flows = aggregate_sector_moneyflow(stocks)
            except Exception as e:
                print(f"[ERR] 板块资金聚合失败: {e}")
                sector_flows = []
            
            data = {
                "stocks": stocks,
                "indices": indices,
                "sector_flows": sector_flows,
                "market_status": market_status,
                "trade_date": trade_date,
                "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            cache.update(data)
            print(f"[OK] 数据更新完成: {len(stocks)} 只股票, {len(indices)} 个指数, {len(sector_flows)} 个板块")
            
            # 原材料价格：精简版，只抓核心几种，避免超时
            now_ts = time.time()
            if now_ts - commodity_cache_info['last_fetch'] >= COMMODITY_FETCH_INTERVAL:
                try:
                    print(f"[{datetime.datetime.now()}] 开始抓取原材料价格...")
                    commodity_data = fetch_commodity_prices()
                    cached = cache.get()
                    cached['commodities'] = commodity_data
                    cached['commodities_timestamp'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cache.update(cached)
                    commodity_cache_info['last_fetch'] = now_ts
                    print(f"[OK] 原材料价格更新完成: {len(commodity_data)} 种")
                except Exception as e:
                    print(f"[ERR] 原材料抓取失败: {e}")
            
            # 检查价格提醒
            check_price_alerts(stocks)
            
        except Exception as e:
            print(f"[ERR] background_fetch: {e}")
        
        # 交易时段每30秒（价格提醒需要极致及时），非交易时段每10分钟
        sleep_seconds = 300 if is_trading_time() else 600
        time.sleep(sleep_seconds)


# ===================== HTTP 服务 =====================
class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WORKSPACE, **kwargs)
    
    def log_message(self, format, *args):
        # 减少日志噪音
        pass
    
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()
    
    def do_GET(self):
        # 提取纯路径（去掉查询参数）
        path = self.path.split('?')[0]
        
        if path == '/':
            self.path = '/dashboard.html'
        elif path == '/api/data':
            self._send_data()
            return
        elif path == '/api/events':
            self._send_events()
            return
        elif path == '/api/premarket':
            self._send_premarket()
            return
        elif path == '/api/margin':
            self._send_margin()
            return
        elif path == '/api/sectors':
            self._send_sectors()
            return
        elif path == '/api/commodities':
            self._send_commodities()
            return
        elif path == '/api/health':
            self._send_health()
            return
        super().do_GET()
    
    def _send_json(self, data):
        body = json.dumps(data, ensure_ascii=False, default=str)
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))
    
    def _send_data(self):
        """返回股票数据"""
        data = cache.get()
        if not data.get("stocks"):
            # 如果没有缓存数据，尝试实时抓取
            stocks, trade_date = fetch_daily_data()
            data = {
                "stocks": stocks,
                "indices": {},
                "market_status": "实时抓取",
                "trade_date": trade_date,
                "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
        self._send_json(data)
    
    def _send_events(self):
        """返回重大事件"""
        result = fetch_all_events()
        self._send_json(result)
    
    # 预盘新闻后台刷新标记（防止并发刷新）
    _premarket_refreshing = False
    
    def _send_premarket(self):
        """盘前新闻候选池API — 缓存优先，不阻塞"""
        global _DashboardHandler_premarket_refreshing
        # 优先返回缓存
        if PREMARKET_CACHE['timestamp'] and PREMARKET_CACHE['data']:
            self._send_json(PREMARKET_CACHE['data'])
        else:
            # 缓存为空，返回空结构（前端会显示静态新闻）
            self._send_json({
                'total': 0,
                'categories': {},
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'note': '新闻缓存为空，后台刷新中...'
            })
        # 启动后台刷新（不阻塞当前请求）
        if not self._premarket_refreshing:
            self._premarket_refreshing = True
            threading.Thread(target=self._refresh_premarket_async, daemon=True).start()
    
    def _refresh_premarket_async(self):
        """后台异步刷新新闻缓存"""
        try:
            print(f"[{datetime.datetime.now()}] 后台刷新新闻缓存...")
            result = fetch_premarket_candidates()
            print(f"[{datetime.datetime.now()}] 新闻缓存刷新完成: {result.get('total', 0)} 条")
        except Exception as e:
            print(f"[ERR] 后台刷新新闻失败: {e}")
        finally:
            self._premarket_refreshing = False
    
    def _send_margin(self):
        """融资融券数据API"""
        margins = fetch_margin_data()
        trade_date = get_last_trade_date()
        self._send_json({
            'data': margins,
            'trade_date': trade_date,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })
    
    def _send_sectors(self):
        """板块资金流向API"""
        data = cache.get()
        sector_flows = data.get('sector_flows', [])
        self._send_json({
            'sector_flows': sector_flows,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })
    
    def _send_commodities(self):
        """原材料价格API（优先从缓存读取，每2小时后台更新）"""
        data = cache.get()
        prices = data.get('commodities', {})
        ts = data.get('commodities_timestamp', '')
        
        # 如果缓存为空或超过2小时，实时抓取
        now_ts = time.time()
        cache_valid = prices and (now_ts - commodity_cache_info['last_fetch'] < COMMODITY_FETCH_INTERVAL)
        
        if not cache_valid:
            print(f"[{datetime.datetime.now()}] 原材料缓存过期/为空，实时抓取...")
            prices = fetch_commodity_prices()
            # 更新 cache
            cached = cache.get()
            cached['commodities'] = prices
            cached['commodities_timestamp'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cache.update(cached)
            commodity_cache_info['last_fetch'] = now_ts
            ts = cached['commodities_timestamp']
        
        next_update_ts = commodity_cache_info['last_fetch'] + COMMODITY_FETCH_INTERVAL
        next_update_str = datetime.datetime.fromtimestamp(next_update_ts).strftime('%H:%M:%S')
        
        self._send_json({
            "prices": prices,
            "count": len(prices),
            "timestamp": ts or datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "source": "缓存" if cache_valid else "实时",
            "next_update": next_update_str,
        })

    def _send_health(self):
        data = cache.get()
        status = {
            "status": "ok",
            "market_status": data.get("market_status"),
            "last_update": data.get("timestamp"),
            "trading_time": is_trading_time(),
            "is_trade_day": _is_trade_day(),
        }
        self._send_json(status)


class ReuseAddrTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

# ===================== 自动推送到 GitHub =====================
import subprocess
import hashlib

GIT_PUSH_ENABLED = True  # 开关：设为False禁用自动推送
GIT_PUSH_INTERVAL = 900  # 15分钟（秒）
GIT_DEPLOY_DIR = os.path.join(WORKSPACE, "vercel-deploy")
GIT_DEPLOY_HTML = os.path.join(GIT_DEPLOY_DIR, "index.html")

def get_file_md5(path):
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def is_trading_day():
    now = datetime.datetime.now()
    if now.weekday() >= 5:
        return False
    # 简单节假日：五一/国庆/春节等需要手动维护
    holidays = [
        (1,1), (4,4),(4,5),(4,6),  # 元旦、清明
        (5,1),(5,2),(5,3),(5,4),(5,5),  # 五一
        (6,19),(6,20),(6,21),(6,22),  # 端午
        (9,27),(9,28),(9,29),(9,30),  # 中秋
        (10,1),(10,2),(10,3),(10,4),(10,5),(10,6),(10,7),(10,8),  # 国庆
    ]
    return (now.month, now.day) not in holidays

def auto_push_github():
    """后台线程：每30分钟检查，交易时段有变化才推送到GitHub"""
    last_md5 = None
    while True:
        try:
            now = datetime.datetime.now()
            hour, minute = now.hour, now.minute
            trading_time = (9 <= hour < 15) or (hour == 15 and minute <= 30)
            
            if not GIT_PUSH_ENABLED:
                time.sleep(GIT_PUSH_INTERVAL)
                continue
            
            if not is_trading_day() or not trading_time:
                # 非交易日或非交易时段，延长等待
                time.sleep(GIT_PUSH_INTERVAL)
                continue
            
            # 复制当前HTML到部署目录
            try:
                import shutil
                shutil.copy2(HTML_FILE, GIT_DEPLOY_HTML)
            except Exception as e:
                print(f"[ERR] copy HTML: {e}")
                time.sleep(GIT_PUSH_INTERVAL)
                continue
            
            # 检查是否有实际变化
            current_md5 = get_file_md5(GIT_DEPLOY_HTML)
            if current_md5 == last_md5:
                print(f"[{now}] GitHub push skipped: no changes")
                time.sleep(GIT_PUSH_INTERVAL)
                continue
            
            # git add / commit / push
            os.chdir(WORKSPACE)
            ts = now.strftime("%Y-%m-%d %H:%M")
            
            r1 = subprocess.run(["git", "add", "-A"], capture_output=True, text=True)
            if r1.returncode != 0:
                print(f"[ERR] git add: {r1.stderr}")
                time.sleep(GIT_PUSH_INTERVAL)
                continue
            
            r2 = subprocess.run(["git", "commit", "-m", f"auto: {ts}"], capture_output=True, text=True)
            if r2.returncode != 0:
                # 可能 nothing to commit，跳过
                if "nothing to commit" in r2.stdout or "nothing to commit" in r2.stderr:
                    print(f"[{now}] GitHub push skipped: nothing to commit")
                else:
                    print(f"[ERR] git commit: {r2.stderr}")
                time.sleep(GIT_PUSH_INTERVAL)
                continue
            
            r3 = subprocess.run(["git", "push"], capture_output=True, text=True)
            if r3.returncode != 0:
                print(f"[ERR] git push: {r3.stderr}")
            else:
                print(f"[OK] GitHub pushed: {ts}")
                last_md5 = current_md5
            
        except Exception as e:
            print(f"[ERR] auto_push_github: {e}")
        
        time.sleep(GIT_PUSH_INTERVAL)

def start_server():
    with ReuseAddrTCPServer(("0.0.0.0", PORT), DashboardHandler) as httpd:
        print(f"服务器启动于端口 {PORT}")
        print(f"本地访问: http://localhost:{PORT}/")
        print(f"局域网访问: http://{socket.gethostname()}.local:{PORT}/")
        print(f"API接口: http://localhost:{PORT}/api/data")
        print(f"事件接口: http://localhost:{PORT}/api/events")
        print(f"盘前新闻: http://localhost:{PORT}/api/premarket")
        print(f"板块资金: http://localhost:{PORT}/api/sectors")
        
        httpd.serve_forever()


if __name__ == '__main__':
    # 启动时立即预抓取一次数据（避免启动后缓存为空）
    try:
        print("[INIT] 启动时预抓取数据...")
        stocks, trade_date = fetch_daily_data()
        moneyflow = fetch_moneyflow()
        basics = fetch_daily_basic()
        indices = fetch_global_indices()
        margins = fetch_margin_data()
        history = fetch_history_changes()
        mas = fetch_moving_averages()
        for code in stocks:
            if code in moneyflow: stocks[code].update(moneyflow[code])
            if code in basics: stocks[code].update(basics[code])
            if code in history: stocks[code].update(history[code])
            if code in mas: stocks[code].update(mas[code])
            if code in margins: stocks[code].update(margins[code])
        try:
            sector_flows = aggregate_sector_moneyflow(stocks)
        except Exception as e:
            print(f"[ERR] 板块资金聚合失败: {e}")
            sector_flows = []
        cache.update({
            "stocks": stocks,
            "indices": indices,
            "sector_flows": sector_flows,
            "market_status": "交易中" if is_trading_time() else "休市",
            "trade_date": trade_date,
            "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })
        print(f"[INIT] 预抓取完成: {len(stocks)} 只股票, {len(indices)} 个指数")
    except Exception as e:
        print(f"[WARN] 启动预抓取失败: {e}")
    
    # 启动后台数据抓取线程
    fetch_thread = threading.Thread(target=background_fetch, daemon=True)
    fetch_thread.start()
    
    # 启动HTTP服务器
    start_server()
