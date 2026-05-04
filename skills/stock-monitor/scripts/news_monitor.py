#!/usr/bin/env python3
"""
新闻监控主脚本 - 持仓股新闻自动抓取、过滤、关联度评分

用法:
    python3 news_monitor.py --filter portfolio --max 50
    python3 news_monitor.py --filter all --max 100 --output /tmp/news.json
    python3 news_monitor.py --keyword 九州一轨 --max 20

过滤:
    portfolio   - 持仓/建仓股直接关联
    all         - 全部新闻（不过滤）
    geo         - 地缘国际
    policy      - 政策宏观
    chain       - 产业链
    market      - 市场资金

关联度:
    direct      - 持仓直接关联（score=3）
    industry    - 行业关联（score=2）
    none        - 一般财经（score=0）
"""
import argparse
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tushare as ts
import json
import re
from datetime import datetime, timedelta
from utils import (
    ALL_STOCK_CODES, HOLDINGS, WATCHLIST, STOCK_KEYWORDS,
    get_tushare_token, save_json
)

# 新闻分类关键词映射
CLASS_KWS = {
    'policy': ['政策', '央行', '财政', '降准', '降息', '税率', '改革', '国务院', '发改委', '监管'],
    'company': ['九州一轨', '宝丰能源', '华友钴业', '红星发展', '禾望电气', '晨鸣', '鑫磊', '科伦', '招商银行', '长江电力', '中国核电', '中国铝业'],
    'material': ['碳酸锂', '电解钴', '锶', '锰', '甲醇', '原油', '纸浆', '铝', '铜', '镍', '锌'],
    'finance': ['A股', '港股', '美股', '涨停', '跌停', '指数', '大盘', '牛市', '熊市', '反弹'],
    'chain': ['新能源', '锂电池', '光伏', '风电', '核电', '轨交', '造纸', '医药', '银行'],
    'geo': ['中东', '以色列', '加沙', '哈马斯', '胡塞', '红海', '朝鲜', '台海', '南海', '俄乌', '北约', '特朗普', '关税', '贸易战', '冲突', '战争', '导弹', '核']
}

# 排除词（社会/娱乐/旅游等无关新闻）
EXCLUDE_KWS = ['票房', '景区', '民警', '门票', '离婚', '水獭', '红旗渠', '五一档', '黄山', '演唱会', '明星', '网红', '综艺', '选秀']


def init_tushare():
    token = get_tushare_token()
    if not token:
        print("[ERR] Tushare Token not found")
        sys.exit(1)
    ts.set_token(token)
    return ts.pro_api()


def classify_multi_tags(title, content=''):
    """多标签分类"""
    text = (title + ' ' + content).lower()
    tags = []
    for cat, kws in CLASS_KWS.items():
        for kw in kws:
            if kw in text:
                tags.append(cat)
                break
    return list(set(tags)) if tags else ['market']


def mark_relevance(title, content=''):
    """标记新闻关联度"""
    text = (title + ' ' + content).lower()
    
    # 直接关联（持仓/建仓股名称）
    direct_names = [STOCK_KEYWORDS[c]['name'] for c in HOLDINGS + WATCHLIST]
    for name in direct_names:
        if name in text:
            return 'direct', 3
    
    # 行业关联
    for code, info in STOCK_KEYWORDS.items():
        if info.get('sector') in text:
            return 'industry', 2
    
    return 'none', 0


def fetch_news(pro, max_items=100, start_date=None, end_date=None):
    """从Tushare抓取新闻"""
    if not end_date:
        end_date = datetime.now().strftime('%Y%m%d')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=3)).strftime('%Y%m%d')
    
    sources = ['sina', '10jqka', 'eastmoney', 'cls', 'yicai']
    all_items = []
    
    for src in sources:
        try:
            df = pro.major_news(src=src, start_date=start_date, end_date=end_date)
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    all_items.append({
                        'id': f"{src}_{row.get('datetime', '')}",
                        'title': row.get('title', ''),
                        'content': row.get('content', ''),
                        'source': src,
                        'time': row.get('datetime', '')
                    })
        except Exception as e:
            print(f"[WARN] {src} fetch failed: {e}")
    
    # 去重（相同标题）
    seen = set()
    unique = []
    for item in all_items:
        key = item['title'][:30]
        if key not in seen:
            seen.add(key)
            unique.append(item)
    
    return unique[:max_items]


def filter_news(items, filter_type='portfolio'):
    """过滤新闻"""
    filtered = []
    
    for item in items:
        title = item.get('title', '')
        
        # 排除社会新闻
        if any(kw in title for kw in EXCLUDE_KWS):
            continue
        
        # 分类和关联度
        cat_tags = classify_multi_tags(title, item.get('content', ''))
        level, score = mark_relevance(title, item.get('content', ''))
        
        item['catTags'] = cat_tags
        item['relevance_level'] = level
        item['relevance_score'] = score
        
        # 过滤
        if filter_type == 'all':
            filtered.append(item)
        elif filter_type == 'portfolio' and level == 'direct':
            filtered.append(item)
        elif filter_type == 'geo' and 'geo' in cat_tags:
            filtered.append(item)
        elif filter_type == 'policy' and 'policy' in cat_tags:
            filtered.append(item)
        elif filter_type == 'chain' and 'chain' in cat_tags:
            filtered.append(item)
        elif filter_type == 'market' and 'market' in cat_tags:
            filtered.append(item)
        elif filter_type == 'company' and 'company' in cat_tags:
            filtered.append(item)
    
    # 排序：关联度高的置顶
    filtered.sort(key=lambda x: (x.get('relevance_score', 0), x.get('time', '')), reverse=True)
    return filtered


def print_news(items, max_display=20):
    """打印新闻列表"""
    print(f"\n{'='*60}")
    print(f"  新闻监控结果（共{len(items)}条）")
    print(f"{'='*60}")
    
    for i, item in enumerate(items[:max_display]):
        level = item.get('relevance_level', 'none')
        score = item.get('relevance_score', 0)
        tags = ','.join(item.get('catTags', []))
        
        # 颜色标记
        prefix = "🔴" if level == 'direct' else ("🟡" if level == 'industry' else "⚪")
        
        print(f"\n{prefix} [{i+1}] {item.get('title', '')}")
        print(f"    来源: {item.get('source', '未知')} | 时间: {item.get('time', '')}")
        print(f"    分类: {tags} | 关联度: {level}(score={score})")


def main():
    parser = argparse.ArgumentParser(description='Stock News Monitor')
    parser.add_argument('--filter', choices=['all', 'portfolio', 'geo', 'policy', 'chain', 'market', 'company'],
                        default='portfolio', help='News filter type')
    parser.add_argument('--max', type=int, default=50, help='Max news items to fetch')
    parser.add_argument('--keyword', help='Custom keyword filter')
    parser.add_argument('--output', help='Output JSON file')
    parser.add_argument('--days', type=int, default=3, help='Fetch news from last N days')
    
    args = parser.parse_args()
    
    pro = init_tushare()
    
    # 抓取新闻
    start_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y%m%d')
    end_date = datetime.now().strftime('%Y%m%d')
    
    print(f"[News] Fetching from {start_date} to {end_date}...")
    items = fetch_news(pro, args.max, start_date, end_date)
    print(f"[News] Fetched {len(items)} raw items")
    
    # 过滤
    filtered = filter_news(items, args.filter)
    
    # 自定义关键词过滤
    if args.keyword:
        filtered = [i for i in filtered if args.keyword in i.get('title', '')]
    
    print(f"[News] Filtered to {len(filtered)} items")
    
    # 打印
    print_news(filtered)
    
    # 保存
    if args.output:
        save_json(filtered, args.output)


if __name__ == '__main__':
    main()
