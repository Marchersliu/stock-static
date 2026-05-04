---
name: browser-web-search
description: 浏览器驱动网页搜索技能。通过控制浏览器直接搜索网页、提取内容、截图保存。当用户需要：(1) 搜索特定网站内容，(2) 需要浏览器渲染后的页面内容，(3) 需要截图保存搜索结果，(4) 绕过纯API搜索的限制时使用。
---

# Browser-Web-Search 浏览器网页搜索

## 核心功能

通过控制浏览器执行搜索：

| 功能 | 命令 | 说明 |
|------|------|------|
| **搜索并提取** | `search_and_extract` | 在搜索引擎输入关键词，提取结果 |
| **特定网站搜索** | `site_search` | `site:example.com 关键词` |
| **页面截图** | `screenshot` | 搜索后截图保存 |
| **滚动加载** | `scroll_and_extract` | 滚动加载更多结果 |

## 支持的搜索场景

```python
from browser_search import BrowserSearch

bs = BrowserSearch()

# 基本搜索
results = bs.search("碳酸锂价格", engine="bing")

# 特定网站搜索
results = bs.site_search("smm.cn", "碳酸锂")

# 搜索并截图
results = bs.search_with_screenshot("A股今日要闻", save_path="/tmp/news.png")
```

## 用法

```bash
# 浏览器搜索
python3 browser_search.py "搜索词" --engine bing

# 搜索特定网站
python3 browser_search.py "关键词" --site sina.com.cn

# 搜索并截图
python3 browser_search.py "今日股市" --screenshot /tmp/stock.png
```

## 快速命令

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/browser-web-search/scripts
python3 browser_search.py "你的搜索词" --engine bing --limit 10
```
