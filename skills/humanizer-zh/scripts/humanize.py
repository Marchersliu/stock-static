#!/usr/bin/env python3
"""中文去AI化脚本"""
import sys, re, argparse
from pathlib import Path

# AI高频词 → 自然表达
REPLACEMENTS = {
    "值得注意的是": ["有意思的是", "多说一句", "这里有个点", ""],
    "综上所述": ["总的来说", "说白了", "一句话总结", ""],
    "首先": ["第一", "先说", "开头", ""],
    "其次": ["第二", "接着", "再说", ""],
    "最后": ["第三", "结尾", "最后一点", ""],
    "因此": ["所以", "结果就是", "这就导致", ""],
    "然而": ["但是", "不过", "有意思的是", ""],
    "此外": ["另外", "还有一点", "顺便提一下", ""],
    "必然": ["大概率", "很可能", "基本上", ""],
    "毫无疑问": ["说实话", "平心而论", "老实说", ""],
    "非常重要": ["很关键", "不能忽视", "得重视", ""],
    "进行": ["做", "搞", "整", ""],
    "实施": ["干", "做", "落地", ""],
    "优化": ["改好", "调好", "弄顺", ""],
    "提升": ["提高", "往上拉", "涨", ""],
    "呈现": ["显示", "表现出来", "看起来是", ""],
    "导致": ["造成", "引来", "带出", ""],
    "显著": ["明显", "挺大", "肉眼可见", ""],
}

# 过于工整的排比结构检测
PARALLEL_PATTERNS = [
    r"(首先|第一).*?(其次|第二).*?(最后|第三|综上所述)",
    r"(一方面).*?(另一方面)",
]

def humanize(text, intensity="medium"):
    # 1. 替换AI高频词
    for old, alternatives in REPLACEMENTS.items():
        def repl(m):
            import random
            return random.choice(alternatives) if alternatives else ""
        text = re.sub(old, repl, text)
    
    # 2. 打散长段落（超过150字且连续3段以上等长）
    if intensity in ("medium", "heavy"):
        paragraphs = text.split("\n\n")
        new_para = []
        for p in paragraphs:
            if len(p) > 200 and intensity == "heavy":
                # 拆成两段
                mid = len(p) // 2
                split_at = p.rfind("。", mid-50, mid+50)
                if split_at > 0:
                    new_para.append(p[:split_at+1])
                    new_para.append(p[split_at+1:].strip())
                else:
                    new_para.append(p)
            else:
                new_para.append(p)
        text = "\n\n".join(new_para)
    
    # 3. 加入口语化停顿（重度）
    if intensity == "heavy":
        sentences = re.split(r'(。！？)', text)
        result = []
        for i in range(0, len(sentences)-1, 2):
            s = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else "")
            if i > 0 and i % 6 == 0:  # 每3句加一个短句
                s = s.replace("。", "。\n\n说实话，", 1)
            result.append(s)
        text = "".join(result)
    
    return text

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="输入文件")
    parser.add_argument("--output", required=True, help="输出文件")
    parser.add_argument("--intensity", choices=["light", "medium", "heavy"], default="medium")
    args = parser.parse_args()
    
    text = Path(args.input).read_text(encoding="utf-8")
    result = humanize(text, args.intensity)
    Path(args.output).write_text(result, encoding="utf-8")
    print(f"去AI化完成：{args.output}（强度：{args.intensity}）")
