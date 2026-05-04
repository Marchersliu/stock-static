---
name: linter
description: 代码检查技能。多语言lint封装：Python(ruff/black)、JavaScript(eslint)、Shell(shellcheck)、Markdown(markdownlint)。一键检查项目代码质量。
---

# Linter 代码检查

## 支持语言

| 语言 | 工具 | 检查内容 |
|------|------|----------|
| Python | ruff, black | 语法、风格、import排序 |
| JavaScript | eslint | 语法、最佳实践 |
| TypeScript | eslint + @typescript-eslint | 类型相关 |
| Shell | shellcheck | 脚本安全 |
| Markdown | markdownlint | 格式规范 |
| JSON | jq | 格式验证 |

## 用法

```bash
python3 linter.py --lang python --dir .
python3 linter.py --lang shell --file script.sh
python3 linter.py --all --dir . --fix
```

## 快速命令

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/linter/scripts
python3 linter.py --lang python --dir /path/to/project
```
