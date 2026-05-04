#!/usr/bin/env python3
"""深度写作研究 - 大纲生成+文章框架"""
import sys, argparse, json
from pathlib import Path

def generate_outline(topic, depth=3):
    """生成文章大纲"""
    outline = {
        "title": topic,
        "sections": [
            {"heading": "执行摘要", "content": "3-5句话核心结论", "research_needed": True},
            {"heading": "1. 背景与定义", "content": "行业定义、发展历程、市场规模", "research_needed": True},
            {"heading": "2. 关键数据", "content": "增长率、市场份额、核心指标", "research_needed": True},
            {"heading": "3. 主要参与者", "content": "竞争格局、龙头公司、新兴玩家", "research_needed": True},
            {"heading": "4. 技术/产品趋势", "content": "创新方向、技术路线、产品演进", "research_needed": depth >= 2},
            {"heading": "5. 政策与监管", "content": "相关政策、法规变化、行业标准", "research_needed": depth >= 2},
            {"heading": "6. 风险与挑战", "content": "行业风险、不确定因素、潜在威胁", "research_needed": depth >= 2},
            {"heading": "7. 结论与建议", "content": "核心判断、行动建议、未来展望", "research_needed": False},
        ]
    }
    return outline

def write_article(topic, depth, output_path):
    outline = generate_outline(topic, depth)
    
    lines = [
        f"# {outline['title']}",
        "\n> **写作提示**：本文档为AI辅助写作框架，每个章节下方标注了需要研究补充的内容。",
        f"\n> **研究深度**：{depth}轮搜索 | 建议配合 `deep-research` 技能使用",
        "\n---\n",
    ]
    
    for section in outline["sections"]:
        lines.append(f"\n## {section['heading']}")
        if section["research_needed"]:
            lines.append(f"\n🔍 **待研究**：{section['content']}")
            lines.append("\n> 提示：使用 `kimi_search` 或 `web_search` 搜索相关数据，填入此处。")
        else:
            lines.append(f"\n{section['content']}")
        lines.append("\n")
    
    lines.extend([
        "\n---\n",
        "\n## 引用来源",
        "\n| 编号 | 来源 | URL |",
        "|------|------|-----|",
        "| [1] | 待补充 | - |",
        "\n---\n",
        f"\n*生成时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}*",
    ])
    
    Path(output_path).write_text("\n".join(lines), encoding="utf-8")
    print(f"文章框架已生成：{output_path}")
    print(f"章节数：{len(outline['sections'])}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("topic", help="文章主题")
    parser.add_argument("--depth", type=int, choices=[1,2,3], default=3)
    parser.add_argument("--output", default="article.md")
    args = parser.parse_args()
    write_article(args.topic, args.depth, args.output)
