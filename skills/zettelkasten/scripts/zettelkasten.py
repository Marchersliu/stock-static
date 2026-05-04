#!/usr/bin/env python3
"""Zettelkasten卡片盒笔记法 - 卢曼笔记系统"""
import argparse, json, os, re
from datetime import datetime

ZK_DIR = '/Users/hf/.kimi_openclaw/workspace/memory/zettelkasten'
INDEX_PATH = os.path.join(ZK_DIR, 'index.json')

def ensure_zk():
    os.makedirs(ZK_DIR, exist_ok=True)
    if not os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, 'w', encoding='utf-8') as f:
            json.dump({'notes': [], 'links': []}, f)

def load_index():
    ensure_zk()
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_index(idx):
    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)

def generate_id(note_type):
    """生成ID: Z202605041200"""
    now = datetime.now()
    seq = len(load_index()['notes']) + 1
    return f"{note_type}{now.strftime('%Y%m%d%H%M')}{seq:04d}"

def add_note(content, note_type='Z', links=None, source=None):
    """添加笔记"""
    idx = load_index()
    note_id = generate_id(note_type)
    
    note = {
        'id': note_id,
        'type': note_type,
        'content': content,
        'links': links or [],
        'source': source,
        'created': datetime.now().isoformat(),
        'accessed': 0
    }
    
    # 保存文件
    filepath = os.path.join(ZK_DIR, f'{note_id}.md')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# {note_id}\n\n")
        f.write(f"**Type**: {note_type} | **Date**: {note['created'][:10]}\n\n")
        if source:
            f.write(f"**Source**: {source}\n\n")
        f.write(f"**Links**: {', '.join(links) if links else 'None'}\n\n")
        f.write("---\n\n")
        f.write(content)
        f.write("\n")
    
    idx['notes'].append(note)
    
    # 记录链接
    for link in (links or []):
        idx['links'].append({'from': note_id, 'to': link})
    
    save_index(idx)
    print(f'[ZK] Added: {note_id} [{note_type}]')
    return note_id

def search_notes(query):
    """搜索笔记"""
    idx = load_index()
    results = []
    for note in idx['notes']:
        score = 0
        if query.lower() in note['content'].lower(): score += 10
        if query.lower() in note['id'].lower(): score += 5
        for link in note.get('links', []):
            if query.lower() in link.lower(): score += 3
        if score > 0:
            results.append((score, note))
    
    results.sort(key=lambda x: x[0], reverse=True)
    print(f'[ZK] Search "{query}" -> {len(results)} results')
    for score, note in results[:10]:
        print(f'  [{score}] {note["id"]}: {note["content"][:60]}...')

def graph_notes():
    """显示笔记网络"""
    idx = load_index()
    notes = {n['id']: n for n in idx['notes']}
    
    print(f'\n[ZK] Network: {len(notes)} notes, {len(idx["links"])} links')
    print('\n  高连接度笔记:')
    link_counts = {}
    for link in idx['links']:
        link_counts[link['from']] = link_counts.get(link['from'], 0) + 1
        link_counts[link['to']] = link_counts.get(link['to'], 0) + 1
    
    top = sorted(link_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    for nid, count in top:
        content = notes.get(nid, {}).get('content', '')[:40]
        print(f'    {nid} ({count} links): {content}...')

def main():
    parser = argparse.ArgumentParser(description='Zettelkasten')
    sub = parser.add_subparsers(dest='cmd')
    
    p = sub.add_parser('add')
    p.add_argument('content')
    p.add_argument('--type', default='Z', choices=['F', 'L', 'Z', 'P'])
    p.add_argument('--links', nargs='+')
    p.add_argument('--source')
    
    p = sub.add_parser('search')
    p.add_argument('query')
    
    sub.add_parser('graph')
    
    p = sub.add_parser('list')
    p.add_argument('--type')
    
    args = parser.parse_args()
    
    if args.cmd == 'add':
        add_note(args.content, args.type, args.links, args.source)
    elif args.cmd == 'search':
        search_notes(args.query)
    elif args.cmd == 'graph':
        graph_notes()
    elif args.cmd == 'list':
        idx = load_index()
        notes = [n for n in idx['notes'] if not args.type or n['type'] == args.type]
        print(f'[ZK] {len(notes)} notes:')
        for n in notes[:20]:
            print(f'  {n["id"]} [{n["type"]}]: {n["content"][:50]}...')
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
