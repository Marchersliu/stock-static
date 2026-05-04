#!/usr/bin/env python3
with open('stock_dashboard.html', 'r') as f:
    content = f.read()

start_marker = '// ===================== 盘前新闻候选抓取 ====================='
end_marker = 'function formatDateRange(dates) {'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

print(f'start_marker at index {start_idx}')
print(f'end_marker at index {end_idx}')
print(f'Replaced region length: {end_idx - start_idx}')

# Show what was replaced
if start_idx != -1 and end_idx != -1:
    replaced = content[start_idx:end_idx]
    print(f'\n=== First 200 chars of replaced region ===')
    print(replaced[:200])
    print(f'\n=== Last 200 chars of replaced region ===')
    print(replaced[-200:])
    
    # Check if renderGlobal or renderNews are in the replaced region
    if 'renderGlobal' in replaced:
        print('\n⚠️ renderGlobal is INSIDE the replaced region!')
    else:
        print('\n✅ renderGlobal is NOT in the replaced region')
    
    if 'renderNews' in replaced:
        print('⚠️ renderNews is INSIDE the replaced region!')
    else:
        print('✅ renderNews is NOT in the replaced region')
