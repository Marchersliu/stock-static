---
name: cognitive-memory
description: 人脑式认知记忆系统。模拟人类记忆分层架构（情境/语义/程序性），通过5W1H情境编码、联想网络和遗忘曲线实现智能记忆检索。当用户需要跨session记住复杂上下文、通过联想找回信息、区分重要与临时记忆时使用。
---

# Cognitive Memory - 人脑式认知记忆

## 核心概念

人类记忆不是简单的键值对存储，而是分层的、关联的、有情感的、会遗忘的。本系统模拟人脑的记忆机制：

| 记忆类型 | 人脑对应 | 系统实现 | 示例 |
|----------|----------|----------|------|
| **情境记忆** | 海马体 | 完整事件记录（5W1H） | "2026-05-04修复恒指+2026%bug" |
| **语义记忆** | 皮层 | 概念网络（定义+关联） | "sed=危险工具，edit=安全工具" |
| **程序性记忆** | 小脑/基底节 | 自动化工作流 | "修复HTML→先edit→再node --check" |
| **联想网络** | 神经元连接 | 标签关联+强度权重 | "股票→九州一轨→目标价60" |
| **情感标记** | 杏仁核 | 重要性/紧急度权重 | 🔴critical 🟡important ⚪routine |

## 5W1H 情境编码

每个记忆片段用完整情境编码，而不只是文本：

```json
{
  "id": "ep_20260504_001",
  "type": "episode",
  "encoding": {
    "when": "2026-05-04 14:00",
    "where": "stock_dashboard.html / inject_live_data.py",
    "who": ["HF", "Kimi"],
    "what": "恒指显示+2026%，修复为+1.62%",
    "why": "腾讯接口字段映射错误，parts[30]是日期字符串不是涨跌幅",
    "how": "前后端统一用parts[31]涨跌额和parts[32]涨跌幅%"
  },
  "tags": ["腾讯接口", "字段映射", "恒指", "bug修复"],
  "emotional_weight": 0.8,
  "access_count": 3,
  "last_access": "2026-05-04 19:20"
}
```

## 联想网络

```json
{
  "concepts": {
    "sed命令": {
      "definition": "流编辑器，单行替换工具",
      "associations": [
        {"to": "HTML破坏", "strength": 0.95, "type": "causes"},
        {"to": "模板字面量", "strength": 0.9, "type": "destroys"},
        {"to": "edit工具", "strength": 0.85, "type": "alternative"}
      ],
      "emotional_tag": "danger"
    },
    "edit工具": {
      "definition": "OpenClaw精确文本替换工具",
      "associations": [
        {"to": "sed命令", "strength": 0.85, "type": "safer_than"},
        {"to": "精确替换", "strength": 0.9, "type": "feature"}
      ],
      "emotional_tag": "safe"
    }
  }
}
```

## 遗忘曲线（Ebbinghaus模型）

```
记忆强度 = base_strength × e^(-decay_rate × days_since_last_access)

参数：
- base_strength: 1.0（新记忆）~ 2.0（巩固记忆）
- decay_rate: 0.1（routine）/ 0.05（important）/ 0.01（critical）
- 每次访问后 base_strength += 0.1，上限 3.0

阈值：
- >0.7: 清晰记忆，可直接提取
- 0.3~0.7: 模糊记忆，需要提示/关联触发
- <0.3: 遗忘区，仅在强烈关联激活时浮现
```

## 记忆检索方式

### 1. 直接回忆（精确匹配）
```bash
python3 memory_manager.py --recall "恒指bug"
```

### 2. 联想回忆（扩散激活）
```bash
python3 memory_manager.py --associate "腾讯接口"
# 返回：恒指bug → 字段映射 → parts数组 → 日期解析
```

### 3. 情境回忆（5W1H查询）
```bash
python3 memory_manager.py --context --who HF --where "stock_dashboard" --when "2026-05"
```

### 4. 情感回忆（按重要性）
```bash
python3 memory_manager.py --emotional critical
# 返回所有 critical 标记的记忆
```

### 5. 程序回忆（如何做）
```bash
python3 memory_manager.py --procedure "修复HTML日期"
# 返回完整步骤链条
```

## 记忆巩固流程

```
Session结束 → 自动扫描 → 提取关键事件 → 5W1H编码 → 写入情境记忆
                                          ↓
                                     概念提取 → 更新语义网络
                                          ↓
                                     流程提取 → 更新程序记忆
                                          ↓
                                     计算关联 → 更新联想网络
                                          ↓
                                     24h后再次激活 → 转入长期记忆
```

## 使用场景

| 场景 | 传统搜索 | 认知记忆 |
|------|----------|----------|
| "上次恒指bug怎么修的" | grep "恒指" → 可能找到几十条 | 联想"腾讯接口"→直接定位到字段映射 |
| "我纠正过你什么" | 翻阅所有memory文件 | 查询corrections概念→列出所有纠正链条 |
| "为什么不用sed" | 搜索sed相关记录 | 联想sed→danger→HTML破坏→具体事件 |
| "股票怎么部署的" | 找stock相关文件 | 程序记忆→完整部署流程（GitHub→Vercel→GitHub Pages） |

## 文件清单

```
cognitive-memory/
├── SKILL.md                          # 本文件
├── scripts/
│   ├── memory_manager.py             # 核心记忆管理器（编码/存储/检索/遗忘）
│   ├── associative_recall.py         # 联想回忆引擎
│   └── consolidation.py             # 记忆巩固脚本（Session结束时运行）
└── references/
    └── memory_model.md               # 认知记忆模型理论文档
```

## 数据库文件

```
workspace/
├── memory/
│   └── cognitive_memory.json          # 核心认知记忆数据库
│   └── preferences.json               # 简单偏好（兼容self-improving）
```

## 与其他技能的关系

| 技能 | 功能 | 关系 |
|------|------|------|
| **self-improving** | 偏好学习、复盘 | cognitive-memory 接收其提取的偏好，存入语义网络 |
| **proactive-claw** | 主动监控 | cognitive-memory 提供"何时发生过类似事件"的历史 |
| **stock-monitor** | 股票数据 | cognitive-memory 记录每次分析的结果和决策 |
| **memory/YYYY-MM-DD.md** | 原始日志 | cognitive-memory 从日志中提取结构化记忆 |

## 核心脚本

| 脚本 | 功能 | 用法 |
|------|------|------|
| `memory_manager.py` | 记忆编码/检索/遗忘 | `--encode`, `--search`, `--associate`, `--health` |
| `consolidation.py` | Session日志→认知记忆 | `--file memory/YYYY-MM-DD.md` |
| `reflect.py` | 自我反思引擎 | `--auto`, `--history` |
| `critique.py` | 自我批评引擎 | `--file`, `--stats` |
| `learn.py` | 自我学习引擎 | `--all`, `--summary`, `--apply` |
| `tiered_memory.py` | 分层记忆管理 | `--rebalance`, `--status` |

## 工作流：完整的自我反思-批评-学习循环

```
Session结束
  ↓
consolidation.py --file memory/2026-05-04.md
  ↓ 提取事件到认知记忆
reflect.py --auto
  ↓ 评估输出质量（5维度评分）
critique.py --file memory/2026-05-04.md
  ↓ 识别错误和可改进点
learn.py --all
  ↓ 从反思+批评+纠正中提取规则
tiered_memory.py --rebalance
  ↓ 晋升/降级记忆层级
USER.md / AGENTS.md 更新
  ↓ 规则固化到长期记忆
下次session自动应用
```

## 从纠正中学习（自动触发）

用户说这些关键词时，自动记录为规则：

| 信号 | 示例 | 记录内容 | 置信度 |
|------|------|----------|--------|
| "不对" | "不对，应该是XXX" | 旧做法→新做法 | 0.9 |
| "错了" | "错了，用YYY才对" | 错误模式→修正 | 0.9 |
| "应该用" | "应该用edit而不是sed" | 工具偏好 | 0.85 |
| "不要" | "不要废话" | 风格偏好 | 0.8 |
| "我喜欢" | "我喜欢简洁的" | 个人偏好 | 0.75 |
| "以后" | "以后都用这种方式" | 默认规则 | 0.85 |

## 分层记忆（HOT/WARM/COLD）

| 层级 | 定义 | 容量 | 衰减 | 晋升条件 |
|------|------|------|------|----------|
| **HOT** | 高频使用，随时提取 | 20条 | 7天 | 3次使用 |
| **WARM** | 项目/领域相关 | 50条 | 30天 | 3次使用 |
| **COLD** | 归档记忆 | 200条 | 90天 | 强关联激活 |
| **ARCHIVED** | 压缩归档 | ∞ | ∞ | 手动恢复 |

## 快速开始

```bash
# 完整的session后处理流程
python3 consolidation.py --latest && \
python3 reflect.py --auto && \
python3 critique.py && \
python3 learn.py --all && \
python3 tiered_memory.py --rebalance

# 编码新记忆
python3 memory_manager.py --encode \
  --what "修复恒指显示bug" \
  --where "stock_dashboard.html" \
  --why "字段映射错误" \
  --how "统一用parts[31]和parts[32]" \
  --tags "腾讯接口,字段映射,恒指" \
  --emotional 0.9

# 联想回忆
python3 memory_manager.py --associate "腾讯接口" --depth 2

# 查看学习成果
python3 learn.py --summary
```
