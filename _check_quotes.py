#!/usr/bin/env python3
with open('stock_dashboard.html', 'r') as f:
    content = f.read()

start = content.find('<script>')
end = content.find('</script>', start)
js = content[start:end]

# Count quotes considering escape sequences
single_open = False
double_open = False
backtick_open = False
line_no = 1
last_quote_line = 0
last_quote_char = ''

for i, c in enumerate(js):
    if c == '\n':
        line_no += 1
    
    # Check for escape - previous char is backslash but not itself escaped
    if i > 0 and js[i-1] == '\\' and (i < 2 or js[i-2] != '\\'):
        continue
    
    if c == '`' and not single_open and not double_open:
        backtick_open = not backtick_open
        if backtick_open:
            last_quote_line = line_no
            last_quote_char = '`'
    elif c == "'" and not double_open and not backtick_open:
        single_open = not single_open
        if single_open:
            last_quote_line = line_no
            last_quote_char = "'"
    elif c == '"' and not single_open and not backtick_open:
        double_open = not double_open
        if double_open:
            last_quote_line = line_no
            last_quote_char = '"'

print(f"Single quotes open at end: {single_open}")
print(f"Double quotes open at end: {double_open}")
print(f"Backticks open at end: {backtick_open}")
if single_open or double_open or backtick_open:
    print(f"Last unclosed quote opened at line ~{last_quote_line} (char: {last_quote_char})")
    # Show context
    lines = js.split('\n')
    if last_quote_line <= len(lines):
        print(f"Context: {lines[last_quote_line-1][:100]}")
