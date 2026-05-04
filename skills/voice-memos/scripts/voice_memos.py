#!/usr/bin/env python3
"""
语音备忘录 - 语音转文字、时间戳、标签、搜索

用法:
    python3 voice_memos.py transcribe /path/to/audio.m4a --output note.md
    python3 voice_memos.py list
    python3 voice_memos.py search "会议"
"""
import argparse
import json
import os
import hashlib
from datetime import datetime

MEMO_DIR = '/Users/hf/.kimi_openclaw/workspace/memory/voice_memos'
INDEX_PATH = os.path.join(MEMO_DIR, 'index.json')


def ensure_dir():
    os.makedirs(MEMO_DIR, exist_ok=True)
    if not os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, 'w', encoding='utf-8') as f:
            json.dump({'memos': []}, f)


def load_index():
    ensure_dir()
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_index(index):
    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def add_memo(text, source, tags=None):
    """添加一条备忘录"""
    now = datetime.now()
    memo_id = now.strftime('%Y%m%d_%H%M%S')
    
    memo = {
        'id': memo_id,
        'timestamp': now.isoformat(),
        'source': source,
        'text': text,
        'tags': tags or [],
        'length': len(text),
    }
    
    # 保存文件
    filename = f"{memo_id}.md"
    filepath = os.path.join(MEMO_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# Voice Memo - {memo_id}\n\n")
        f.write(f"**Time**: {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Source**: {source}\n\n")
        if tags:
            f.write(f"**Tags**: {', '.join(tags)}\n\n")
        f.write("---\n\n")
        f.write(text)
        f.write("\n")
    
    # 更新索引
    index = load_index()
    index['memos'].insert(0, memo)
    save_index(index)
    
    return memo


def list_memos(limit=20):
    """列出备忘录"""
    index = load_index()
    memos = index['memos'][:limit]
    
    print(f"\n{'='*60}")
    print(f"  语音备忘录 ({len(index['memos'])}条, 显示前{limit}条)")
    print(f"{'='*60}")
    
    for i, memo in enumerate(memos, 1):
        ts = memo['timestamp'][:16].replace('T', ' ')
        text_preview = memo['text'][:60].replace('\n', ' ')
        tags = ', '.join(memo.get('tags', []))
        print(f"\n  {i}. [{ts}] {text_preview}...")
        if tags:
            print(f"     Tags: {tags}")
        print(f"     ID: {memo['id']}")


def search_memos(query):
    """搜索备忘录"""
    index = load_index()
    results = []
    
    for memo in index['memos']:
        score = 0
        text_lower = memo['text'].lower()
        query_lower = query.lower()
        
        # 文本匹配
        if query_lower in text_lower:
            score += 10
        # 标签匹配
        for tag in memo.get('tags', []):
            if query_lower in tag.lower():
                score += 5
        # 部分匹配
        words = query_lower.split()
        for word in words:
            if word in text_lower:
                score += 1
        
        if score > 0:
            results.append((score, memo))
    
    # 排序
    results.sort(key=lambda x: x[0], reverse=True)
    
    print(f"\n{'='*60}")
    print(f"  搜索结果: '{query}' ({len(results)}条)")
    print(f"{'='*60}")
    
    for score, memo in results[:10]:
        ts = memo['timestamp'][:16].replace('T', ' ')
        text_preview = memo['text'][:80].replace('\n', ' ')
        print(f"\n  [{score}分] {ts}")
        print(f"  {text_preview}...")
        print(f"  ID: {memo['id']}")


def transcribe_file(audio_path, output=None):
    """转录音频文件（框架函数）"""
    print(f"[Voice] Transcribing: {audio_path}")
    
    # 检查文件
    if not os.path.exists(audio_path):
        print(f"[ERR] File not found: {audio_path}")
        return
    
    size = os.path.getsize(audio_path)
    print(f"  Size: {size:,} bytes")
    
    # 框架提示
    print()
    print("="*60)
    print("  语音转文字框架")
    print("="*60)
    print()
    print("  支持的音频格式: .wav, .mp3, .m4a, .flac")
    print()
    print("  实际转录方式:")
    print("  1. OpenAI Whisper API (在线)")
    print("  2. 本地 whisper 模型 (pip3 install openai-whisper)")
    print("  3. macOS 系统听写 (快捷键按两下Fn)")
    print()
    print("  使用方法：告诉agent '转录这个音频文件'")
    print("  agent会自动调用合适的转录工具")
    print("="*60)
    
    # 生成占位记录
    memo = add_memo(
        text=f"[待转录] {audio_path}\n\n文件大小: {size:,} bytes\n",
        source=f"audio:{audio_path}",
        tags=['pending', 'transcription']
    )
    
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            f.write(f"# Transcription - {audio_path}\n\n")
            f.write(f"Status: Pending\n")
            f.write(f"File: {audio_path}\n")
            f.write(f"Size: {size:,} bytes\n")
        print(f"\n[OK] Placeholder saved: {output}")
    
    print(f"\n[OK] Memo recorded: {memo['id']}")


def main():
    parser = argparse.ArgumentParser(description='Voice Memos')
    subparsers = parser.add_subparsers(dest='command')
    
    # transcribe
    p = subparsers.add_parser('transcribe')
    p.add_argument('audio', help='Audio file path')
    p.add_argument('--output', help='Output file')
    
    # list
    subparsers.add_parser('list')
    
    # search
    p = subparsers.add_parser('search')
    p.add_argument('query', help='Search query')
    
    # add (manual)
    p = subparsers.add_parser('add')
    p.add_argument('text', help='Memo text')
    p.add_argument('--tags', nargs='+', help='Tags')
    
    args = parser.parse_args()
    
    if args.command == 'transcribe':
        transcribe_file(args.audio, args.output)
    
    elif args.command == 'list':
        list_memos()
    
    elif args.command == 'search':
        search_memos(args.query)
    
    elif args.command == 'add':
        memo = add_memo(args.text, 'manual', args.tags)
        print(f"[OK] Added: {memo['id']}")
    
    else:
        parser.print_help()
        print()
        print("Storage:", MEMO_DIR)
        ensure_dir()
        index = load_index()
        print(f"Total memos: {len(index['memos'])}")


if __name__ == '__main__':
    main()
