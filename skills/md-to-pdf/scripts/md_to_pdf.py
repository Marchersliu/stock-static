#!/usr/bin/env python3
"""Markdown转PDF"""
import sys, argparse, subprocess
from pathlib import Path

DEFAULT_CSS = """
@page { size: A4; margin: 2cm; }
body {
  font-family: 'PingFang SC', 'Microsoft YaHei', 'Noto Sans CJK SC', sans-serif;
  font-size: 11pt; line-height: 1.7; color: #1f2937;
}
h1 { font-size: 20pt; color: #1e3a5f; border-bottom: 2px solid #1e3a5f; padding-bottom: 8px; }
h2 { font-size: 15pt; color: #334155; margin-top: 24px; }
h3 { font-size: 13pt; color: #475569; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; }
th, td { border: 1px solid #cbd5e1; padding: 6px 10px; text-align: left; }
th { background: #f1f5f9; font-weight: 600; }
code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 10pt; }
pre { background: #f8fafc; padding: 12px; border-radius: 6px; overflow-x: auto; }
blockquote { border-left: 4px solid #94a3b8; padding-left: 12px; color: #64748b; margin: 0; }
"""

def md_to_pdf(md_path, output_path, css_path=None):
    try:
        import markdown
        from weasyprint import HTML, CSS
    except ImportError:
        print("请先安装依赖：pip install markdown weasyprint")
        sys.exit(1)
    
    md_text = Path(md_path).read_text(encoding="utf-8")
    html_body = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])
    
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>{DEFAULT_CSS}</style>
</head><body>{html_body}</body></html>"""
    
    if css_path and Path(css_path).exists():
        css = CSS(filename=css_path)
    else:
        css = CSS(string=DEFAULT_CSS)
    
    HTML(string=html).write_pdf(output_path, stylesheets=[css])
    print(f"PDF已生成：{output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Markdown文件路径")
    parser.add_argument("--output", required=True, help="PDF输出路径")
    parser.add_argument("--css", help="自定义CSS文件路径")
    args = parser.parse_args()
    md_to_pdf(args.input, args.output, args.css)
