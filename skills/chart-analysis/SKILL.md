---
name: chart-analysis
description: K线图技术分析技能。读取K线数据计算技术指标（MA/MACD/KDJ/RSI/BOLL），生成买卖信号，支持可视化。适用于股票技术面快速分析。
---

# Chart Analysis K线分析

## 技术指标

| 指标 | 信号 | 权重 |
|------|------|------|
| MA | 金叉/死叉 | 0.2 |
| MACD | 红柱放大/绿柱放大 | 0.25 |
| KDJ | K上穿D/下穿 | 0.2 |
| RSI | <30超卖/>70超买 | 0.15 |
| BOLL | 触及上轨/下轨 | 0.1 |
| 成交量 | 放量/缩量 | 0.1 |

## 用法

```bash
python3 chart_analysis.py 688485.SH --days 60 --indicators all
python3 chart_analysis.py 600989.SH --signal --notify
```

## 快速命令

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/chart-analysis/scripts
python3 chart_analysis.py 688485.SH --signal
```
