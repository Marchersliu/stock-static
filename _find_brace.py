#!/usr/bin/env python3
# Find unbalanced brace in JS
with open('stock_dashboard.html', 'r') as f:
    content = f.read()

# Find script content
start = content.find('<script')
end = content.find('</script>', start)
js = content[start:end]

# Track brace balance with line numbers
lines = js.split('\n')
balance = 0
line_no = 0
for line in lines:
    line_no += 1
    # Skip comments and strings (simplified)
    in_string = False
    string_char = None
    in_comment = False
    i = 0
    while i < len(line):
        c = line[i]
        next_c = line[i+1] if i+1 < len(line) else ''
        
        if in_comment:
            if c == '*' and next_c == '/':
                in_comment = False
                i += 2
                continue
            i += 1
            continue
        
        if in_string:
            if c == '\\':
                i += 2
                continue
            if c == string_char:
                in_string = False
                string_char = None
            i += 1
            continue
        
        if c == '/' and next_c == '/':
            break  # rest of line is comment
        if c == '/' and next_c == '*':
            in_comment = True
            i += 2
            continue
        
        if c in "'\"`":
            in_string = True
            string_char = c
            i += 1
            continue
        
        if c == '{':
            balance += 1
            if balance > 0 and balance < 5:
                print(f"  + {{ at line {line_no} (balance={balance}): {line[:80]}")
        elif c == '}':
            balance -= 1
            if balance >= 0 and balance < 5:
                print(f"  - }} at line {line_no} (balance={balance}): {line[:80]}")
        
        i += 1

print(f"\nFinal balance: {balance}")
if balance != 0:
    print("UNBALANCED!")
    # Find the last unmatched opening brace
    # Re-scan and print lines where balance never returns to 0
    balance = 0
    max_balance = 0
    max_line = 0
    line_no = 0
    for line in lines:
        line_no += 1
        for c in line:
            if c == '{':
                balance += 1
                if balance > max_balance:
                    max_balance = balance
                    max_line = line_no
            elif c == '}':
                balance -= 1
    print(f"Max balance reached: {max_balance} at around line {max_line}")
