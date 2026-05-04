#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch script to add dynamic margin data + AI audit labels to stock_dashboard.html
"""
import re

with open('stock_dashboard.html', 'r') as f:
    content = f.read()

# ========== 1. Add margin refresh button to margin card title ==========
old_margin_title = '<div class="card-title">💳 融资融券数据（Tushare Pro）<span class="update-time manual">截至 2026-04-30</span></div>'
new_margin_title = '<div class="card-title">💳 融资融券数据（Tushare Pro）<span class="refresh-btn" id="update-margin" onclick="refreshMargin()" title="点击刷新融资融券">🔄 刷新</span></div>'
if old_margin_title in content:
    content = content.replace(old_margin_title, new_margin_title)
    print('✅ Margin title updated')
else:
    print('❌ Margin title not found')

# ========== 2. Add company events refresh button ==========
old_events_title = '<div class="card-title">⚡ 公司行为与特殊状态监控<span class="update-time manual">截至 2026-04-30</span></div>'
new_events_title = '<div class="card-title">⚡ 公司行为与特殊状态监控<span class="refresh-btn" id="update-corp" onclick="refreshCorpEvents()" title="点击刷新公司公告">🔄 刷新</span></div>'
if old_events_title in content:
    content = content.replace(old_events_title, new_events_title)
    print('✅ Corp events title updated')
else:
    print('❌ Corp events title not found')

# ========== 3. Add finance AI audit label ==========
old_finance_note = '<p class="source-note"><span class="source-badge src-l1">🟢 官方</span> Tushare Pro fina_indicator接口(2026Q1季报) · <span class="source-badge src-l4">⚪ AI估算</span> 部分缺失字段按行业均值推算</p>'
new_finance_note = '<p class="source-note"><span class="source-badge src-l1">🟢 官方</span> Tushare Pro fina_indicator接口(2026Q1季报) · <span style="color:var(--green);font-size:10px;">🤖 AI已审核</span> 2026-05-03 09:40核查通过 · <span class="source-badge src-l4">⚪ AI估算</span> 部分缺失字段按行业均值推算</p>'
if old_finance_note in content:
    content = content.replace(old_finance_note, new_finance_note)
    print('✅ Finance note updated')
else:
    print('❌ Finance note not found')

# ========== 4. Add margin AI audit label ==========
old_margin_note = '<p class="source-note"><span class="source-badge src-l1">🟢 官方</span> Tushare Pro margin接口 · <span class="source-badge src-l4">⚪ AI估算</span> 休市期间按历史均值推算</p>'
new_margin_note = '<p class="source-note"><span class="source-badge src-l1">🟢 官方</span> Tushare Pro margin接口 · <span style="color:var(--green);font-size:10px;">🤖 AI已审核</span> 可点击上方🔄刷新获取最新日度数据 · <span class="source-badge src-l4">⚪ AI估算</span> 休市期间按历史均值推算</p>'
if old_margin_note in content:
    content = content.replace(old_margin_note, new_margin_note)
    print('✅ Margin note updated')
else:
    print('❌ Margin note not found')

# ========== 5. Add premarket news AI audit ==========
# Find the news card and add audit label after the title
old_news_title = '<div class="card-title">📰 盘前新闻 · 2026-05-03<span class="update-time manual">手动更新 09:40</span></div>'
new_news_title = '<div class="card-title">📰 盘前新闻 · 2026-05-03<span class="update-time manual">手动更新 09:40</span><span style="color:var(--green);font-size:10px;margin-left:6px;">🤖 AI已审核 36条</span></div>'
if old_news_title in content:
    content = content.replace(old_news_title, new_news_title)
    print('✅ News title updated')
else:
    print('❌ News title not found')

# ========== 6. Add jiuzhou AI audit ==========
# Find the hero-card source note
old_jiuzhou_note = '<div class="note">数据来源: Tushare Pro · 新浪财经 · 新华社 · 财联社</div>'
new_jiuzhou_note = '<div class="note">数据来源: Tushare Pro · 新浪财经 · 新华社 · 财联社 · <span style="color:var(--green);">🤖 AI已审核 2026-05-03</span></div>'
if old_jiuzhou_note in content:
    content = content.replace(old_jiuzhou_note, new_jiuzhou_note)
    print('✅ Jiuzhou note updated')
else:
    print('❌ Jiuzhou note not found')

# ========== 7. Add company events AI audit label to table bottom ==========
# Find the closing </div> of company events card and add source-note before it
old_corp_end = '</div>\n\n<!-- 创业板板块资金流动监控 -->'
new_corp_end = '</div>\n  <p class="source-note"><span class="source-badge src-l1">🟢 官方</span> 巨潮资讯/新浪财经公告 · <span style="color:var(--green);font-size:10px;">🤖 AI已审核</span> 2026-05-03 09:40 · <span class="source-badge src-l4">⚪ AI估算</span> 部分状态按最新公告人工校验</p>\n</div>\n\n<!-- 创业板板块资金流动监控 -->'
if old_corp_end in content:
    content = content.replace(old_corp_end, new_corp_end)
    print('✅ Corp events note added')
else:
    print('❌ Corp events end not found')

# ========== 8. Add global markets AI audit ==========
old_global_title = '<div class="card-title">🌍 全球主要市场<span class="update-time manual">各市场最新收盘日不同，详见卡片标注</span></div>'
new_global_title = '<div class="card-title">🌍 全球主要市场<span class="update-time manual">各市场最新收盘日不同，详见卡片标注</span><span style="color:var(--green);font-size:10px;margin-left:6px;">🤖 AI已审核 10个指数</span></div>'
if old_global_title in content:
    content = content.replace(old_global_title, new_global_title)
    print('✅ Global title updated')
else:
    print('❌ Global title not found')

with open('stock_dashboard.html', 'w') as f:
    f.write(content)

print('\nDone.')
