import json
import re

# 完整修复脚本：清理混乱文件，提取原始数据，重新组装

with open('shl-jgyj-formulas.html', 'r', encoding='utf-8') as f:
    html = f.read()

script_start = html.find('<script>')
script_end = html.find('</script>')
html_before = html[:script_start + 8]
html_after = html[script_end:]
script_content = html[script_start + 8:script_end]

# ========== 1. 提取 prescriptions（原始，不包含新增） ==========
rx_start = script_content.find('const prescriptions = {')
rx_end = script_content.find('const symptomList = [')
prescriptions_raw = script_content[rx_start:rx_end].strip()

# 检查是否包含新增方剂
if '30问新增方剂' in prescriptions_raw:
    # 需要删除新增部分
    idx = prescriptions_raw.find('  // ========== 倪海厦30问新增方剂 ==========')
    prescriptions_raw = prescriptions_raw[:idx].rstrip()
    # 确保末尾没有逗号
    while prescriptions_raw.endswith(','):
        prescriptions_raw = prescriptions_raw[:-1].rstrip()
    # 确保末尾有 };
    if not prescriptions_raw.endswith('};'):
        if prescriptions_raw.endswith('}'):
            prescriptions_raw += ';'
        else:
            prescriptions_raw += '\n};'

# ========== 2. 提取 symptomList（原始，不包含新增） ==========
sym_start = script_content.find('const symptomList = [')
sym_end = script_content.find('const tianxing12 = {')
# 但symptomList后面可能有重复的tianxing12，找到第一个即可
symptomList_raw = script_content[sym_start:sym_end].strip()

if '30问新增症状' in symptomList_raw:
    idx = symptomList_raw.find('  // ========== 30问新增症状选项 ==========')
    symptomList_raw = symptomList_raw[:idx].rstrip()
    # 确保末尾没有逗号
    while symptomList_raw.endswith(','):
        symptomList_raw = symptomList_raw[:-1].rstrip()
    # 确保末尾有 ];
    if not symptomList_raw.endswith('];'):
        if symptomList_raw.endswith(']'):
            symptomList_raw += ';'
        else:
            symptomList_raw += '\n];'

# ========== 3. 提取 tianxing12（原始，不包含重复） ==========
tx_start = script_content.find('const tianxing12 = {')
# 找到第一个tianxing12的结束
tx_block = script_content[tx_start:]
# 跟踪大括号找到结束
i = tx_start + len('const tianxing12 = {')
depth = 1
while i < len(script_content) and depth > 0:
    if script_content[i] == '{':
        depth += 1
    elif script_content[i] == '}':
        depth -= 1
    elif script_content[i] in '"\'`':
        quote = script_content[i]
        i += 1
        while i < len(script_content) and script_content[i] != quote:
            if script_content[i] == '\\':
                i += 2
            else:
                i += 1
    i += 1
tianxing12_raw = script_content[tx_start:i].strip()

# ========== 4. 提取 acupointTonification（原始） ==========
ton_start = script_content.find('const acupointTonification = {')
# 找到结束（};）
ton_block = script_content[ton_start:]
# 找到第一个 };
ton_end = ton_block.find('};')
tianxing_after = ton_block.find('const tianxing12 = {', ton_end)
if tianxing_after != -1:
    # 说明后面有重复的tianxing12，这是acupointTonification的结束
    acupointTonification_raw = script_content[ton_start:ton_start+tianxing_after].strip()
else:
    # 找到第一个 }; 作为结束
    i = ton_start + len('const acupointTonification = {')
    depth = 1
    while i < len(script_content) and depth > 0:
        if script_content[i] == '{':
            depth += 1
        elif script_content[i] == '}':
            depth -= 1
        elif script_content[i] in '"\'`':
            quote = script_content[i]
            i += 1
            while i < len(script_content) and script_content[i] != quote:
                if script_content[i] == '\\':
                    i += 2
                else:
                    i += 1
        i += 1
    acupointTonification_raw = script_content[ton_start:i].strip()

if '30问新增穴位补泻' in acupointTonification_raw:
    idx = acupointTonification_raw.find('  // ========== 30问新增穴位补泻 ==========')
    acupointTonification_raw = acupointTonification_raw[:idx].rstrip()
    while acupointTonification_raw.endswith(','):
        acupointTonification_raw = acupointTonification_raw[:-1].rstrip()
    if not acupointTonification_raw.endswith('};'):
        if acupointTonification_raw.endswith('}'):
            acupointTonification_raw += ';'
        else:
            acupointTonification_raw += '\n};'

# ========== 5. 提取 acupointMapping ==========
map_start = script_content.find('const acupointMapping = {')
# 找到结束
i = map_start + len('const acupointMapping = {')
depth = 1
while i < len(script_content) and depth > 0:
    if script_content[i] == '{':
        depth += 1
    elif script_content[i] == '}':
        depth -= 1
    elif script_content[i] in '"\'`':
        quote = script_content[i]
        i += 1
        while i < len(script_content) and script_content[i] != quote:
            if script_content[i] == '\\':
                i += 2
            else:
                i += 1
    i += 1
acupointMapping_raw = script_content[map_start:i].strip()

if '30问新增针灸' in acupointMapping_raw:
    idx = acupointMapping_raw.find('  // ========== 30问新增针灸配穴 ==========')
    acupointMapping_raw = acupointMapping_raw[:idx].rstrip()
    while acupointMapping_raw.endswith(','):
        acupointMapping_raw = acupointMapping_raw[:-1].rstrip()
    if not acupointMapping_raw.endswith('};'):
        if acupointMapping_raw.endswith('}'):
            acupointMapping_raw += ';'
        else:
            acupointMapping_raw += '\n};'

# ========== 6. 提取全局状态+函数部分 ==========
# 从acupointMapping之后到script结束
global_start = i
global_raw = script_content[global_start:].strip()

# ========== 7. 读取merge_data ==========
with open('merge_data.json', 'r', encoding='utf-8') as f:
    merge_data = json.load(f)

# ========== 8. 构建新增数据字符串 ==========
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

rx_insert = ',\n  // ========== 倪海厦30问新增方剂 ==========\n' + ',\n'.join(new_rx)

new_sym = []
for item in merge_data['new_symptoms']:
    new_sym.append(f'  {{ label: "{item["label"]}", key: "{item["key"]}" }}')

sym_insert = ',\n  // ========== 30问新增症状选项 ==========\n' + ',\n'.join(new_sym)

new_map = []
for key, data in merge_data['new_acupoints'].items():
    pts = ', '.join([f'"{p}"' for p in data['points']])
    new_map.append(f'  "{key}": {{\n    effect: "{data["effect"]}",\n    points: [{pts}]\n  }}')

map_insert = ',\n  // ========== 30问新增针灸配穴 ==========\n' + ',\n'.join(new_map)

new_ton = []
for name, data in merge_data['new_tonifications'].items():
    new_ton.append(f'  "{name}": {{ type: "{data["type"]}", method: "{data["method"]}" }}')

ton_insert = ',\n  // ========== 30问新增穴位补泻 ==========\n' + ',\n'.join(new_ton)

# ========== 9. 重新组装 ==========
# prescriptions: 在末尾 } 前加逗号和新方剂
if prescriptions_raw.endswith('};'):
    prescriptions_final = prescriptions_raw[:-2].rstrip() + rx_insert + '\n};'
elif prescriptions_raw.endswith('}'):
    prescriptions_final = prescriptions_raw + rx_insert + '\n};'
else:
    prescriptions_final = prescriptions_raw + rx_insert + '\n};'

# symptomList: 在 ] 前加逗号和新症状
if symptomList_raw.endswith('];'):
    symptomList_final = symptomList_raw[:-2].rstrip() + sym_insert + '\n];'
elif symptomList_raw.endswith(']'):
    symptomList_final = symptomList_raw + sym_insert + '\n];'
else:
    symptomList_final = symptomList_raw + sym_insert + '\n];'

# acupointMapping: 在末尾 } 前加逗号和新针灸
if acupointMapping_raw.endswith('};'):
    acupointMapping_final = acupointMapping_raw[:-2].rstrip() + map_insert + '\n};'
elif acupointMapping_raw.endswith('}'):
    acupointMapping_final = acupointMapping_raw + map_insert + '\n};'
else:
    acupointMapping_final = acupointMapping_raw + map_insert + '\n};'

# acupointTonification: 在末尾 } 前加逗号和新穴位
if acupointTonification_raw.endswith('};'):
    acupointTonification_final = acupointTonification_raw[:-2].rstrip() + ton_insert + '\n};'
elif acupointTonification_raw.endswith('}'):
    acupointTonification_final = acupointTonification_raw + ton_insert + '\n};'
else:
    acupointTonification_final = acupointTonification_raw + ton_insert + '\n};'

# tianxing12 保持不变
tianxing12_final = tianxing12_raw

# 组装完整脚本
new_script = prescriptions_final + '\n\n' + symptomList_final + '\n\n' + tianxing12_final + '\n\n' + acupointTonification_final + '\n\n' + acupointMapping_final + '\n\n' + global_raw

# 组装完整HTML
new_html = html_before + new_script + html_after

with open('shl-jgyj-formulas.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f'File rebuilt: {len(new_html)} bytes')
print(f'prescriptions: {len(prescriptions_final)} chars')
print(f'symptomList: {len(symptomList_final)} chars')
print(f'tianxing12: {len(tianxing12_final)} chars')
print(f'acupointTonification: {len(acupointTonification_final)} chars')
print(f'acupointMapping: {len(acupointMapping_final)} chars')
print(f'global: {len(global_raw)} chars')
