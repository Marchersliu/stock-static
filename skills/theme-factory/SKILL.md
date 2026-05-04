---
name: theme-factory
description: 给报告/网页统一配色主题。生成专业的配色方案（主色/辅色/强调色/背景色），支持一键应用到HTML/CSS/Markdown。使用场景：(1) 股票dashboard配色升级，(2) PDF报告品牌化，(3) PPT配色方案生成。
---

# 主题工厂技能

## 核心功能

| 功能 | 说明 |
|------|------|
| 配色生成 | 基于色彩理论生成和谐配色方案 |
| 预设主题 | 金融蓝、科技紫、医疗绿、政府红等 |
| CSS导出 | 生成 CSS 变量文件 |
| HTML应用 | 一键替换现有HTML的配色 |
| 对比度检查 | 确保文字可读性（WCAG标准） |

## 预设主题

```python
THEMES = {
    "finance":   {"primary": "#1e3a5f", "accent": "#f59e0b", "bg": "#0f172a", "text": "#e2e8f0"},
    "tech":      {"primary": "#6366f1", "accent": "#22d3ee", "bg": "#0f172a", "text": "#e2e8f0"},
    "medical":   {"primary": "#059669", "accent": "#34d399", "bg": "#f0fdf4", "text": "#1f2937"},
    "government":{"primary": "#b91c1c", "accent": "#f59e0b", "bg": "#fff7ed", "text": "#1f2937"},
    "minimal":   {"primary": "#18181b", "accent": "#3f3f46", "bg": "#ffffff", "text": "#18181b"},
}
```

## 快速使用

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/theme-factory/scripts
python3 apply_theme.py /path/to/report.html --theme finance --output themed.html
```

## 文件清单

```
theme-factory/
├── SKILL.md
├── scripts/
│   ├── apply_theme.py            # 主题应用脚本
│   └── generate_theme.py         # 配色生成
├── references/
│   └── color_theory.md           # 色彩理论参考
└── assets/
    └── themes/                   # 预设主题CSS文件
```