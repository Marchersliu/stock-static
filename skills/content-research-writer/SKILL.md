---
name: content-research-writer
description: 辅助深度写作研究。多轮搜索+信息提取+交叉验证+结构化写作，生成高质量长文。使用场景：(1) 行业深度分析报告，(2) 投资研报撰写，(3) 技术评估白皮书，(4) 竞品调研报告。
---

# 内容研究写作技能

## 核心流程

```
用户输入写作主题
  ↓
第1轮搜索 → 建立知识框架，提取关键子主题
  ↓
第2轮搜索 → 深入各子主题，收集数据/案例/引用
  ↓
交叉验证 → 多源对比，标注矛盾信息
  ↓
结构化写作 → 按大纲逐段生成
  ↓
自检润色 → 检查逻辑/数据/引用完整性
```

## 输出规范

- **执行摘要**：3-5句话核心结论
- **章节结构**：背景→数据→分析→结论→建议
- **引用标注**：每条关键数据标注来源 `[1] URL`
- **置信度评级**：高/中/低，标注不确定信息

## 与 deep-research 的区别

| | deep-research | content-research-writer |
|---|---|---|
| 输出 | 研究报告（信息聚合） | 可发布的长文章（叙事+论证） |
| 风格 | 客观、数据密集 | 有观点、有故事线 |
| 长度 | 3000-5000字 | 5000-15000字 |
| 用途 | 内部决策参考 | 对外发布、公众号、知乎 |

## 快速使用

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/content-research-writer/scripts
python3 write_article.py "固态电池技术路线分析" --depth 3 --output article.md
```

## 文件清单

```
content-research-writer/
├── SKILL.md
├── scripts/
│   ├── write_article.py          # 写作主脚本
│   └── research_outline.py       # 大纲生成
├── references/
│   └── writing_guide.md          # 写作风格指南
└── assets/
    └── article_template.md       # 文章模板
```