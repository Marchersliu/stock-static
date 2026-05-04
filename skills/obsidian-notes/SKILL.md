---
name: obsidian-notes
description: Obsidian笔记深度集成技能。与Obsidian vault交互，读取/创建/更新笔记，支持标签、链接、 frontmatter。实现AI助手与个人知识库的无缝连接。
---

# Obsidian Notes Obsidian笔记

## 功能

| 功能 | 说明 |
|------|------|
| 读取笔记 | 按标题/标签/路径搜索 |
| 创建笔记 | 自动生成frontmatter |
| 更新笔记 | 追加内容或修改 |
| 链接图谱 | 发现笔记间关联 |
| 标签管理 | 添加/删除标签 |

## 配置

```bash
# 设置vault路径
python3 obsidian_notes.py config --vault ~/Documents/Obsidian
```

## 用法

```bash
python3 obsidian_notes.py search "股票"
python3 obsidian_notes.py create "九州一轨分析" --content "..." --tags 股票,分析
python3 obsidian_notes.py update "九州一轨分析" --append "..."
```

## 快速命令

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/obsidian-notes/scripts
python3 obsidian_notes.py list --tags 股票
```
