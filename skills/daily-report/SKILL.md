---
name: daily-report
description: 生成每日情报简报PDF。自动聚合多源数据（股票持仓、新闻、天气、日程），生成结构化的每日简报并导出为PDF。使用场景：(1) 交易日早晨生成盘前简报，(2) 工作日报汇总，(3) 个人每日信息摘要。
---

# 每日情报简报技能

## 工作流程

1. **数据收集** → 调用各数据源接口
   - 股票持仓数据（Tushare）
   - 新闻摘要（RSS/Tushare major_news）
   - 天气（wttr.in）
   - 日历事件（Apple Calendar）
2. **内容生成** → Markdown 结构化
3. **PDF导出** → 调用 md-to-pdf 技能或 `scripts/generate_pdf.py`

## 简报结构

```markdown
# 每日情报简报 · 2026-05-05

## 📊 持仓概览
## 📰 重大新闻
## 🏭 原材料价格
## 🌤️ 天气
## 📅 今日日程
## ⚡ 风险提示
```

## 快速使用

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/daily-report/scripts
python3 generate_daily_report.py --date 2026-05-05 --output ~/Desktop/日报.pdf
```

## 依赖

- `md-to-pdf` 技能（PDF生成）
- `stock-monitor` 技能（股票数据）
- `weather` 技能（天气数据）
- `weasyprint` 或 `wkhtmltopdf`

## 文件清单

```
daily-report/
├── SKILL.md
├── scripts/
│   ├── generate_daily_report.py  # 主脚本
│   └── collect_data.py           # 数据收集
├── references/
│   └── report_sections.md        # 各板块写作规范
└── assets/
    └── report.css                # PDF样式
```