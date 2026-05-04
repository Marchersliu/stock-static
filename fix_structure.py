#!/usr/bin/env python3
"""
修复 stock_dashboard.html 结构损坏
问题：产业链透视表格被分裂为两部分，计划建仓卡片被嵌套进 tbody
"""

with open('/Users/hf/.kimi_openclaw/workspace/stock_dashboard.html', 'r') as f:
    lines = f.readlines()

# ====== 分析当前损坏结构 ======
# Area 1: line 300-348 (0-indexed 299-347) - "幽灵"产业链卡片尾部
#   303: <td><strong>招商银行</strong></td> - 缺失 <tr> 开头
#   ...
#   344: </tbody>
#   345: </table>
#   346: </div>
#   347: <p class="source-note">...</p>
#   348: </div>
#   349: (empty)
#   350: <!-- 九州一轨重点仓位 -->

# Area 2: line 604-713 (0-indexed 603-712) - "损坏"产业链卡片头部
#   604: <div class="card">
#   605: <div class="card-title">🏭 ...
#   606: <p>...
#   607: <div class="overflow-x">
#   608: <table>
#   609: <thead>...
#   610: </tr></thead>
#   611: (empty)
#   612: <tbody>
#   613-622: 九州一轨 row
#   623-632: 红星发展 row
#   633-642: 禾望电气 row
#   643-652: ST晨鸣 row
#   653-662: 鑫磊股份 row
#   663-672: 宝丰能源 row
#   673-682: 华友钴业 row
#   683-692: 科伦药业 row
#   693: <tr>  (dangling!)
#   694: <!-- 计划建仓标的 -->
#   695: <div class="card">
#   696: <div class="card-title">📅 计划建仓标的</div>
#   ...
#   713: </div>  (closes plan target card AND supply chain card)

# ====== 修复策略 ======
# 1. 提取正确的前8行 + 表头 + 卡片开头 (lines 604-692)
# 2. 从"幽灵"卡片中提取后4行 + 关闭标签 (lines 303-342)
# 3. 从嵌套区域提取完整的计划建仓卡片 (lines 694-713)
# 4. 组合成正确结构

# --- Extract supply chain card header (correct part, lines 604-692, 0-indexed 603-691) ---
sc_header = lines[603:692]  # lines 604-692 inclusive

# --- Extract the 4 rows from "ghost" card (lines 303-342, 0-indexed 302-341) ---
# Line 303 (0-indexed 302) is "          <td><strong>招商银行</strong></td>"
# This row is MISSING its <tr> opening tag
# The row content spans: 303-311 (0-indexed 302-310)
# Line 312 (0-indexed 311) is "        </tr>"
zhangshang_content = lines[302:311]  # 303-311 inclusive, missing <tr>
zhangshang_close = lines[311]        # line 312: </tr>

# 中国核电: 313-321 (0-indexed 312-320)
zhonghe_open = lines[312]            # line 313: <tr>
zhonghe_content = lines[313:321]       # 314-321
zhonghe_close = lines[321]           # line 322: </tr>

# 中国铝业: 323-331 (0-indexed 322-330)
zhonglv_open = lines[322]            # line 323: <tr>
zhonglv_content = lines[323:331]       # 324-331
zhonglv_close = lines[331]           # line 332: </tr>

# 长江电力: 333-341 (0-indexed 332-340)
changjiang_open = lines[332]         # line 333: <tr>
changjiang_content = lines[333:341]  # 334-341
changjiang_close = lines[341]        # line 342: </tr>

# --- Extract closing tags from ghost card (lines 343-348, 0-indexed 342-347) ---
sc_closing = lines[342:348]  # </tbody>, </table>, </div>, <p>, </div>

# --- Extract plan target card from nested area (lines 694-713, 0-indexed 693-712) ---
plan_card = lines[693:713]  # lines 694-713 inclusive

# ====== Build the new file ======
new_lines = []

# Part 1: Everything BEFORE the ghost card (lines 1-302, 0-indexed 0-301)
new_lines.extend(lines[:302])

# Part 2: Supply chain card (corrected)
#   - Header with first 8 rows (from area 2)
new_lines.extend(sc_header)
#   - 招商银行 row (add missing <tr>)
new_lines.append('        <tr>\n')
new_lines.extend(zhangshang_content)
new_lines.append(zhangshang_close)
#   - 中国核电 row
new_lines.append(zhonghe_open)
new_lines.extend(zhonghe_content)
new_lines.append(zhonghe_close)
#   - 中国铝业 row
new_lines.append(zhonglv_open)
new_lines.extend(zhonglv_content)
new_lines.append(zhonglv_close)
#   - 长江电力 row
new_lines.append(changjiang_open)
new_lines.extend(changjiang_content)
new_lines.append(changjiang_close)
#   - Closing tags
new_lines.extend(sc_closing)

# Part 3: Empty line + 九州一轨 comment
new_lines.append('\n')
new_lines.append('<!-- 九州一轨重点仓位 -->\n')

# Part 4: Everything between ghost card end and supply chain card start
# Lines 350-603 (0-indexed 349-602)
# This includes the 九州一轨重点仓位 card and other content
new_lines.extend(lines[349:603])

# Part 5: Plan target card (as independent card, NOT nested)
new_lines.append('\n')
new_lines.append('<!-- 计划建仓标的 -->\n')
new_lines.extend(plan_card)

# Part 6: Everything after the supply chain card end (line 714 onwards)
# Lines 714 to end (0-indexed 713 onwards)
new_lines.extend(lines[713:])

with open('/Users/hf/.kimi_openclaw/workspace/stock_dashboard.html', 'w') as f:
    f.writelines(new_lines)

# Verify
print("=== Fix applied ===")
print(f"Removed ghost supply chain card (lines 303-348)")
print(f"Rebuilt supply chain card with all 12 rows")
print(f"Plan target card is now independent (not nested)")

# Quick balance check
with open('/Users/hf/.kimi_openclaw/workspace/stock_dashboard.html', 'r') as f:
    content = f.read()
    div_opens = content.count('<div')
    div_closes = content.count('</div>')
    print(f"\nDiv balance: opens={div_opens}, closes={div_closes}, diff={div_opens - div_closes}")
    
    tbody_opens = content.count('<tbody')
    tbody_closes = content.count('</tbody>')
    print(f"Tbody balance: opens={tbody_opens}, closes={tbody_closes}, diff={tbody_opens - tbody_closes}")
    
    table_opens = content.count('<table')
    table_closes = content.count('</table>')
    print(f"Table balance: opens={table_opens}, closes={table_closes}, diff={table_opens - table_closes}")
