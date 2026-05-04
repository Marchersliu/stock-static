---
name: md-to-pdf
description: Markdown转PDF。支持自定义CSS样式、页眉页脚、封面页、目录。使用场景：(1) 将研究报告导出PDF，(2) 合同审查报告打印，(3) 简报生成PDF分发。
---

# Markdown转PDF技能

## 核心功能

| 功能 | 说明 |
|------|------|
| 基础转换 | MD → PDF，保留标题/列表/表格/代码块 |
| 自定义CSS | 支持自定义字体、配色、边距 |
| 封面页 | 自动生成带标题/日期/作者的封面 |
| 页眉页脚 | 自动添加页码、文档标题 |
| 目录(TOC) | 可选自动生成目录页 |
| 中文优化 | 自动处理中文字体（使用系统字体回退） |

## 快速使用

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/md-to-pdf/scripts
python3 md_to_pdf.py input.md --output report.pdf --css style.css
```

## 依赖

- `weasyprint`（推荐）：`pip install weasyprint`
- 或 `wkhtmltopdf` + `pdfkit`

## 字体回退策略

```css
body {
  font-family: 'PingFang SC', 'Microsoft YaHei', 'Noto Sans CJK SC', sans-serif;
}
```

## 文件清单

```
md-to-pdf/
├── SKILL.md
├── scripts/
│   └── md_to_pdf.py              # 转换主脚本
├── references/
│   └── css_guide.md              # CSS自定义指南
└── assets/
    └── default.css               # 默认样式模板
```