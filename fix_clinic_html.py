import re

with open('shl-jgyj-formulas.html', 'r') as f:
    content = f.read()

# 找到 </html> 的位置
html_end = content.find('</html>')
if html_end != -1:
    # 检查 </html> 后面是否还有内容
    after_html = content[html_end+7:].strip()
    print(f"</html> found at position {html_end}")
    print(f"Content after </html> (first 200 chars): {repr(after_html[:200])}")
    print(f"Total length after </html>: {len(after_html)}")
    
    # 截断到 </html> 后面加换行
    if after_html:
        new_content = content[:html_end+7] + '\n'
        with open('shl-jgyj-formulas.html', 'w') as f:
            f.write(new_content)
        print(f"Truncated to {len(new_content)} bytes")
    else:
        print("Already clean, no content after </html>")
else:
    print("</html> not found!")
