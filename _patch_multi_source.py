#!/usr/bin/env python3
"""
Patch stock_service.py to add multi-source news aggregation
"""
import re

with open('stock_service.py', 'r') as f:
    content = f.read()

# 1. Update NEWS_SOURCE_STATUS to include new sources
old_status = """NEWS_SOURCE_STATUS = {
    '新浪财经': '✅ 已接入',
    '巨潮资讯': '✅ 已接入',
    '东方财富': '✅ 已接入',
    '央行/财政部': '✅ 已接入',
    '财联社': '⏳ 待接入（反爬）',
    '金十数据': '⏳ 待接入（反爬）',
    '同花顺': '⏳ 待接入',
    '雪球': '⏳ 待接入（需认证）',
    '第一财经': '⏳ 待接入',
    '路透社': '⏳ 待接入（付费墙）',
    '彭博社': '⏳ 待接入（付费墙）',
}"""

new_status = """NEWS_SOURCE_STATUS = {
    '新浪财经': '✅ 已接入',
    '巨潮资讯': '✅ 已接入',
    '东方财富': '✅ 已接入',
    '央行/财政部': '✅ 已接入',
    '人民网': '✅ 已接入',
    '环球时报': '✅ 已接入',
    '财联社': '⏳ 待接入（反爬）',
    '金十数据': '⏳ 待接入（反爬）',
    '同花顺': '⏳ 待接入',
    '雪球': '⏳ 待接入（需认证）',
    '第一财经': '⏳ 待接入',
    '路透社': '⏳ 待接入（付费墙）',
    '彭博社': '⏳ 待接入（付费墙）',
    '华尔街见闻': '⏳ 待接入',
    '腾讯新闻': '⏳ 待接入',
    '央视网': '⏳ 待接入',
}"""

content = content.replace(old_status, new_status)

# 2. Add new RSS fetch functions after fetch_jin10_news
rss_funcs = '''
# ===================== 人民网RSS抓取 =====================
def fetch_people_rss(max_items=8):
    """抓取人民网时政要闻RSS"""
    items = []
    try:
        url = 'http://www.people.com.cn/rss/politics.xml'
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        resp.encoding = 'utf-8'
        import xml.etree.ElementTree as ET
        root = ET.fromstring(resp.text)
        for item in root.findall('.//item')[:max_items]:
            title = item.findtext('title', '')
            pub_date = item.findtext('pubDate', '')
            link = item.findtext('link', '')
            if title:
                # Parse date
                date_str = ''
                try:
                    from email.utils import parsedate_to_datetime
                    dt = parsedate_to_datetime(pub_date)
                    date_str = dt.strftime('%Y-%m-%d')
                except:
                    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
                items.append({
                    'title': title,
                    'date': date_str,
                    'time': '',
                    'source': '人民网',
                    'sourceClass': 'people',
                    'category': 'policy',
                    'url': link,
                })
        print(f"[OK] 人民网RSS: {len(items)} 条")
    except Exception as e:
        print(f"[ERR] 人民网RSS: {e}")
    return items

# ===================== 环球时报RSS抓取 =====================
def fetch_huanqiu_rss(max_items=8):
    """抓取环球时报国际新闻RSS"""
    items = []
    try:
        url = 'https://www.huanqiu.com/rss/world.xml'
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        resp.encoding = 'utf-8'
        import xml.etree.ElementTree as ET
        root = ET.fromstring(resp.text)
        for item in root.findall('.//item')[:max_items]:
            title = item.findtext('title', '')
            pub_date = item.findtext('pubDate', '')
            link = item.findtext('link', '')
            if title:
                date_str = ''
                try:
                    from email.utils import parsedate_to_datetime
                    dt = parsedate_to_datetime(pub_date)
                    date_str = dt.strftime('%Y-%m-%d')
                except:
                    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
                items.append({
                    'title': title,
                    'date': date_str,
                    'time': '',
                    'source': '环球时报',
                    'sourceClass': 'huanqiu',
                    'category': 'policy',
                    'url': link,
                })
        print(f"[OK] 环球时报RSS: {len(items)} 条")
    except Exception as e:
        print(f"[ERR] 环球时报RSS: {e}")
    return items
'''

# Insert RSS functions after fetch_jin10_news
jin10_marker = "# ===================== 统一盘前新闻候选抓取 ====================="
content = content.replace(jin10_marker, rss_funcs + "\n" + jin10_marker)

# 3. Update fetch_premarket_candidates to include WATCHLIST and new sources
old_candidates = """def fetch_premarket_candidates():
    \"\"\"
    抓取盘前新闻候选池。
    聚合多来源新闻，去重+分类+排序。
    不分交易日/非交易日，随时可调用。
    \"\"\"
    all_items = []
    source_counts = {}
    
    for stock in HOLDINGS:"""

new_candidates = """def fetch_premarket_candidates():
    \"\"\"
    抓取盘前新闻候选池。
    聚合多来源新闻（持仓股+建仓股+宏观政策），去重+分类+排序。
    不分交易日/非交易日，随时可调用。
    \"\"\"
    all_items = []
    source_counts = {}
    
    # 持仓股 + 建仓股统一抓取
    all_stocks = HOLDINGS + WATCHLIST
    
    for stock in all_stocks:"""

content = content.replace(old_candidates, new_candidates)

# 4. Update the policy news section in fetch_premarket_candidates
old_policy = """    # 政策/宏观新闻
    policy_items = fetch_policy_news()
    all_items.extend(policy_items)
    for item in policy_items:
        source_counts[item['source']] = source_counts.get(item['source'], 0) + 1"""

new_policy = """    # 政策/宏观新闻（多源聚合）
    policy_items = fetch_policy_news()
    all_items.extend(policy_items)
    for item in policy_items:
        source_counts[item['source']] = source_counts.get(item['source'], 0) + 1
    
    # RSS时政/国际新闻
    people_items = fetch_people_rss(max_items=8)
    all_items.extend(people_items)
    source_counts['人民网'] = source_counts.get('人民网', 0) + len(people_items)
    
    huanqiu_items = fetch_huanqiu_rss(max_items=8)
    all_items.extend(huanqiu_items)
    source_counts['环球时报'] = source_counts.get('环球时报', 0) + len(huanqiu_items)"""

content = content.replace(old_policy, new_policy)

# 5. Update fetch_all_events to use multi-source aggregation
old_events = """def fetch_all_events():
    \"\"\"抓取所有持仓+建仓股的最新新闻，聚合分类\"\"\"
    all_news = []
    for stock in MONITOR_STOCKS:
        news = fetch_sina_stock_news(stock['code'], max_items=5)"""

new_events = """def fetch_all_events():
    \"\"\"
    抓取所有持仓+建仓股的最新新闻，聚合多来源分类。
    来源：新浪财经 + 巨潮资讯 + 东方财富 + 人民网 + 环球时报
    \"\"\"
    all_news = []
    
    # 1. 新浪财经个股新闻（核心来源）
    for stock in MONITOR_STOCKS:
        news = fetch_sina_stock_news(stock['code'], max_items=5)"""

content = content.replace(old_events, new_events)

# 6. Add multi-source aggregation after sina fetch in fetch_all_events
old_events_body = """    # 去重（按title+date）
    seen = set()
    unique = []
    for n in all_news:
        key = n['title'] + n['date']
        if key not in seen:
            seen.add(key)
            unique.append(n)
    
    # 按日期倒序
    unique.sort(key=lambda x: x['date'] + x['time'], reverse=True)
    
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
    
    return categories, len(unique)"""

new_events_body = """    # 2. 巨潮资讯公告
    for stock in MONITOR_STOCKS:
        cninfo_news = fetch_cninfo_announcements(stock['code'], page_size=3)
        for n in cninfo_news:
            n['stock_name'] = stock['name']
        all_news.extend(cninfo_news)
    
    # 3. 东方财富新闻
    for stock in MONITOR_STOCKS:
        em_news = fetch_eastmoney_news(stock['code'], max_items=3)
        for n in em_news:
            n['stock_name'] = stock['name']
        all_news.extend(em_news)
    
    # 4. 宏观政策新闻（筛选与持仓/建仓股相关的）
    policy_news = fetch_policy_news() + fetch_people_rss(max_items=5) + fetch_huanqiu_rss(max_items=5)
    stock_keywords = set()
    for s in MONITOR_STOCKS:
        stock_keywords.add(s['name'])
        stock_keywords.add(s['code'].replace('.SH', '').replace('.SZ', ''))
    # 主营业务关键词
    business_kw = ['轨交', '半导体', '锶盐', '电解锰', '电气设备', '造纸', '通用设备',
                   '煤制烯烃', '钴', '镍', '锂电', '医药', '银行', '核电', '铝', '水电',
                   '锂电设备', '新能源', '光伏', '储能']
    stock_keywords.update(business_kw)
    
    for n in policy_news:
        title = n.get('title', '')
        if any(kw in title for kw in stock_keywords):
            n['stock_name'] = '宏观关联'
            all_news.append(n)
    
    # 去重（按title+date+source）
    seen = set()
    unique = []
    for n in all_news:
        key = n.get('title', '') + n.get('date', '') + n.get('source', '')
        if key and key not in seen:
            seen.add(key)
            unique.append(n)
    
    # 按日期倒序
    unique.sort(key=lambda x: x.get('date', '') + x.get('time', ''), reverse=True)
    
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
    
    return categories, len(unique)"""

content = content.replace(old_events_body, new_events_body)

with open('stock_service.py', 'w') as f:
    f.write(content)

print("✅ stock_service.py patched successfully")
