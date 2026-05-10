import re

with open('dashboard.html', 'r') as f:
    html = f.read()

# 找到 PREMARKET_NEWS 数组
start = html.find('const PREMARKET_NEWS = [')
end = html.find('];\n\n// ===================== 初始化', start)
news_block = html[start:end+2]

# 检查每个条目是否有 tags 字段
entries = news_block.split('},\n  {')
print(f'总条目数: {len(entries)}')

no_tags = []
for i, entry in enumerate(entries):
    if 'tags:' not in entry:
        title_match = re.search(r'title:\s*"([^"]+)"', entry)
        title = title_match.group(1) if title_match else 'unknown'
        no_tags.append((i, title))

if no_tags:
    print(f'缺少 tags: {len(no_tags)}')
    for idx, title in no_tags[:5]:
        print(f'  条目 {idx}: {title}')
else:
    print('所有条目都有 tags')

no_cat = []
for i, entry in enumerate(entries):
    if 'catTags' not in entry:
        title_match = re.search(r'title:\s*"([^"]+)"', entry)
        title = title_match.group(1) if title_match else 'unknown'
        no_cat.append((i, title))

if no_cat:
    print(f'缺少 catTags: {len(no_cat)}')
    for idx, title in no_cat[:5]:
        print(f'  条目 {idx}: {title}')
else:
    print('所有条目都有 catTags')
