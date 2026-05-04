import json
import re

# 最终修复脚本：正确处理prescriptions对象的插入

with open('shl-jgyj-formulas.html', 'r', encoding='utf-8') as f:
    html = f.read()

script_start = html.find('<script>')
script_end = html.find('</script>')
html_before = html[:script_start + 8]
html_after = html[script_end:]
script_content = html[script_start + 8:script_end]

# ========== 1. 提取干净的 prescriptions ==========
# 找到 const prescriptions = { 到 const symptomList = [ 之间的内容
rx_start = script_content.find('const prescriptions = {')
rx_end = script_content.find('const symptomList = [')

# 提取并清理
def clean_block(block, marker_name, end_str='};'):
    """删除新增数据，确保以正确的结束符结尾"""
    # 删除新增部分
    idx = block.find(f'  // ========== {marker_name} ==========')
    if idx != -1:
        block = block[:idx].rstrip()
    
    # 删除尾部多余的逗号
    while block.endswith(','):
        block = block[:-1].rstrip()
    
    # 确保以正确的结束符结尾
    if not block.endswith(end_str):
        # 找到最后一个 } 或 ]
        if end_str == '};':
            # 找到 }; 的位置
            last_semi = block.rfind('};')
            if last_semi != -1:
                block = block[:last_semi+2]
            else:
                # 手动添加
                block = block.rstrip() + '\n};'
        elif end_str == '];':
            last_bracket = block.rfind('];')
            if last_bracket != -1:
                block = block[:last_bracket+2]
            else:
                block = block.rstrip() + '\n];'
    
    return block

prescriptions_raw = clean_block(script_content[rx_start:rx_end], '倪海厦30问新增方剂', '};')
symptomList_raw = clean_block(script_content[rx_end:script_content.find('const tianxing12 = {')], '30问新增症状选项', '];')

# ========== 2. 读取 merge_data ==========
with open('merge_data.json', 'r', encoding='utf-8') as f:
    merge_data = json.load(f)

# ========== 3. 构建新增数据 ==========
new_rx = []
for name, data in merge_data['new_formulas'].items():
    ing_str = ',\n      '.join([
        f'{{ name: "{ing["name"]}", unit: "{ing["unit"]}", base: {ing["base"]} }}'
        for ing in data['ingredients']
    ])
    block = f'''  "{data['key']}": {{
    source: "{data['source']}", category: "{data['category']}",
    name: "{name}",
    symptoms: "{data['symptoms']}",
    ingredients: [
      {ing_str}
    ],
    decoction: "{data['decoction']}",
    note: "{data['note']}",
    complexity: {data['complexity']}
  }}'''
    new_rx.append(block)

new_sym = []
for item in merge_data['new_symptoms']:
    new_sym.append(f'  {{ label: "{item["label"]}", key: "{item["key"]}" }}')

# ========== 4. 正确插入到 prescriptions ==========
# 找到 prescriptions_raw 中最后一个 "};" 之前的 "}"
# 即在最后一个方块的 } 和 prescriptions 的 }; 之间插入
# 更简单的方法：找到 "};" 的位置，在 "}" 后面插入逗号+新方剂
last_semi = prescriptions_raw.rfind('};')
if last_semi != -1:
    # 在 "};" 的 "}" 后面（也就是 prescriptions_raw[:last_semi] 的末尾）插入
    before_semi = prescriptions_raw[:last_semi]
    # 确保 before_semi 以 } 结束（最后一个方块的结束）
    if before_semi.rstrip().endswith('}'):
        # 在最后一个 } 后面加逗号
        before_semi = before_semi.rstrip() + ','
        # 插入新方剂
        rx_insert = '\n  // ========== 倪海厦30问新增方剂 ==========\n' + ',\n'.join(new_rx)
        prescriptions_final = before_semi + rx_insert + '\n};'
    else:
        prescriptions_final = prescriptions_raw  # fallback
else:
    prescriptions_final = prescriptions_raw

# ========== 5. 正确插入到 symptomList ==========
last_bracket = symptomList_raw.rfind('];')
if last_bracket != -1:
    before_bracket = symptomList_raw[:last_bracket]
    if before_bracket.rstrip().endswith('}'):
        before_bracket = before_bracket.rstrip() + ','
        sym_insert = '\n  // ========== 30问新增症状选项 ==========\n' + ',\n'.join(new_sym)
        symptomList_final = before_bracket + sym_insert + '\n];'
    else:
        symptomList_final = symptomList_raw
else:
    symptomList_final = symptomList_raw

# ========== 6. 提取其他块（原始） ==========
# tianxing12
tx_start = script_content.find('const tianxing12 = {')
# 找到第一个tianxing12的结束（通过跟踪大括号）
tx_block = script_content[tx_start:]
depth = 1
i = len('const tianxing12 = {')
while i < len(tx_block) and depth > 0:
    if tx_block[i] == '{':
        depth += 1
    elif tx_block[i] == '}':
        depth -= 1
    elif tx_block[i] in '"\'`':
        quote = tx_block[i]
        i += 1
        while i < len(tx_block) and tx_block[i] != quote:
            if tx_block[i] == '\\':
                i += 2
            else:
                i += 1
    i += 1
tianxing12_raw = tx_block[:i]

# acupointTonification
ton_start = script_content.find('const acupointTonification = {', tx_start + i)
# 找到结束（后面有重复的tianxing12的话）
tianxing_after = script_content.find('const tianxing12 = {', ton_start)
if tianxing_after != -1:
    acupointTonification_raw = script_content[ton_start:tianxing_after]
else:
    # 找到第一个 };
    ton_block = script_content[ton_start:]
    depth = 1
    i = len('const acupointTonification = {')
    while i < len(ton_block) and depth > 0:
        if ton_block[i] == '{':
            depth += 1
        elif ton_block[i] == '}':
            depth -= 1
        elif ton_block[i] in '"\'`':
            quote = ton_block[i]
            i += 1
            while i < len(ton_block) and ton_block[i] != quote:
                if ton_block[i] == '\\':
                    i += 2
                else:
                    i += 1
        i += 1
    acupointTonification_raw = ton_block[:i]

# acupointMapping
map_start = script_content.find('const acupointMapping = {', ton_start)
map_block = script_content[map_start:]
depth = 1
i = len('const acupointMapping = {')
while i < len(map_block) and depth > 0:
    if map_block[i] == '{':
        depth += 1
    elif map_block[i] == '}':
        depth -= 1
    elif map_block[i] in '"\'`':
        quote = map_block[i]
        i += 1
        while i < len(map_block) and map_block[i] != quote:
            if map_block[i] == '\\':
                i += 2
            else:
                i += 1
    i += 1
acupointMapping_raw = map_block[:i]

# 全局状态+函数
global_start = map_start + i
global_raw = script_content[global_start:]

# ========== 7. 重新组装 ==========
new_script = (prescriptions_final + '\n\n' + 
              symptomList_final + '\n\n' + 
              tianxing12_raw + '\n\n' + 
              acupointTonification_raw + '\n\n' + 
              acupointMapping_raw + '\n\n' + 
              global_raw)

new_html = html_before + new_script + html_after

with open('shl-jgyj-formulas.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f'File rebuilt: {len(new_html)} bytes')
print(f'prescriptions: {len(prescriptions_final)} chars')
print(f'symptomList: {len(symptomList_final)} chars')
