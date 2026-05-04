import json

def merge_into_html(filepath, output_path, merge_data, is_moxa=False):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 1. 插入新增方剂到 prescriptions 对象末尾
    # 找到 prescriptions 的结束位置（最后一个 } 后面跟 // ========== 天星十二穴）
    rx_insert_marker = "\n\n// ========== 天星十二穴数据库 =========="
    rx_insert_pos = html.find(rx_insert_marker)
    
    if rx_insert_pos != -1:
        # 在 marker 之前插入，确保前面有逗号
        # 先找到 marker 前面的非空白字符
        before = html[:rx_insert_pos].rstrip()
        # 确保最后一个字符是 }，然后加逗号
        if before.endswith('}'):
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
            html = before + rx_insert + '\n' + html[rx_insert_pos:]
    
    # 2. 插入新增 symptomList 条目
    # 找到 symptomList 的结束 ]; 
    sym_end_marker = '{ label: "咽中如有炙脔，咽喉异物感，胸闷嗳气（金匮要略·半夏厚朴汤）", key: "梅核气" }\n];'
    sym_end_pos = html.find(sym_end_marker)
    if sym_end_pos != -1:
        sym_end_pos = sym_end_pos + len(sym_end_marker) - 2  # 指向 ]; 的 ]
        new_sym = []
        for item in merge_data['new_symptoms']:
            new_sym.append(f'  {{ label: "{item["label"]}", key: "{item["key"]}" }}')
        sym_insert = ',\n  // ========== 30问新增症状选项 ==========\n' + ',\n'.join(new_sym)
        html = html[:sym_end_pos] + sym_insert + '\n];' + html[sym_end_pos+2:]
    
    # 3. 插入新增 acupointMapping 条目
    # 找到 acupointMapping 的最后一个条目
    map_end_marker = '"梅核气": {\n    effect: "行气散结、降逆化痰（倪海厦：天突+膻中利咽）",\n    points: ["天突", "膻中", "丰隆", "内关", "太冲", "廉泉"]\n  }'
    map_end_pos = html.find(map_end_marker)
    if map_end_pos != -1:
        map_end_pos = map_end_pos + len(map_end_marker)
        new_map = []
        for key, data in merge_data['new_acupoints'].items():
            pts = ', '.join([f'"{p}"' for p in data['points']])
            new_map.append(f'  "{key}": {{\n    effect: "{data["effect"]}",\n    points: [{pts}]\n  }}')
        map_insert = ',\n  // ========== 30问新增针灸配穴 ==========\n' + ',\n'.join(new_map)
        html = html[:map_end_pos] + map_insert + '\n' + html[map_end_pos:]
    
    # 4. 插入新增 acupointTonification 条目
    ton_end_marker = '"风市": { type: "泻", method: "拇指向后捻转，轻插重提，以祛风通络" }'
    ton_end_pos = html.find(ton_end_marker)
    if ton_end_pos != -1:
        ton_end_pos = ton_end_pos + len(ton_end_marker)
        new_ton = []
        for name, data in merge_data['new_tonifications'].items():
            new_ton.append(f'  "{name}": {{ type: "{data["type"]}", method: "{data["method"]}" }}')
        ton_insert = ',\n  // ========== 30问新增穴位补泻 ==========\n' + ',\n'.join(new_ton)
        html = html[:ton_end_pos] + ton_insert + '\n' + html[ton_end_pos:]
    
    # 保存
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f'Saved to {output_path}')
    return True

# 读取 merge 数据
with open('merge_data.json', 'r', encoding='utf-8') as f:
    merge_data = json.load(f)

# 处理原版
merge_into_html('shl-jgyj-formulas.html', 'shl-jgyj-formulas.html', merge_data, is_moxa=False)

# 处理艾灸版  
merge_into_html('shl-jgyj-formulas-moxa.html', 'shl-jgyj-formulas-moxa.html', merge_data, is_moxa=True)

print('Done!')
