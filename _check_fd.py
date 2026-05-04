#!/usr/bin/env python3
with open('stock_dashboard.html', 'r') as f:
    content = f.read()

# Find the region around formatDateRange
marker = 'function formatDateRange'
idx = content.find(marker)
if idx == -1:
    print('NOT FOUND')
else:
    # Show 200 chars before and 100 after
    start = max(0, idx - 200)
    end = min(len(content), idx + 100)
    snippet = content[start:end]
    print('=== Context around formatDateRange ===')
    print(snippet)
    
    # Count how many times the marker appears
    count = content.count(marker)
    print(f'\nMarker appears {count} times')
    
    # Check if there's an unmatched brace before the closing </script>
    script_start = content.find('<script>')
    script_end = content.find('</script>', script_start)
    js = content[script_start:script_end]
    
    # Simple brace balance
    open_b = js.count('{')
    close_b = js.count('}')
    print(f'Braces: {open_b} open / {close_b} close = {open_b - close_b}')
