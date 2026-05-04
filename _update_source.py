#!/usr/bin/env python3
"""Update source status in stock_dashboard.html"""

with open('stock_dashboard.html', 'r') as f:
    content = f.read()

old = '🟢 已接入 新浪财经 · 巨潮资讯 · 东方财富 · 央行/财政部'
new = '🟢 已接入 新浪财经 · 巨潮资讯 · 东方财富 · 央行/财政部 · 人民网 · 环球时报'

if old in content:
    content = content.replace(old, new)
    print('✅ Updated source status')
else:
    print('⚠️ Could not find old text')

with open('stock_dashboard.html', 'w') as f:
    f.write(content)
