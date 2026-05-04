#!/usr/bin/env python3
"""Obsidian笔记集成 - 读写Obsidian vault"""
import argparse, json, os, re

VAULT_PATH = os.path.expanduser('~/Documents/Obsidian')

def find_vault():
    """查找Obsidian vault路径"""
    candidates = [
        os.path.expanduser('~/Documents/Obsidian'),
        os.path.expanduser('~/Library/Mobile Documents/iCloud~md~obsidian/Documents'),
        os.path.expanduser('~/Obsidian'),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return VAULT_PATH

def search_notes(query, vault=None):
    """搜索笔记"""
    vault = vault or find_vault()
    results = []
    for root, dirs, files in os.walk(vault):
        for f in files:
            if f.endswith('.md'):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8') as fh:
                        content = fh.read()
                    if query.lower() in content.lower() or query.lower() in f.lower():
                        # 提取frontmatter
                        fm = {}
                        if content.startswith('---'):
                            fm_end = content.find('---', 3)
                            if fm_end > 0:
                                fm_text = content[3:fm_end].strip()
                                for line in fm_text.split('\n'):
                                    if ':' in line:
                                        k, v = line.split(':', 1)
                                        fm[k.strip()] = v.strip()
                        
                        results.append({
                            'file': f,
                            'path': path.replace(vault, ''),
                            'title': fm.get('title', f.replace('.md', '')),
                            'tags': fm.get('tags', '').split(',') if 'tags' in fm else [],
                            'preview': content[:200].replace('\n', ' ')
                        })
                except:
                    pass
    return results

def create_note(title, content, tags=None, vault=None):
    """创建笔记"""
    vault = vault or find_vault()
    os.makedirs(vault, exist_ok=True)
    filename = re.sub(r'[^\w\-]', '_', title) + '.md'
    filepath = os.path.join(vault, filename)
    
    frontmatter = f"""---
title: {title}
date: {__import__('datetime').datetime.now().isoformat()}
{('tags: ' + ', '.join(tags)) if tags else ''}
---

"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(frontmatter + content)
    print(f'[OK] Created: {filepath}')
    return filepath

def update_note(title, append=None, vault=None):
    """更新笔记"""
    vault = vault or find_vault()
    filename = re.sub(r'[^\w\-]', '_', title) + '.md'
    filepath = os.path.join(vault, filename)
    
    if os.path.exists(filepath) and append:
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(f'\n\n{append}\n')
        print(f'[OK] Updated: {filepath}')
    else:
        print(f'[ERR] Note not found: {filepath}')

def list_notes(vault=None, tag=None):
    """列出笔记"""
    vault = vault or find_vault()
    notes = []
    for root, dirs, files in os.walk(vault):
        for f in files:
            if f.endswith('.md'):
                notes.append(os.path.join(root, f).replace(vault, ''))
    
    if tag:
        filtered = []
        for n in notes:
            try:
                with open(os.path.join(vault, n.lstrip('/')), 'r', encoding='utf-8') as f:
                    content = f.read()
                if tag.lower() in content.lower():
                    filtered.append(n)
            except:
                pass
        notes = filtered
    
    print(f'[Notes] {len(notes)} notes in vault')
    for n in notes[:20]:
        print(f'  • {n}')

def main():
    parser = argparse.ArgumentParser(description='Obsidian Notes')
    sub = parser.add_subparsers(dest='cmd')
    
    p = sub.add_parser('search')
    p.add_argument('query')
    p.add_argument('--vault')
    
    p = sub.add_parser('create')
    p.add_argument('title')
    p.add_argument('--content', default='')
    p.add_argument('--tags', nargs='+')
    p.add_argument('--vault')
    
    p = sub.add_parser('update')
    p.add_argument('title')
    p.add_argument('--append', required=True)
    p.add_argument('--vault')
    
    p = sub.add_parser('list')
    p.add_argument('--vault')
    p.add_argument('--tag')
    
    args = parser.parse_args()
    
    if args.cmd == 'search':
        results = search_notes(args.query, args.vault)
        print(f'[Search] {len(results)} results:')
        for r in results[:10]:
            print(f'  • {r["title"]} {r["path"]}')
            print(f'    {r["preview"][:80]}...')
    
    elif args.cmd == 'create':
        create_note(args.title, args.content, args.tags, args.vault)
    
    elif args.cmd == 'update':
        update_note(args.title, args.append, args.vault)
    
    elif args.cmd == 'list':
        list_notes(args.vault, args.tag)
    
    else:
        parser.print_help()
        print(f'\nVault: {find_vault()}')

if __name__ == '__main__':
    main()
