---
name: rss-feeds
description: RSS订阅聚合技能。管理多个RSS源，自动抓取、去重、分类、摘要。支持关键词过滤和关键词高亮。适用于新闻聚合和资讯监控。
---

# RSS Feeds RSS订阅

## 支持的源

| 类型 | 示例源 |
|------|--------|
| 时政 | 人民网、环球时报 |
| 财经 | 华尔街见闻、新浪财经 |
| 行业 | 卓创资讯、SMM |
| 自定义 | 任意RSS/Atom feed |

## 用法

```bash
python3 rss_feeds.py add https://people.com.cn/rss/politics.xml --tag 时政
python3 rss_feeds.py fetch --limit 50
python3 rss_feeds.py search "碳酸锂"
```

## 快速命令

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/rss-feeds/scripts
python3 rss_feeds.py list
```
