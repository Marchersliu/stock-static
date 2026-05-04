---
name: task-manager
description: 任务管理技能。创建、跟踪、优先级排序任务，支持标签、截止日期、状态流转。与OpenClaw heartbeat/cron集成实现任务提醒。
---

# Task Manager 任务管理

## 功能

| 功能 | 说明 |
|------|------|
| 添加任务 | `add` 标题、描述、截止日期、优先级 |
| 列表 | `list` 按状态/优先级筛选 |
| 完成 | `done` 标记完成 |
| 删除 | `delete` 删除任务 |
| 提醒 | 截止日期前自动提醒 |

## 优先级

| 级别 | 标识 | 说明 |
|------|------|------|
| P0 | 🔴 | 紧急重要，今天必须做 |
| P1 | 🟡 | 重要，本周完成 |
| P2 | 🟢 | 一般，有空做 |
| P3 | ⚪ | 低优先级，备忘 |

## 用法

```bash
python3 task_manager.py add "完成九州一轨研报" --priority P1 --due 2026-05-05 --tags 股票,研报
python3 task_manager.py list --status pending --priority P0,P1
python3 task_manager.py done 1
```

## 快速命令

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/task-manager/scripts
python3 task_manager.py list
```
