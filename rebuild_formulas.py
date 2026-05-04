# 由于文件已被多次修改导致结构混乱，使用Python重建整个文件
# 策略：读取当前文件，提取所有数据，重新组装成正确的结构

import re

with open('shl-jgyj-formulas.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 提取HTML部分（<script>之前和</script>之后）
script_start = html.find('<script>')
script_end = html.find('</script>')

html_before = html[:script_start + 8]  # 包含 <script>
html_after = html[script_end:]  # 包含 </script>
script_content = html[script_start + 8:script_end]

# 提取 prescriptions 对象（从开头到 symptomList 之前）
# 找到 symptomList 的定义位置
symptomList_pos = script_content.find('const symptomList = [')
prescriptions_block = script_content[:symptomList_pos]

# 提取 symptomList
acupointMapping_pos = script_content.find('const acupointMapping = {')
symptomList_block = script_content[symptomList_pos:acupointMapping_pos]

# 提取 acupointMapping
tianxing_pos = script_content.find('const tianxing12 = {')
acupointMapping_block = script_content[acupointMapping_pos:tianxing_pos]

# 提取天星十二穴
acupointTonification_pos = script_content.find('const acupointTonification = {')
tianxing_block = script_content[tianxing_pos:acupointTonification_pos]

# 提取穴位补泻
acupointMapping2_pos = script_content.find('// ========== 病症 → 针灸配穴映射', acupointTonification_pos)
# 等等，acupointMapping 已经提取过了
# 从 acupointTonification 到脚本结束
acupointTonification_block = script_content[acupointTonification_pos:]

# 清理 prescriptions_block：删除已插入的新增方剂（它们在 symptomList 后面）
# 找到 prescriptions 对象的结束（}后面跟着 const symptomList）
# 实际上，prescriptions_block 已经只包含到 symptomList 之前的内容

# 现在读取 merge_data.json
import json
with open('merge_data.json', 'r', encoding='utf-8') as f:
    merge_data = json.load(f)

# 构建新增方剂字符串
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

# 找到 prescriptions_block 中最后一个 } 后面跟着 \n\nconst symptomList 的位置
# 在 prescriptions_block 末尾添加逗号和新方剂
if prescriptions_block.rstrip().endswith('}'):
    prescriptions_block = prescriptions_block.rstrip() + rx_insert + '\n\n'

# 构建新增 symptomList
new_sym = []
for item in merge_data['new_symptoms']:
    new_sym.append(f'  {{ label: "{item["label"]}", key: "{item["key"]}" }}')

# 找到 symptomList_block 中 ]; 的位置，替换为 , 新条目 ];
if '];' in symptomList_block:
    sym_end = symptomList_block.rfind('];')
    sym_insert = ',\n  // ========== 30问新增症状选项 ==========\n' + ',\n'.join(new_sym)
    symptomList_block = symptomList_block[:sym_end] + sym_insert + '\n];' + symptomList_block[sym_end+2:]

# 构建新增 acupointMapping
new_map = []
for key, data in merge_data['new_acupoints'].items():
    pts = ', '.join([f'"{p}"' for p in data['points']])
    new_map.append(f'  "{key}": {{\n    effect: "{data["effect"]}",\n    points: [{pts}]\n  }}')

# 找到 acupointMapping_block 中最后一个 }; 或 } 后面跟着 // 的位置
# 实际上 acupointMapping_block 以 }; 结束吗？不，它以 acupointMapping 对象结束，后面跟着 tianxing
# 找到 acupointMapping 的最后一个条目后面
if acupointMapping_block.rstrip().endswith('}'):
    map_insert = ',\n  // ========== 30问新增针灸配穴 ==========\n' + ',\n'.join(new_map)
    acupointMapping_block = acupointMapping_block.rstrip() + map_insert + '\n\n'

# 构建新增 acupointTonification
new_ton = []
for name, data in merge_data['new_tonifications'].items():
    new_ton.append(f'  "{name}": {{ type: "{data["type"]}", method: "{data["method"]}" }}')

# 找到 acupointTonification_block 中最后一个 }; 之前的位置
if '};' in acupointTonification_block:
    ton_end = acupointTonification_block.rfind('};')
    ton_insert = ',\n  // ========== 30问新增穴位补泻 ==========\n' + ',\n'.join(new_ton)
    acupointTonification_block = acupointTonification_block[:ton_end] + ton_insert + '\n' + acupointTonification_block[ton_end:]

# 重新组装
new_script = prescriptions_block + symptomList_block + acupointMapping_block + tianxing_block + acupointTonification_block

# 组装完整HTML
new_html = html_before + new_script + html_after

with open('shl-jgyj-formulas.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print('Rebuilt shl-jgyj-formulas.html')
print(f'New file size: {len(new_html)} bytes')
