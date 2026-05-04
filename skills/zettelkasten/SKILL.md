---
name: zettelkasten
description: 卡片盒笔记法技能。实现卢曼卡片盒系统： fleeting→literature→permanent 笔记流转，自动生成笔记ID、链接网络、索引卡片。适用于深度知识积累。
---

# Zettelkasten 卡片盒笔记法

## 笔记类型

| 类型 | 前缀 | 说明 |
|------|------|------|
| 闪念笔记 | F | 临时想法，快速记录 |
| 文献笔记 | L | 阅读摘录，带来源 |
| 永久笔记 | Z | 原子化知识卡片 |
| 项目笔记 | P | 特定项目相关 |

## ID格式

```
Z202605041200  =  Z + 年月日 + 4位序号
```

## 用法

```bash
python3 zettelkasten.py add "价值投资的核心是安全边际" --type Z --links "Z202605041100"
python3 zettelkasten.py search "安全边际"
python3 zettelkasten.py graph
```

## 快速命令

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/zettelkasten/scripts
python3 zettelkasten.py add "笔记内容" --type Z
```
