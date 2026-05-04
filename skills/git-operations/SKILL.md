---
name: git-operations
description: Git高级操作技能。封装常用Git工作流：批量提交、分支管理、stash操作、cherry-pick、冲突解决、log分析。简化日常Git操作。
---

# Git Operations Git高级操作

## 功能

| 命令 | 说明 |
|------|------|
| `smart-commit` | 自动stage+提交，生成规范message |
| `bulk-add` | 批量添加文件，按类型分组 |
| `safe-push` | pull+merge+push，避免强制推送 |
| `undo` | 安全撤销上次提交（保留改动） |
| `cleanup` | 清理已合并分支 |
| `log-graph` | 可视化分支图 |

## 提交规范

```
type(scope): subject

body

footer
```

## 用法

```bash
python3 git_operations.py smart-commit "feat: add stock monitor"
python3 git_operations.py undo --soft
python3 git_operations.py log-graph --since "1 week ago"
```

## 快速命令

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/git-operations/scripts
python3 git_operations.py smart-commit "更新股票数据"
```
