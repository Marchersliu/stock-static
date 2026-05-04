from docx import Document
import sys
import os

def extract_docx_content(docx_path, output_path):
    """读取docx文档，提取所有段落和表格内容，保留原始格式和结构"""
    doc = Document(docx_path)
    
    lines = []
    
    # 处理文档中的所有元素（段落和表格交替）
    # docx库的Document对象有一个element.body，我们可以遍历其中的所有子元素
    from docx.oxml.ns import qn
    
    body = doc.element.body
    
    for child in body:
        tag = child.tag
        
        # 段落
        if tag == qn('w:p'):
            p = child
            # 获取段落中的所有文本
            texts = []
            for run in p.findall(qn('w:r')):
                t_elem = run.find(qn('w:t'))
                if t_elem is not None and t_elem.text:
                    texts.append(t_elem.text)
            
            paragraph_text = ''.join(texts).strip()
            if paragraph_text:
                # 根据样式判断是否为标题
                pPr = p.find(qn('w:pPr'))
                style = ''
                if pPr is not None:
                    pStyle = pPr.find(qn('w:pStyle'))
                    if pStyle is not None:
                        style = pStyle.get(qn('w:val'), '')
                
                # 简单的缩进检测
                indent = ''
                if pPr is not None:
                    ind = pPr.find(qn('w:ind'))
                    if ind is not None:
                        left = ind.get(qn('w:left'), '')
                        if left:
                            indent = '    '  # 缩进用4个空格
                
                # 粗体检测（所有runs都粗体的话标记）
                all_bold = True
                any_bold = False
                for run in p.findall(qn('w:r')):
                    rPr = run.find(qn('w:rPr'))
                    if rPr is not None:
                        b = rPr.find(qn('w:b'))
                        if b is not None:
                            any_bold = True
                        else:
                            all_bold = False
                    else:
                        all_bold = False
                
                if all_bold and any_bold:
                    paragraph_text = f"**{paragraph_text}**"
                
                lines.append(indent + paragraph_text)
            else:
                # 空段落也保留一个空行
                lines.append('')
                
        # 表格
        elif tag == qn('w:tbl'):
            tbl = child
            # 构建表格
            table_data = []
            max_cols = 0
            
            for tr in tbl.findall(qn('w:tr')):
                row = []
                for tc in tr.findall(qn('w:tc')):
                    # 单元格中的所有文本
                    cell_texts = []
                    for p in tc.findall(qn('w:p')):
                        p_texts = []
                        for run in p.findall(qn('w:r')):
                            t_elem = run.find(qn('w:t'))
                            if t_elem is not None and t_elem.text:
                                p_texts.append(t_elem.text)
                        p_text = ''.join(p_texts)
                        cell_texts.append(p_text)
                    cell_text = ' | '.join(cell_texts)  # 单元格内多段落用 | 连接
                    row.append(cell_text)
                
                if row:
                    max_cols = max(max_cols, len(row))
                    table_data.append(row)
            
            if table_data:
                # 输出表格
                lines.append('')  # 表格前空行
                # 用制表符分隔输出表格内容
                for row in table_data:
                    # 补齐缺失的列
                    while len(row) < max_cols:
                        row.append('')
                    lines.append('\t'.join(row))
                lines.append('')  # 表格后空行
    
    # 写入输出文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"已保存: {output_path} ({len(lines)} 行)")

# 主程序
if __name__ == '__main__':
    files = [
        (
            '/Users/hf/.openclaw/workspace/downloads/19defe05-1442-8cfd-8000-0000b4f3ef20_千问倪海厦问诊30问.docx',
            '/Users/hf/.kimi_openclaw/workspace/千问30问_raw.txt'
        ),
        (
            '/Users/hf/.openclaw/workspace/downloads/19defe05-18a2-8418-8000-0000e1495277_基于倪海厦的六经辨证体系和临床实践经验_我整理了这份_倪海厦中医问诊断症对照表_30问精准版_包含详细的问诊问题_辨证结果_对应经方_完整配方组成_煎服方法以及方解使.docx',
            '/Users/hf/.kimi_openclaw/workspace/豆包30问_raw.txt'
        )
    ]
    
    for src, dst in files:
        if not os.path.exists(src):
            print(f"文件不存在: {src}")
            sys.exit(1)
        
        extract_docx_content(src, dst)
