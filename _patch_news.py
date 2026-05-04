#!/usr/bin/env python3
with open('stock_dashboard.html', 'r') as f:
    content = f.read()

old_start = content.find('// ===================== 盘前新闻候选抓取 =====================')
old_end_marker = 'function formatDateRange(dates) {'
old_end = content.find(old_end_marker)

if old_start == -1 or old_end == -1:
    print(f'Not found: start={old_start}, end={old_end}')
else:
    new_func = """// ===================== 盘前新闻候选抓取 =====================
function fetchNewsCandidates() {
  const btn = document.getElementById('update-news-candidates');
  const timeEl = document.getElementById('update-news-candidates-time');
  const area = document.getElementById('news-candidates-area');
  const grid = document.getElementById('news-candidates-grid');
  const countEl = document.getElementById('news-candidates-count');
  
  if (btn) btn.textContent = '⏳ 抓取中...';
  if (timeEl) timeEl.textContent = '抓取中...';
  
  fetch('/api/premarket')
    .then(r => r.json())
    .then(data => {
      if (!data.categories || !area || !grid) {
        if (timeEl) { timeEl.textContent = '⏳ 后端未启动'; timeEl.className = 'update-time manual'; }
        if (btn) { btn.textContent = '🔄 抓取候选'; btn.className = 'refresh-btn'; }
        return;
      }
      
      const now = new Date();
      const timeStr = now.toLocaleTimeString('zh-CN', {hour:'2-digit', minute:'2-digit'});
      
      // 提取所有候选新闻
      let candidates = [];
      for (const [key, cat] of Object.entries(data.categories)) {
        for (const item of (cat.items || [])) {
          candidates.push(item);
        }
      }
      
      // 按日期倒序
      candidates.sort((a, b) => (b.date + b.time || '').localeCompare(a.date + a.time || ''));
      
      // 构建来源状态HTML
      let sourceHtml = '';
      if (data.source_status) {
        const active = Object.entries(data.source_status).filter(([k, v]) => v.includes('✅'));
        const pending = Object.entries(data.source_status).filter(([k, v]) => v.includes('⏳'));
        sourceHtml = `<div style="font-size:10px;color:var(--text3);margin-bottom:10px;display:flex;flex-wrap:wrap;gap:4px;">
          <span>来源：</span>
          ${active.map(([k, v]) => `<span style="color:var(--green);">${k}</span>`).join(' · ')}
          ${pending.length > 0 ? '<span style="color:var(--text3);margin-left:8px;">待接：' + pending.map(([k, v]) => k).join(' · ') + '</span>' : ''}
        </div>`;
      }
      
      if (candidates.length === 0) {
        grid.innerHTML = sourceHtml + '<div style="color:var(--text2);text-align:center;padding:20px;">暂无候选新闻（所有来源返回为空）</div>';
      } else {
        let html = sourceHtml + '<div style="display:grid;grid-template-columns:1fr;gap:8px;">';
        for (const item of candidates.slice(0, 30)) { // 最多30条
          const dateStr = item.date ? item.date.substring(5).replace('-', '/') : '';
          const stockTag = item.stock_name ? `<span style="color:var(--gold);font-weight:600;">${item.stock_name}</span> · ` : '';
          const catLabel = {policy:'🏛️政策', finance:'🏦金融', company:'🏢公司', material:'🛢️原料'}[item.category] || '🔍其他';
          const srcBadge = `<span style="font-size:10px;color:var(--text3);background:var(--bg);padding:1px 4px;border-radius:3px;">${item.source || '未知'}</span>`;
          html += `<div class="news-item candidate">
            <div class="candidate-badge">${catLabel} · 候选 · 未入精选 · ${srcBadge}</div>
            <div class="news-source"><span class="dot ${item.sourceClass || 'sina'}"></span>${item.source || '新浪财经'} · ${dateStr} ${item.time ? item.time : ''}</div>
            <div class="news-title">${stockTag}${item.title}</div>
            ${item.url ? `<div style="font-size:11px;margin-top:4px;"><a href="${item.url}" target="_blank" style="color:var(--accent);text-decoration:none;">查看原文 →</a></div>` : ''}
          </div>`;
        }
        html += '</div>';
        grid.innerHTML = html;
      }
      
      area.style.display = 'block';
      if (countEl) countEl.textContent = `共 ${candidates.length} 条 · ${Object.keys(data.source_counts || {}).length} 个来源`;
      if (timeEl) { timeEl.textContent = `抓取于 ${timeStr}`; timeEl.className = 'update-time live'; }
      if (btn) { btn.textContent = '🔄 抓取候选'; btn.className = 'refresh-btn'; }
      console.log(`[NewsCandidates] 已展示 ${candidates.length} 条候选新闻`);
    })
    .catch(err => {
      console.log('[NewsCandidates] 后端未启动', err);
      if (timeEl) { timeEl.textContent = '等待抓取'; timeEl.className = 'update-time manual'; }
      if (btn) { btn.textContent = '🔄 抓取候选'; btn.className = 'refresh-btn'; }
    });
}

function formatDateRange(dates) {"""
    
    content = content[:old_start] + new_func + content[old_end:]
    
    with open('stock_dashboard.html', 'w') as f:
        f.write(content)
    print('✅ fetchNewsCandidates updated')
