import re

def fix_file(filename):
    with open(filename, 'r') as f:
        content = f.read()
    
    # 找到 DOMContentLoaded 的起始位置
    start_marker = "document.addEventListener('DOMContentLoaded', () => {\n  // 初始化所有 select"
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print(f'{filename}: DOMContentLoaded not found, skipping')
        return
    
    # 找到 DOMContentLoaded 的结束位置（最后的 }); 在 </script> 之前）
    # 从文件末尾往前找 "});\n</script>"
    end_marker = "});\n</script>"
    end_idx = content.rfind(end_marker)
    if end_idx == -1:
        print(f'{filename}: DOMContentLoaded end not found')
        return
    
    # 提取 DOMContentLoaded 内部的内容
    inner_start = start_idx + len("document.addEventListener('DOMContentLoaded', () => {\n  // 初始化所有 select\n")
    inner_content = content[inner_start:end_idx]
    
    # 找出函数定义的位置（以 function 或 const xxx = 开头的）
    # 我们要把函数定义移到外面
    lines = inner_content.split('\n')
    
    init_lines = []  # DOM 初始化代码（留在 DOMContentLoaded 里）
    func_lines = []  # 函数定义（移到外面）
    
    in_function = False
    func_depth = 0
    func_buffer = []
    
    for line in lines:
        stripped = line.strip()
        
        # 检测函数定义开始
        if not in_function and (
            stripped.startswith('function ') or 
            (stripped.startswith('const ') and ' = ' in stripped and ('function' in stripped or '=>' in stripped)) or
            stripped.startswith('let selectedSymptoms') or
            stripped.startswith('const MAX_SYMPTOMS') or
            stripped.startswith('const symptomSelect') or
            stripped.startswith('const patientSelect') or
            stripped.startswith('const emptyState') or
            stripped.startswith('const resultArea')
        ):
            in_function = True
            func_depth = 0
            func_buffer = [line]
            # 计算当前行的括号深度
            func_depth += line.count('{') - line.count('}')
            if func_depth <= 0 and (';' in line or stripped.startswith('let ') or stripped.startswith('const ')):
                # 单行变量声明，直接输出
                func_lines.append(line)
                in_function = False
                func_buffer = []
            continue
        
        if in_function:
            func_buffer.append(line)
            func_depth += line.count('{') - line.count('}')
            if func_depth <= 0:
                # 函数/对象结束
                func_lines.extend(func_buffer)
                in_function = False
                func_buffer = []
            continue
        
        # 普通行，留在 init_lines
        init_lines.append(line)
    
    # 如果还有未闭合的函数，也输出
    if func_buffer:
        func_lines.extend(func_buffer)
    
    # 构造新内容
    # 1. DOMContentLoaded 之前的内容（到 start_idx）
    before = content[:start_idx]
    
    # 2. 函数定义（移到 DOMContentLoaded 前面）
    func_text = '\n'.join(func_lines)
    
    # 3. DOMContentLoaded 内部（只保留初始化代码）
    init_text = '\n'.join(init_lines)
    
    # 4. DOMContentLoaded 之后的内容
    after = content[end_idx + len(end_marker):]
    
    # 组装：before + func_text + DOMContentLoaded(init_text) + after
    new_content = before + func_text + "\n\ndocument.addEventListener('DOMContentLoaded', () => {\n" + init_text + "\n});\n" + after
    
    with open(filename, 'w') as f:
        f.write(new_content)
    
    print(f'{filename}: FIXED')
    print(f'  Functions moved out: {len(func_lines)} lines')
    print(f'  Init code kept: {len(init_lines)} lines')
    
    # Verify JS
    start = new_content.find('<script>')
    end = new_content.find('</script>')
    script = new_content[start+8:end]
    import subprocess
    result = subprocess.run(['node', '--check', '/dev/stdin'], input=script, capture_output=True, text=True)
    ok = "OK" if result.returncode == 0 else "ERROR: " + result.stderr[:150]
    print(f'  JS Syntax: {ok}')

fix_file('shl-jgyj-formulas.html')
fix_file('shl-jgyj-formulas-moxa.html')
