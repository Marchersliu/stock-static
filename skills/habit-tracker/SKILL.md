---
name: habit-tracker
description: 习惯追踪技能。记录习惯完成情况，生成 streak（连续天数）、周/月统计、可视化图表。支持打卡提醒和趋势分析。
---

# Habit Tracker 习惯追踪

## 功能

| 功能 | 说明 |
|------|------|
| 添加习惯 | 名称、频率、目标 |
| 打卡 | 标记今天完成 |
| 统计 | streak、完成率、趋势 |
| 图表 | 周/月热力图 |
| 提醒 | 未打卡提醒 |

## 频率类型

| 类型 | 说明 |
|------|------|
| daily | 每天 |
| weekday | 工作日 |
| weekly | 每周N次 |
| custom | 自定义 |

## 用法

```bash
python3 habit_tracker.py add "晨读" --frequency daily --goal "每天30分钟"
python3 habit_tracker.py checkin "晨读"
python3 habit_tracker.py stats
python3 habit_tracker.py chart
```

## 快速命令

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/habit-tracker/scripts
python3 habit_tracker.py list
```
