import json
import urllib.request

# 1. Fetch latest API data
req = urllib.request.Request('http://localhost:8888/api/premarket')
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read().decode('utf-8'))

# 2. Extract 05-04 items
cats = data.get('categories', {})
all_items = []
for cat_name, cat in cats.items():
    for item in cat.get('items', []):
        all_items.append(item)

may4 = [i for i in all_items if i.get('date', '').startswith('2026-05-04')]

# 3. Read HTML
with open('/Users/hf/.kimi_openclaw/workspace/stock_dashboard.html', 'r') as f:
    html = f.read()

# 4. Find PREMARKET_NEWS start
marker = 'const PREMARKET_NEWS = ['
start = html.find(marker)
if start == -1:
    print('PREMARKET_NEWS not found')
    exit(1)

# 5. Build new entries (top 15)
entries = []
for idx, i in enumerate(may4[:15]):
    title = i.get('title', '').replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
    summary = i.get('summary', '')[:100].replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
    cat_tags = i.get('catTags', [])
    cat_tags_js = ', '.join(['"' + t + '"' for t in cat_tags]) if cat_tags else '"market"'
    date = i.get('date', '2026-05-04')
    time = i.get('time', '')
    source = i.get('source', 'Tushare').replace('"', '\\"')
    source_class = i.get('sourceClass', 'sina')
    level = i.get('relevance_level', 'normal')
    rel_score = i.get('relevance_score', 0)
    time_str = (date[5:7] + '-' + date[8:10] + ' ' + time) if time else (date[5:7] + '-' + date[8:10])
    tag_text = '📈' if rel_score >= 2 else '⚠️'
    tag_cls = 'market' if rel_score >= 2 else 'geo'
    
    entry = f"""  {{
    id: 'm4_{idx}', catTags: [{cat_tags_js}], category: '{source_class}', level: '{level}',
    source: "{source}", sourceClass: '{source_class}',
    title: "{title}",
    summary: "{summary}",
    time: "{time_str}", tags: [{{text:"{tag_text}", cls:"{tag_cls}"}}]
  }},"""
    entries.append(entry)

new_block = '\n'.join(entries)

# 6. Insert after the opening bracket
insert_pos = start + len(marker)
new_html = html[:insert_pos] + '\n' + new_block + '\n' + html[insert_pos:]

# 7. Write back
with open('/Users/hf/.kimi_openclaw/workspace/stock_dashboard.html', 'w') as f:
    f.write(new_html)

print(f'Injected {len(entries)} 05-04 news items into PREMARKET_NEWS')

# 8. Verify JS
script_start = new_html.find('<script>')
script_end = new_html.find('</script>', script_start)
script = new_html[script_start+8:script_end]
with open('/tmp/check_inject.js', 'w') as f:
    f.write(script)

import subprocess
result = subprocess.run(['node', '--check', '/tmp/check_inject.js'], capture_output=True, text=True)
if result.returncode == 0:
    print('JS Syntax: OK')
else:
    print('JS Syntax ERROR:', result.stderr[:200])
