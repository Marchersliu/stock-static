---
name: pdf-extract
description: PDF内容提取技能。提取PDF文本、表格、图片，支持研报/财报/论文等结构化文档。自动识别目录、页眉页脚、表格，输出Markdown或结构化JSON。适用于批量处理研报、提取财务数据。
---

# PDF Extract PDF内容提取

## 核心功能

| 功能 | 说明 | 依赖 |
|------|------|------|
| **文本提取** | 提取全部文本，保留段落结构 | PyPDF2 / pdfplumber |
| **表格提取** | 识别表格，输出CSV/JSON | pdfplumber / tabula |
| **图片提取** | 提取内嵌图片 | PyMuPDF (fitz) |
| **目录识别** | 自动识别文档目录结构 | PyPDF2 |
| **研报专用** | 识别摘要、关键数据、图表标题 | 自定义规则 |

## 输出格式

```markdown
# {文件名}

## 元数据
- 页数: {n}
- 作者: {author}
- 日期: {date}

## 目录
1. {章节1} (p{x})
2. {章节2} (p{y})

## 摘要
{提取的摘要段落}

## 关键数据
| 指标 | 数值 | 页码 |
|------|------|------|
| 营收 | 100亿 | p5 |
| 净利润 | 10亿 | p5 |

## 正文
{正文内容}

## 表格
{提取的表格}
```

## 用法

```bash
# 提取文本
python3 pdf_extract.py report.pdf --output report.md

# 提取表格
python3 pdf_extract.py report.pdf --tables --output tables.json

# 研报模式（自动识别关键数据）
python3 pdf_extract.py research.pdf --mode research --output research.md

# 批量处理
python3 pdf_extract.py --batch "*.pdf" --output-dir ./extracted/
```

## 快速命令

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/pdf-extract/scripts
python3 pdf_extract.py /path/to/file.pdf --output /tmp/out.md
```

## 依赖安装

```bash
pip3 install pdfplumber PyMuPDF
```
