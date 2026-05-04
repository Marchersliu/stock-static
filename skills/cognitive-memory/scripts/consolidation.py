#!/usr/bin/env python3
"""
记忆巩固脚本 - 从session日志自动提取认知记忆

功能:
    读取memory/YYYY-MM-DD.md日志文件
    自动提取关键事件（bug修复、决策、纠正、错误）
    5W1H编码写入cognitive_memory.json
    更新概念网络和联想关联

用法:
    python3 consolidation.py --file memory/2026-05-04.md
    python3 consolidation.py --latest          # 自动找最新日志
    python3 consolidation.py --auto            # 扫描最近3天并巩固
"""
import argparse
import json
import os
import re
import glob
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory_manager import init_db, load_db, save_db, encode_episode, encode_concept

MEMORY_DIR = '/Users/hf/.kimi_openclaw/workspace/memory'


# 事件提取模式
EVENT_PATTERNS = {
    'bug_fix': {
        'patterns': [
            r'【现象】[:：](.+?)(?=【|$)',
            r'【根因】[:：](.+?)(?=【|$)',
            r'【修复】[:：](.+?)(?=【|$)',
            r'Bug[修复Fix][:：](.+?)(?=\n|$)',
            r'修复[:：](.+?)(?=\n|$)',
        ],
        'emotional_weight': 0.8,
        'tags': ['bug修复']
    },
    'decision': {
        'patterns': [
            r'【决定】[:：](.+?)(?=【|$)',
            r'【结论】[:：](.+?)(?=【|$)',
            r'决定[:：](.+?)(?=\n|$)',
            r'采用(.+?)(?=方案|策略|方法)',
        ],
        'emotional_weight': 0.7,
        'tags': ['决策']
    },
    'correction': {
        'patterns': [
            r'纠正[:：](.+?)(?=\n|$)',
            r'【纠正】[:：](.+?)(?=【|$)',
            r'[对错]了[:：](.+?)(?=\n|$)',
        ],
        'emotional_weight': 0.9,
        'tags': ['纠正']
    },
    'creation': {
        'patterns': [
            r'创建(.+?)(?=文件|脚本|技能|模块)',
            r'新建(.+?)(?=文件|脚本|技能|模块)',
            r'安装(.+?)(?=技能|模块)',
        ],
        'emotional_weight': 0.6,
        'tags': ['创建']
    },
    'issue': {
        'patterns': [
            r'【问题】[:：](.+?)(?=【|$)',
            r'遗留问题[:：](.+?)(?=\n|$)',
            r'TODO[:：](.+?)(?=\n|$)',
        ],
        'emotional_weight': 0.5,
        'tags': ['待解决']
    }
}


def extract_events_from_log(filepath):
    """从日志文件中提取事件"""
    if not os.path.exists(filepath):
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    events = []
    date_str = os.path.basename(filepath).replace('.md', '')
    
    # 按行扫描
    lines = content.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        for event_type, config in EVENT_PATTERNS.items():
            for pattern in config['patterns']:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    # 提取上下文
                    context_start = max(0, i - 3)
                    context_end = min(len(lines), i + 5)
                    context = '\n'.join(lines[context_start:context_end])
                    
                    # 提取5W1H
                    what = match.group(1).strip()[:200]
                    where = extract_where(context, content)
                    why = extract_why(context)
                    how = extract_how(context)
                    
                    event = {
                        'type': event_type,
                        'what': what,
                        'where': where,
                        'why': why,
                        'how': how,
                        'tags': config['tags'] + extract_additional_tags(context),
                        'emotional_weight': config['emotional_weight'],
                        'date': date_str,
                        'source_line': line[:200]
                    }
                    events.append(event)
                    break  # 匹配到一种模式后跳过其他模式
    
    return events


def extract_where(context, full_content):
    """从上下文提取地点/文件"""
    # 匹配文件路径
    paths = re.findall(r'`([^`]+\.(?:py|js|html|css|json|md|sh))`', context)
    if paths:
        return ', '.join(paths[:3])
    
    # 匹配引用文件
    refs = re.findall(r'\[([^\]]+\.(?:py|js|html))\]', context)
    if refs:
        return ', '.join(refs[:3])
    
    # 匹配代码块中的文件
    code_files = re.findall(r'`([^`]+)`', context)
    for cf in code_files:
        if '.' in cf and len(cf) < 50:
            return cf
    
    return "workspace"


def extract_why(context):
    """从上下文提取原因"""
    why_patterns = [
        r'(?:根因|原因|因为|due to|because)[:：]?\s*(.+?)(?:\n|$)',
        r'(?:导致|造成|引起)[:：]?\s*(.+?)(?:\n|$)',
    ]
    for pattern in why_patterns:
        match = re.search(pattern, context, re.IGNORECASE)
        if match:
            return match.group(1).strip()[:200]
    return ""


def extract_how(context):
    """从上下文提取解决方法"""
    how_patterns = [
        r'(?:修复|解决|方法|方案|通过|使用)[:：]?\s*(.+?)(?:\n|$)',
        r'(?:改用|换成|调整为|统一为)[:：]?\s*(.+?)(?:\n|$)',
    ]
    for pattern in how_patterns:
        match = re.search(pattern, context, re.IGNORECASE)
        if match:
            return match.group(1).strip()[:200]
    return ""


def extract_additional_tags(context):
    """从上下文提取额外标签"""
    tags = []
    
    # 技术关键词
    tech_keywords = {
        'Tushare': ['tushare', 'ts.pro_api'],
        'GitHub': ['github', 'git push'],
        'Vercel': ['vercel'],
        '腾讯接口': ['qt.gtimg.cn', '腾讯'],
        '恒指': ['恒指', 'hsi', 'HSI'],
        '股票': ['股票', '行情', '持仓'],
        '中医': ['伤寒论', '方剂', '艾灸'],
        'HTML': ['html', 'html\b'],
        'JavaScript': ['js', 'javascript', '\bscript\b'],
        'Python': ['python', '\.py\b'],
        'CSS': ['css', '样式'],
        'API': ['api', '接口'],
        '缓存': ['缓存', 'cache'],
        '部署': ['部署', 'deploy'],
    }
    
    context_lower = context.lower()
    for tag, keywords in tech_keywords.items():
        if any(kw in context_lower for kw in keywords):
            tags.append(tag)
    
    return list(set(tags))[:5]  # 最多5个标签


def consolidate_file(filepath, dry_run=False):
    """巩固单个日志文件"""
    events = extract_events_from_log(filepath)
    
    if not events:
        print(f"[Consolidate] No events found in {os.path.basename(filepath)}")
        return 0
    
    print(f"[Consolidate] {os.path.basename(filepath)}: {len(events)} events found")
    
    if dry_run:
        for i, ev in enumerate(events[:5], 1):
            print(f"  {i}. [{ev['type']}] {ev['what'][:60]}")
        return len(events)
    
    init_db()
    db = load_db()
    
    encoded = 0
    for ev in events:
        # 去重检查
        exists = any(
            e['encoding']['what'] == ev['what'] and 
            e['encoding']['when'].startswith(ev['date'])
            for e in db['episodes']
        )
        if exists:
            continue
        
        # 编码情境记忆
        ep_id = encode_episode(
            what=ev['what'],
            where=ev['where'],
            why=ev['why'],
            how=ev['how'],
            tags=ev['tags'],
            emotional_weight=ev['emotional_weight']
        )
        
        # 提取关键概念
        key_concepts = ev['tags'] + [w for w in ev['what'].split() if len(w) > 2][:3]
        for concept in key_concepts:
            if concept not in db['concepts']:
                encode_concept(
                    name=concept,
                    definition=f"从'{ev['what'][:50]}'中提取的概念",
                    emotional_tag="neutral"
                )
        
        encoded += 1
    
    print(f"[Consolidate] Encoded {encoded} new memories")
    return encoded


def consolidate_latest():
    """巩固最新日志"""
    files = sorted(
        glob.glob(f"{MEMORY_DIR}/2026-*.md"),
        key=os.path.getmtime,
        reverse=True
    )
    if not files:
        print("[Consolidate] No memory files found")
        return 0
    
    return consolidate_file(files[0])


def consolidate_auto(days=3):
    """自动巩固最近N天"""
    files = sorted(
        glob.glob(f"{MEMORY_DIR}/2026-*.md"),
        key=os.path.getmtime,
        reverse=True
    )[:days]
    
    total = 0
    for f in files:
        total += consolidate_file(f)
    
    print(f"\n[Consolidate] Total {total} memories consolidated from {len(files)} files")
    return total


def main():
    parser = argparse.ArgumentParser(description='Memory Consolidation')
    parser.add_argument('--file', help='Specific memory file to consolidate')
    parser.add_argument('--latest', action='store_true', help='Consolidate latest log')
    parser.add_argument('--auto', action='store_true', help='Auto-consolidate recent logs')
    parser.add_argument('--days', type=int, default=3, help='Days to auto-consolidate')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    
    args = parser.parse_args()
    
    if args.file:
        consolidate_file(args.file, args.dry_run)
    elif args.latest:
        consolidate_latest()
    elif args.auto:
        consolidate_auto(args.days)
    else:
        consolidate_latest()


if __name__ == '__main__':
    main()
