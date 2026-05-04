import tushare as ts
import re
from datetime import datetime

# Tushare Pro setup
import os
TS_TOKEN = os.environ.get('TUSHARE_TOKEN', '')
if not TS_TOKEN:
    raise ValueError("TUSHARE_TOKEN environment variable not set")
ts.set_token(TS_TOKEN)
pro = ts.pro_api()

trade_date = '20260430'

# Stock definitions
stocks_info = {
    '688485.SH': {'name': '九州一轨', 'target': '60/65', 'stop': '49.00', 'hero': True},
    '600989.SH': {'name': '宝丰能源', 'target': '38', 'stop': None, 'hero': False},
    '603799.SH': {'name': '华友钴业', 'target': '50', 'stop': None, 'hero': False},
    '600367.SH': {'name': '红星发展', 'target': '22', 'stop': None, 'hero': False},
    '603063.SH': {'name': '禾望电气', 'target': '35', 'stop': None, 'hero': False},
    '000488.SZ': {'name': 'ST晨鸣', 'target': '3.5', 'stop': None, 'hero': False},
    '301317.SZ': {'name': '鑫磊股份', 'target': '25', 'stop': None, 'hero': False},
    '002422.SZ': {'name': '科伦药业', 'target': '28-30', 'stop': None, 'hero': False},
    '600036.SH': {'name': '招商银行', 'target': '35-36', 'stop': None, 'hero': False},
    '600900.SH': {'name': '长江电力', 'target': '26-26.5', 'stop': '22', 'hero': False},
    '601985.SH': {'name': '中国核电', 'target': '7.5-8.0', 'stop': '6.5', 'hero': False},
    '601600.SH': {'name': '中国铝业', 'target': '9.5-10.0', 'stop': '7.8', 'hero': False},
}

# Fetch all data
print('Fetching data from Tushare...')
data = {}
for code, info in stocks_info.items():
    entry = {'name': info['name'], 'target': info['target'], 'stop': info['stop'], 'hero': info['hero']}
    
    # Daily price
    try:
        df = pro.daily(ts_code=code, trade_date=trade_date)
        if len(df) > 0:
            r = df.iloc[0]
            entry['close'] = r['close']
            entry['open'] = r['open']
            entry['high'] = r['high']
            entry['low'] = r['low']
            entry['pre_close'] = r['pre_close']
            entry['pct_chg'] = r['pct_chg']
            entry['vol'] = r['vol'] / 10000  # 手 -> 万手
            entry['amount'] = r['amount'] / 10000  # 万元 -> 亿元
    except Exception as e:
        print(f'{info["name"]} daily error: {e}')
    
    # Money flow
    try:
        df = pro.moneyflow(ts_code=code, trade_date=trade_date)
        if len(df) > 0:
            r = df.iloc[0]
            # Net amounts in 万元
            entry['net_mf'] = r['net_mf_amount']  # 主力净额（万元）
            entry['elg_net'] = r['buy_elg_amount'] - r['sell_elg_amount']  # 超大单净额
            entry['lg_net'] = r['buy_lg_amount'] - r['sell_lg_amount']  # 大单净额
            entry['md_net'] = r['buy_md_amount'] - r['sell_md_amount']  # 中单净额
            entry['sm_net'] = r['buy_sm_amount'] - r['sell_sm_amount']  # 小单净额
    except Exception as e:
        print(f'{info["name"]} moneyflow error: {e}')
    
    # Daily basic
    try:
        df = pro.daily_basic(ts_code=code, trade_date=trade_date)
        if len(df) > 0:
            r = df.iloc[0]
            entry['pe'] = r['pe']
            entry['pb'] = r['pb']
            entry['total_mv'] = r['total_mv'] / 10000 if r['total_mv'] else None  # 万元->亿元
            entry['circ_mv'] = r['circ_mv'] / 10000 if r['circ_mv'] else None
            entry['turnover'] = r['turnover_rate']
    except Exception as e:
        print(f'{info["name"]} basic error: {e}')
    
    data[code] = entry

# Format helpers
def fmt_money(val):
    """Format money flow in 万元 to readable string"""
    if val is None:
        return 'N/A'
    if abs(val) >= 10000:
        return f"{val/10000:+.1f}亿"
    else:
        return f"{val:+.0f}万"

def fmt_num(val, dec=2):
    if val is None:
        return 'N/A'
    return f"{val:.{dec}f}"

def updown_class(pct):
    if pct > 0:
        return 'up'
    elif pct < 0:
        return 'down'
    return 'neutral'

def updown_color(pct):
    if pct > 0:
        return '#ef4444'
    elif pct < 0:
        return '#22c55e'
    return '#64748b'

# Print summary
print('\n=== DATA SUMMARY ===')
for code, d in data.items():
    print(f"{d['name']}({code}): 收{d.get('close','N/A')}, 涨跌{d.get('pct_chg','N/A'):.2f}%, 主力{fmt_money(d.get('net_mf'))}, PE{d.get('pe','N/A')}, 市值{d.get('total_mv','N/A'):.0f}亿")

# Read original HTML
with open('/Users/hf/.kimi_openclaw/workspace/投资组合实时监控中心.html', 'r', encoding='utf-8') as f:
    html = f.read()

print('\nUpdating HTML...')

# Update 九州一轨 hero section
jz_code = '688485.SH'
jz = data[jz_code]

jz_hero_update = f'''<!-- 核心指标 -->
    <div class="hero-grid">
      <div class="hero-stat">
        <div class="label">现价</div>
        <div class="value" style="color:{updown_color(jz.get('pct_chg',0))};">{jz.get('close','--'):.2f}</div>
        <div class="sub">{jz.get('pct_chg',0):+.2f}%</div>
      </div>
      <div class="hero-stat">
        <div class="label">你的成本</div>
        <div class="value">46.70</div>
        <div class="sub">已持有</div>
      </div>
      <div class="hero-stat">
        <div class="label">浮盈</div>
        <div class="value" style="color:#ef4444;">{(jz.get('close',55.2)/46.70-1)*100:+.1f}%</div>
        <div class="sub">+{jz.get('close',55.2)-46.70:.2f}元/股</div>
      </div>
      <div class="hero-stat">
        <div class="label">止损线</div>
        <div class="value" style="color:#ef4444;">49.00</div>
        <div class="sub">跌破清仓</div>
      </div>
    </div>

    <!-- 目标价 -->
    <div class="hero-grid" style="margin-top: 12px;">
      <div class="hero-stat">
        <div class="label">第一目标</div>
        <div class="value" style="color:#fbbf24;">60.00</div>
        <div class="sub">突破后加仓</div>
      </div>
      <div class="hero-stat">
        <div class="label">清仓目标</div>
        <div class="value" style="color:#fbbf24;">65.00</div>
        <div class="sub">全额止盈</div>
      </div>
      <div class="hero-stat">
        <div class="label">月涨跌</div>
        <div class="value" style="color:#ef4444;">+30.2%</div>
        <div class="sub">4月表现</div>
      </div>
      <div class="hero-stat">
        <div class="label">仓位建议</div>
        <div class="value" style="color:#22c55e;">25%</div>
        <div class="sub">当前上限</div>
      </div>
    </div>

    <!-- 技术面 -->
    <div style="margin-top: 20px;">
      <div class="card-subtitle">📈 技术面信号</div>
      <div class="tech-grid">
        <div class="tech-box">
          <div class="label">MACD</div>
          <div class="value" style="color:#fbbf24;">低位金叉</div>
          <div class="signal" style="background:#2a2a0d;color:#fbbf24;">观察中</div>
        </div>
        <div class="tech-box">
          <div class="label">KDJ</div>
          <div class="value" style="color:#ef4444;">J=89</div>
          <div class="signal" style="background:#450a0a;color:#ef4444;">超买区</div>
        </div>
        <div class="tech-box">
          <div class="label">RSI</div>
          <div class="value" style="color:#fbbf24;">56</div>
          <div class="signal" style="background:#1e293b;color:#94a3b8;">中性</div>
        </div>
        <div class="tech-box">
          <div class="label">均线</div>
          <div class="value" style="color:#ef4444;">多头排列</div>
          <div class="signal" style="background:#4a0d0d;color:#ef4444;">强势</div>
        </div>
      </div>
    </div>

    <!-- 资金面 -->
    <div style="margin-top: 20px;">
      <div class="card-subtitle">💰 资金面（4/30 · Tushare Pro）</div>
      <div class="money-row">
        <div class="money-box">
          <div class="label">主力净流入</div>
          <div class="value" style="color:{updown_color(jz.get('net_mf',0))};">{fmt_money(jz.get('net_mf',0))}</div>
        </div>
        <div class="money-box">
          <div class="label">超大单</div>
          <div class="value" style="color:{updown_color(jz.get('elg_net',0))};">{fmt_money(jz.get('elg_net',0))}</div>
        </div>
        <div class="money-box">
          <div class="label">大单</div>
          <div class="value" style="color:{updown_color(jz.get('lg_net',0))};">{fmt_money(jz.get('lg_net',0))}</div>
        </div>
        <div class="money-box">
          <div class="label">中单</div>
          <div class="value" style="color:{updown_color(jz.get('md_net',0))};">{fmt_money(jz.get('md_net',0))}</div>
        </div>
        <div class="money-box">
          <div class="label">小单</div>
          <div class="value" style="color:{updown_color(jz.get('sm_net',0))};">{fmt_money(jz.get('sm_net',0))}</div>
        </div>
      </div>
      <p style="color:#475569;font-size:11px;margin-top:8px;">📊 Tushare Pro实时数据 | 近5日主力流向需手动更新</p>
    </div>'''

# Find and replace the 九州一轨 section
jz_start = html.find('<!-- 核心指标 -->')
jz_end = html.find('<!-- 操作建议 -->', jz_start)
if jz_start > 0 and jz_end > 0:
    html = html[:jz_start] + jz_hero_update + html[jz_end:]
    print('✅ Updated 九州一轨 section')

# Update 持仓总览 table rows
# Find the tbody of the holdings table
tbody_start = html.find('<tbody>')
tbody_end = html.find('</tbody>', tbody_start)
if tbody_start > 0 and tbody_end > 0:
    # Build new tbody content
    rows_html = []
    for code in ['688485.SH', '600989.SH', '603799.SH', '600367.SH', '603063.SH', 
                 '000488.SZ', '301317.SZ', '002422.SZ', '600036.SH', '600900.SH', 
                 '601985.SH', '601600.SH']:
        d = data[code]
        close = d.get('close', 0)
        pct = d.get('pct_chg', 0)
        target = d['target']
        
        # Calculate distance to target
        dist = 0
        if '/' in str(target):
            t_parts = target.split('/')
            t_val = float(t_parts[0])  # use first target
            dist = (t_val / close - 1) * 100 if close > 0 else 0
        elif '-' in str(target):
            t_parts = target.split('-')
            t_low = float(t_parts[0])
            dist = (t_low / close - 1) * 100 if close > 0 else 0
        else:
            try:
                t_val = float(target)
                dist = (t_val / close - 1) * 100 if close > 0 else 0
            except:
                dist = 0
        
        # Money flow
        mf = d.get('net_mf', 0)
        mf_fmt = fmt_money(mf)
        mf_class = updown_class(mf)
        
        # Action suggestion
        if d['hero']:
            action = '<span class="up">持有</span>'
        elif pct > 3 and mf > 0:
            action = '<span class="up">持有</span>'
        elif pct < -2 and mf < 0:
            action = '<span class="down">观望</span>'
        else:
            action = '<span class="neutral">观察中</span>'
        
        # Special cases
        if code == '600900.SH':  # 长江电力
            action = '<span class="up">可建仓</span>'
        
        name_color = 'color:#c4b5fd;' if d['hero'] else ''
        
        row = f'''          <tr>
            <td><strong style="{name_color}">{d['name']}</strong></td>
            <td>{code.split('.')[0]}</td>
            <td class="highlight">{close:.2f}</td>
            <td class="{updown_class(pct)}">{pct:+.2f}%</td>
            <td class="{updown_class(pct)}">{'+' if pct > 0 else ''}{pct:.1f}%</td>
            <td>{target}</td>
            <td>{dist:+.1f}%</td>
            <td class="{mf_class}">{mf_fmt}</td>
            <td>{action}</td>
          </tr>'''
        rows_html.append(row)
    
    new_tbody = '<tbody>\n' + '\n'.join(rows_html) + '\n        </tbody>'
    html = html[:tbody_start] + new_tbody + html[tbody_end+8:]
    print('✅ Updated 持仓总览 table')

# Update update time in header
header_time = html.find('<p class="update-time">')
if header_time > 0:
    time_end = html.find('</p>', header_time)
    html = html[:header_time] + '<p class="update-time">数据截至 2026-04-30 15:00 | Tushare Pro实时接入 | 共跟踪 12 只股票</p>' + html[time_end+4:]
    print('✅ Updated header time')

# Update 盘前信息汇总 section
# This is a major update - replace the entire pre-market section
pre_market_old_start = html.find('<!-- ==================== ⭐ 盘前信息汇总 ==================== -->')
pre_market_old_end = html.find('<!-- ==================== ⭐ 九州一轨 重点模块 ==================== -->')

if pre_market_old_start > 0 and pre_market_old_end > 0:
    pre_market_new = '''<!-- ==================== ⭐ 盘前信息汇总 ==================== -->
  <div class="card" style="border:2px solid #fbbf24;background:linear-gradient(135deg,#111827 0%,#1a150a 50%,#111827 100%);">
    <div style="display:inline-block;background:#fbbf24;color:#111827;padding:3px 10px;border-radius:4px;font-size:12px;font-weight:700;margin-bottom:12px;">📰 盘前信息汇总 · 节后首个交易日 5/6（周二）</div>
    <div class="card-title" style="color:#fbbf24;">🌍 假期全球市场扫描</div>

    <!-- 港股5/2开门红 -->
    <div style="margin-bottom:16px;">
      <div class="card-subtitle">🇭🇰 港股 5/2（周五）· 5月开门红</div>
      <div class="hero-grid" style="margin-top:8px;">
        <div class="hero-stat">
          <div class="label">恒生指数</div>
          <div class="value" style="color:#ef4444;">+1.74%</div>
          <div class="sub">科网股全线大涨</div>
        </div>
        <div class="hero-stat">
          <div class="label">恒生科技</div>
          <div class="value" style="color:#ef4444;">+3.08%</div>
          <div class="sub">科技股领涨</div>
        </div>
        <div class="hero-stat">
          <div class="label">小米集团</div>
          <div class="value" style="color:#ef4444;">+6%</div>
          <div class="sub">科技股龙头</div>
        </div>
        <div class="hero-stat">
          <div class="label">阿里巴巴</div>
          <div class="value" style="color:#ef4444;">+3.8%</div>
          <div class="sub">中概情绪偏暖</div>
        </div>
      </div>
      <p style="color:#64748b;font-size:11px;margin-top:6px;">📌 港股5月开门红，科网股全线大涨，小米+6%、阿里+3.8%、腾讯+2.56%</p>
    </div>

    <!-- 美股5/1 -->
    <div style="margin-bottom:16px;">
      <div class="card-subtitle">🇺🇸 美股 5/1 收盘 · 特朗普关税+伊朗表态扰动</div>
      <div class="hero-grid" style="margin-top:8px;">
        <div class="hero-stat">
          <div class="label">道琼斯</div>
          <div class="value" style="color:#22c55e;">+0.37%</div>
          <div class="sub">盘中由涨转跌</div>
        </div>
        <div class="hero-stat">
          <div class="label">纳斯达克</div>
          <div class="value" style="color:#22c55e;">+0.5%</div>
          <div class="sub">存储芯片领涨</div>
        </div>
        <div class="hero-stat">
          <div class="label">标普500</div>
          <div class="value" style="color:#22c55e;">+0.3%</div>
          <div class="sub">小幅收涨</div>
        </div>
        <div class="hero-stat">
          <div class="label">中概金龙</div>
          <div class="value" style="color:#ef4444;">+2.01%</div>
          <div class="sub">贝壳+7% 百度+4.6%</div>
        </div>
      </div>
      <p style="color:#64748b;font-size:11px;margin-top:6px;">📌 特朗普威胁对欧盟汽车加征25%关税；存储芯片概念股（闪迪、希捷、美光）创历史新高</p>
    </div>

    <!-- 个股亮点与风险 -->
    <div class="two-col" style="margin-bottom:16px;">
      <div>
        <div class="card-subtitle">📈 个股亮点</div>
        <ul class="event-list" style="font-size:13px;">
          <li><span class="event-tag tag-up">新高</span><strong>闪迪/希捷/美光</strong> 存储芯片概念股集体创历史新高</li>
          <li><span class="event-tag tag-up">+6%</span><strong>小米集团（港股）</strong> 港股开门红领涨科技</li>
          <li><span class="event-tag tag-up">+7%</span><strong>药明康德（港股）</strong> CXO概念股大涨</li>
        </ul>
      </div>
      <div>
        <div class="card-subtitle">⚠️ 个股风险</div>
        <ul class="event-list" style="font-size:13px;">
          <li><span class="event-tag tag-down">盘中跳</span><strong>美股大盘</strong> 特朗普对伊朗方案"不满意"，标普/纳指回吐涨幅</li>
          <li><span class="event-tag tag-down">-8%</span><strong>西部数据（盘前）</strong> 存储概念意外暴跌，获利了结</li>
          <li><span class="event-tag tag-down">跌</span><strong>欧洲汽车股</strong> 特朗普威胁加征25%关税，Stellantis跌3%</li>
        </ul>
      </div>
    </div>

    <!-- 油价与地缘 -->
    <div class="two-col" style="margin-bottom:16px;">
      <div>
        <div class="card-subtitle">⛽ 油价与大宗商品</div>
        <div class="commodity-grid" style="grid-template-columns:repeat(2,1fr);gap:8px;">
          <div class="commodity-box">
            <div class="name">布伦特原油</div>
            <div class="price" style="color:#ef4444;">$114</div>
            <div class="change down">-3.4%</div>
            <div class="note">6月合约到期，曾破126</div>
          </div>
          <div class="commodity-box">
            <div class="name">WTI原油</div>
            <div class="price" style="color:#ef4444;">$104</div>
            <div class="change down">-2%</div>
            <div class="note">6月期货</div>
          </div>
        </div>
      </div>
      <div>
        <div class="card-subtitle">⚔️ 美伊/中美局势最新</div>
        <ul class="event-list" style="font-size:13px;">
          <li><span class="event-tag tag-neutral">谈判</span>美方主动向中方传递信息希望谈起来，中方回应：正在评估</li>
          <li><span class="event-tag tag-up">升级</span>4/30 特朗普提出建立"海上联盟"重开霍尔木兹海峡</li>
          <li><span class="event-tag tag-up">备战</span>6500吨军事装备从美国运抵以色列</li>
          <li><span class="event-tag tag-down">紧张</span>特朗普对伊朗最新方案"不满意"，选项包括"彻底打击"</li>
        </ul>
      </div>
    </div>

    <!-- A股开盘影响分析 -->
    <div style="background:#0f172a;padding:14px;border-radius:10px;margin-top:12px;">
      <div class="card-subtitle">🇨🇳 对节后A股开盘影响（5/6 周二）</div>
      <div class="hero-grid" style="margin-top:8px;">
        <div class="hero-stat" style="border-left:3px solid #22c55e;">
          <div class="label" style="color:#22c55e;">✅ 正面</div>
          <div class="value" style="font-size:14px;color:#e2e8f0;">港股开门红+3%</div>
          <div class="sub">科网股情绪提振</div>
        </div>
        <div class="hero-stat" style="border-left:3px solid #22c55e;">
          <div class="label" style="color:#22c55e;">✅ 正面</div>
          <div class="value" style="font-size:14px;color:#e2e8f0;">中概股金龙+2%</div>
          <div class="sub">A股科技情绪偏暖</div>
        </div>
        <div class="hero-stat" style="border-left:3px solid #22c55e;">
          <div class="label" style="color:#22c55e;">✅ 正面</div>
          <div class="value" style="font-size:14px;color:#e2e8f0;">油价回落</div>
          <div class="sub">利好航空、化工，降通胀</div>
        </div>
        <div class="hero-stat" style="border-left:3px solid #fbbf24;">
          <div class="label" style="color:#fbbf24;">⚠️ 关注</div>
          <div class="value" style="font-size:14px;color:#e2e8f0;">美伊仍紧张</div>
          <div class="sub">军工、黄金留意</div>
        </div>
      </div>
      <p style="color:#475569;font-size:11px;margin-top:8px;">📌 节后首个交易日 5/6（周二）· 建议关注：科技股情绪、油价敏感板块、军工黄金动向、中美谈判进展</p>
    </div>

    <p style="color:#475569;font-size:11px;margin-top:12px;text-align:right;">数据来源：Tushare Pro、新浪财经、新华社、财联社 · 更新时间：2026-05-02</p>
  </div>

'''
    html = html[:pre_market_old_start] + pre_market_new + html[pre_market_old_end:]
    print('✅ Updated 盘前信息汇总 section')

# Save updated HTML
output_path = '/Users/hf/.kimi_openclaw/workspace/投资组合实时监控中心.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'\n✅ Updated HTML saved: {output_path}')

# Sync to iCloud
import shutil
shutil.copy(output_path, '/Users/hf/Library/Mobile Documents/com~apple~CloudDocs/下载文件/HF/投资组合实时监控中心.html')
print('✅ Synced to iCloud')
