---
name: self-improving
description: 自我复盘与持续优化技能。自动分析工作记录、识别低效模式、提出改进方案、追踪优化效果、学习用户偏好。当用户需要：(1) 复盘最近工作找出问题和改进点，(2) 优化重复性工作流减少token浪费，(3) 建立更好的文件组织和命名规范，(4) 减少同类bug重复发生，(5) 提升跨session连续性，(6) 记录用户偏好和纠正让助手越用越聪明时使用。
---

# Self-Improving 自我优化技能

## 核心功能

| 模块 | 功能 | 触发条件 |
|------|------|----------|
| **工作复盘** | 分析session日志，找出错误模式和低效操作 | 用户说"复盘"、"总结一下"、"哪里可以改进" |
| **效率优化** | 识别重复性任务，提出自动化/脚本化方案 | 发现同一操作执行3次以上 |
| **错误预防** | 从过往错误中提取规则，写入AGENTS.md | 同类bug发生2次以上 |
| **知识沉淀** | 将session中的重要决策写入MEMORY.md | 关键决策、约定、教训 |
| **连续性检查** | 确保跨session的记忆不丢失 | 每次session启动时 |
| **偏好学习** | 记录用户纠正和偏好，自动应用 | 用户说"不对"、"我喜欢"、"改成"、"不要" |

## 偏好学习模块（越用越聪明）

### 工作原理

当用户纠正助手或表达偏好时，自动提取并记录：

| 用户信号 | 示例 | 记录内容 |
|----------|------|----------|
| **纠正错误** | "不对，应该是XXX" | 错误模式 → 正确做法 |
| **表达偏好** | "我喜欢简洁的" | 风格偏好 |
| **拒绝方案** | "不要这样" | 禁止事项 |
| **确认习惯** | "以后都这样做" | 默认规则 |
| **调整参数** | "改成15分钟" | 数值偏好 |

### 偏好存储

```
workspace/
├── USER.md              # 用户基本信息（手动维护）
├── MEMORY.md            # 长期记忆（助手主动更新）
├── memory/
│   └── preferences.json  # 结构化偏好数据库（自动维护）
```

**preferences.json 结构：**
```json
{
  "corrections": [
    {
      "date": "2026-05-04",
      "context": "股票监控",
      "trigger": "新闻日期不对",
      "old_behavior": "只更新PREMARKET_NEWS数组，不更新标题日期",
      "new_behavior": "同时更新news-date-title元素",
      "applied_count": 3
    }
  ],
  "preferences": [
    {
      "date": "2026-05-04",
      "category": "沟通风格",
      "preference": "简洁直接，不要废话",
      "confidence": "high",
      "source": "USER.md"
    },
    {
      "date": "2026-05-04",
      "category": "股票数据",
      "preference": "自动更新间隔15分钟",
      "confidence": "high",
      "source": "用户直接设定"
    }
  ],
  "banned_patterns": [
    {
      "date": "2026-05-04",
      "pattern": "用sed修改HTML",
      "reason": "会破坏多属性行和模板字面量",
      "severity": "critical"
    }
  ]
}
```

### 偏好应用规则

1. **启动时加载**：每次session启动读取 `preferences.json`，在system prompt中隐性应用
2. **高置信度优先**：`confidence=high` 的偏好直接应用，`medium` 的偏好询问确认
3. **冲突检测**：新偏好与旧偏好冲突时，优先使用日期更新的
4. **遗忘机制**：超过90天未应用的 `medium` 偏好降级为 `low`
5. **正向反馈**：应用偏好后如果用户未纠正，增加 `applied_count` 提升置信度

### 偏好学习脚本

```bash
# 手动触发偏好学习
python3 scripts/preference_learner.py --scan memory/2026-05-04.md

# 列出所有记录的偏好
python3 scripts/preference_learner.py --list

# 应用偏到 USER.md
python3 scripts/preference_learner.py --apply

# 检查偏好健康度（重复/冲突/过时）
python3 scripts/preference_learner.py --health
```

### 偏好学习关键词触发

| 关键词 | 类型 | 处理方式 |
|--------|------|----------|
| "不对"、"错了"、"应该是" | 纠正 | 提取old→new，写入corrections |
| "我喜欢"、"我希望"、"prefer" | 偏好 | 提取preference，写入preferences |
| "不要"、"别"、"禁止"、"never" | 禁止 | 提取pattern，写入banned_patterns |
| "以后"、"always"、"默认" | 规则 | 提取rule，写入default_rules |
| "太慢"、"太快"、"改成X" | 数值 | 提取数值参数，写入settings |

## 复盘流程

### 1. 读取工作日志

```bash
# 读取最近的memory文件
ls -lt memory/2026-*.md | head -5
cat memory/2026-05-04.md
```

### 2. 识别问题模式

| 问题类型 | 识别方法 | 示例 |
|----------|----------|------|
| **重复错误** | 同一关键词出现>=2次 | "sed破坏"、"语法错误"、"缓存" |
| **低效流程** | 同一操作>=3次且无脚本化 | "手动复制"、"逐个修改" |
| **token浪费** | 大段无意义输出/重复确认 | "好的"、"明白了"刷屏 |
| **记忆丢失** | 用户重复问过的问题 | "服务器PID多少"重复问 |
| **安全违规** | 敏感信息泄露 | token出现在对话中 |

### 3. 提出改进方案

**方案模板：**
```markdown
## 改进建议

### 问题：[问题描述]
- 发生次数：X次
- 影响：[时间损失/数据错误/用户体验]

### 根因：[为什么发生]

### 解决方案：[具体做法]
1. [步骤1]
2. [步骤2]

### 预防措施：[写入规则]
- AGENTS.md 新增：[规则]
- TOOLS.md 新增：[快捷命令]
```

### 4. 写入规则文件

**AGENTS.md 新增规则示例：**
```markdown
### 🚫 sed禁令（2026-05-04）
任何包含多属性HTML/JS的行，禁止用sed，必须用edit工具精确替换。
违反后果：模板字面量闭合反引号被摧毁，整个script块失效。

### ✅ 验证铁律（2026-05-04）
任何数据插入后必须 node --check 验证JS语法，python3 -m py_compile验证Python语法。
```

## 常用复盘命令

```bash
# 统计今日错误关键词
grep -i "error\|err\|fail\|warn\|bug\|fix\|修复" memory/2026-05-04.md | wc -l

# 查找重复操作
grep -o "sed\|edit\|cp\|python3\|curl" memory/2026-05-04.md | sort | uniq -c | sort -rn | head -10

# 检查敏感信息泄露
grep -i "token\|password\|secret\|key" memory/2026-05-04.md | grep -v "[REDACTED]"

# 统计token消耗（估算）
wc -w memory/2026-05-04.md
```

## 效率指标

| 指标 | 目标 | 监控方法 |
|------|------|----------|
| 同类错误重复率 | <20% | 统计同一错误关键词出现次数 |
| 自动化覆盖率 | >60% | 手动操作 / 脚本化操作比例 |
| 跨session记忆完整度 | >90% | 用户重复提问的比例 |
| 验证通过率 | >95% | node --check / py_compile 一次通过率 |

## 文件清单

```
self-improving/
├── SKILL.md                          # 本文件
├── scripts/
│   ├── review_session.py             # 自动复盘脚本
│   └── preference_learner.py         # 偏好学习脚本（越用越聪明）
└── references/
    └── review_template.md            # 复盘报告模板
```
