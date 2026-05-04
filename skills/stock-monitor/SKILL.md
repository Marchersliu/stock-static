---
name: stock-monitor
description: A股股票实时监控与自动化分析技能。包含数据抓取、报告生成、技术分析、新闻监控、异常提醒五大模块。使用当用户需要：(1) 抓取A股实时行情/期货/板块资金流向，(2) 生成持仓日报/周报/技术分析报告，(3) 计算KDJ/MACD/RSI等技术指标并提示买卖点，(4) 监控持仓股新闻并自动过滤关联度，(5) 设置盘中异常提醒（涨跌停/±7%/大单异动）。与Tushare Pro和腾讯接口集成，支持12只持仓股票实时监控。
---

# Stock Monitor 股票监控技能

## 模块概览

| 模块 | 脚本 | 功能 |
|------|------|------|
| 数据抓取 | `scripts/fetch_data.py` | Tushare/腾讯接口实时拉取、期货价格、板块资金 |
| 报告生成 | `scripts/generate_report.py` | 自动生成持仓日报/周报（HTML/PDF） |
| 技术分析 | `scripts/tech_analysis.py` | KDJ/MACD/RSI计算、买卖点提示 |
| 新闻监控 | `scripts/news_monitor.py` | 持仓股新闻自动抓取、过滤、关联度评分 |
| 异常提醒 | `scripts/alert_system.py` | 涨跌停/±7%/大单异动自动通知 |

## 持仓股票列表

读取 `references/stock_codes.md` 获取完整股票映射（代码、名称、板块、目标价、止损）。

## 前置条件

- Tushare Pro Token（需购买）
- Python 3.8+
- 依赖包：`pip install tushare requests pandas numpy python-docx`

## 快速开始

### 1. 数据抓取
```bash
python3 scripts/fetch_data.py --type all --output /tmp/stock_data.json
```

支持类型：`all|price|moneyflow|sector|commodity|index`

### 2. 报告生成
```bash
python3 scripts/generate_report.py --type daily --output ~/Desktop/持仓日报.html
```

支持类型：`daily|weekly|monthly`

### 3. 技术分析
```bash
python3 scripts/tech_analysis.py --code 688485.SH --indicators kdj,macd,rsi
```

### 4. 新闻监控
```bash
python3 scripts/news_monitor.py --filter portfolio --max 50
```

### 5. 异常提醒
```bash
python3 scripts/alert_system.py --watch --threshold 7
```

## 详细模块说明

### 数据抓取模块

**API来源：**
- Tushare Pro：`pro.daily()`, `pro.moneyflow()`, `pro.daily_basic()`, `pro.fut_daily()`, `pro.index_daily()`
- 腾讯接口：`https://qt.gtimg.cn/q=...`（港股/实时行情）

**数据类型：**
- 个股行情：开/高/低/收/量/额
- 资金流向：主力净流入、散户净流入
- 板块资金：12大行业主力净流入聚合
- 期货价格：20种原料期货收盘价
- 指数行情：上证指数、深成指、创业板指、恒生指数

**缓存策略：**
- 交易日盘中：120秒缓存
- 非交易日：600秒缓存

读取 `references/tushare_api.md` 获取完整API文档和调用示例。

### 报告生成模块

**报告内容：**
1. 持仓总览（现价、日涨跌、3日/5日/7日涨跌）
2. 计划建仓表（8只观察股）
3. 三因子标识（消息面/资金面/技术面）
4. 盘前新闻（PREMARKET_NEWS，AI审核+关联分析）
5. 产业链表格（原料价格、关联度）
6. 全球市场价格（美股/港股/油价/金价）
7. 重大事件监控（5日内·直接相关）

**输出格式：**
- HTML：带CSS样式的完整页面
- PDF：通过浏览器打印转换
- Markdown：纯文本摘要

### 技术分析模块

**指标计算：**
- **KDJ**：K值、D值、J值，金叉死叉提示
- **MACD**：DIF、DEA、MACD柱，背离检测
- **RSI**：6日/12日/24日，超买超卖提示
- **MA**：5/10/20/60日均线，多头排列检测
- **BOLL**：上轨/中轨/下轨，突破提示

**买卖信号：**
- 买入信号：KDJ金叉+MACD红柱放大+RSI<70
- 卖出信号：KDJ死叉+MACD绿柱放大+RSI>80
- 止损提示：跌破止损线（如九州一轨49元）

### 新闻监控模块

**新闻来源：**
- Tushare Pro：`pro.major_news()`（每分钟400次，已购买独立权限）
- 巨潮资讯：上市公司公告
- 东方财富：公告/研报
- 新浪财经：快讯

**过滤逻辑：**
1. 关联度评分：`direct`(持仓直接关联) > `industry`(行业关联) > `none`
2. 分类标签：`portfolio`(持仓) / `chain`(产业链) / `policy`(政策) / `geo`(地缘) / `market`(市场)
3. 排除词：票房、景区、民警、门票、离婚、水獭等社会新闻
4. 时间过滤：当日优先，无则近3日

**输出：**
- 关联度>=2的新闻：红色边框高亮
- 持仓/建仓股新闻：置顶显示

### 异常提醒模块

**监控条件：**
- 持仓股单日涨跌幅 >= ±7%
- 触及目标价（九州一轨60/65，宝丰29建仓等）
- 触及止损线（九州一轨49，迈瑞140等）
- 主力资金异常流入/流出（±5000万+）
- 原材料价格重大变化（锂/钴/镍/锶/原油单日±5%）
- 持仓股突发公告、龙虎榜、大宗交易

**提醒方式：**
- 控制台输出（带颜色）
- 日志文件：`/tmp/stock_alerts.log`
- 可选：接入消息推送（需要额外配置）

## 配置文件

在脚本同级目录创建 `.env` 文件：
```
TUSHARE_TOKEN=你的Tushare Pro Token
LAST_TRADE_DATE=2026-04-30
```

## 错误处理

| 错误 | 原因 | 解决 |
|------|------|------|
| `token不对` | Tushare Token失效 | 检查 `.env` 或重新购买 |
| `频率超限` | 达到Tushare限制 | 检查是否购买独立权限 |
| `0 rows` | 港股数据无权限 | 改用腾讯接口替代 |
| `ET is not defined` | RSS解析缺少依赖 | `pip install lxml` |

## 文件清单

```
stock-monitor/
├── SKILL.md                          # 本文件
├── scripts/
│   ├── fetch_data.py                 # 数据抓取主脚本
│   ├── generate_report.py            # 报告生成主脚本
│   ├── tech_analysis.py              # 技术分析主脚本
│   ├── news_monitor.py              # 新闻监控主脚本
│   ├── alert_system.py              # 异常提醒主脚本
│   └── utils.py                     # 公共工具函数
├── references/
│   ├── tushare_api.md               # Tushare API完整文档
│   ├── stock_codes.md               # 持仓股票映射表
│   └── indicators_formula.md       # 技术指标计算公式
└── assets/
    └── report_template.html          # 报告HTML模板
```

## 注意事项

1. **Tushare Token安全**：Token存在`.env`或环境变量，不提交到GitHub
2. **API频率限制**：`major_news` 30次/小时（未买独立权限时），`news` 2次/天
3. **港股数据**：Tushare `index_global` 对恒指返回0行，用腾讯`qt.gtimg.cn`替代
4. **缓存策略**：盘中120秒，休市600秒，避免频繁调用
5. **数据验证**：所有注入HTML的数据需`node --check`验证JS语法
