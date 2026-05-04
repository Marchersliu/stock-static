#!/usr/bin/env python3
"""合同风险评级主脚本"""
import sys, re, json, argparse
from pathlib import Path

# 风险模式库（简化版，完整版应放在 references/risk_patterns.md）
RISK_PATTERNS = {
    "违约责任": [
        (r"违约金.{0,10}(\d{2,3})%", "违约金超过30%可能过高", 15),
        (r"单方.*解除|任意.*解除", "单方解除权不对等", 12),
        (r"不承担.*责任|免责.*全部", "过度免责条款", 20),
        (r"赔偿.*全部.*损失|无限.*赔偿", "无限赔偿风险极高", 25),
    ],
    "知识产权": [
        (r"知识产权.*归.*(甲方|乙方|对方).*所有", "知识产权归属偏向一方", 15),
        (r"许可.*永久|授权.*无限期", "永久授权范围不清", 10),
        (r"竞业限制.{0,20}(\d{1,2}).*年|两年.*以上", "竞业限制期超过2年", 12),
    ],
    "付款交付": [
        (r"账期.{0,10}(\d{2,3}).*天|(\d{2,3})日.*付款", "账期超过90天", 10),
        (r"验收.*合理|合理.*期间", "验收标准模糊", 8),
        (r"不可抗力.*免责.*全部", "不可抗力免责过宽", 10),
    ],
    "管辖争议": [
        (r"管辖.{0,10}(对方|甲方|乙方).*所在地", "管辖地偏向一方", 10),
        (r"仲裁.*终局|一裁.*终局", "一裁终局放弃诉讼权", 12),
    ],
    "终止变更": [
        (r"自动.*续约|自动.*续期", "自动续约陷阱", 8),
        (r"通知.*(30|六十|60).*日|提前.*(30|60).*日", "提前通知期过长", 5),
    ],
}

def assess_contract(text):
    results = []
    total_score = 0
    for category, patterns in RISK_PATTERNS.items():
        cat_hits = []
        for pattern, desc, score in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for m in matches:
                # 提取上下文
                start = max(0, m.start() - 30)
                end = min(len(text), m.end() + 30)
                context = text[start:end].replace("\n", " ")
                cat_hits.append({"desc": desc, "score": score, "context": context})
                total_score += score
        if cat_hits:
            results.append({"category": category, "hits": cat_hits})
    
    # 评级
    if total_score <= 20: grade = "A"
    elif total_score <= 40: grade = "B"
    elif total_score <= 60: grade = "C"
    else: grade = "D"
    
    return {"grade": grade, "total_score": total_score, "results": results}

def generate_report(data, output_path):
    lines = [
        "# 合同风险审查报告",
        f"\n**风险评级：{data['grade']}（总分 {data['total_score']}）**",
        f"\n| 评级 | 说明 |",
        f"|------|------|",
        f"| A | 低风险，条款公平 |",
        f"| B | 中风险，有1-2处需注意 |",
        f"| C | 高风险，建议律师介入 |",
        f"| D | 极高风险，强烈不建议签署 |",
        "\n---\n",
    ]
    
    for cat in data["results"]:
        lines.append(f"\n## {cat['category']}")
        for hit in cat["hits"]:
            lines.append(f"\n⚠️ **{hit['desc']}**（风险分：{hit['score']}）")
            lines.append(f"> {hit['context']}")
            lines.append("")
    
    if data["total_score"] > 40:
        lines.append("\n---\n")
        lines.append("## 🔴 高风险提示")
        lines.append("本合同存在多处不对等条款，建议在签署前咨询专业律师。")
    
    Path(output_path).write_text("\n".join(lines), encoding="utf-8")
    print(f"报告已生成：{output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="合同文本文件路径")
    parser.add_argument("--output", default="contract_review.md")
    args = parser.parse_args()
    
    text = Path(args.input).read_text(encoding="utf-8")
    data = assess_contract(text)
    generate_report(data, args.output)
    print(f"评级：{data['grade']} | 总分：{data['total_score']}")
