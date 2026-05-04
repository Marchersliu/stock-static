---
name: news-summarizer
description: 新闻自动摘要技能。对长文章进行抽取式/生成式摘要，提取关键信息（5W1H），生成TL;DR版本。支持批量处理和关键词提取。
---

# News Summarizer 新闻摘要

## 摘要模式

| 模式 | 长度 | 适用 |
|------|------|------|
| headline | 1句 | 标题生成 |
| brief | 3句 | 快速浏览 |
| standard | 5句 | 常规摘要 |
| detailed | 10句+ | 深度摘要 |

## 用法

```bash
python3 news_summarizer.py --file article.txt --mode standard
python3 news_summarizer.py --url https://example.com/news --keywords
python3 news_summarizer.py --batch news_dir/ --output summaries.json
```

## 快速命令

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/news-summarizer/scripts
python3 news_summarizer.py --text "长文章文本..." --mode brief
```
