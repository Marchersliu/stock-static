import re

with open('stock_dashboard.html', 'r') as f:
    html = f.read()

# 1. 替换卡片标题：日期+时间合在一起
old_title = '<span id="news-date-title">2026-05-03</span><span class="update-time manual" id="news-manual-time">手动更新 20:15</span>'
new_title = '<span id="news-date-title">2026-05-03 20:15</span>'

if old_title in html:
    html = html.replace(old_title, new_title, 1)
    print('Fixed title')
else:
    print('Title old text not found')

# 2. 替换JS里的更新逻辑
# 原来只更新 newsManualTime，现在改成更新 newsDateTitle 为 "日期 时间"
old_js = """        // 更新手动更新时间显示
        const newsManualTime = document.getElementById('news-manual-time');
        if (newsManualTime) {
          const t = LAST_NEWS_UPDATE.split(' ')[1] || LAST_NEWS_UPDATE;
          newsManualTime.textContent = `手动更新 ${t}`;
        }
        
        // 更新卡片标题日期
        const newsDateTitle = document.getElementById('news-date-title');
        if (newsDateTitle && latest.date) {
          newsDateTitle.textContent = latest.date;
        }"""

new_js = """        // 更新卡片标题日期+时间
        const newsDateTitle = document.getElementById('news-date-title');
        if (newsDateTitle && latest.date && latest.time) {
          newsDateTitle.textContent = `${latest.date} ${latest.time}`;
        }"""

if old_js in html:
    html = html.replace(old_js, new_js, 1)
    print('Fixed JS update logic')
else:
    print('JS old text not found')

with open('stock_dashboard.html', 'w') as f:
    f.write(html)

print('Done')
