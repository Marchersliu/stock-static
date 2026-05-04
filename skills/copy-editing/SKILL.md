---
name: copy-editing
description: 改文案，比重写轻。专注润色：修正语法、优化表达、统一风格，不改变原文核心意思。使用场景：(1) 快速润色邮件/报告，(2) 统一团队文档风格，(3) 修正翻译腔/病句。
---

# 文案编辑技能

## 编辑维度

| 维度 | 说明 | 示例 |
|------|------|------|
| 语法修正 | 错别字、标点、病句 | "的得地"混用、逗号滥用 |
| 表达优化 | 同义替换、去冗余 | "进行了大量的研究"→"研究了大量资料" |
| 风格统一 | 术语一致、语气一致 | 前文用"客户"后文用"用户" |
| 结构优化 | 段落逻辑、过渡自然 | 两个无关段落间加过渡句 |
| 节奏调整 | 长短句交替 | 连续3个长句后插入短句 |

## 与 humanizer-zh 的区别

| | copy-editing | humanizer-zh |
|---|---|---|
| 目标 | 修正+优化，保持风格 | 去AI化，改变风格 |
| 改动幅度 | 小，单句/词级别 | 大，段落/结构级别 |
| 适用 | 专业文档、商务文案 | 自媒体、对外发布 |
| 输出 | 更准、更顺 | 更像人写的 |

## 快速使用

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/copy-editing/scripts
python3 edit_copy.py input.md --output edited.md --focus grammar,style
```

## 聚焦选项

- `grammar`：仅语法修正
- `style`：仅风格优化
- `structure`：仅结构调整
- `all`：全部（默认）

## 文件清单

```
copy-editing/
├── SKILL.md
├── scripts/
│   └── edit_copy.py              # 编辑主脚本
├── references/
│   └── style_guide.md            # 风格规范参考
└── assets/
    └── common_fixes.json         # 常见修正规则库
```