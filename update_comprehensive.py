#!/usr/bin/env python3
"""
Tushare 综合数据自动更新脚本
整合：基础数据、财务数据、融资融券、龙虎榜、公司行为、ST/沪港通
用于更新 投资组合实时监控中心.html

运行方式:
    python3 update_comprehensive.py
"""

import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
import re

# ============= 配置 =============
TS_TOKEN = 'e53f440e3d606fab37832317782450f3d3aa0a54c296c8834ba61038'

STOCKS = {
    '688485.SH': '九州一轨',
    '600989.SH': '宝丰能源',
    '603799.SH': '华友钴业',
    '600367.SH': '红星发展',
    '603063.SH': '禾望电气',
    '000488.SZ': 'ST晨鸣',
    '301317.SZ': '鑫磊股份',
    '002422.SZ': '科伦药业',
    '600036.SH': '招商银行',
    '600900.SH': '长江电力',
    '601985.SH': '中国核电',
    '601600.SH': '中国铝业',
}

# 创业板抱团股（板块轮动监测）
CYB_STOCKS = {
    '300750.SZ': '宁德时代',
    '300308.SZ': '中际旭创',
    '300502.SZ': '新易盛',
    '300059.SZ': '东方财富',
    '300274.SZ': '阳光电源',
    '300476.SZ': '胜宏科技',
    '300394.SZ': '天孚通信',
    '300124.SZ': '汇川技术',
    '300760.SZ': '迈瑞医疗',
    '300014.SZ': '亿纬锂能',
}

CYB_TAGS = {
    '300750.SZ': '电池龙头',
    '300308.SZ': '光模块',
    '300502.SZ': '光模块',
    '300059.SZ': '券商龙头',
    '300274.SZ': '逆变器',
    '300476.SZ': 'PCB',
    '300394.SZ': '光器件',
    '300124.SZ': '工控龙头',
    '300760.SZ': '医疗器械',
    '300014.SZ': '锂电池',
}

HTML_PATH = '/Users/hf/.kimi_openclaw/workspace/投资组合实时监控中心.html'
ICLOUD_PATH = '/Users/hf/Library/Mobile Documents/com~apple~CloudDocs/下载文件/HF/投资组合实时监控中心.html'


def get_trade_date(offset=0):
    """获取最近交易日"""
    today = datetime.now() - timedelta(days=offset)
    if today.month == 5 and today.day <= 5:
        return '20260430'
    weekday = today.weekday()
    if weekday == 5:
        today -= timedelta(days=1)
    elif weekday == 6:
        today -= timedelta(days=2)
    return today.strftime('%Y%m%d')


class TushareDataCollector:
    def __init__(self):
        ts.set_token(TS_TOKEN)
        self.pro = ts.pro_api()
        self.trade_date = get_trade_date()
        self.data = {}
        
    def fetch_all(self):
        print(f"=== 综合数据抓取 ({self.trade_date}) ===")
        self._fetch_basic()
        self._fetch_finance()
        self._fetch_margin()
        self._fetch_pledge()
        self._fetch_company_actions()
        self._fetch_longhubang()
        self._check_st()
        self._check_hsgt()
        self._fetch_moneyflow()
        self._fetch_cyb_moneyflow()
        print(f"\n[OK] 全部抓取完成")
        
    def _fetch_basic(self):
        """基础数据：PE/PB/市值/行业"""
        print("\n[1/7] 抓取基础数据...")
        for code, name in STOCKS.items():
            try:
                # 每日指标
                df = self.pro.daily_basic(ts_code=code, trade_date=self.trade_date)
                if len(df) > 0:
                    row = df.iloc[0]
                    pe = row.get('pe')
                    pb = row.get('pb')
                    mv = row.get('total_mv')  # 总市值（万元）
                    
                    # 基础信息
                    df2 = self.pro.stock_basic(ts_code=code)
                    industry = df2.iloc[0].get('industry', '') if len(df2) > 0 else ''
                    
                    self.data[code] = {
                        'name': name,
                        'pe': round(pe, 1) if pd.notna(pe) else None,
                        'pb': round(pb, 2) if pd.notna(pb) else None,
                        'mv': round(mv/10000, 1) if pd.notna(mv) else None,  # 转亿
                        'industry': industry,
                    }
            except Exception as e:
                print(f"  [WARN] {code} 基础数据: {e}")
                self.data[code] = {'name': name}
    
    def _fetch_finance(self):
        """财务数据：营收/净利润/负债率"""
        print("\n[2/7] 抓取财务数据...")
        for code in STOCKS.keys():
            try:
                # 利润表（最近一期）
                df_income = self.pro.income(ts_code=code, period='20251231')
                if len(df_income) > 0:
                    row = df_income.iloc[0]
                    revenue = row.get('total_revenue')
                    net_profit = row.get('n_income')
                    self.data[code]['revenue'] = round(revenue/100000000, 2) if pd.notna(revenue) else None
                    self.data[code]['net_profit'] = round(net_profit/100000000, 2) if pd.notna(net_profit) else None
                    self.data[code]['profit_status'] = '盈利' if net_profit and net_profit > 0 else '亏损'
                
                # 资产负债表
                df_bs = self.pro.balancesheet(ts_code=code, period='20251231')
                if len(df_bs) > 0:
                    row = df_bs.iloc[0]
                    total_assets = row.get('total_assets', 0)
                    total_liab = row.get('total_liab', 0)
                    if total_assets and total_assets > 0:
                        ratio = total_liab / total_assets * 100
                        self.data[code]['debt_ratio'] = round(ratio, 1)
                    else:
                        self.data[code]['debt_ratio'] = None
            except Exception as e:
                print(f"  [WARN] {code} 财务数据: {e}")
    
    def _fetch_margin(self):
        """融资融券"""
        print("\n[3/7] 抓取融资融券...")
        for code in STOCKS.keys():
            try:
                df = self.pro.margin_detail(ts_code=code, start_date=self.trade_date, end_date=self.trade_date)
                if len(df) > 0:
                    row = df.iloc[0]
                    self.data[code]['rz_ye'] = round(row.get('rzye', 0)/10000, 1) if pd.notna(row.get('rzye')) else None
                    self.data[code]['rq_ye'] = round(row.get('rqye', 0)/10000, 1) if pd.notna(row.get('rqye')) else None
                    self.data[code]['rz_jmr'] = round(row.get('rzjme', 0)/10000, 2) if pd.notna(row.get('rzjme')) else None
            except Exception as e:
                print(f"  [WARN] {code} 融资融券: {e}")
    
    def _fetch_pledge(self):
        """质押统计"""
        print("\n[4/7] 抓取质押数据...")
        for code in STOCKS.keys():
            try:
                df = self.pro.pledge_stat(ts_code=code)
                if len(df) > 0:
                    latest = df.sort_values('end_date', ascending=False).iloc[0]
                    pledge_count = latest.get('pledge_count', 0)
                    self.data[code]['pledge_count'] = int(pledge_count) if pd.notna(pledge_count) else 0
                else:
                    self.data[code]['pledge_count'] = 0
            except Exception as e:
                print(f"  [WARN] {code} 质押: {e}")
                self.data[code]['pledge_count'] = None
    
    def _fetch_company_actions(self):
        """回购、增减持、解禁"""
        print("\n[5/7] 抓取公司行为...")
        year_start = '20260101'
        for code in STOCKS.keys():
            # 回购
            try:
                df = self.pro.repurchase(ts_code=code, start_date=year_start)
                self.data[code]['repurchase'] = len(df)
            except:
                self.data[code]['repurchase'] = None
            
            # 增减持
            try:
                df = self.pro.stk_holdertrade(ts_code=code, start_date=year_start)
                self.data[code]['holder_trade'] = len(df)
            except:
                self.data[code]['holder_trade'] = None
            
            # 解禁（最近6个月）
            try:
                df = self.pro.share_float(ts_code=code)
                if len(df) > 0:
                    df['float_date'] = pd.to_datetime(df['float_date'])
                    future = df[df['float_date'] >= datetime.now()]
                    self.data[code]['float_count'] = len(future)
                    if len(future) > 0:
                        next_float = future.sort_values('float_date').iloc[0]
                        self.data[code]['next_float_date'] = next_float['float_date'].strftime('%Y-%m-%d')
                        self.data[code]['next_float_ratio'] = round(next_float.get('float_ratio', 0), 2)
                    else:
                        self.data[code]['next_float_date'] = None
                        self.data[code]['next_float_ratio'] = None
                else:
                    self.data[code]['float_count'] = 0
            except Exception as e:
                self.data[code]['float_count'] = None
    
    def _fetch_longhubang(self):
        """龙虎榜"""
        print("\n[6/7] 抓取龙虎榜...")
        try:
            df = self.pro.top_inst(trade_date=self.trade_date)
            if len(df) > 0:
                for code in STOCKS.keys():
                    count = len(df[df['ts_code'] == code])
                    self.data[code]['longhubang'] = count > 0
            else:
                for code in STOCKS.keys():
                    self.data[code]['longhubang'] = False
        except Exception as e:
            print(f"  [WARN] 龙虎榜: {e}")
            for code in STOCKS.keys():
                self.data[code]['longhubang'] = False
    
    def _check_st(self):
        """检查ST状态"""
        print("\n[7/7] 检查ST状态...")
        for code in STOCKS.keys():
            try:
                df = self.pro.stock_basic(ts_code=code)
                if len(df) > 0:
                    name = df.iloc[0].get('name', '')
                    self.data[code]['is_st'] = 'ST' in name or '*ST' in name
                    self.data[code]['current_name'] = name
            except:
                self.data[code]['is_st'] = False
    
    def _fetch_moneyflow(self):
        """资金流向（复用 moneyflow 逻辑）"""
        print("\n[8/8] 抓取资金流向...")
        for code in STOCKS.keys():
            try:
                df = self.pro.moneyflow(ts_code=code, start_date=self.trade_date, end_date=self.trade_date)
                if len(df) > 0:
                    row = df.iloc[0]
                    elg_net = row['buy_elg_amount'] - row['sell_elg_amount']
                    lg_net = row['buy_lg_amount'] - row['sell_lg_amount']
                    main_net = elg_net + lg_net
                    self.data[code]['main_net'] = main_net
                    self.data[code]['elg_net'] = elg_net
                    self.data[code]['lg_net'] = lg_net
                    self.data[code]['md_net'] = row['buy_md_amount'] - row['sell_md_amount']
                    self.data[code]['sm_net'] = row['buy_sm_amount'] - row['sell_sm_amount']
            except Exception as e:
                print(f"  [WARN] {code} 资金流向: {e}")

    def _fetch_cyb_moneyflow(self):
        """创业板抱团股资金流向"""
        print("\n[9/9] 抓取创业板抱团股资金流向...")
        self.cyb_data = {}
        for code, name in CYB_STOCKS.items():
            try:
                df = self.pro.moneyflow(ts_code=code, start_date=self.trade_date, end_date=self.trade_date)
                if len(df) > 0:
                    row = df.iloc[0]
                    elg_net = row['buy_elg_amount'] - row['sell_elg_amount']
                    lg_net = row['buy_lg_amount'] - row['sell_lg_amount']
                    main_net = elg_net + lg_net
                    self.cyb_data[code] = {
                        'name': name,
                        'tag': CYB_TAGS.get(code, ''),
                        'main_net': main_net,
                        'elg_net': elg_net,
                        'lg_net': lg_net,
                        'md_net': row['buy_md_amount'] - row['sell_md_amount'],
                        'sm_net': row['buy_sm_amount'] - row['sell_sm_amount'],
                    }
            except Exception as e:
                print(f"  [WARN] {code} {name}: {e}")
        
        # 统计
        out_count = sum(1 for d in self.cyb_data.values() if d['main_net'] < 0)
        in_count = len(self.cyb_data) - out_count
        total_out = sum(d['main_net'] for d in self.cyb_data.values() if d['main_net'] < 0)
        total_in = sum(d['main_net'] for d in self.cyb_data.values() if d['main_net'] >= 0)
        print(f"  汇总: {out_count}只流出({total_out/10000:.1f}亿) / {in_count}只流入(+{total_in/10000:.1f}亿)")

    def _check_hsgt(self):
        """检查沪港通"""
        print("  检查沪港通...")
        for code in STOCKS.keys():
            try:
                df = self.pro.hk_hold(ts_code=code, start_date=self.trade_date, end_date=self.trade_date)
                self.data[code]['is_hsgt'] = len(df) > 0
                if len(df) > 0:
                    row = df.iloc[0]
                    self.data[code]['hsgt_vol'] = round(row.get('vol', 0)/10000, 1)
                    self.data[code]['hsgt_ratio'] = round(row.get('ratio', 0), 2)
            except:
                self.data[code]['is_hsgt'] = False
                self.data[code]['hsgt_vol'] = None
                self.data[code]['hsgt_ratio'] = None
        """检查沪港通"""
        print("  检查沪港通...")
        for code in STOCKS.keys():
            try:
                df = self.pro.hk_hold(ts_code=code, start_date=self.trade_date, end_date=self.trade_date)
                self.data[code]['is_hsgt'] = len(df) > 0
                if len(df) > 0:
                    row = df.iloc[0]
                    self.data[code]['hsgt_vol'] = round(row.get('vol', 0)/10000, 1)
                    self.data[code]['hsgt_ratio'] = round(row.get('ratio', 0), 2)
            except:
                self.data[code]['is_hsgt'] = False
                self.data[code]['hsgt_vol'] = None
                self.data[code]['hsgt_ratio'] = None
    
    def print_summary(self):
        print("\n=== 数据摘要 ===")
        for code, d in self.data.items():
            st_mark = '⚠️ST' if d.get('is_st') else ''
            hsgt_mark = '🌐通' if d.get('is_hsgt') else ''
            lb_mark = '🐉龙' if d.get('longhubang') else ''
            profit = d.get('profit_status', '—')
            pe = d.get('pe') if d.get('pe') else '亏损'
            print(f"  {d['name']} {st_mark} {hsgt_mark} {lb_mark}: PE={pe} PB={d.get('pb','—')} 负债率={d.get('debt_ratio','—')}% 净利润={d.get('net_profit','—')}亿 {profit}")


def generate_finance_html(data):
    """生成财务透视 HTML"""
    def fmt(v, suffix=''):
        if v is None or pd.isna(v):
            return '—'
        return f"{v}{suffix}"
    
    rows = ""
    for code in STOCKS.keys():
        d = data.get(code, {})
        if not d:
            continue
        pe = d.get('pe')
        pe_str = f"{pe}" if pe else '<span style="color:#ef4444;">亏损</span>'
        pb = fmt(d.get('pb'))
        mv = fmt(d.get('mv'))
        debt = d.get('debt_ratio')
        debt_color = '#22c55e' if debt and debt < 50 else '#fbbf24' if debt and debt < 70 else '#ef4444'
        debt_str = f'<span style="color:{debt_color}">{fmt(debt)}%</span>'
        revenue = fmt(d.get('revenue'))
        profit = d.get('net_profit')
        profit_color = '#22c55e' if profit and profit > 0 else '#ef4444'
        profit_str = f'<span style="color:{profit_color}">{fmt(profit)}亿</span>'
        
        rows += f"""
      <tr>
        <td><strong>{d['name']}</strong><br><span style="font-size:11px;color:#64748b;">{code}</span></td>
        <td style="text-align:right;padding:10px 8px;">{pe_str}</td>
        <td style="text-align:right;padding:10px 8px;">{pb}</td>
        <td style="text-align:right;padding:10px 8px;">{mv}</td>
        <td style="text-align:right;padding:10px 8px;">{debt_str}</td>
        <td style="text-align:right;padding:10px 8px;">{revenue}</td>
        <td style="text-align:right;padding:10px 8px;">{profit_str}</td>
      </tr>"""
    
    return f"""    <!-- BEGIN_FINANCE -->
    <h3 style="color:#fbbf24;font-size:15px;margin:16px 0 10px;">🏦 财务透视（2025年报 · Tushare）</h3>
    <div style="overflow-x:auto;">
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <thead>
          <tr style="background:#1e293b;color:#94a3b8;font-size:12px;">
            <th style="padding:8px;text-align:left;border-bottom:1px solid #334155;">股票</th>
            <th style="padding:8px;text-align:right;border-bottom:1px solid #334155;">市盈率</th>
            <th style="padding:8px;text-align:right;border-bottom:1px solid #334155;">市净率</th>
            <th style="padding:8px;text-align:right;border-bottom:1px solid #334155;">总市值(亿)</th>
            <th style="padding:8px;text-align:right;border-bottom:1px solid #334155;">负债率</th>
            <th style="padding:8px;text-align:right;border-bottom:1px solid #334155;">营收(亿)</th>
            <th style="padding:8px;text-align:right;border-bottom:1px solid #334155;">净利润(亿)</th>
          </tr>
        </thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </div>
    <p style="color:#475569;font-size:11px;margin-top:8px;">数据来源：Tushare · PE=股价/每股收益 · 负债率=总负债/总资产 · 红色=亏损/高负债</p>
    <!-- END_FINANCE -->"""


def generate_margin_html(data):
    """生成融资融券 HTML"""
    def fmt(v, suffix=''):
        if v is None or pd.isna(v):
            return '—'
        return f"{v}{suffix}"
    
    rows = ""
    for code in STOCKS.keys():
        d = data.get(code, {})
        rz = d.get('rz_ye')
        rq = d.get('rq_ye')
        jmr = d.get('rz_jmr')
        
        rz_str = fmt(rz, '亿')
        rq_str = fmt(rq, '亿')
        jmr_color = '#ef4444' if jmr and jmr > 0 else '#22c55e' if jmr and jmr < 0 else '#94a3b8'
        jmr_str = f'<span style="color:{jmr_color}">{fmt(jmr, "亿")}</span>' if jmr else '—'
        
        rows += f"""
      <tr>
        <td><strong>{d.get('name','—')}</strong></td>
        <td style="text-align:right;padding:10px 8px;">{rz_str}</td>
        <td style="text-align:right;padding:10px 8px;">{rq_str}</td>
        <td style="text-align:right;padding:10px 8px;">{jmr_str}</td>
      </tr>"""
    
    return f"""    <!-- BEGIN_MARGIN -->
    <h3 style="color:#fbbf24;font-size:15px;margin:16px 0 10px;">📊 融资融券（{datetime.now().strftime('%Y-%m-%d')} · Tushare）</h3>
    <div style="overflow-x:auto;">
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <thead>
          <tr style="background:#1e293b;color:#94a3b8;font-size:12px;">
            <th style="padding:8px;text-align:left;border-bottom:1px solid #334155;">股票</th>
            <th style="padding:8px;text-align:right;border-bottom:1px solid #334155;">融资余额</th>
            <th style="padding:8px;text-align:right;border-bottom:1px solid #334155;">融券余额</th>
            <th style="padding:8px;text-align:right;border-bottom:1px solid #334155;">融资净买入</th>
          </tr>
        </thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </div>
    <p style="color:#475569;font-size:11px;margin-top:8px;">数据来源：Tushare · 融资余额=杠杆资金看多规模 · 融券余额=做空规模</p>
    <!-- END_MARGIN -->"""


def generate_actions_html(data):
    """生成公司行为监控 HTML"""
    rows = ""
    for code in STOCKS.keys():
        d = data.get(code, {})
        
        # 质押
        pledge = d.get('pledge_count', 0)
        pledge_str = f'<span style="color:#ef4444;">{pledge}笔</span>' if pledge else '<span style="color:#22c55e;">无</span>'
        
        # 回购
        repurchase = d.get('repurchase', 0)
        repurchase_str = f'{repurchase}笔' if repurchase else '—'
        
        # 增减持
        holder = d.get('holder_trade', 0)
        holder_str = f'{holder}笔' if holder else '—'
        
        # 解禁
        float_count = d.get('float_count', 0)
        if float_count and float_count > 0:
            next_date = d.get('next_float_date', '')
            next_ratio = d.get('next_float_ratio', 0)
            float_str = f'<span style="color:#ef4444;">{float_count}笔 最近{next_date} {next_ratio}%</span>'
        else:
            float_str = '<span style="color:#22c55e;">近期无</span>'
        
        # 沪港通
        hsgt = d.get('is_hsgt', False)
        hsgt_vol = d.get('hsgt_vol')
        hsgt_ratio = d.get('hsgt_ratio')
        if hsgt and hsgt_vol:
            hsgt_str = f'<span style="color:#22c55e;">✅ 北向{hsgt_vol}万股 ({hsgt_ratio}%)</span>'
        elif hsgt:
            hsgt_str = '<span style="color:#22c55e;">✅ 纳入</span>'
        else:
            hsgt_str = '<span style="color:#64748b;">❌ 未纳入</span>'
        
        # ST
        st = d.get('is_st', False)
        st_str = '<span style="color:#ef4444;font-weight:700;">⚠️ ST</span>' if st else '<span style="color:#22c55e;">正常</span>'
        
        rows += f"""
      <tr>
        <td><strong>{d.get('name','—')}</strong></td>
        <td style="text-align:center;padding:10px 8px;">{st_str}</td>
        <td style="text-align:center;padding:10px 8px;">{pledge_str}</td>
        <td style="text-align:center;padding:10px 8px;">{repurchase_str}</td>
        <td style="text-align:center;padding:10px 8px;">{holder_str}</td>
        <td style="text-align:center;padding:10px 8px;">{float_str}</td>
        <td style="text-align:center;padding:10px 8px;">{hsgt_str}</td>
      </tr>"""
    
    return f"""    <!-- BEGIN_ACTIONS -->
    <h3 style="color:#fbbf24;font-size:15px;margin:16px 0 10px;">🏛️ 公司行为 & 特殊状态（Tushare）</h3>
    <div style="overflow-x:auto;">
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <thead>
          <tr style="background:#1e293b;color:#94a3b8;font-size:12px;">
            <th style="padding:8px;text-align:left;border-bottom:1px solid #334155;">股票</th>
            <th style="padding:8px;text-align:center;border-bottom:1px solid #334155;">ST状态</th>
            <th style="padding:8px;text-align:center;border-bottom:1px solid #334155;">股权质押</th>
            <th style="padding:8px;text-align:center;border-bottom:1px solid #334155;">回购</th>
            <th style="padding:8px;text-align:center;border-bottom:1px solid #334155;">增减持</th>
            <th style="padding:8px;text-align:center;border-bottom:1px solid #334155;">限售解禁</th>
            <th style="padding:8px;text-align:center;border-bottom:1px solid #334155;">沪港通</th>
          </tr>
        </thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </div>
    <p style="color:#475569;font-size:11px;margin-top:8px;">数据来源：Tushare · ST=特别处理 · 质押=大股东股权质押笔数 · 解禁=限售股解禁</p>
    <!-- END_ACTIONS -->"""


def generate_longhubang_html(data, trade_date):
    """生成龙虎榜 HTML"""
    lb_stocks = [code for code in STOCKS.keys() if data.get(code, {}).get('longhubang')]
    
    if not lb_stocks:
        return f"""    <!-- BEGIN_LHB -->
    <h3 style="color:#fbbf24;font-size:15px;margin:16px 0 10px;">🐉 龙虎榜异动（{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}</h3>
    <p style="color:#64748b;font-size:13px;padding:12px;background:#0f172a;border-radius:8px;">
      📭 今日持仓股无龙虎榜记录
    </p>
    <!-- END_LHB -->"""
    
    rows = ""
    for code in lb_stocks:
        d = data.get(code, {})
        rows += f"""
      <tr>
        <td><strong>{d.get('name','—')}</strong><br><span style="font-size:11px;color:#64748b;">{code}</span></td>
        <td style="text-align:center;padding:10px 8px;"><span style="color:#ef4444;font-weight:700;">🔥 上榜</span></td>
      </tr>"""
    
    return f"""    <!-- BEGIN_LHB -->
    <h3 style="color:#fbbf24;font-size:15px;margin:16px 0 10px;">🐉 龙虎榜异动（{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}</h3>
    <div style="overflow-x:auto;">
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <thead>
          <tr style="background:#1e293b;color:#94a3b8;font-size:12px;">
            <th style="padding:8px;text-align:left;border-bottom:1px solid #334155;">股票</th>
            <th style="padding:8px;text-align:center;border-bottom:1px solid #334155;">状态</th>
          </tr>
        </thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </div>
    <p style="color:#475569;font-size:11px;margin-top:8px;">数据来源：Tushare · 龙虎榜=当日涨跌幅/换手率/振幅达到交易所披露标准的个股</p>
    <!-- END_LHB -->"""


def generate_cyb_html(cyb_data, trade_date):
    """生成创业板抱团股 HTML"""
    def fmt_yi(v):
        if v is None or pd.isna(v):
            return '—'
        return f"{v/10000:+.2f}亿"
    
    rows = ""
    for code in CYB_STOCKS.keys():
        d = cyb_data.get(code, {})
        if not d:
            continue
        
        main_net = d.get('main_net', 0)
        main_color = '#ef4444' if main_net >= 0 else '#22c55e'
        main_bg = '#4a0d0d' if main_net >= 0 else '#0d4a1a'
        main_sign = '流入' if main_net >= 0 else '流出'
        
        elg_color = '#ef4444' if d.get('elg_net', 0) >= 0 else '#22c55e'
        lg_color = '#ef4444' if d.get('lg_net', 0) >= 0 else '#22c55e'
        md_color = '#ef4444' if d.get('md_net', 0) >= 0 else '#22c55e'
        sm_color = '#ef4444' if d.get('sm_net', 0) >= 0 else '#22c55e'
        
        # 轮动信号
        if main_net < -50000:
            signal = '🔥 警报'; signal_color = '#ef4444'
        elif main_net < -10000:
            signal = '⚠️ 关注'; signal_color = '#fbbf24'
        elif main_net > 50000:
            signal = '✅ 强势'; signal_color = '#22c55e'
        else:
            signal = '➖ 中性'; signal_color = '#94a3b8'
        
        rows += f"""
      <tr>
        <td><strong>{d.get('name','—')}</strong><br><span style="font-size:11px;color:#64748b;">{code} · {d.get('tag','')}</span></td>
        <td style="color:{main_color};font-weight:700;text-align:right;padding:10px 8px;">{fmt_yi(main_net)}</td>
        <td style="color:{elg_color};text-align:right;padding:10px 8px;">{fmt_yi(d.get('elg_net'))}</td>
        <td style="color:{lg_color};text-align:right;padding:10px 8px;">{fmt_yi(d.get('lg_net'))}</td>
        <td style="color:{md_color};text-align:right;padding:10px 8px;">{fmt_yi(d.get('md_net'))}</td>
        <td style="color:{sm_color};text-align:right;padding:10px 8px;">{fmt_yi(d.get('sm_net'))}</td>
        <td style="text-align:center;padding:10px 8px;"><span style="display:inline-block;padding:3px 10px;border-radius:4px;font-size:12px;font-weight:600;background:{main_bg};color:{main_color};">{main_sign}</span></td>
        <td style="text-align:center;padding:10px 8px;"><span style="color:{signal_color};font-weight:700;">{signal}</span></td>
      </tr>"""
    
    # 汇总统计
    out_count = sum(1 for d in cyb_data.values() if d.get('main_net', 0) < 0)
    in_count = len(cyb_data) - out_count
    total_out = sum(d.get('main_net', 0) for d in cyb_data.values() if d.get('main_net', 0) < 0)
    total_in = sum(d.get('main_net', 0) for d in cyb_data.values() if d.get('main_net', 0) >= 0)
    max_out = min((d.get('main_net', 0) for d in cyb_data.values()), default=0)
    max_in = max((d.get('main_net', 0) for d in cyb_data.values()), default=0)
    max_out_name = next((d['name'] for d in cyb_data.values() if d.get('main_net', 0) == max_out), '')
    max_in_name = next((d['name'] for d in cyb_data.values() if d.get('main_net', 0) == max_in), '')
    date_str = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"
    
    return f"""    
    <!-- BEGIN_CYB -->
    <h3 style="color:#fbbf24;font-size:15px;margin:16px 0 10px;">🔥 创业板抱团股资金监控（399006 · Tushare）</h3>
    <p style="color:#94a3b8;font-size:13px;margin-bottom:12px;">创业板"七姐妹"+前十大权重 · 资金一旦流出抱团股 → 板块轮动信号 ⚡</p>
    <div style="overflow-x:auto;">
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <thead>
          <tr style="background:#1e293b;color:#94a3b8;font-size:12px;">
            <th style="padding:8px;text-align:left;border-bottom:1px solid #334155;">股票</th>
            <th style="padding:8px;text-align:right;border-bottom:1px solid #334155;">主力净流入</th>
            <th style="padding:8px;text-align:right;border-bottom:1px solid #334155;">超大单</th>
            <th style="padding:8px;text-align:right;border-bottom:1px solid #334155;">大单</th>
            <th style="padding:8px;text-align:right;border-bottom:1px solid #334155;">中单</th>
            <th style="padding:8px;text-align:right;border-bottom:1px solid #334155;">小单</th>
            <th style="padding:8px;text-align:center;border-bottom:1px solid #334155;">方向</th>
            <th style="padding:8px;text-align:center;border-bottom:1px solid #334155;">轮动信号</th>
          </tr>
        </thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </div>
    <div style="background:#0f172a;padding:14px;border-radius:10px;margin-top:14px;">
      <div style="color:#c4b5fd;font-size:14px;font-weight:700;margin-bottom:8px;">🔄 板块轮动信号分析（{date_str}）</div>
      <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-top:8px;">
        <div style="background:rgba(15,23,42,0.7);padding:12px;border-radius:10px;text-align:center;border:1px solid #1e293b;border-left:3px solid #ef4444;">
          <div style="color:#64748b;font-size:11px;">🔥 抱团松动</div>
          <div style="font-size:16px;font-weight:700;color:#e2e8f0;">{out_count}/10 流出</div>
          <div style="color:#475569;font-size:11px;">合计流出 {total_out/10000:.1f}亿</div>
        </div>
        <div style="background:rgba(15,23,42,0.7);padding:12px;border-radius:10px;text-align:center;border:1px solid #1e293b;border-left:3px solid #22c55e;">
          <div style="color:#64748b;font-size:11px;">✅ 资金流入</div>
          <div style="font-size:16px;font-weight:700;color:#e2e8f0;">{in_count}/10 流入</div>
          <div style="color:#475569;font-size:11px;">合计流入 +{total_in/10000:.1f}亿</div>
        </div>
        <div style="background:rgba(15,23,42,0.7);padding:12px;border-radius:10px;text-align:center;border:1px solid #1e293b;border-left:3px solid #ef4444;">
          <div style="color:#64748b;font-size:11px;">🔥 最大流出</div>
          <div style="font-size:14px;font-weight:700;color:#e2e8f0;">{max_out_name}</div>
          <div style="color:#475569;font-size:11px;">{max_out/10000:.1f}亿</div>
        </div>
        <div style="background:rgba(15,23,42,0.7);padding:12px;border-radius:10px;text-align:center;border:1px solid #1e293b;border-left:3px solid #22c55e;">
          <div style="color:#64748b;font-size:11px;">✅ 最大流入</div>
          <div style="font-size:14px;font-weight:700;color:#e2e8f0;">{max_in_name}</div>
          <div style="color:#475569;font-size:11px;">+{max_in/10000:.1f}亿</div>
        </div>
      </div>
      <p style="color:#94a3b8;font-size:12px;margin-top:10px;line-height:1.6;">
        💡 <strong style="color:#fbbf24;">轮动逻辑</strong>：创业板10大权重中{out_count}只主力净流出（合计{total_out/10000:.1f}亿），资金正在撤离新能源/光模块抱团股。若节后持续流出 → 资金可能转向<strong style="color:#ef4444;">主板蓝筹、周期、医药</strong>等防御板块。建议节后关注：① 长江电力/招商银行是否获资金流入 ② 主板是否放量补涨。
      </p>
    </div>
    <p style="color:#475569;font-size:11px;margin-top:8px;">数据来源：Tushare · 主力=超大单+大单 · 轮动信号基于主力资金流向判断 · 不构成投资建议</p>
    <!-- END_CYB -->
"""


def update_html(html_path, data, cyb_data, trade_date):
    """更新 HTML 文件"""
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 财务透视
    finance_html = generate_finance_html(data)
    content = replace_section(content, 'BEGIN_FINANCE', 'END_FINANCE', finance_html)
    
    # 2. 融资融券
    margin_html = generate_margin_html(data)
    content = replace_section(content, 'BEGIN_MARGIN', 'END_MARGIN', margin_html)
    
    # 3. 公司行为
    actions_html = generate_actions_html(data)
    content = replace_section(content, 'BEGIN_ACTIONS', 'END_ACTIONS', actions_html)
    
    # 4. 龙虎榜
    lhb_html = generate_longhubang_html(data, trade_date)
    content = replace_section(content, 'BEGIN_LHB', 'END_LHB', lhb_html)
    
    # 5. 创业板抱团股
    cyb_html = generate_cyb_html(cyb_data, trade_date)
    content = replace_section(content, 'BEGIN_CYB', 'END_CYB', cyb_html)
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True


def replace_section(content, begin_marker, end_marker, new_html):
    """替换或插入标记区域"""
    begin = f'<!-- {begin_marker} -->'
    end = f'<!-- {end_marker} -->'
    
    if begin in content and end in content:
        # 替换已有区域
        pattern = re.escape(begin) + '.*?' + re.escape(end)
        content = re.sub(pattern, new_html, content, flags=re.DOTALL)
    else:
        # 在资金流向模块之前插入
        insert_before = '<!-- BEGIN_MONEYFLOW -->'
        if insert_before in content:
            content = content.replace(insert_before, new_html + '\n\n    ' + insert_before)
        else:
            # 最后手段：在footer前插入
            footer = '<!-- ==================== Footer ==================== -->'
            if footer in content:
                content = content.replace(footer, new_html + '\n\n  ' + footer)
    
    return content


def sync_to_icloud():
    import shutil
    try:
        shutil.copy2(HTML_PATH, ICLOUD_PATH)
        print(f"[OK] 已同步到 iCloud")
        return True
    except Exception as e:
        print(f"[WARN] iCloud 同步失败: {e}")
        return False


def main():
    print(f"=== Tushare 综合数据更新 ===")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    collector = TushareDataCollector()
    collector.fetch_all()
    collector.print_summary()
    
    # 更新 HTML
    if update_html(HTML_PATH, collector.data, collector.cyb_data, collector.trade_date):
        sync_to_icloud()
        print(f"\n[OK] 更新完成!")
    else:
        print(f"\n[ERR] 更新失败")


if __name__ == '__main__':
    main()
