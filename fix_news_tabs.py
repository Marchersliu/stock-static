with open('stock_dashboard.html', 'r') as f:
    html = f.read()

# 找到 renderNews 函数中过滤逻辑的开始
marker1 = "const newsSource = DYNAMIC_NEWS.length > 0 ? DYNAMIC_NEWS : PREMARKET_NEWS;"
marker2 = "console.log(`[News] 已渲染"

idx1 = html.find(marker1)
idx2 = html.find(marker2)

if idx1 == -1 or idx2 == -1:
    print(f'Markers not found: {idx1}, {idx2}')
    exit(1)

print(f'Found block from {idx1} to {idx2}')

new_block = """  const newsSource = DYNAMIC_NEWS.length > 0 ? DYNAMIC_NEWS : PREMARKET_NEWS;
  // 先按关联度降序，同关联度按时间倒序
  const sorted = [...newsSource].sort((a, b) => {
    const scoreA = a.relevance_score || 0;
    const scoreB = b.relevance_score || 0;
    if (scoreB !== scoreA) return scoreB - scoreA;
    return parseNewsTime(b.time) - parseNewsTime(a.time);
  });
  const all = sorted.filter(n => isWithin7Days(n.time));
  
  // 新标签过滤逻辑（支持多标签：一条新闻可属于多个分类）
  const portfolio = all.filter(n => (n.tags || []).some(t => t.type === 'portfolio'));
  const chain = all.filter(n => (n.tags || []).some(t => t.type === 'chain'));
  const policy = all.filter(n => (n.tags || []).some(t => t.type === 'policy'));
  const geo = all.filter(n => (n.tags || []).some(t => t.type === 'geo'));
  const market = all.filter(n => (n.tags || []).some(t => t.type === 'market'));

  document.getElementById('news-all').innerHTML = `<div class="news-grid">${all.map(renderNewsItem).join('')}</div>`;
  document.getElementById('news-portfolio').innerHTML = portfolio.length > 0 ? `<div class="news-grid">${portfolio.map(renderNewsItem).join('')}</div>` : '<div style="color:var(--text2);text-align:center;padding:20px;">暂无持仓直击新闻</div>';
  document.getElementById('news-chain').innerHTML = chain.length > 0 ? `<div class="news-grid">${chain.map(renderNewsItem).join('')}</div>` : '<div style="color:var(--text2);text-align:center;padding:20px;">暂无产业链新闻</div>';
  document.getElementById('news-policy').innerHTML = policy.length > 0 ? `<div class="news-grid">${policy.map(renderNewsItem).join('')}</div>` : '<div style="color:var(--text2);text-align:center;padding:20px;">暂无政策宏观新闻</div>';
  document.getElementById('news-geo').innerHTML = geo.length > 0 ? `<div class="news-grid">${geo.map(renderNewsItem).join('')}</div>` : '<div style="color:var(--text2);text-align:center;padding:20px;">暂无地缘国际新闻</div>';
  document.getElementById('news-market').innerHTML = market.length > 0 ? `<div class="news-grid">${market.map(renderNewsItem).join('')}</div>` : '<div style="color:var(--text2);text-align:center;padding:20px;">暂无市场资金新闻</div>';
  
"""

html = html[:idx1] + new_block + html[idx2:]

with open('stock_dashboard.html', 'w') as f:
    f.write(html)

print('Replaced. Size:', len(html))
