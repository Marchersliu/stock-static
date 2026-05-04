#!/usr/bin/env python3
with open('stock_dashboard.html', 'r') as f:
    content = f.read()
start = content.find('<script>')
end = content.find('</script>', start)
js = content[start:end]

import re
# Check for </script> inside string literals
for pattern in [r'"[^"]*</script>[^"]*"', r"'[^']*</script>[^']*'", r'`[^`]*</script>[^`]*`']:
    matches = re.findall(pattern, js)
    for m in matches:
        print(f"Found </script> in string: {m[:80]}...")

# Count </script> occurrences in script section
pos = 0
count = 0
while True:
    pos = js.find('</script>', pos)
    if pos == -1: break
    count += 1
    print(f"  </script> at offset {pos}")
    pos += 9
print(f"Total </script> occurrences in script section: {count}")
