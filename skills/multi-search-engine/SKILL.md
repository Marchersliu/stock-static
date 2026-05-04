---
name: multi-search-engine
description: 多引擎聚合搜索技能。同时查询多个搜索引擎（Google/Bing/DuckDuckGo/Brave/百度），去重、评分、排序后返回最佳结果。当用户需要：(1) 搜索不确定信息需要从多源验证，(2) 对比不同引擎的结果差异，(3) 需要更全面的搜索结果时使用。
---

# Multi-Search-Engine 多引擎搜索

## 支持的搜索引擎

| 引擎 | 方法 | 状态 | 说明 |
|------|------|------|------|
| **Brave Search** | API | ✅ 首选 | 无需Key，结果质量高 |
| **DuckDuckGo** | HTML抓取 | ✅ | 无API限制，隐私友好 |
| **Bing** | HTML抓取 | ✅ | 国内可用 |
| **百度** | HTML抓取 | ✅ | 中文内容 |
| **Google** | HTML抓取 | ⚠️ | 需要处理验证码 |

## 核心功能

```python
from multi_search import search

results = search(
    query="碳酸锂价格走势 2026",
    engines=['brave', 'duckduckgo', 'bing'],
    limit=10,
    timeout=15
)
# 返回去重后的最佳结果
```

### 结果评分

| 维度 | 权重 | 说明 |
|------|------|------|
| 引擎置信度 | 0.3 | Brave > DuckDuckGo > Bing > 百度 > Google |
| 时效性 | 0.25 | 新内容得分高 |
| 多引擎确认 | 0.25 | 多个引擎出现同一URL得分高 |
| 域名权威度 | 0.2 | 知名域名得分高 |

## 用法

```bash
# 基本搜索
python3 multi_search.py "碳酸锂最新价格"

# 多引擎搜索
python3 multi_search.py "AI芯片行业报告" --engines brave,duckduckgo --limit 20

# 对比模式
python3 multi_search.py "中国核电政策" --compare

# 保存结果
python3 multi_search.py "新能源车销量" --output /tmp/results.json
```

## 快速命令

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/multi-search-engine/scripts
python3 multi_search.py "你的搜索词" --engines brave,duckduckgo,bing
```
