import re

with open('stock_dashboard.html', 'r') as f:
    html = f.read()

start = html.find('const PREMARKET_NEWS = [')
end = html.find('];', start)
block = html[start:end+2]

# 提取每条新闻
news_pattern = r'\{\s*id:\s*(\d+),\s*category:\s*"([^"]+)",\s*level:\s*"([^"]+)",\s*source:\s*"([^"]+)",\s*sourceClass:\s*"([^"]+)",\s*title:\s*"([^"]+)",\s*summary:\s*"([^"]+)",\s*time:\s*"([^"]+)",\s*tags:\s*(\[[^\]]*\])'

matches = re.findall(news_pattern, block)
print(f'Found {len(matches)} news items')

# classify_multi_tags 逻辑
def classify_multi_tags(title):
    t = title.lower()
    tags = []
    
    portfolio_kw = ['九州一轨', '688485', '红星发展', '600367', '禾望电气', '603063',
        'st晨鸣', '000488', '鑫磊股份', '301317', '宝丰能源', '600989',
        '华友钴业', '603799', '科伦药业', '002422', '招商银行', '600036',
        '长江电力', '600900', '中国核电', '601985', '中国铝业', '601600']
    if any(k in t for k in portfolio_kw):
        tags.append('portfolio')
    
    chain_kw = ['碳酸锂', '氢氧化锂', '钴', '镍', '铝', '铜', '锶', '锰', '电解锰',
        '氧化铝', '电解铝', '铝锭', '铝价', '纸浆', '文化纸', '白卡纸',
        '甲醇', '聚烯烃', '煤化工', '煤制烯烃', '电气设备', '变流器',
        '风电', '光伏', '储能', '核电', '水电', '大坝', '核燃料', '铀',
        '轨交', '高铁', '铁路', '地铁', '轨道交通', '减震', '降噪',
        '创新药', '大输液', '抗生素', 'adc药物', '仿制药', '原料药',
        '压缩机', '风机', '水泵', '真空泵',
        'wti', '布伦特', '原油', 'opec', 'lme', '期货', '现货']
    if any(k in t for k in chain_kw):
        tags.append('chain')
    
    policy_kw = ['降准', '降息', '央行', '政治局', '证监会', '国务院', '财政部',
        '外汇局', '监管', '改革', '制度', 'lpr', 'mlf', '逆回购',
        '社融', 'm2', 'cpi', 'ppi', 'pmi', 'gdp', '财政', '货币政策']
    if any(k in t for k in policy_kw):
        tags.append('policy')
    
    geo_kw = ['伊朗', '霍尔木兹', '制裁', '关税', '贸易战', '中美', '特朗普', '拜登',
        '欧盟', '俄罗斯', '俄乌', '中东', '海湾', '石油', '原油',
        '黄金', '白银', '避险', '冲突', '战争', '军事', '导弹', '核']
    if any(k in t for k in geo_kw):
        tags.append('geo')
    
    market_kw = ['a股', '沪指', '深成指', '创业板', '科创板', '北交所',
        '涨停', '跌停', '大涨', '大跌', '暴跌', '飙升',
        '主力资金', '北向资金', '南向资金', '外资', '机构',
        'ipo', '上市', '退市', '停牌', '复牌', '并购',
        '财报', '年报', '季报', '业绩预告', '营收', '净利润',
        '分红', '股息', '增持', '减持', '回购',
        '牛市', '熊市', '反弹', '回调',
        '板块', '概念股', '龙头股', '妖股',
        '股价', '市盈率', '市净率', '估值',
        '港股', '美股', '恒指', '纳指', '标普',
        '指数', '收盘', '开盘', '道指', '突破']
    if any(k in t for k in market_kw):
        tags.append('market')
    
    if not tags:
        tags.append('market')
    return tags

# 给每条新闻加 catTags
new_block = block
for m in matches:
    news_id, cat, level, source, src_cls, title, summary, time_str, tags_str = m
    cats = classify_multi_tags(title)
    cat_tags_str = ', '.join([f'"{c}"' for c in cats])
    
    # 找到这条新闻在 block 中的位置，插入 catTags
    old_news = f'id: {news_id}, category: "{cat}", level: "{level}",'
    new_news = f'id: {news_id}, catTags: [{cat_tags_str}], category: "{cat}", level: "{level}",'
    new_block = new_block.replace(old_news, new_news, 1)

html = html[:start] + new_block + html[end+2:]

with open('stock_dashboard.html', 'w') as f:
    f.write(html)

print('Done. Size:', len(html))
