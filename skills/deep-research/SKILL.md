---
name: deep-research
description: 深度研究技能。多轮搜索+信息提取+交叉验证+结构化总结，生成高质量研究报告。适用于行业分析、竞品调研、技术评估、投资研究等需要深度信息的场景。
---

# Deep Research 深度研究

## 核心流程

```
用户输入研究主题
  ↓
第1轮搜索 → 获取广泛信息，建立知识框架
  ↓
提取关键子主题
  ↓
第2轮搜索 → 深入子主题
  ↓
交叉验证（多源对比）
  ↓
第3轮搜索 → 补充细节/数据
  ↓
结构化总结
  ↓
输出研究报告
```

## 研究维度

| 维度 | 说明 | 工具 |
|------|------|------|
| **背景概况** | 定义、历史、市场规模 | kimi_search |
| **关键数据** | 数字、增长率、市场份额 | kimi_search + kimi_finance |
| **主要玩家** | 公司、产品、竞争格局 | web_search |
| **技术趋势** | 技术路线、创新点 | kimi_search |
| **政策监管** | 政策、法规、行业标准 | web_search |
| **风险因素** | 风险、挑战、不确定性 | 综合分析 |

## 交叉验证规则

- 关键数据需 **2+ 独立来源** 确认
- 矛盾信息标注 ⚠️ 并列出不同说法
- 引用来源 URL
- 区分"事实"和"观点"

## 输出格式

```markdown
# 研究报告: {主题}

## 执行摘要
（3-5句话核心结论）

## 1. 背景概况
## 2. 市场数据
## 3. 竞争格局
## 4. 技术趋势
## 5. 政策监管
## 6. 风险与挑战
## 7. 结论与建议

---
数据来源: [1] URL1 | [2] URL2 | ...
研究时间: {date}
置信度: {high/medium/low}
```

## 用法

```bash
# 生成研究报告
python3 deep_research.py "固态电池技术路线" --depth 3 --output report.md

# 快速研究（2轮）
python3 deep_research.py "人形机器人市场规模" --depth 2

# 带数据验证
python3 deep_research.py "钙钛矿太阳能电池效率" --depth 3 --verify
```

## 快速命令

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/deep-research/scripts
python3 deep_research.py "研究主题" --depth 3
```
