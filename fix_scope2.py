import re

def fix_file(filename):
    with open(filename, 'r') as f:
        content = f.read()
    
    # 找到 DOMContentLoaded 起始
    start_marker = "document.addEventListener('DOMContentLoaded', () => {\n  // 初始化所有 select\n"
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print(f'{filename}: DOMContentLoaded not found')
        return
    
    # 找到 DOMContentLoaded 的结束（从后往前找 "});\n</script>"）
    end_marker = "});\n</script>"
    end_idx = content.rfind(end_marker)
    if end_idx == -1:
        print(f'{filename}: end marker not found')
        return
    
    # 提取内部内容
    inner_start = start_idx + len(start_marker)
    inner = content[inner_start:end_idx]
    
    # 找到 "// 添加症状" 的位置，从这里开始是函数定义
    func_split = inner.find("// 添加症状")
    if func_split == -1:
        print(f'{filename}: "// 添加症状" not found')
        return
    
    # 找到 "// 初始化所有 select" 之前的代码（initCustomSelect 调用 + symptomList 填充）
    init_code = inner[:func_split]
    func_code = inner[func_split:]
    
    # 构造新内容：
    # 1. 原来 DOMContentLoaded 之前的所有内容
    before = content[:start_idx]
    # 2. 函数定义（放在全局）
    # 3. 精简的 DOMContentLoaded（只包含初始化代码）
    # 4. </script> 之后的内容
    after = content[end_idx + len(end_marker):]
    
    new_inner = init_code + "});\n\n" + func_code
    
    new_content = before + start_marker + new_inner + after
    
    with open(filename, 'w') as f:
        f.write(new_content)
    
    print(f'{filename}: FIXED')
    
    # Verify
    start = new_content.find('<script>')
    end = new_content.find('</script>')
    script = new_content[start+8:end]
    import subprocess
    result = subprocess.run(['node', '--check', '/dev/stdin'], input=script, capture_output=True, text=True)
    ok = "OK" if result.returncode == 0 else "ERROR: " + result.stderr[:150]
    print(f'  JS Syntax: {ok}')

fix_file('shl-jgyj-formulas.html')
fix_file('shl-jgyj-formulas-moxa.html')
