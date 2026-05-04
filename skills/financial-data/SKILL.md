---
name: financial-data
description: 财报数据抓取技能。从巨潮资讯、东方财富、Tushare等来源抓取上市公司财报数据（营收、净利润、ROE、现金流等），支持批量导出和分析。
---

# Financial Data 财报数据

## 数据源

| 来源 | 覆盖 | 方式 |
|------|------|------|
| Tushare Pro | 全A股财报 | API |
| 巨潮资讯 | 官方公告 | JSON API |
| 东方财富 | 财务指标 | JSON API |
| 新浪财经 | 财报摘要 | HTML |

## 功能

```bash
python3 financial_data.py --stock 688485.SH --year 2025 --quarter q1
python3 financial_data.py --batch stocks.txt --output report.csv
```

## 快速命令

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/financial-data/scripts
python3 financial_data.py --help
```
