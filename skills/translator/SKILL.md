---
name: translator
description: 多语言翻译技能。支持中英/中日/中韩/中法/中德/中西/中俄等主流语言互译。自动检测源语言，支持专业术语对照表，保留原文格式。适用于研报、新闻、技术文档翻译。
---

# Translator 多语言翻译

## 支持语言

| 语言 | 代码 | 方向 |
|------|------|------|
| 简体中文 | zh | ↔ 所有 |
| 英语 | en | ↔ 所有 |
| 日语 | ja | ↔ zh, en |
| 韩语 | ko | ↔ zh, en |
| 法语 | fr | ↔ zh, en |
| 德语 | de | ↔ zh, en |
| 西班牙语 | es | ↔ zh, en |
| 俄语 | ru | ↔ zh, en |
| 阿拉伯语 | ar | ↔ en |

## 翻译模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **标准** | 通用翻译，平衡准确与流畅 | 日常文本 |
| **专业** | 保留术语，提供术语对照 | 研报、技术文档 |
| **简洁** | 压缩表达，去冗余 | 摘要、 bullet points |
| **逐句** | 原文+译文对照 | 学习、校对 |

## 专业术语对照

可加载自定义术语表：
```json
{
  "碳酸锂": "Lithium Carbonate",
  "固态电池": "Solid-state Battery",
  "人形机器人": "Humanoid Robot"
}
```

## 用法

```bash
# 翻译文本
python3 translator.py "Hello world" --to zh

# 翻译文件
python3 translator.py --file report_en.md --to zh --output report_zh.md

# 专业模式（保留术语）
python3 translator.py "Solid-state battery energy density" --to zh --mode professional

# 批量翻译（JSON术语表）
python3 translator.py --terms terms.json --file input.txt --to zh
```

## 快速命令

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/translator/scripts
python3 translator.py "要翻译的文本" --to en
```
