#!/usr/bin/env python3
"""主题应用脚本 - 一键替换HTML/CSS配色"""
import sys, json, argparse, re
from pathlib import Path

THEMES = {
    "finance":   {"primary": "#1e3a5f", "accent": "#f59e0b", "bg": "#0f172a", "text": "#e2e8f0", "border": "#334155", "up": "#ef4444", "down": "#22c55e"},
    "tech":      {"primary": "#6366f1", "accent": "#22d3ee", "bg": "#0f172a", "text": "#e2e8f0", "border": "#334155", "up": "#f87171", "down": "#4ade80"},
    "medical":   {"primary": "#059669", "accent": "#34d399", "bg": "#f0fdf4", "text": "#1f2937", "border": "#d1d5db", "up": "#dc2626", "down": "#16a34a"},
    "minimal":   {"primary": "#18181b", "accent": "#3f3f46", "bg": "#ffffff", "text": "#18181b", "border": "#e4e4e7", "up": "#dc2626", "down": "#16a34a"},
}

def apply_theme(html_path, theme_name, output_path):
    if theme_name not in THEMES:
        print(f"可用主题：{', '.join(THEMES.keys())}")
        sys.exit(1)
    
    t = THEMES[theme_name]
    html = Path(html_path).read_text(encoding="utf-8")
    
    # 替换CSS变量
    css_vars = f""":root {{
  --primary: {t['primary']};
  --accent: {t['accent']};
  --bg: {t['bg']};
  --text: {t['text']};
  --border: {t['border']};
  --up: {t['up']};
  --down: {t['down']};
}}"""
    
    # 插入或替换 :root 定义
    if ':root' in html:
        html = re.sub(r':root\s*\{[^}]*\}', css_vars.strip(), html)
    else:
        # 在第一个 <style> 标签内插入
        html = html.replace('<style>', f'<style>\n{css_vars}\n', 1)
    
    Path(output_path).write_text(html, encoding="utf-8")
    print(f"主题 '{theme_name}' 已应用到：{output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="HTML文件路径")
    parser.add_argument("--theme", required=True, help="主题名称")
    parser.add_argument("--output", required=True, help="输出路径")
    args = parser.parse_args()
    apply_theme(args.input, args.theme, args.output)
