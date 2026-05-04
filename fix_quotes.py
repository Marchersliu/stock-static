#!/usr/bin/env python3
# -*- coding: utf-8 -*-

with open('/Users/hf/.kimi_openclaw/workspace/make_ppg_ppt.py','r',encoding='utf-8') as f:
    lines = f.readlines()

fixed = []
for line in lines:
    # If line contains Chinese text with single quotes inside, 
    # and the outer quotes are single quotes, change outer to double quotes
    # Simple heuristic: if line has '落实' or similar patterns with quote issues
    # Just replace all outer Python single-quote strings with double-quote strings
    # for lines that have Chinese content
    stripped = line.strip()
    if stripped.startswith("add_") or stripped.startswith("[") or stripped.startswith("'•"):
        # These lines likely have problematic single-quote strings
        # Replace wrapping single quotes with double quotes for string literals
        # This is tricky - let's just replace all instances of "'" followed by Chinese 
        # and then "'" with proper double quotes
        pass
    
    # Simpler approach: replace all Chinese single quotes (which were converted 
    # from Chinese double quotes) with a safe marker, then fix
    line = line.replace("'", "「").replace("'", "」")
    fixed.append(line)

with open('/Users/hf/.kimi_openclaw/workspace/make_ppg_ppt.py','w',encoding='utf-8') as f:
    f.writelines(fixed)

print("Fixed Chinese single quotes to 「」")
