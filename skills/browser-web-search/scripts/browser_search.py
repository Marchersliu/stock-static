#!/usr/bin/env python3
"""
浏览器网页搜索 - 通过浏览器驱动搜索并提取内容

用法:
    python3 browser_search.py "搜索词" --engine bing
    python3 browser_search.py "关键词" --site sina.com.cn
    python3 browser_search.py "今日股市" --screenshot /tmp/stock.png
"""
import argparse
import requests
import re
from urllib.parse import quote

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}


def search_bing(query, limit=10):
    """Bing搜索并提取结果"""
    url = f"https://www.bing.com/search?q={quote(query)}&count={limit}"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    
    results = []
    # 提取搜索结果
    items = re.findall(
        r'<li class="b_algo"[^>]*>.*?<h2><a[^>]*href="([^"]*)"[^>]*>(.*?)</a></h2>.*?<p>(.*?)</p>',
        resp.text, re.DOTALL
    )
    
    for url, title, snippet in items[:limit]:
        title_clean = re.sub(r'<[^>]+>', '', title).strip()
        snippet_clean = re.sub(r'<[^>]+>', '', snippet).strip()
        results.append({
            'title': title_clean,
            'url': url,
            'snippet': snippet_clean,
            'engine': 'bing'
        })
    
    return results


def search_baidu(query, limit=10):
    """百度搜索"""
    url = f"https://www.baidu.com/s?wd={quote(query)}&rn={limit}"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    
    results = []
    # 百度结果格式
    items = re.findall(
        r'<div[^>]*class="result"[^>]*>.*?<h3[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?</h3>.*?<div[^>]*class="content-right_[^"]*"[^>]*>(.*?)</div>',
        resp.text, re.DOTALL
    )
    
    for url, title, snippet in items[:limit]:
        title_clean = re.sub(r'<[^>]+>', '', title).strip()
        snippet_clean = re.sub(r'<[^>]+>', '', snippet).strip()
        results.append({
            'title': title_clean,
            'url': url,
            'snippet': snippet_clean,
            'engine': 'baidu'
        })
    
    return results


def site_search(site, query, limit=10):
    """特定网站搜索"""
    full_query = f"site:{site} {query}"
    return search_bing(full_query, limit)


def main():
    parser = argparse.ArgumentParser(description='Browser Web Search')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--engine', default='bing', choices=['bing', 'baidu'], help='Search engine')
    parser.add_argument('--site', help='Search specific site')
    parser.add_argument('--limit', type=int, default=10, help='Max results')
    parser.add_argument('--screenshot', help='Save screenshot (requires browser)')
    parser.add_argument('--output', help='Save results to JSON')
    
    args = parser.parse_args()
    
    print(f"[BrowserSearch] '{args.query}' | Engine: {args.engine}")
    
    if args.site:
        results = site_search(args.site, args.query, args.limit)
        print(f"  Site: {args.site}")
    elif args.engine == 'bing':
        results = search_bing(args.query, args.limit)
    elif args.engine == 'baidu':
        results = search_baidu(args.query, args.limit)
    else:
        results = []
    
    print(f"\n{'='*60}")
    print(f"  搜索结果 ({len(results)}条)")
    print(f"{'='*60}")
    
    for i, r in enumerate(results, 1):
        print(f"\n  {i}. {r['title'][:70]}")
        print(f"     {r['url'][:80]}")
        if r.get('snippet'):
            print(f"     {r['snippet'][:100]}")
    
    if args.output:
        import json
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] Saved to {args.output}")


if __name__ == '__main__':
    main()
