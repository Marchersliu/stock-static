---
name: legal-risk-assessment
description: 合同/协议风险自动评级与条款审查。使用场景：(1) 审查商业合同中的风险条款（违约责任、管辖权、知识产权归属），(2) 评估投资协议/对赌条款的潜在法律风险，(3) 识别劳动合同中的不合理条款，(4) 给合同按A/B/C/D四级风险评级并生成审查报告。
---

# 合同风险评级技能

## 工作流程

1. **接收合同文本**（PDF/Word/纯文本）
2. **条款结构化提取** → 调用 `scripts/extract_clauses.py`
3. **风险识别** → 对照 `references/risk_patterns.md` 中的风险模式库
4. **评级打分** → A（低风险）/ B（中风险）/ C（高风险）/ D（极高风险）
5. **生成审查报告** → Markdown 格式，含条款原文+风险提示+修改建议

## 风险维度

| 维度 | 权重 | 说明 |
|------|------|------|
| 违约责任 | 25% | 违约金过高、单方免责、不对等赔偿 |
| 知识产权 | 20% | 归属不清、授权范围模糊、竞业限制 |
| 付款/交付 | 20% | 账期过长、验收标准模糊、不可抗力免责 |
| 管辖/争议 | 15% | 管辖地不利、仲裁条款陷阱 |
| 终止/变更 | 10% | 单方解除权、自动续约陷阱 |
| 其他 | 10% | 保密条款、数据安全、合规性 |

## 评级标准

- **A（低风险）**：总分 ≤ 20，条款公平，无明显风险点
- **B（中风险）**：总分 21-40，有1-2处需注意的条款
- **C（高风险）**：总分 41-60，多处不对等条款，建议律师介入
- **D（极高风险）**：总分 > 60，重大风险条款，强烈不建议签署

## 快速使用

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/legal-risk-assessment/scripts
python3 assess_contract.py /path/to/contract.pdf --output report.md
```

## 文件清单

```
legal-risk-assessment/
├── SKILL.md
├── scripts/
│   ├── extract_clauses.py      # 条款提取
│   └── assess_contract.py       # 风险评估主脚本
├── references/
│   └── risk_patterns.md         # 风险模式库（300+条规则）
└── assets/
    └── report_template.md       # 报告模板
```