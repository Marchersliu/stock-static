import re

for filename in ['shl-jgyj-formulas.html', 'shl-jgyj-formulas-moxa.html']:
    with open(filename, 'r') as f:
        content = f.read()
    
    # 找到 "// 初始化所有 select" 的位置
    marker = "// 初始化所有 select"
    idx = content.find(marker)
    if idx == -1:
        print(f'{filename}: marker NOT FOUND')
        continue
    
    # 在 marker 前插入 DOMContentLoaded 包裹
    before = content[:idx]
    after = content[idx:]
    
    # 找到 </script> 的位置，在它前面插入闭合
    script_end = after.rfind('</script>')
    if script_end == -1:
        print(f'{filename}: </script> NOT FOUND')
        continue
    
    # 构造新内容：marker前 + DOMContentLoaded开始 + 中间内容 + 闭合 + </script>
    new_content = before + "document.addEventListener('DOMContentLoaded', () => {\n  " + after[:script_end] + "\n});\n" + after[script_end:]
    
    with open(filename, 'w') as f:
        f.write(new_content)
    
    print(f'{filename}: FIXED, added DOMContentLoaded wrapper')

# 验证JS语法
print("\n--- JS Syntax Check ---")
for filename in ['shl-jgyj-formulas.html', 'shl-jgyj-formulas-moxa.html']:
    with open(filename, 'r') as f:
        content = f.read()
    start = content.find('<script>')
    end = content.find('</script>')
    script = content[start+8:end]
    import subprocess
    result = subprocess.run(['node', '--check', '/dev/stdin'], input=script, capture_output=True, text=True)
    ok = "OK" if result.returncode == 0 else "ERROR: " + result.stderr[:150]
    print(f'{filename}: {ok}')
