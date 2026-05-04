#!/usr/bin/env python3
"""文案编辑脚本 - 改文案比重写轻"""
import sys, re, argparse
from pathlib import Path

# 常见修正规则
FIXES = [
    # 语法修正
    (r"([\u4e00-\u9fa5])的([\u4e00-\u9fa5]{2,})了", r"\1\2了", "的地得修正"),
    (r"([\u4e00-\u9fa5])地([\u4e00-\u9fa5]{2,})", r"\1的\2", "的地得修正"),
    (r"进行了(.{2,10})(研究|分析|讨论|修改)", r"\1\2", "去冗余：进行了"),
    (r"实施了(.{2,10})(方案|计划|操作)", r"\1\2", "去冗余：实施了"),
    (r"呈现出(.{2,10})(趋势|状态|结果)", r"\1\2", "去冗余：呈现出"),
    (r"非常(.{1,5})(重要|关键|必要|好)", r"很\1\2", "去冗余：非常"),
    (r"特别(.{1,5})(重要|关键|突出)", r"\1\2", "去冗余：特别"),
    (r"以及(.{2,10})和", r"和\1", "重复连接词"),
    (r"，，", "，", "双逗号"),
    (r"。。", "。", "双句号"),
]

STYLE_FIXES = [
    # 风格优化
    (r"客户", "用户", "术语统一：用户"),  # 只在需要时启用
    (r"([\u4e00-\u9fa5]{100,}。)", r"\1\n\n", "长句分段（100字+）"),
]

def edit_copy(text, focus="all"):
    applied = []
    
    if focus in ("all", "grammar"):
        for pattern, repl, desc in FIXES:
            new_text, count = re.subn(pattern, repl, text)
            if count > 0:
                text = new_text
                applied.append(f"{desc}：{count}处")
    
    if focus in ("all", "style"):
        for pattern, repl, desc in STYLE_FIXES:
            new_text, count = re.subn(pattern, repl, text)
            if count > 0:
                text = new_text
                applied.append(f"{desc}：{count}处")
    
    return text, applied

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="输入文件")
    parser.add_argument("--output", required=True, help="输出文件")
    parser.add_argument("--focus", choices=["grammar", "style", "structure", "all"], default="all")
    args = parser.parse_args()
    
    text = Path(args.input).read_text(encoding="utf-8")
    result, applied = edit_copy(text, args.focus)
    Path(args.output).write_text(result, encoding="utf-8")
    
    print(f"编辑完成：{args.output}")
    print(f"应用修正：{len(applied)}项")
    for a in applied:
        print(f"  - {a}")
