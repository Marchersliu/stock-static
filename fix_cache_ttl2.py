import re

with open('stock_service.py', 'r') as f:
    content = f.read()

# 1. 在 def fetch_premarket_candidates(): 之前插入 is_trading_time 和 get_cache_ttl
insert_code = '''# ===================== 交易日判断与盘中缓存策略 =====================
def is_trading_time():
    """
    判断当前是否在盘中时段（9:15-15:30）。
    用于决定缓存时长：盘中2分钟，休市10分钟。
    """
    now = datetime.datetime.now()
    weekday = now.weekday()
    # 周末休市
    if weekday >= 5:
        return False
    hour, minute = now.hour, now.minute
    # 9:15 - 15:30 为盘中时段
    start = 9 * 60 + 15  # 555
    end = 15 * 60 + 30   # 930
    current = hour * 60 + minute
    return start <= current <= end

def get_cache_ttl():
    """返回当前时段的缓存秒数：盘中2分钟，休市10分钟"""
    return 120 if is_trading_time() else 600


'''

marker = 'def fetch_premarket_candidates():'
idx = content.find(marker)
if idx != -1:
    content = content[:idx] + insert_code + content[idx:]
    print("Inserted trading_time functions")
else:
    print("fetch_premarket_candidates not found!")
    exit(1)

# 2. 修改 fetch_premarket_candidates 中的缓存检查
old1 = """    # 检查缓存
    now = datetime.datetime.now()
    if PREMARKET_CACHE['timestamp'] and PREMARKET_CACHE['data']:
        cache_age = (now - PREMARKET_CACHE['timestamp']).total_seconds()
        if cache_age < 600:  # 10分钟缓存
            print(f"[CACHE] 候选池缓存命中，{int(cache_age)}秒前更新")
            return PREMARKET_CACHE['data']"""

new1 = """    # 检查缓存（盘中2分钟，休市10分钟）
    now = datetime.datetime.now()
    ttl = get_cache_ttl()
    if PREMARKET_CACHE['timestamp'] and PREMARKET_CACHE['data']:
        cache_age = (now - PREMARKET_CACHE['timestamp']).total_seconds()
        if cache_age < ttl:
            print(f"[CACHE] 候选池缓存命中，{int(cache_age)}秒前更新（盘中2min/休市10min）")
            return PREMARKET_CACHE['data']"""

if old1 in content:
    content = content.replace(old1, new1, 1)
    print("Updated PREMARKET cache")
else:
    print("PREMARKET block not found")

# 3. 修改 fetch_all_events 中的缓存检查  
old2 = """    # 检查缓存
    now = datetime.datetime.now()
    if EVENTS_CACHE['timestamp'] and EVENTS_CACHE['data']:
        cache_age = (now - EVENTS_CACHE['timestamp']).total_seconds()
        if cache_age < 600:  # 10分钟缓存
            print(f"[CACHE] 事件缓存命中，{int(cache_age)}秒前更新")
            return EVENTS_CACHE['data']"""

new2 = """    # 检查缓存（盘中2分钟，休市10分钟）
    now = datetime.datetime.now()
    ttl = get_cache_ttl()
    if EVENTS_CACHE['timestamp'] and EVENTS_CACHE['data']:
        cache_age = (now - EVENTS_CACHE['timestamp']).total_seconds()
        if cache_age < ttl:
            print(f"[CACHE] 事件缓存命中，{int(cache_age)}秒前更新（盘中2min/休市10min）")
            return EVENTS_CACHE['data']"""

if old2 in content:
    content = content.replace(old2, new2, 1)
    print("Updated EVENTS cache")
else:
    print("EVENTS block not found")

with open('stock_service.py', 'w') as f:
    f.write(content)

print("Done. Size:", len(content))
