#!/usr/bin/env python3
"""
更新 stock_dashboard.html 中的 PREMARKET_NEWS 静态数组
供 GitHub Pages 静态托管使用
"""
import json, re, os, sys, urllib.parse

# 加载 .env 环境变量
from pathlib import Path
dotenv_path = Path('/Users/hf/.kimi_openclaw/workspace/.env')
if dotenv_path.exists():
    with open(dotenv_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key, value)

# 导入 stock_service 的函数
sys.path.insert(0, '/Users/hf/.kimi_openclaw/workspace')
from stock_service import fetch_premarket_candidates

HTML_FILE = '/Users/hf/.kimi_openclaw/workspace/stock_dashboard.html'
INDEX_FILE = '/Users/hf/.kimi_openclaw/workspace/index.html'

def build_premarket_array(result):
    """把 API 结果格式化为 PREMARKET_NEWS JavaScript 数组"""
    items = []
    # 扁平化所有分类的新闻
    for cat_key, cat_data in result.get('categories', {}).items():
        items.extend(cat_data.get('items', []))
    
    # 按时间倒序（最新的在前）
    items.sort(key=lambda x: x.get('date', '') + x.get('time', ''), reverse=True)
    
    # category 到 catTags 的映射
    CAT_TAG_MAP = {
        'policy': ['policy'],
        'company': ['company'],
        'material': ['chain'],
        'finance': ['market'],
    }
    
    lines = ['const PREMARKET_NEWS = [']
    for i, item in enumerate(items[:50]):  # 最多50条
        cat = item.get('category', 'company')
        cat_tags = CAT_TAG_MAP.get(cat, [cat])
        level = item.get('relevance_level', 'none')
        source = item.get('source', '未知')
        source_class = item.get('sourceClass', 'sina')
        title = item.get('title', '').replace('"', '\\"')
        summary = item.get('summary', '').replace('"', '\\"')
        time_str = item.get('time', '')
        date_str = item.get('date', '')
        
        # 时间格式：MM-DD HH:MM
        if date_str and time_str:
            display_time = f"{date_str[5:]} {time_str}"
        elif time_str:
            display_time = time_str
        else:
            display_time = ""
        
        # tags 根据 level
        if level == 'direct':
            tag_text = '🔴'
            tag_cls = 'portfolio'
        elif level == 'industry':
            tag_text = '🟡'
            tag_cls = 'industry'
        else:
            tag_text = '⚠️'
            tag_cls = cat_tags[0] if cat_tags else 'market'
        
        # 百度搜索标题作为链接
        url = f'https://news.baidu.com/ns?word={urllib.parse.quote(title)}&tn=news'
        
        lines.append('  {')
        lines.append(f"    id: 'auto_{i}', catTags: {json.dumps(cat_tags)}, category: '{source_class}', level: '{level}',")
        lines.append(f"    source: \"{source}\", sourceClass: '{source_class}',")
        lines.append(f"    title: \"{title}\",")
        lines.append(f"    summary: \"{summary}\",")
        lines.append(f'    url: "{url}",')
        lines.append(f'    time: "{display_time}", tags: [{{text:"{tag_text}", cls:"{tag_cls}"}}]')
        lines.append('  },')
    
    lines.append('];')
    return '\n'.join(lines)

def update_html_file(filepath, new_array):
    """用正则替换 HTML 中的 PREMARKET_NEWS 数组"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 正则匹配 const PREMARKET_NEWS = [ ... ];
    pattern = r'const PREMARKET_NEWS = \[.*?\];'
    if not re.search(pattern, content, re.DOTALL):
        print(f"[ERR] 未找到 PREMARKET_NEWS 数组 in {filepath}")
        return False
    
    content = re.sub(pattern, new_array, content, count=1, flags=re.DOTALL)
    
    # 同时更新 PAGE_BUILD 版本号
    now_str = os.popen('date +%m%d-%H%M').read().strip()
    content = re.sub(
        r"const PAGE_BUILD = 'v[\d-]+';",
        f"const PAGE_BUILD = 'v{now_str}';",
        content
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[OK] 已更新 {filepath}，PAGE_BUILD=v{now_str}")
    return True

if __name__ == '__main__':
    print("[INFO] 抓取盘前新闻并更新 HTML...")
    result = fetch_premarket_candidates()
    if result.get('status') != 'ok':
        print("[ERR] 抓取失败")
        sys.exit(1)
    
    new_array = build_premarket_array(result)
    
    # 更新 stock_dashboard.html
    ok1 = update_html_file(HTML_FILE, new_array)
    # 同时更新 index.html
    ok2 = update_html_file(INDEX_FILE, new_array)
    
    if ok1 and ok2:
        print(f"[OK] 共 {result['total']} 条新闻已写入 HTML")
    else:
        sys.exit(1)
