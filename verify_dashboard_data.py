#!/usr/bin/env python3
"""
Dashboard Data & News Verification Script
验证 stock_dashboard.html 中所有硬编码数据的准确性
"""
import re, json, sys
sys.path.insert(0, '/Users/hf/Library/Python/3.9/lib/python/site-packages')
import tushare as ts

TS_TOKEN = '16e1c68c578e1c26ef7797f17acc2764bcfddb25692b52c3ef8a9878'
pro = ts.pro_api(TS_TOKEN)

# ===================== 1. 读取新闻数据 =====================
with open('/Users/hf/.kimi_openclaw/workspace/stock_dashboard.html', 'r') as f:
    html = f.read()

# 提取 PREMARKET_NEWS 数组
m = re.search(r'const\s+PREMARKET_NEWS\s*=\s*(\[.*?\]);', html, re.DOTALL)
if not m:
    print("❌ 无法提取 PREMARKET_NEWS")
    sys.exit(1)

# 简单解析（用eval不安全，这里用正则逐条提取）
news_items = []
# 提取每个 {id: ... } 块
blocks = re.findall(r'\{\s*id:\s*\d+.*?\},?', m.group(1), re.DOTALL)
for block in blocks:
    item = {}
    for key in ['id', 'category', 'level', 'source', 'sourceClass', 'title', 'summary', 'time']:
        p = rf"{key}:\s*([^,\n]+)"
        km = re.search(p, block)
        if km:
            val = km.group(1).strip().strip('"').strip("'")
            item[key] = val
    news_items.append(item)

print(f"📰 共提取 {len(news_items)} 条新闻")
print("=" * 70)

# ===================== 2. 财务数据声明提取器 =====================
def extract_claims(text):
    claims = []
    # 营收 X亿/Y万（±Y%）—— 要求数字紧跟营收
    for m in re.finditer(r'营收[\s]*([\d\.]+)\s*([万亿])?元?[\s]*[（\(]([\+\-]?\d+\.?\d*)%[）\)]', text):
        unit = m.group(2) or '亿'
        claims.append({'type': '营收', 'value': float(m.group(1)), 'unit': unit, 'change': float(m.group(3))})
    # 净利润/归母净利润/净利 X亿/Y万（±Y%）—— 要求数字紧跟净利
    for m in re.finditer(r'(?:归母)?净利润?[\s]*([\d\.]+)\s*([万亿])?元?[\s]*[（\(]([\+\-]?\d+\.?\d*)%[）\)]', text):
        unit = m.group(2) or '万'
        claims.append({'type': '净利润', 'value': float(m.group(1)), 'unit': unit, 'change': float(m.group(3))})
    # 净利润 亏损X万/X亿
    for m in re.finditer(r'(?:归母)?净利润[\s]*.*?亏损[\s]*([\d\.]+)\s*([万亿])?元?', text):
        unit = m.group(2) or '万'
        claims.append({'type': '净利润', 'value': -float(m.group(1)), 'unit': unit, 'change': None})
    return claims

# 股票代码映射（从新闻标题提取）
CODE_MAP = {
    '九州一轨': '688485.SH', '红星发展': '600367.SH', 'ST晨鸣': '000488.SZ',
    '禾望电气': '603063.SH', '鑫磊股份': '301317.SZ', '宝丰能源': '600989.SH',
    '华友钴业': '603799.SH', '科伦药业': '002422.SZ', '招商银行': '600036.SH',
    '中国核电': '601985.SH', '中国铝业': '601600.SH', '长江电力': '600900.SH',
    '赢合科技': '300457.SZ'
}

def find_stock_code(title, summary):
    text = title + summary
    for name, code in CODE_MAP.items():
        if name in text:
            return code
    # 尝试提取6位数字
    m = re.search(r'(\d{6})', text)
    if m:
        num = m.group(1)
        if num.startswith('6'):
            return num + '.SH'
        elif num.startswith('0') or num.startswith('3'):
            return num + '.SZ'
    return None

# ===================== 3. 核查每条新闻 =====================
VERIFIED = []
WARNINGS = []
ERRORS = []

for item in news_items:
    nid = item.get('id', '?')
    title = item.get('title', '')
    summary = item.get('summary', '')
    time_str = item.get('time', '')
    level = item.get('level', 'normal')
    text = title + ' ' + summary
    
    # 3.1 日期合理性检查
    try:
        m = re.match(r'(\d{2})-(\d{2})', time_str)
        if m:
            month, day = int(m.group(1)), int(m.group(2))
            # 简单检查：当前是5月，新闻月份不应超过5（除非跨年，暂不考虑）
            if month > 5 or (month == 5 and day > 3):
                WARNINGS.append(f"[新闻{nid}] 日期 {time_str} 可能为未来日期，请确认")
    except:
        pass
    
    # 3.2 提取财务声明
    claims = extract_claims(text)
    code = find_stock_code(title, summary)
    
    if claims and code:
        # 尝试用Tushare验证
        try:
            # 判断是Q1新闻还是年报新闻
            is_q1 = any(k in text for k in ['Q1', '一季度', '季报', '第一季度'])
            is_annual = any(k in text for k in ['年报', '年度', '2025年'])
            if is_q1:
                df = pro.income(ts_code=code, period='20260331', fields='ts_code,period,total_revenue,n_income,n_income_attr_p')
            elif is_annual:
                df = pro.income(ts_code=code, period='20251231', fields='ts_code,period,total_revenue,n_income,n_income_attr_p')
            else:
                # 默认先试年报，再试Q1
                df = pro.income(ts_code=code, period='20251231', fields='ts_code,period,total_revenue,n_income,n_income_attr_p')
                if df.empty:
                    df = pro.income(ts_code=code, period='20260331', fields='ts_code,period,total_revenue,n_income,n_income_attr_p')
            
            if not df.empty:
                actual_revenue = df.iloc[0]['total_revenue'] / 1e8  # 转亿
                actual_profit = df.iloc[0]['n_income_attr_p'] / 1e4 if 'n_income_attr_p' in df.columns else df.iloc[0]['n_income'] / 1e4
                
                for claim in claims:
                    if claim['type'] == '营收':
                        # 统一转亿元
                        claim_val = claim['value']
                        if claim['unit'] == '万':
                            claim_val = claim_val / 1e4
                        diff_pct = abs(claim_val - actual_revenue) / max(actual_revenue, 0.1) * 100
                        if diff_pct > 10:
                            ERRORS.append(f"[新闻{nid} {code}] 营收声明 {claim['value']}{claim['unit']} vs Tushare实际 {actual_revenue:.2f}亿，偏差{diff_pct:.0f}%")
                        else:
                            VERIFIED.append(f"[新闻{nid} {code}] 营收 {claim['value']}{claim['unit']} vs Tushare {actual_revenue:.2f}亿 ✅")
                    elif claim['type'] == '净利润':
                        # 统一转万元
                        claim_val = claim['value']
                        if claim['unit'] == '亿':
                            claim_val = claim_val * 1e4
                        diff_pct = abs(claim_val - actual_profit) / max(abs(actual_profit), 1) * 100
                        if diff_pct > 15:
                            ERRORS.append(f"[新闻{nid} {code}] 净利润声明 {claim['value']}{claim['unit']} vs Tushare实际 {actual_profit:.0f}万，偏差{diff_pct:.0f}%")
                        else:
                            VERIFIED.append(f"[新闻{nid} {code}] 净利润 {claim['value']}{claim['unit']} vs Tushare {actual_profit:.0f}万 ✅")
            else:
                WARNINGS.append(f"[新闻{nid} {code}] Tushare无财报数据，无法自动验证")
        except Exception as e:
            WARNINGS.append(f"[新闻{nid} {code}] Tushare验证异常: {str(e)[:50]}")
    elif claims:
        WARNINGS.append(f"[新闻{nid}] 含财务数据但无法识别股票代码，需人工核查: {title[:40]}")
    
    # 3.3 不可自动验证的关键词标记
    unverifiable_keywords = ['在手订单', '意向协议', '战略合作', '将', '拟', '计划']
    for kw in unverifiable_keywords:
        if kw in text:
            WARNINGS.append(f"[新闻{nid}] 含不可自动验证关键词「{kw}」: {title[:40]}")
            break
    
    # 3.4 过时新闻检测（超过7天）
    try:
        m = re.match(r'(\d{2})-(\d{2})', time_str)
        if m:
            month, day = int(m.group(1)), int(m.group(2))
            # 假设当前5月3日
            age_days = (5 - month) * 30 + (3 - day)
            if age_days > 7:
                WARNINGS.append(f"[新闻{nid}] 发布时间{time_str}，距今{age_days}天，可能已过时")
    except:
        pass

# ===================== 4. 核查产业链表格静态数据 =====================
print("\n🏭 产业链成本透视表静态数据核查")
print("-" * 70)
# 提取所有带数字的表格内容，标记为"⚪ AI估算/行业均值，需人工定期复核"
commodity_claims = re.findall(r'<td[^>]*>([^<]*?\d[\d,\.]*[^<]*?)</td>', html)
print(f"  发现 {len(commodity_claims)} 个含数字的表格单元格")
print("  ⚠️  产业链数据（产品价格/原料成本/水电气）多为行业均值或公告摘录，")
print("      无实时API来源，建议每月人工复核一次")

# ===================== 5. 输出报告 =====================
print("\n" + "=" * 70)
print("📊 核查报告")
print("=" * 70)

print(f"\n✅ 已通过 ({len(VERIFIED)}):")
for v in VERIFIED[:10]:
    print(f"  {v}")
if len(VERIFIED) > 10:
    print(f"  ... 共 {len(VERIFIED)} 条")

print(f"\n⚠️  警告 ({len(WARNINGS)}):")
for w in WARNINGS:
    print(f"  {w}")

print(f"\n❌ 错误 ({len(ERRORS)}):")
for e in ERRORS:
    print(f"  {e}")

print(f"\n📌 总结: {len(VERIFIED)}项通过, {len(WARNINGS)}项警告, {len(ERRORS)}项错误")

if ERRORS:
    sys.exit(1)
else:
    print("\n🟢 核查完成，无严重数据错误")
    sys.exit(0)
