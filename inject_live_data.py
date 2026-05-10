#!/usr/bin/env python3
"""
自动注入脚本：每30分钟将最新数据注入 stock_dashboard.html 静态文件
让手机（无法连接 localhost）也能看到当日较新数据

使用方法:
    # 单次执行
    python3 /Users/hf/.kimi_openclaw/workspace/inject_live_data.py

    # 后台定时执行（每30分钟）
    nohup python3 /Users/hf/.kimi_openclaw/workspace/inject_live_data.py --daemon > /tmp/inject_live.log 2>&1 &

    # 或用 launchctl 定时任务（推荐 Mac）
"""
import json
import urllib.request
import urllib.error
import subprocess
import sys
import time
import re
import os

HTML_PATH = '/Users/hf/.kimi_openclaw/workspace/stock_dashboard.html'
ICLOUD_DIR = '/Users/hf/Library/Mobile Documents/com~apple~CloudDocs/下载文件/HF/📊股票监控/'
API_BASE = 'http://localhost:8888'


def api_get(endpoint):
    try:
        req = urllib.request.Request(f'{API_BASE}{endpoint}')
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f'[ERR] API {endpoint}: {e}')
        return None


def fetch_hsi():
    """从腾讯接口获取恒指实时数据"""
    try:
        req = urllib.request.Request(
            'https://qt.gtimg.cn/q=hkHSI',
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            text = resp.read().decode('gbk', errors='ignore')
        m = re.search(r'v_hkHSI="([^"]+)"', text)
        if not m:
            return None
        parts = m.group(1).split('~')
        if len(parts) < 35:
            return None
        return {
            'close': float(parts[3]),
            'change': float(parts[31]),
            'pct': float(parts[32]),
            'date_time': parts[30],
        }
    except Exception as e:
        print(f'[ERR] HSI fetch: {e}')
        return None


def build_news_entries(api_data):
    """从 API 数据构建 PREMARKET_NEWS 数组条目"""
    if not api_data:
        return []
    cats = api_data.get('categories', {})
    all_items = []
    for cat_name, cat in cats.items():
        for item in cat.get('items', []):
            all_items.append(item)

    # 优先取今日，没有则取全部（按时间倒序）
    all_items.sort(key=lambda x: x.get('date', '') + x.get('time', ''), reverse=True)

    today_str = time.strftime('%Y-%m-%d')
    today_items = [i for i in all_items if i.get('date', '').startswith(today_str)]
    selected = today_items[:20] if today_items else all_items[:20]

    entries = []
    for idx, i in enumerate(selected):
        title = i.get('title', '').replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
        summary = i.get('summary', '')[:120].replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
        cat_tags = i.get('catTags', [])
        cat_tags_js = ', '.join(['"' + t + '"' for t in cat_tags]) if cat_tags else '"market"'
        date = i.get('date', today_str)
        t = i.get('time', '')
        source = i.get('source', 'Tushare').replace('"', '\\"')
        source_class = i.get('sourceClass', 'sina')
        level = i.get('relevance_level', 'normal')
        rel_score = i.get('relevance_score', 0)
        time_str = (date[5:7] + '-' + date[8:10] + ' ' + t) if t else (date[5:7] + '-' + date[8:10])
        tag_text = '📈' if rel_score >= 2 else '⚠️'
        tag_cls = 'market' if rel_score >= 2 else 'geo'

        entry = f"""  {{
    id: 'auto_{idx}', catTags: [{cat_tags_js}], category: '{source_class}', level: '{level}',
    source: "{source}", sourceClass: '{source_class}',
    title: "{title}",
    summary: "{summary}",
    time: "{time_str}", tags: [{{text:"{tag_text}", cls:"{tag_cls}"}}]
  }}"""
        entries.append(entry)
    return entries


def update_news_array(html, entries):
    """替换 PREMARKET_NEWS 数组内容"""
    marker = 'const PREMARKET_NEWS = ['
    start = html.find(marker)
    if start == -1:
        print('[WARN] PREMARKET_NEWS not found')
        return html

    # 找到数组结束（]; 后紧跟换行或注释）
    array_start = start + len(marker)
    # 找匹配的 ]
    depth = 1
    end_pos = array_start
    for i in range(array_start, len(html)):
        if html[i] == '[':
            depth += 1
        elif html[i] == ']':
            depth -= 1
            if depth == 0:
                end_pos = i
                break

    if end_pos <= array_start:
        print('[WARN] Could not find end of PREMARKET_NEWS')
        return html

    new_array = '\n' + ',\n'.join(entries) + '\n'
    new_html = html[:array_start] + new_array + html[end_pos:]
    return new_html


def update_global_markets(html, hsi_data):
    """更新 GLOBAL_MARKETS 中的恒指数据"""
    if not hsi_data:
        return html

    # 找到恒生指数条目
    pattern = r'("恒生指数": \{close: )([\d.]+)(, pct: )([\d.-]+)(, region: "hk", tradeDate: ")([^"]+)("\})'
    def replacer(m):
        dt = hsi_data.get('date_time', '')
        trade_date = dt.split()[0].replace('/', '-') if dt else time.strftime('%Y-%m-%d')
        return f'{m.group(1)}{hsi_data["close"]}{m.group(3)}{hsi_data["pct"]}{m.group(5)}{trade_date}{m.group(7)}'

    new_html = re.sub(pattern, replacer, html)
    if new_html == html:
        print('[WARN] HSI pattern not matched, trying fallback')
        # Fallback: replace any恒生指数 close/pct line
        new_html = re.sub(
            r'"恒生指数": \{close: [\d.]+, pct: [\d.-]+',
            f'"恒生指数": {{close: {hsi_data["close"]}, pct: {hsi_data["pct"]}',
            html
        )
    return new_html


def update_timestamp(html):
    """更新 LAST_NEWS_UPDATE 时间戳和新闻标题日期"""
    now_str = time.strftime('%Y-%m-%d %H:%M')
    today_str = time.strftime('%Y-%m-%d')
    # 替换 LAST_NEWS_UPDATE
    new_html = re.sub(
        r"let LAST_NEWS_UPDATE = '[^']*';",
        f"let LAST_NEWS_UPDATE = '{now_str}';",
        html
    )
    # 同时替换 PAGE_BUILD 版本号
    build_str = time.strftime('v%m%d-%H%M')
    new_html = re.sub(
        r"const PAGE_BUILD = '[^']*';",
        f"const PAGE_BUILD = '{build_str}';",
        new_html
    )
    # 更新盘前新闻卡片标题日期（硬编码的静态值）
    new_html = re.sub(
        r'<span id="news-date-title">[^<]*</span>',
        f'<span id="news-date-title">{today_str} 盘前</span>',
        new_html
    )
    return new_html


def verify_js(html):
    """node --check 验证 JS 语法"""
    script_start = html.find('<script>')
    script_end = html.find('</script>', script_start)
    if script_start == -1 or script_end == -1:
        return False, 'Script tags not found'
    script = html[script_start + 8:script_end]
    try:
        with open('/tmp/check_inject_live.js', 'w') as f:
            f.write(script)
        result = subprocess.run(
            ['node', '--check', '/tmp/check_inject_live.js'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return True, 'OK'
        return False, result.stderr[:200]
    except Exception as e:
        return False, str(e)[:200]


def sync_icloud():
    try:
        if os.path.exists(ICLOUD_DIR):
            subprocess.run([
                'cp', HTML_PATH,
                os.path.join(ICLOUD_DIR, 'stock_dashboard.html')
            ], check=True, timeout=10)
            print('[OK] Synced to iCloud')
        else:
            print('[WARN] iCloud dir not found, skipping sync')
    except Exception as e:
        print(f'[WARN] iCloud sync failed: {e}')


def inject_once():
    print(f'\n=== {time.strftime("%Y-%m-%d %H:%M:%S")} ===')

    # 1. 读取 HTML
    with open(HTML_PATH, 'r') as f:
        html = f.read()

    # 2. 获取数据
    premarket = api_get('/api/premarket')
    hsi = fetch_hsi()

    # 3. 构建新闻条目
    entries = build_news_entries(premarket)
    if not entries:
        print('[WARN] No news entries built, skipping')
        return False

    # 4. 更新 HTML
    new_html = update_news_array(html, entries)
    new_html = update_global_markets(new_html, hsi)
    new_html = update_timestamp(new_html)

    # 5. 验证语法
    ok, msg = verify_js(new_html)
    if not ok:
        print(f'[ERR] JS syntax check failed: {msg}')
        return False

    # 6. 写入文件
    with open(HTML_PATH, 'w') as f:
        f.write(new_html)
    print(f'[OK] Updated HTML: {len(entries)} news, HSI={hsi["close"] if hsi else "N/A"}')

    # 7. 同步 iCloud
    sync_icloud()
    return True


def run_daemon():
    """后台循环：每30分钟执行一次"""
    print('[Daemon] Started, interval=30min')
    while True:
        try:
            inject_once()
        except Exception as e:
            print(f'[ERR] inject_once failed: {e}')
        print('[Daemon] Sleeping 30min...\n')
        time.sleep(1800)  # 30 minutes


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        run_daemon()
    else:
        success = inject_once()
        sys.exit(0 if success else 1)
