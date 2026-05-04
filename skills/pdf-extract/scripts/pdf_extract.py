#!/usr/bin/env python3
"""
PDF内容提取 - 提取文本、表格、图片，支持研报模式

用法:
    python3 pdf_extract.py report.pdf --output report.md
    python3 pdf_extract.py report.pdf --tables --output tables.json
    python3 pdf_extract.py --batch "*.pdf" --output-dir ./extracted/
"""
import argparse
import json
import os
import re
from glob import glob


def extract_text_pypdf2(pdf_path):
    """使用PyPDF2提取文本"""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n\n"
        return text
    except ImportError:
        return "[ERR] PyPDF2 not installed. Run: pip3 install PyPDF2"
    except Exception as e:
        return f"[ERR] {e}"


def extract_text_pdfplumber(pdf_path):
    """使用pdfplumber提取文本（更准确）"""
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        return text
    except ImportError:
        return extract_text_pypdf2(pdf_path)
    except Exception as e:
        return f"[ERR] {e}"


def extract_tables(pdf_path):
    """提取表格"""
    try:
        import pdfplumber
        tables = []
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_tables = page.extract_tables()
                for table in page_tables:
                    tables.append({
                        'page': i + 1,
                        'data': table
                    })
        return tables
    except ImportError:
        return []
    except Exception as e:
        return [{'error': str(e)}]


def get_metadata(pdf_path):
    """获取PDF元数据"""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        meta = reader.metadata or {}
        return {
            'pages': len(reader.pages),
            'author': meta.get('/Author', 'Unknown'),
            'title': meta.get('/Title', 'Unknown'),
            'subject': meta.get('/Subject', ''),
            'creator': meta.get('/Creator', ''),
        }
    except:
        return {'pages': 0, 'error': 'Cannot read metadata'}


def research_mode(text, metadata):
    """研报模式：自动识别关键数据"""
    # 提取数字模式
    patterns = {
        'revenue': r'(?:营收|营业收入|Revenue)[^\d]*(\d+(?:\.\d+)?)\s*(?:亿|万|亿元|万美元|百万美元)',
        'net_profit': r'(?:净利润|归母净利润|Net Profit)[^\d]*(\d+(?:\.\d+)?)\s*(?:亿|万|亿元)',
        'gross_margin': r'(?:毛利率|Gross Margin)[^\d]*(\d+(?:\.\d+)?)\s*%',
        'pe': r'(?:市盈率|P/E)[^\d]*(\d+(?:\.\d+)?)',
        'pb': r'(?:市净率|P/B)[^\d]*(\d+(?:\.\d+)?)',
        'roe': r'(?:ROE|净资产收益率)[^\d]*(\d+(?:\.\d+)?)\s*%',
    }
    
    extracted = {}
    for key, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            extracted[key] = matches[:3]  # 取前3个
    
    return extracted


def format_as_markdown(text, metadata, tables, research_data=None):
    """格式化为Markdown"""
    md = f"""# {metadata.get('title', 'Extracted Document')}

## 元数据
- **页数**: {metadata.get('pages', 'Unknown')}
- **作者**: {metadata.get('author', 'Unknown')}
- **创建工具**: {metadata.get('creator', 'Unknown')}

"""
    
    if research_data:
        md += """## 关键数据提取

| 指标 | 数值 | 备注 |
|------|------|------|
"""
        for key, values in research_data.items():
            md += f"| {key} | {', '.join(values[:2])} | 自动提取 |\n"
        md += "\n"
    
    if tables:
        md += f"## 表格 ({len(tables)}个)\n\n"
        for i, table in enumerate(tables[:3], 1):  # 只显示前3个
            if 'error' in table:
                continue
            md += f"### 表格 {i} (第{table['page']}页)\n\n"
            md += "| " + " | ".join(str(c) for c in table['data'][0]) + " |\n"
            md += "| " + " | ".join("---" for _ in table['data'][0]) + " |\n"
            for row in table['data'][1:5]:  # 只显示前5行
                md += "| " + " | ".join(str(c) if c else "" for c in row) + " |\n"
            md += "\n"
    
    md += """## 正文

"""
    md += text[:50000]  # 限制长度
    
    return md


def main():
    parser = argparse.ArgumentParser(description='PDF Extract')
    parser.add_argument('pdf', nargs='?', help='PDF file path')
    parser.add_argument('--output', '-o', help='Output file')
    parser.add_argument('--tables', action='store_true', help='Extract tables')
    parser.add_argument('--mode', choices=['standard', 'research'], default='standard', help='Extraction mode')
    parser.add_argument('--batch', help='Batch pattern (e.g., "*.pdf")')
    parser.add_argument('--output-dir', help='Output directory for batch mode')
    
    args = parser.parse_args()
    
    # 批量模式
    if args.batch:
        files = glob(args.batch)
        output_dir = args.output_dir or './extracted'
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"[Batch] {len(files)} files found")
        for pdf_path in files:
            basename = os.path.splitext(os.path.basename(pdf_path))[0]
            output = os.path.join(output_dir, f"{basename}.md")
            
            print(f"  Processing: {pdf_path} → {output}")
            text = extract_text_pdfplumber(pdf_path)
            meta = get_metadata(pdf_path)
            
            with open(output, 'w', encoding='utf-8') as f:
                f.write(format_as_markdown(text, meta, []))
        
        print(f"[OK] All files saved to {output_dir}/")
        return
    
    # 单文件模式
    if not args.pdf:
        print("[ERR] Provide PDF file or --batch")
        return
    
    pdf_path = args.pdf
    print(f"[PDF] Extracting: {pdf_path}")
    
    # 提取
    text = extract_text_pdfplumber(pdf_path)
    meta = get_metadata(pdf_path)
    
    print(f"[PDF] Pages: {meta.get('pages', 'Unknown')}")
    print(f"[PDF] Text: {len(text)} chars")
    
    # 表格
    tables = []
    if args.tables:
        tables = extract_tables(pdf_path)
        print(f"[PDF] Tables: {len(tables)}")
    
    # 研报模式
    research_data = None
    if args.mode == 'research':
        research_data = research_mode(text, meta)
        print(f"[PDF] Research data: {list(research_data.keys())}")
    
    # 格式化
    md = format_as_markdown(text, meta, tables, research_data)
    
    # 输出
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f"[OK] Saved: {args.output}")
    else:
        print()
        print(md[:3000])
        if len(md) > 3000:
            print(f"\n... ({len(md)} chars total, use --output to save full text)")


if __name__ == '__main__':
    main()
