#!/usr/bin/env python3
"""条款提取脚本 - 从合同文本中提取关键条款"""
import re, argparse
from pathlib import Path

CLAUSE_KEYWORDS = {
    "违约责任": ["违约", "违约金", "赔偿", "损失", "责任"],
    "知识产权": ["知识产权", "专利", "商标", "著作权", "许可", "授权"],
    "付款交付": ["付款", "支付", "交付", "验收", "账期", "发票"],
    "管辖争议": ["管辖", "仲裁", "诉讼", "争议解决", "法院"],
    "终止变更": ["终止", "解除", "续约", "续期", "变更", "修改"],
    "保密条款": ["保密", "商业秘密", "机密", "泄露"],
    "不可抗力": ["不可抗力", "意外", "天灾", "疫情"],
}

def extract_clauses(text):
    """按章节提取条款"""
    clauses = {}
    
    # 按段落分割
    paragraphs = text.split("\n")
    current_section = None
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # 检测章节标题（常见格式：第X条/第X章/X、/X.）
        if re.match(r'^(第[一二三四五六七八九十\d]+[条章节]|\d+[\.、]|【.+】)', para):
            current_section = para[:50]
            clauses[current_section] = para
        elif current_section:
            clauses[current_section] += "\n" + para
    
    # 按关键词分类
    categorized = {k: [] for k in CLAUSE_KEYWORDS}
    for title, content in clauses.items():
        for category, keywords in CLAUSE_KEYWORDS.items():
            if any(kw in content for kw in keywords):
                categorized[category].append({"title": title, "content": content[:500]})
    
    return categorized

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="合同文本文件")
    parser.add_argument("--output", help="输出JSON文件")
    args = parser.parse_args()
    
    text = Path(args.input).read_text(encoding="utf-8")
    result = extract_clauses(text)
    
    if args.output:
        import json
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"条款已提取：{args.output}")
    else:
        for cat, items in result.items():
            if items:
                print(f"\n## {cat}（{len(items)}条）")
                for item in items[:3]:  # 只显示前3条
                    print(f"  - {item['title'][:40]}...")
