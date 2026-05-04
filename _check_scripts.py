#!/usr/bin/env python3
with open('stock_dashboard.html', 'rb') as f:
    content = f.read()

# Find all script tags
text = content.decode('utf-8', errors='replace')
idx = 0
count = 0
scripts = []
while True:
    start = text.find('<script>', idx)
    if start == -1: break
    end = text.find('</script>', start)
    if end == -1: break
    js = text[start:end]
    scripts.append(js)
    print(f"Script #{count+1}: start={start}, end={end}, length={len(js)}")
    idx = end + 9
    count += 1

print(f"\nTotal scripts: {count}")
print(f"Total JS length: {sum(len(s) for s in scripts)}")
