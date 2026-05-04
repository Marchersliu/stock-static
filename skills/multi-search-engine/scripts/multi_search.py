#!/usr/bin/env python3
"""
多引擎聚合搜索 - 同时查询多个搜索引擎，去重评分排序

用法:
    python3 multi_search.py "搜索词" --engines brave,duckduckgo --limit 10
    python3 multi_search.py "AI芯片" --compare
    python3 multi_search.py "碳酸锂价格" --output results.json
"""
import argparse
import json
import requests
import re
import time
from urllib.parse import quote, urljoin
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 引擎置信度权重
ENGINE_WEIGHTS = {
    'brave': 0.95,
    'duckduckgo': 0.85,
    'bing': 0.80,
    'baidu': 0.70,
    'google': 0.75,
}

# 域名权威度
DOMAIN_AUTHORITY = {
    'gov.cn': 0.95, 'pbc.gov.cn': 0.95, 'stats.gov.cn': 0.95,
    'smm.cn': 0.90, 'mysteel.com': 0.90, 'sci99.com': 0.90,
    'eastmoney.com': 0.85, 'sina.com.cn': 0.80, 'qq.com': 0.80,
    'zhihu.com': 0.75, 'csdn.net': 0.70,
}


def brave_search(query, limit=10):
    """Brave Search API（免费额度）"""
    try:
        # Brave Search 公开端点（无需key，有限制）
        url = f"https://search.brave.com/api/suggest?q={quote(query)}"
        # 或者使用 html 抓取
        url = f"https://search.brave.com/search?q={quote(query)}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        # 简单提取结果
        results = []
        # 提取标题和链接
        titles = re.findall(r'<a[^>]*class="[^"]*result-title[^"]*"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', resp.text, re.DOTALL)
        for url, title in titles[:limit]:
            title_clean = re.sub(r'<[^>]+>', '', title).strip()
            results.append({'title': title_clean, 'url': url, 'engine': 'brave', 'snippet': ''})
        return results
    except Exception as e:
        return [{'title': f'[ERR] Brave: {e}', 'url': '', 'engine': 'brave', 'snippet': ''}]


def duckduckgo_search(query, limit=10):
    """DuckDuckGo HTML搜索"""
    try:
        url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        results = []
        # 提取结果
        items = re.findall(
            r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?'
            r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
            resp.text, re.DOTALL
        )
        for url, title, snippet in items[:limit]:
            title_clean = re.sub(r'<[^>]+>', '', title).strip()
            snippet_clean = re.sub(r'<[^>]+>', '', snippet).strip()
            results.append({'title': title_clean, 'url': url, 'engine': 'duckduckgo', 'snippet': snippet_clean})
        return results
    except Exception as e:
        return [{'title': f'[ERR] DDG: {e}', 'url': '', 'engine': 'duckduckgo', 'snippet': ''}]


def bing_search(query, limit=10):
    """Bing HTML搜索"""
    try:
        url = f"https://www.bing.com/search?q={quote(query)}&count={limit}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        results = []
        # 提取结果
        items = re.findall(
            r'<li class="b_algo"[^>]*>.*?<h2><a[^>]*href="([^"]*)"[^>]*>(.*?)</a></h2>.*?'
            r'<p>(.*?)</p>',
            resp.text, re.DOTALL
        )
        for url, title, snippet in items[:limit]:
            title_clean = re.sub(r'<[^>]+>', '', title).strip()
            snippet_clean = re.sub(r'<[^>]+>', '', snippet).strip()
            results.append({'title': title_clean, 'url': url, 'engine': 'bing', 'snippet': snippet_clean})
        return results
    except Exception as e:
        return [{'title': f'[ERR] Bing: {e}', 'url': '', 'engine': 'bing', 'snippet': ''}]


def score_result(result, all_results):
    """对单个结果评分"""
    score = 0
    
    # 引擎权重
    engine = result.get('engine', 'unknown')
    score += ENGINE_WEIGHTS.get(engine, 0.5) * 30
    
    # 多引擎确认
    url = result.get('url', '')
    same_url_count = sum(1 for r in all_results if r.get('url') == url and r.get('url'))
    score += same_url_count * 25
    
    # 域名权威度
    domain = re.search(r'https?://([^/]+)', url)
    if domain:
        domain_str = domain.group(1)
        for auth_domain, weight in DOMAIN_AUTHORITY.items():
            if auth_domain in domain_str:
                score += weight * 20
                break
    
    # 时效性（标题中有日期）
    title = result.get('title', '')
    if re.search(r'202[456]', title):
        score += 10
    
    # 完整性（有snippet）
    if result.get('snippet') and len(result['snippet']) > 20:
        score += 10
    
    return round(score, 1)


def deduplicate_results(results):
    """去重并评分"""
    # 按URL分组
    url_map = {}
    for r in results:
        url = r.get('url', '')
        if not url:
            continue
        # 规范化URL
        url_norm = re.sub(r'\?.*$', '', url)
        if url_norm not in url_map:
            url_map[url_norm] = []
        url_map[url_norm].append(r)
    
    # 合并同一URL的结果
    merged = []
    for url_norm, items in url_map.items():
        best = items[0]
        # 合并引擎信息
        engines = list(set(r.get('engine', '') for r in items))
        best['engines'] = engines
        best['url'] = url_norm
        merged.append(best)
    
    # 评分
    all_results = results
    for r in merged:
        r['score'] = score_result(r, all_results)
    
    # 排序
    merged.sort(key=lambda x: x['score'], reverse=True)
    return merged


def search(query, engines=None, limit=10, compare=False):
    """多引擎搜索主函数"""
    if engines is None:
        engines = ['brave', 'duckduckgo', 'bing']
    
    print(f"[Search] Query: '{query}'")
    print(f"[Search] Engines: {', '.join(engines)}")
    
    all_results = []
    engine_results = {}
    
    for engine in engines:
        if engine == 'brave':
            results = brave_search(query, limit)
        elif engine == 'duckduckgo':
            results = duckduckgo_search(query, limit)
        elif engine == 'bing':
            results = bing_search(query, limit)
        else:
            continue
        
        engine_results[engine] = results
        all_results.extend(results)
        print(f"  [{engine}] {len(results)} results")
        time.sleep(0.5)  # 礼貌延迟
    
    # 去重评分
    final_results = deduplicate_results(all_results)
    
    if compare:
        return final_results, engine_results
    return final_results[:limit]


def main():
    parser = argparse.ArgumentParser(description='Multi-Engine Search')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--engines', default='brave,duckduckgo,bing', help='Comma-separated engines')
    parser.add_argument('--limit', type=int, default=10, help='Max results')
    parser.add_argument('--compare', action='store_true', help='Show per-engine results')
    parser.add_argument('--output', help='Save to JSON file')
    
    args = parser.parse_args()
    
    engines = [e.strip() for e in args.engines.split(',')]
    
    if args.compare:
        final, per_engine = search(args.query, engines, args.limit, compare=True)
        print(f"\n{'='*60}")
        print(f"  各引擎原始结果")
        print(f"{'='*60}")
        for eng, results in per_engine.items():
            print(f"\n  [{eng}] {len(results)}条")
            for i, r in enumerate(results[:5], 1):
                print(f"    {i}. {r['title'][:60]}")
    else:
        final = search(args.query, engines, args.limit)
    
    print(f"\n{'='*60}")
    print(f"  🏆 聚合结果（去重评分排序）")
    print(f"{'='*60}")
    
    for i, r in enumerate(final[:args.limit], 1):
        engines_str = ','.join(r.get('engines', [r.get('engine', '')]))
        print(f"\n  {i}. [{r['score']:.0f}分] {r['title'][:70]}")
        print(f"     URL: {r['url'][:80]}")
        if r.get('snippet'):
            print(f"     {r['snippet'][:120]}")
        print(f"     来源: {engines_str}")
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(final, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] Saved to {args.output}")


if __name__ == '__main__':
    main()
