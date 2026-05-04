import re

with open('/tmp/moxa_mapping_extracted.js', 'r') as f:
    moxa_text = f.read()

with open('shl-jgyj-formulas-moxa.html', 'r') as f:
    content = f.read()

# 在 acupointMapping 的 }; 之后插入 moxaMapping
insert_pos = 65026  # after the semicolon
new_content = content[:insert_pos] + '\n\n' + moxa_text + '\n' + content[insert_pos:]

with open('shl-jgyj-formulas-moxa.html', 'w') as f:
    f.write(new_content)

print(f'Inserted moxaMapping at position {insert_pos}')
print(f'New file size: {len(new_content)}')

# Verify JS syntax
start = new_content.find('<script>')
end = new_content.find('</script>')
script = new_content[start+8:end]
import subprocess
result = subprocess.run(['node', '--check', '/dev/stdin'], input=script, capture_output=True, text=True)
print(f'JS Syntax: {"OK" if result.returncode==0 else "ERROR: " + result.stderr[:150]}')
