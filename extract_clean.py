import json
import re

# 清理混乱的文件，提取唯一数据，重建正确结构

with open('shl-jgyj-formulas.html', 'r', encoding='utf-8') as f:
    html = f.read()

script_start = html.find('<script>')
script_end = html.find('</script>')
html_before = html[:script_start + 8]
html_after = html[script_end:]
script_content = html[script_start + 8:script_end]

# 提取HTML中的const定义（可能有重复的）
def extract_const(name, content):
    """提取所有匹配name的const定义，返回第一个完整匹配的"""
    pattern = f'const {name} = '
    positions = []
    start = 0
    while True:
        pos = content.find(pattern, start)
        if pos == -1:
            break
        positions.append(pos)
        start = pos + 1
    
    print(f'Found {len(positions)} occurrences of "const {name}"')
    
    if not positions:
        return None
    
    # 返回第一个完整匹配
    pos = positions[0]
    # 找到匹配的结束括号
    # 从pos + len(pattern)开始，跟踪大括号/中括号层级
    i = pos + len(pattern)
    if content[i] == '{':
        bracket = '}'
    elif content[i] == '[':
        bracket = ']'
    else:
        return None
    
    depth = 1
    i += 1
    while i < len(content) and depth > 0:
        if content[i] == content[pos + len(pattern)]:
            depth += 1
        elif content[i] == bracket:
            depth -= 1
        elif content[i] == '"' or content[i] == "'" or content[i] == '`':
            # 跳过字符串
            quote = content[i]
            i += 1
            while i < len(content) and content[i] != quote:
                if content[i] == '\\':
                    i += 2
                else:
                    i += 1
        i += 1
    
    return content[pos:i]

# 提取 prescriptions
rx_block = extract_const('prescriptions', script_content)
sym_block = extract_const('symptomList', script_content)
tianxing_block = extract_const('tianxing12', script_content)
ton_block = extract_const('acupointTonification', script_content)
map_block = extract_const('acupointMapping', script_content)

print(f'\nExtracted blocks:')
print(f'prescriptions: {len(rx_block) if rx_block else 0} chars')
print(f'symptomList: {len(sym_block) if sym_block else 0} chars')
print(f'tianxing12: {len(tianxing_block) if tianxing_block else 0} chars')
print(f'acupointTonification: {len(ton_block) if ton_block else 0} chars')
print(f'acupointMapping: {len(map_block) if map_block else 0} chars')

# 检查是否有新增数据混在里面
if rx_block and '30问新增方剂' in rx_block:
    print('WARNING: prescriptions already contains 30问新增方剂')
if sym_block and '30问新增症状' in sym_block:
    print('WARNING: symptomList already contains 30问新增症状')
if map_block and '30问新增针灸' in map_block:
    print('WARNING: acupointMapping already contains 30问新增针灸')
if ton_block and '30问新增穴位补泻' in ton_block:
    print('WARNING: acupointTonification already contains 30问新增穴位补泻')

# 如果有，需要清理掉重复/新增部分
# 由于提取的是第一个完整匹配，应该不包含重复

# 保存提取的原始数据
original_data = {
    'prescriptions': rx_block,
    'symptomList': sym_block,
    'tianxing12': tianxing_block,
    'acupointTonification': ton_block,
    'acupointMapping': map_block
}

with open('original_data.json', 'w', encoding='utf-8') as f:
    json.dump({k: v[:100] if v else None for k, v in original_data.items()}, f)

print('\nSaved extraction preview to original_data.json')
