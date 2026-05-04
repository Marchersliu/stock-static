#!/usr/bin/env python3
with open('stock_dashboard.html', 'rb') as f:
    content = f.read()

# Find renderGlobal in binary
marker = b'function renderGlobal() {'
idx = content.find(marker)
if idx == -1:
    print('renderGlobal not found in binary!')
else:
    print(f'renderGlobal found at byte {idx}')
    # Show surrounding bytes
    start = max(0, idx - 50)
    end = min(len(content), idx + len(marker) + 50)
    snippet = content[start:end]
    print(f'Hex dump: {snippet.hex()}')
    print(f'As text: {snippet.decode("utf-8", errors="replace")}')

# Also check if there are any null bytes or BOM before script
script_idx = content.find(b'<script>')
print(f'\n<script> at byte {script_idx}')
pre_script = content[max(0, script_idx-10):script_idx+20]
print(f'Hex around <script>: {pre_script.hex()}')

# Check for null bytes in JS
script_end = content.find(b'</script>', script_idx)
js = content[script_idx:script_end]
null_count = js.count(b'\x00')
print(f'\nNull bytes in JS: {null_count}')

bom = content[:3]
print(f'File starts with: {bom.hex()} (EFBBBF=BOM)')
