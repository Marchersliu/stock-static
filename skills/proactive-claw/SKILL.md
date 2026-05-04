---
name: proactive-claw
description: 主动监控与智能提醒技能。不等用户提问，自动监控股票/日历/邮件/天气/项目状态，主动推送重要信息。当用户需要：(1) 盘中股票异动自动提醒，(2) 日历事件临近提醒，(3) 重要邮件到达通知，(4) 天气变化出门提醒，(5) 项目截止日期预警，(6) 定期数据核查自动化时使用。
---

# Proactive-Claw 主动型技能

## 核心功能

| 模块 | 监控内容 | 检查频率 | 提醒方式 |
|------|----------|----------|----------|
| **股票监控** | 持仓股涨跌停/±7%/目标价/止损/主力异动 | 盘中6次+收盘1次 | 消息推送 |
| **日历提醒** | 未来24-48h事件 | 每天2-4次 | 消息推送 |
| **邮件通知** | 重要未读邮件 | 每天2-4次 | 消息推送 |
| **天气提醒** | 雨天/降温/高温 | 每天1-2次 | 消息推送 |
| **项目预警** | 截止日期/里程碑 | 每天1次 | 消息推送 |
| **数据核查** | 股票数据一致性 | 交易日15:30 | 自动修复+报告 |

## 股票监控规则

### 检查时间点（交易日）

| 时间 | 检查内容 |
|------|----------|
| **9:35** | 开盘价、集合竞价、早盘资金流向、隔夜消息 |
| **10:30** | 实时价格、成交量、涨跌幅、±7%异动 |
| **11:25** | 午前检查、上午走势记录 |
| **13:05** | 午后开盘、大单异动 |
| **14:30** | 尾盘检查、主力动向 |
| **16:00** | 收盘总结、技术面更新、明日策略 |

### 触发提醒条件

```python
ALERT_RULES = {
    'price_move': {'threshold': 7, 'desc': '持仓股单日涨跌幅≥±7%'},
    'target_hit': {'desc': '触及目标价（九州一轨60/65等）'},
    'stop_loss': {'desc': '触及止损线（九州一轨49等）'},
    'moneyflow': {'threshold': 5000, 'desc': '主力净流入/流出≥5000万'},
    'commodity': {'threshold': 5, 'desc': '原材料价格单日±5%'},
    'announcement': {'desc': '持仓股突发公告/龙虎榜/大宗交易'},
}
```

### 静默规则

- **无异常** → 回复 `HEARTBEAT_OK`（不打扰）
- **有异常** → 推送提醒（含价格、原因、建议操作）
- **深夜23:00-08:00** → 除非urgent，否则静默
- **连续8h无互动** → 主动说点什么（非股票内容）

## 数据核查流程

### 核查时间
- **交易日 15:30**：Tushare发布当日日线后运行
- **非交易日**：跳过，使用最后交易日静态数据

### 核查内容

| 检查项 | 数据源 | 误差允许 |
|--------|--------|----------|
| 持仓现价 | Tushare pro.daily() | ±0.02% |
| 日涨跌 | Tushare pro.daily() | ±0.02% |
| 3日/5日/7日涨跌 | Tushare pro.daily() | ±0.02% |
| 主力流向 | Tushare pro.moneyflow() | ±0.1% |
| 新闻日期 | 日期不能为未来，超7天标记过时 | — |
| 财务数据 | Tushare pro.income() | 营收±10%, 净利±15% |

### 错误阈值
- 营收偏差 > 10% → ❌ 立即修正
- 净利润偏差 > 15% → ❌ 立即修正
- 任何差异 > ±0.02% → ❌ 输出差异并修正

## 主动推送模板

### 股票异动提醒
```
🚨 [股票名称] 异动提醒

当前价: XX.XX (±X.XX%)
触发条件: [涨跌停/±7%/目标价/止损/主力异动]

建议操作: [买入/卖出/观望/止损]

详细数据:
- 主力净流入: XXXX万
- 换手率: X.XX%
- 成交量: XXXX万
```

### 日历事件提醒
```
⏰ 日程提醒

[事件名称]
时间: [X月X日 XX:XX]
距离现在: [X小时X分钟]

准备事项: [如有]
```

## 配置文件

创建 `~/.proactive-claw.json`：

```json
{
  "stock": {
    "enabled": true,
    "holdings": ["688485.SH", "600989.SH"],
    "watchlist": ["600036.SH", "600900.SH"],
    "alert_threshold": 7,
    "moneyflow_threshold": 5000
  },
  "calendar": {
    "enabled": true,
    "lookahead_hours": 48
  },
  "email": {
    "enabled": false,
    "check_interval": "4h"
  },
  "weather": {
    "enabled": true,
    "location": "上海"
  },
  "quiet_hours": {
    "start": "23:00",
    "end": "08:00"
  }
}
```

## 定时任务设置

### Mac launchctl（推荐）

```bash
cat > ~/Library/LaunchAgents/com.hf.proactive-claw.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hf.proactive-claw</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Library/Developer/CommandLineTools/usr/bin/python3</string>
        <string>/Users/hf/.kimi_openclaw/workspace/skills/proactive-claw/scripts/proactive_daemon.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/proactive-claw.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/proactive-claw.log</string>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.hf.proactive-claw.plist
```

## 文件清单

```
proactive-claw/
├── SKILL.md                          # 本文件
├── scripts/
│   ├── proactive_daemon.py           # 主动监控守护进程
│   ├── stock_alert.py                # 股票异动检查
│   ├── calendar_check.py             # 日历事件检查
│   └── data_verify.py                # 数据核查脚本
└── references/
    └── alert_rules.md                # 完整提醒规则清单
```
