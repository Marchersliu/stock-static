#!/usr/bin/env python3
"""RSS订阅聚合 - 管理RSS源，抓取、去重、分类、摘要"""
import argparse, json, os, feedparser, hashlib
from datetime import datetime

DB_PATH = '/Users/hf/.kimi_openclaw/workspace/memory/rss_feeds.json'

def load_db():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'feeds': [], 'items': []}

def save_db(db):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def add_feed(url, tag='general'):
    db = load_db()
    if not any(f['url'] == url for f in db['feeds']):
        db['feeds'].append({'url': url, 'tag': tag, 'added': datetime.now().isoformat()})
        save_db(db)
        print(f'[OK] Feed added: {url} [{tag}]')
    else:
        print(f'[INFO] Feed already exists: {url}')

def fetch_feeds(limit=50):
    db = load_db()
    new_items = []
    for feed in db['feeds']:
        try:
            d = feedparser.parse(feed['url'])
            for entry in d.entries[:limit]:
                item_id = hashlib.md5((feed['url'] + entry.get('title', '')).encode()).hexdigest()[:16]
                if not any(i['id'] == item_id for i in db['items']):
                    item = {
                        'id': item_id,
                        'title': entry.get('title', ''),
                        'link': entry.get('link', ''),
                        'summary': entry.get('summary', '')[:200],
                        'published': entry.get('published', ''),
                        'feed': feed['url'],
                        'tag': feed['tag'],
                        'fetched': datetime.now().isoformat()
                    }
                    new_items.append(item)
        except Exception as e:
            print(f'[ERR] {feed["url"]}: {e}')
    
    db['items'] = new_items + db['items']
    db['items'] = db['items'][:500]  # Keep last 500
    save_db(db)
    print(f'[OK] Fetched {len(new_items)} new items. Total: {len(db["items"])}')

def search_items(query):
    db = load_db()
    results = [i for i in db['items'] if query.lower() in i['title'].lower() or query.lower() in i['summary'].lower()]
    print(f'[Search] "{query}" -> {len(results)} results')
    for i, r in enumerate(results[:10], 1):
        print(f'  {i}. {r["title"][:60]} ({r["tag"]})')

def list_feeds():
    db = load_db()
    print(f'[Feeds] {len(db["feeds"])} subscribed:')
    for f in db['feeds']:
        print(f'  • {f["url"]} [{f["tag"]}]')

def main():
    parser = argparse.ArgumentParser(description='RSS Feeds')
    sub = parser.add_subparsers(dest='cmd')
    
    p = sub.add_parser('add')
    p.add_argument('url')
    p.add_argument('--tag', default='general')
    
    p = sub.add_parser('fetch')
    p.add_argument('--limit', type=int, default=50)
    
    p = sub.add_parser('search')
    p.add_argument('query')
    
    sub.add_parser('list')
    
    args = parser.parse_args()
    
    if args.cmd == 'add': add_feed(args.url, args.tag)
    elif args.cmd == 'fetch': fetch_feeds(args.limit)
    elif args.cmd == 'search': search_items(args.query)
    elif args.cmd == 'list': list_feeds()
    else: parser.print_help()

if __name__ == '__main__':
    main()
