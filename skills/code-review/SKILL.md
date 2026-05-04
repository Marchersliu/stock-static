---
name: code-review
description: 代码审查技能。自动检查代码中的潜在问题：bug、安全漏洞、性能问题、风格问题。生成审查报告，支持diff模式对比修改前后。
---

# Code Review 代码审查

## 检查维度

| 维度 | 检查内容 |
|------|----------|
| Bugs | 空指针、资源泄漏、逻辑错误 |
| Security | SQL注入、XSS、硬编码密钥 |
| Performance | N+1查询、循环内IO、内存泄漏 |
| Style | 命名规范、注释、复杂度 |
| Maintainability | 重复代码、超长函数、圈复杂度 |

## 用法

```bash
python3 code_review.py --file script.py
python3 code_review.py --diff before.py after.py
python3 code_review.py --dir src/ --output review.md
```

## 快速命令

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/code-review/scripts
python3 code_review.py --file /path/to/code.py
```
