#!/usr/bin/env python3
"""
Fix fetch_all_events in stock_service.py to add multi-source aggregation
"""
with open('stock_service.py', 'r') as f:
    content = f.read()

# Find fetch_all_events function and replace its body
old_body = '''    # 去重（按title+date）
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
        categories[cat]['items'].append(n)
    
    return {
        'categories': categories,
        'total': len(unique),
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }'''

new_body = '''    # 2. 巨潮资讯公告
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
    
    return {
        'categories': categories,
        'total': len(unique),
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }'''

if old_body in content:
    content = content.replace(old_body, new_body)
    print("✅ fetch_all_events body replaced")
else:
    print("⚠️ old_body not found, trying partial match")
    # Try to find and replace the return block only
    old_return = """    return {
        'categories': categories,
        'total': len(unique),
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }"""
    
    new_return = """    return {
        'categories': categories,
        'total': len(unique),
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }"""
    
    # Actually we need to insert the multi-source code before the dedup block
    # Find the dedup block
    dedup_marker = "    # 去重（按title+date）"
    if dedup_marker in content:
        idx = content.find(dedup_marker)
        # Insert multi-source code before dedup
        multi_source_code = '''    # 2. 巨潮资讯公告
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
    
'''
        content = content[:idx] + multi_source_code + content[idx:]
        print("✅ Multi-source code inserted before dedup")
    else:
        print("❌ Could not find dedup marker")

with open('stock_service.py', 'w') as f:
    f.write(content)

# Verify syntax
import py_compile
try:
    py_compile.compile('stock_service.py', doraise=True)
    print("✅ Syntax check passed")
except Exception as e:
    print(f"❌ Syntax error: {e}")
