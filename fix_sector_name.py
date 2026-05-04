import re

with open('stock_service.py', 'r') as f:
    content = f.read()

# Find and replace the stock_details.append block
old = """            if mn:
                total_net += mn
                stock_details.append({
                    'name': s.get('name', code),
                    'code': code.split('.')[0],
                    'main_net': mn,
                })"""

new = """            if mn:
                total_net += mn
                stock_name = STOCK_KEYWORDS.get(code, {}).get('name', code)
                stock_details.append({
                    'name': stock_name,
                    'code': code.split('.')[0],
                    'main_net': mn,
                })"""

if old in content:
    content = content.replace(old, new, 1)
    with open('stock_service.py', 'w') as f:
        f.write(content)
    print('Fixed stock name lookup')
else:
    print('Old text not found')
    # Try to find similar text
    idx = content.find("stock_details.append")
    if idx != -1:
        print('Found at', idx)
        print(repr(content[idx-50:idx+200]))
