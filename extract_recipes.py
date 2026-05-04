import re
import json

with open('豆包30问_raw.txt', 'r') as f:
    text = f.read()

# 提取每个方剂区块
# 模式："**对应经方：XXX**" 开始，到下一个 "**对应经方" 或 "**第N问" 或 "2.N" 章节标题结束

recipes = {}
current_name = None
current_data = {}

lines = text.split('\n')
i = 0
while i < len(lines):
    line = lines[i].strip()
    
    # 检测方剂名
    m = re.match(r'\*\*对应经方：(.+?)\*\*$', line)
    if m:
        if current_name and current_data:
            recipes[current_name] = current_data
        current_name = m.group(1).strip()
        current_data = {'name': current_name}
        i += 1
        continue
    
    # 如果没有当前方剂，跳过
    if not current_name:
        i += 1
        continue
    
    # 检测组成
    if line.startswith('组成：'):
        comp = line[3:].strip()
        # 解析组成：药材名+剂量
        ingredients = []
        parts = comp.split('、')
        for p in parts:
            p = p.strip()
            # 匹配：药材名+数字+单位
            m2 = re.match(r'(.+?)(\d+(?:\.\d+)?)\s*(克|枚|g|ml|个|碗|升|寸匕)', p)
            if m2:
                name = m2.group(1).strip()
                base = float(m2.group(2))
                unit = m2.group(3)
                if unit == '克':
                    unit = 'g'
                ingredients.append({'name': name, 'base': base, 'unit': unit})
            else:
                # 可能有"各等分"、"各X克"等
                m3 = re.match(r'(.+?)(各\d+)', p)
                if m3:
                    pass  # 复杂情况先跳过
        current_data['ingredients'] = ingredients
        i += 1
        continue
    
    if line.startswith('功效：'):
        current_data['effect'] = line[3:].strip()
    elif line.startswith('主治：'):
        current_data['indication'] = line[3:].strip()
    elif line.startswith('煎服方法：') or line.startswith('煎服：'):
        current_data['decoction'] = line[line.find('：')+1:].strip()
    elif line.startswith('方解：'):
        current_data['explanation'] = line[3:].strip()
    elif line.startswith('注意事项：'):
        current_data['note'] = line[5:].strip()
    
    # 检测新章节或新问，结束当前方剂
    if re.match(r'\*\*第\d+问', line) or re.match(r'2\.\d+\s+第', line) or re.match(r'\*\*对应经方', line):
        if current_name and current_data and len(current_data) > 1:
            recipes[current_name] = current_data
        current_name = None
        current_data = {}
        continue
    
    i += 1

# 保存最后一个
if current_name and current_data and len(current_data) > 1:
    recipes[current_name] = current_data

# 去重和清洗
final = {}
for name, data in recipes.items():
    name = name.strip()
    if name in ['', '小柴胡汤（同第10问）', '麻黄汤（同第4问）']:
        continue
    final[name] = data

print(f'Extracted {len(final)} unique recipes')
for name in sorted(final.keys()):
    data = final[name]
    ings = len(data.get('ingredients', []))
    has_decoction = 'decoction' in data
    has_note = 'note' in data
    print(f'{name}: {ings}味药材, 煎服:{has_decoction}, 注意:{has_note}')

# 保存
with open('extracted_recipes.json', 'w', encoding='utf-8') as f:
    json.dump(final, f, ensure_ascii=False, indent=2)
print('Saved to extracted_recipes.json')
