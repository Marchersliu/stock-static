# 修复当前已损坏的文件的语法错误
import re

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 修复1: symptomList区域多余的逗号
    # 查找: ];
    #   
    #   ,
    #   // ========== 倪海厦30问新增方剂 ==========
    bad_pattern = '];\n\n  ,\n  // ========== 倪海厦30问新增方剂 =========='
    good_pattern = '];\n\n  // ========== 倪海厦30问新增方剂 =========='
    html = html.replace(bad_pattern, good_pattern)
    
    # 修复2: 确保prescriptions和天星十二穴之间没有多余的逗号
    # 如果 prescriptions 最后以 },\n\n// ========== 开头，说明没问题
    # 如果 prescriptions 最后以 }\n\n// ========== 开头（无逗号），需要修复
    rx_end = html.find('  }\n\n// ========== 天星十二穴数据库 ==========')
    if rx_end != -1:
        # 这个没问题，因为最后一个 } 后面是空行+注释
        pass
    
    # 修复3: 检查 prescriptions 新插入的方剂ingredients缩进
    # 查找 pattern: ingredients: [\n    { name:...  (缩进4个空格而不是6个)
    # 这会导致语法正确但格式不对，不影响运行
    
    # 修复4: 检查是否有重复的 // ========== 30问新增症状选项 ==========
    # 可能有多次运行留下的重复
    count = html.count('// ========== 30问新增症状选项 ==========')
    if count > 1:
        print(f'Warning: found {count} symptomList insert markers')
    
    count2 = html.count('// ========== 倪海厦30问新增方剂 ==========')
    if count2 > 1:
        print(f'Warning: found {count2} prescriptions insert markers')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Fixed {filepath}')

fix_file('shl-jgyj-formulas.html')
fix_file('shl-jgyj-formulas-moxa.html')
print('Done')
