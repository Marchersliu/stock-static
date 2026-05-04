import json

# 修复艾灸版：删除symptomList后面的重复prescriptions数据，插入到prescriptions内部

with open('shl-jgyj-formulas-moxa.html', 'r', encoding='utf-8') as f:
    html = f.read()

script_start = html.find('<script>')
script_end = html.find('</script>')
html_before = html[:script_start + 8]
html_after = html[script_end:]
script = html[script_start + 8:script_end]

# 1. 提取 prescriptions 原始数据（不包含新增）
rx_start = script.find('const prescriptions = {')
rx_end = script.find('};', rx_start)
prescriptions_raw = script[rx_start:rx_end + 2]

# 2. 提取 symptomList（不包含后面的重复数据）
sym_start = script.find('const symptomList = [')
sym_end = script.find('];', sym_start)
symptomList_raw = script[sym_start:sym_end + 2]

# 3. 提取其他块
tx_start = script.find('const tianxing12 = {')
ton_start = script.find('const acupointTonification = {')
map_start = script.find('const acupointMapping = {')
let_start = script.find('let selectedSymptoms = []')

# 提取 tianxing12
tx_block = script[tx_start:ton_start]
# 提取 acupointTonification
ton_block = script[ton_start:map_start]
# 提取 acupointMapping
map_block = script[map_start:let_start]
# 提取全局
global_block = script[let_start:]

# 4. 读取 merge_data
with open('merge_data.json', 'r', encoding='utf-8') as f:
    merge_data = json.load(f)

# 5. 构建新增数据
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

new_map = []
for key, data in merge_data['new_acupoints'].items():
    pts = ', '.join([f'"{p}"' for p in data['points']])
    new_map.append(f'  "{key}": {{\n    effect: "{data["effect"]}",\n    points: [{pts}]\n  }}')

new_ton = []
for name, data in merge_data['new_tonifications'].items():
    new_ton.append(f'  "{name}": {{ type: "{data["type"]}", method: "{data["method"]}" }}')

# 6. 组装新增数据字符串
rx_insert = ',\n  // ========== 倪海厦30问新增方剂 ==========\n' + ',\n'.join(new_rx)
sym_insert = ',\n  // ========== 30问新增症状选项 ==========\n' + ',\n'.join(new_sym)
map_insert = ',\n  // ========== 30问新增针灸配穴 ==========\n' + ',\n'.join(new_map)
ton_insert = ',\n  // ========== 30问新增穴位补泻 ==========\n' + ',\n'.join(new_ton)

# 7. 正确插入
# prescriptions: 在 }; 前面插入
if prescriptions_raw.endswith('};'):
    prescriptions_final = prescriptions_raw[:-2].rstrip() + rx_insert + '\n};'
else:
    prescriptions_final = prescriptions_raw + rx_insert + '\n};'

# symptomList: 在 ]; 前面插入
if symptomList_raw.endswith('];'):
    symptomList_final = symptomList_raw[:-2].rstrip() + sym_insert + '\n];'
else:
    symptomList_final = symptomList_raw + sym_insert + '\n];'

# acupointMapping: 在末尾 } 前插入
if map_block.rstrip().endswith('}'):
    acupointMapping_final = map_block.rstrip() + map_insert + '\n};'
else:
    acupointMapping_final = map_block + map_insert + '\n};'

# acupointTonification: 在末尾 }; 前插入
if ton_block.rstrip().endswith('};'):
    acupointTonification_final = ton_block.rstrip()[:-2].rstrip() + ton_insert + '\n};'
else:
    acupointTonification_final = ton_block.rstrip() + ton_insert + '\n};'

# 8. 重新组装
new_script = (prescriptions_final + '\n\n' + 
              symptomList_final + '\n\n' + 
              tx_block + '\n' + 
              acupointTonification_final + '\n\n' + 
              acupointMapping_final + '\n\n' + 
              global_block)

new_html = html_before + new_script + html_after

with open('shl-jgyj-formulas-moxa.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f'Moxa file rebuilt: {len(new_html)} bytes')
print(f'prescriptions: {len(prescriptions_final)} chars')
print(f'symptomList: {len(symptomList_final)} chars')
print(f'tianxing12: {len(tx_block)} chars')
print(f'acupointTonification: {len(acupointTonification_final)} chars')
print(f'acupointMapping: {len(acupointMapping_final)} chars')
print(f'global: {len(global_block)} chars')
