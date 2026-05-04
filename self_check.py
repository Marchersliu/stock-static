#!/usr/bin/env python3
"""
stock_dashboard.html 自我检查脚本
每次修改后运行，确保排版/数据/格式正确
用法: python3 self_check.py
"""
import re, sys
from pathlib import Path

def find_commodity_boxes(html):
    """提取所有完整的commodity-box卡片内容"""
    start_marker = '<div class="commodity-box'
    boxes = []
    idx = 0
    while True:
        start = html.find(start_marker, idx)
        if start == -1:
            break
        # Find matching </div>
        depth = 1
        pos = html.find('>', start) + 1
        while depth > 0 and pos < len(html):
            next_open = html.find('<div', pos)
            next_close = html.find('</div>', pos)
            if next_close == -1:
                break
            if next_open != -1 and next_open < next_close:
                depth += 1
                pos = next_open + 4
            else:
                depth -= 1
                pos = next_close + 6
        if depth == 0:
            # Extract inner content (excluding outer <div class="commodity-box..."> and final </div>)
            inner_start = html.find('>', start) + 1
            inner_end = pos - 6
            boxes.append({
                'outer_start': start,
                'outer_end': pos,
                'inner': html[inner_start:inner_end]
            })
        idx = pos
    return boxes

def check():
    path = Path(__file__).parent / "stock_dashboard.html"
    if not path.exists():
        print("ERROR: stock_dashboard.html not found")
        return 1
    html = path.read_text()
    errors = []
    warnings = []

    # 1. HTML标签平衡
    open_tr = html.count('<tr>')
    close_tr = html.count('</tr>')
    open_td = html.count('<td')
    close_td = html.count('</td>')
    if open_tr != close_tr:
        errors.append(f"TR mismatch: open={open_tr} close={close_tr}")
    if open_td != close_td:
        errors.append(f"TD mismatch: open={open_td} close={close_td}")

    # 2. 计划建仓表列数匹配
    wl_start = html.find('<!-- 计划建仓标的 -->')
    wl_end = html.find('<!-- 财务透视表 -->')
    if wl_start > 0 and wl_end > 0:
        wl = html[wl_start:wl_end]
        header = wl[wl.find('<thead>'):wl.find('</thead>')]
        ths = [t.split('</th>')[0] for t in header.split('<th>')[1:]]
        first_row = wl[wl.find('<tbody'):wl.find('</tr>', wl.find('<tbody'))]
        td_count = first_row.count('<td>') + first_row.count('<td class=')
        if len(ths) != td_count:
            errors.append(f"Watchlist columns: header={len(ths)}({ths}) vs data={td_count}")

    # 3. 日期格式检查
    render_global = html[html.find('function renderGlobal()'):html.find('renderGlobal();')]
    if 'substring(5)' in render_global and 'parseInt' not in render_global:
        errors.append("renderGlobal uses old date format substring(5)")

    # 4. 重复行检查
    watch_lym = wl.count('洛阳钼业') if wl_start > 0 else 0
    chain_start = html.find('产业链成本透视')
    chain_end = html.find('⭐ 重点关注')
    chain_lym = html[chain_start:chain_end].count('洛阳钼业') if chain_start > 0 else 0
    if watch_lym > 1:
        errors.append(f"Watchlist has {watch_lym} 洛阳钼业 entries (should be 1)")
    if chain_lym > 1:
        errors.append(f"Chain table has {chain_lym} 洛阳钼业 entries (should be 1)")

    # 5. 原材料卡片结构检查
    comm_start = html.find('原材料价格监控')
    comm_end = html.find('<!-- 财务透视表 -->')
    if comm_start > 0 and comm_end > 0:
        cs = html[comm_start:comm_end]
        boxes = find_commodity_boxes(cs)
        for box in boxes:
            inner = box['inner']
            name_match = re.search(r'<div class="name">(.*?)</div>', inner)
            name = name_match.group(1) if name_match else 'unknown'
            has_price = 'class="price"' in inner
            has_change = 'class="change' in inner
            has_note = 'class="note"' in inner
            if not all([has_price, has_change, has_note]):
                errors.append(f"Commodity '{name}' missing: price={has_price} change={has_change} note={has_note}")
            # Check inner div balance (excluding outer commodity-box)
            div_open = inner.count('<div')
            div_close = inner.count('</div>')
            if div_open != div_close:
                errors.append(f"Commodity '{name}' inner div mismatch: open={div_open} close={div_close}")

    # 6. 错别字检查
    if '原油短纤' in html:
        errors.append("Typo: 原油短纤 -> should be 原油短线")

    # 7. 全局市场数据
    m = re.search(r'const GLOBAL_MARKETS = \{([^}]+)\}', html, re.DOTALL)
    if m:
        dates = re.findall(r'tradeDate: "(\d{4}-\d{2}-\d{2})"', m.group(1))
        from collections import Counter
        date_counts = Counter(dates)
        print(f"  Market dates: {dict(date_counts)}")
        japan_note = re.search(r'日经225.*note: "([^"]+)"', html)
        if japan_note and '休市' not in japan_note.group(1):
            warnings.append("日经225 missing holiday note")

    # Report
    print(f"=== Self-Check Results ===")
    print(f"  TR: {open_tr}/{close_tr} {'OK' if open_tr==close_tr else 'FAIL'}")
    print(f"  TD: {open_td}/{close_td} {'OK' if open_td==close_td else 'FAIL'}")
    print(f"  Watchlist columns: {len(ths) if 'ths' in dir() else 'N/A'}")
    print(f"  洛阳钼业 watchlist: {watch_lym}, chain: {chain_lym}")
    print(f"  Date format: {'parseInt OK' if 'parseInt(d.tradeDate' in html else 'OLD FORMAT'}")
    print(f"  Commodity boxes: {len(boxes) if 'boxes' in dir() else 'N/A'}")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")

    if errors:
        print("\n❌ ERRORS:")
        for e in errors:
            print(f"  - {e}")
    if warnings:
        print("\n⚠️ WARNINGS:")
        for w in warnings:
            print(f"  - {w}")

    if not errors and not warnings:
        print("\n✅ All checks passed!")
        return 0
    elif not errors:
        print("\n⚠️ Warnings only")
        return 0
    else:
        print(f"\n❌ {len(errors)} errors found - DO NOT COMMIT")
        return 1

if __name__ == '__main__':
    sys.exit(check())
