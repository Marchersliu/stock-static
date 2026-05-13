#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五朵金花技术分析报告生成器
数据源：腾讯财经K线接口（前复权）
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime

# ============ 配置 ============
STOCKS = {
    '002364.SZ': {'name': '中恒电气', 'tencent': 'sz002364'},
    '002484.SZ': {'name': '江海股份', 'tencent': 'sz002484'},
    '688485.SH': {'name': '九州一轨', 'tencent': 'sh688485'},
    '002439.SZ': {'name': '启明星辰', 'tencent': 'sz002439'},
    '002158.SZ': {'name': '汉钟精机', 'tencent': 'sz002158'},
}

HOLDINGS = {
    '688485.SH': {'shares': 19569, 'cost': 44.0},
    '002158.SZ': {'shares': 13100, 'cost': 31.8},
}

TARGETS = {
    '688485.SH': {'target': [60, 65], 'stop': 49},
}


def get_tencent_klines(tencent_code, days=120):
    """从腾讯接口获取前复权日K线"""
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={tencent_code},day,,,{days},qfq"
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        klines = data.get('data', {}).get(tencent_code, {}).get('qfqday', [])
        if not klines:
            return pd.DataFrame()
        df = pd.DataFrame(klines, columns=['trade_date', 'open', 'close', 'high', 'low', 'vol'])
        for col in ['open', 'close', 'high', 'low', 'vol']:
            df[col] = df[col].astype(float)
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df = df.sort_values('trade_date').reset_index(drop=True)
        df['pre_close'] = df['close'].shift(1)
        df['change'] = df['close'] - df['pre_close']
        df['pct_chg'] = df['change'] / df['pre_close'] * 100
        return df
    except Exception as e:
        print(f"  获取{tencent_code}失败: {e}")
        return pd.DataFrame()


def compute_td_setup(df):
    n = len(df)
    buy_count = np.zeros(n, dtype=int)
    sell_count = np.zeros(n, dtype=int)
    td_buy_9 = np.zeros(n, dtype=bool)
    td_sell_9 = np.zeros(n, dtype=bool)
    td_buy_perfect9 = np.zeros(n, dtype=bool)
    td_sell_perfect9 = np.zeros(n, dtype=bool)

    close = df['close'].values
    high = df['high'].values
    low = df['low'].values

    for i in range(n):
        if i >= 4:
            if close[i] < close[i-4]:
                buy_count[i] = buy_count[i-1] + 1 if i > 0 else 1
            else:
                buy_count[i] = 0
            if close[i] > close[i-4]:
                sell_count[i] = sell_count[i-1] + 1 if i > 0 else 1
            else:
                sell_count[i] = 0
        else:
            buy_count[i] = 0
            sell_count[i] = 0

        if buy_count[i] == 9:
            td_buy_9[i] = True
            if i >= 7:
                cond = (low[i-1] < min(low[i-3], low[i-2])) or (low[i] < min(low[i-3], low[i-2]))
                td_buy_perfect9[i] = bool(cond)
        if sell_count[i] == 9:
            td_sell_9[i] = True
            if i >= 7:
                cond = (high[i-1] > max(high[i-3], high[i-2])) or (high[i] > max(high[i-3], high[i-2]))
                td_sell_perfect9[i] = bool(cond)

    df['td_buy_count'] = buy_count
    df['td_sell_count'] = sell_count
    df['td_buy_9'] = td_buy_9
    df['td_sell_9'] = td_sell_9
    df['td_buy_perfect9'] = td_buy_perfect9
    df['td_sell_perfect9'] = td_sell_perfect9
    return df


def compute_macd(df):
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd_dif'] = exp1 - exp2
    df['macd_dea'] = df['macd_dif'].ewm(span=9, adjust=False).mean()
    df['macd_bar'] = 2 * (df['macd_dif'] - df['macd_dea'])
    return df


def compute_rsi(df, period=14):
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    df['rsi_14'] = 100 - (100 / (1 + rs))
    return df


def compute_ma(df):
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma10'] = df['close'].rolling(window=10).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['ma60'] = df['close'].rolling(window=60).mean()
    return df


def compute_bollinger(df, period=20, std_dev=2):
    df['boll_mid'] = df['close'].rolling(window=period).mean()
    df['boll_std'] = df['close'].rolling(window=period).std()
    df['boll_up'] = df['boll_mid'] + std_dev * df['boll_std']
    df['boll_down'] = df['boll_mid'] - std_dev * df['boll_std']
    return df


def compute_volume_analysis(df):
    df['vol_ma5'] = df['vol'].rolling(window=5).mean()
    df['vol_ma20'] = df['vol'].rolling(window=20).mean()
    return df


def analyze_stock(ts_code, name, tencent_code):
    df = get_tencent_klines(tencent_code, days=120)
    if df.empty or len(df) < 60:
        return None

    df = compute_td_setup(df)
    df = compute_macd(df)
    df = compute_rsi(df)
    df = compute_ma(df)
    df = compute_bollinger(df)
    df = compute_volume_analysis(df)

    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    latest_date = latest['trade_date'].strftime('%Y-%m-%d')

    # TD序列
    td_buy = latest['td_buy_count']
    td_sell = latest['td_sell_count']
    if td_buy >= 9:
        td_state = f"底部九转延续中：{int(td_buy)}（已低9）"
    elif td_sell >= 9:
        td_state = f"顶部九转延续中：{int(td_sell)}（已高9）"
    elif td_buy > 0:
        td_state = f"下跌九转计数中：{int(td_buy)}"
    elif td_sell > 0:
        td_state = f"上涨九转计数中：{int(td_sell)}"
    else:
        td_state = "无九转信号"

    recent_buy9 = df['td_buy_9'].iloc[-10:].any()
    recent_sell9 = df['td_sell_9'].iloc[-10:].any()
    if recent_buy9 and not latest['td_buy_9']:
        td_state += "（近期出现低9，已重置）"
    elif recent_sell9 and not latest['td_sell_9']:
        td_state += "（近期出现高9，已重置）"

    # MACD
    dif = latest['macd_dif']
    dea = latest['macd_dea']
    bar = latest['macd_bar']
    if prev['macd_dif'] < prev['macd_dea'] and dif > dea:
        macd_cross = "刚刚金叉"
    elif prev['macd_dif'] > prev['macd_dea'] and dif < dea:
        macd_cross = "刚刚死叉"
    elif dif > dea:
        macd_cross = "金叉状态"
    else:
        macd_cross = "死叉状态"

    if bar > prev['macd_bar'] and bar > 0:
        macd_trend = "红柱放大"
    elif abs(bar) > abs(prev['macd_bar']) and bar < 0:
        macd_trend = "绿柱放大"
    elif bar > 0:
        macd_trend = "红柱缩小"
    else:
        macd_trend = "绿柱缩小"

    # RSI
    rsi = latest['rsi_14']
    if rsi > 70:
        rsi_state = "超买区"
    elif rsi < 30:
        rsi_state = "超卖区"
    elif rsi > 50:
        rsi_state = "强势区"
    else:
        rsi_state = "弱势区"

    # 成交量
    vol = latest['vol']
    vol_ma5 = latest['vol_ma5']
    vol_ma20 = latest['vol_ma20']
    vol_vs_5d = vol / vol_ma5 if vol_ma5 > 0 else 1
    vol_vs_20d = vol / vol_ma20 if vol_ma20 > 0 else 1
    vol_trend = "放量" if vol_vs_5d > 1.2 else ("缩量" if vol_vs_5d < 0.8 else "平量")

    # 均线
    price = latest['close']
    ma5 = latest['ma5']
    ma10 = latest['ma10']
    ma20 = latest['ma20']
    ma60 = latest['ma60']
    ma_position = []
    if price > ma5: ma_position.append("站上5日线")
    else: ma_position.append("跌破5日线")
    if price > ma10: ma_position.append("站上10日线")
    else: ma_position.append("跌破10日线")
    if price > ma20: ma_position.append("站上20日线")
    else: ma_position.append("跌破20日线")
    if price > ma60: ma_position.append("站上60日线")
    else: ma_position.append("跌破60日线")

    if ma5 > ma10 > ma20 > ma60:
        ma_arrange = "多头排列"
    elif ma5 < ma10 < ma20 < ma60:
        ma_arrange = "空头排列"
    else:
        ma_arrange = "纠缠状态"

    supports = []
    resistances = []
    if price > ma5: supports.append(f"5日线 {ma5:.2f}")
    else: resistances.append(f"5日线 {ma5:.2f}")
    if price > ma10: supports.append(f"10日线 {ma10:.2f}")
    else: resistances.append(f"10日线 {ma10:.2f}")
    if price > ma20: supports.append(f"20日线 {ma20:.2f}")
    else: resistances.append(f"20日线 {ma20:.2f}")
    if price > ma60: supports.append(f"60日线 {ma60:.2f}")
    else: resistances.append(f"60日线 {ma60:.2f}")

    # 布林带
    boll_up = latest['boll_up']
    boll_mid = latest['boll_mid']
    boll_down = latest['boll_down']
    boll_width = (boll_up - boll_down) / boll_mid * 100 if boll_mid > 0 else 0
    if price > boll_up:
        boll_pos = "突破上轨（超买）"
    elif price > boll_mid:
        boll_pos = "上轨与中轨之间（强势区）"
    elif price > boll_down:
        boll_pos = "中轨与下轨之间（弱势区）"
    else:
        boll_pos = "跌破下轨（超卖）"

    # 综合评分
    score = 50
    if latest['td_buy_9']:
        score += 15
    elif td_buy > 0 and td_buy < 9:
        score += td_buy
    if latest['td_sell_9']:
        score -= 15
    elif td_sell > 0 and td_sell < 9:
        score -= td_sell
    if dif > dea and bar > 0:
        score += 10
    elif dif > dea:
        score += 5
    elif dif < dea and bar < 0:
        score -= 10
    else:
        score -= 5
    if rsi < 30:
        score += 10
    elif rsi > 70:
        score -= 10
    elif rsi > 50:
        score += 3
    else:
        score -= 3
    if ma_arrange == "多头排列":
        score += 10
    elif ma_arrange == "空头排列":
        score -= 10
    if price < boll_down:
        score += 5
    elif price > boll_up:
        score -= 5
    if vol_vs_5d > 1.2 and price > prev['close']:
        score += 5
    elif vol_vs_5d > 1.2 and price < prev['close']:
        score -= 5

    score = max(0, min(100, score))
    if score >= 60:
        rating = "看多"
    elif score <= 40:
        rating = "看空"
    else:
        rating = "中性"

    if rating == "看多":
        if latest['td_buy_9']:
            action = "买入/加仓（低9完成，反弹概率高）"
        elif rsi < 40:
            action = "逢低买入"
        else:
            action = "持有/适量买入"
    elif rating == "看空":
        if latest['td_sell_9']:
            action = "减仓/卖出（高9完成，回调风险大）"
        else:
            action = "减仓/观望"
    else:
        action = "观望（等待方向明朗）"

    return {
        'code': ts_code, 'name': name, 'date': latest_date,
        'price': price, 'pre_close': latest['pre_close'], 'change_pct': latest['pct_chg'],
        'td_state': td_state, 'td_buy_count': int(td_buy), 'td_sell_count': int(td_sell),
        'macd_dif': dif, 'macd_dea': dea, 'macd_bar': bar,
        'macd_cross': macd_cross, 'macd_trend': macd_trend,
        'rsi': rsi, 'rsi_state': rsi_state,
        'vol': vol, 'vol_vs_5d': vol_vs_5d, 'vol_vs_20d': vol_vs_20d, 'vol_trend': vol_trend,
        'ma5': ma5, 'ma10': ma10, 'ma20': ma20, 'ma60': ma60,
        'ma_position': ma_position, 'ma_arrange': ma_arrange,
        'supports': supports, 'resistances': resistances,
        'boll_up': boll_up, 'boll_mid': boll_mid, 'boll_down': boll_down,
        'boll_pos': boll_pos, 'boll_width': boll_width,
        'score': score, 'rating': rating, 'action': action,
    }


def generate_markdown():
    report_lines = []
    report_lines.append("# 五朵金花综合技术分析报告")
    report_lines.append(f"\n**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report_lines.append("**数据来源：** 腾讯财经 前复权日线")
    report_lines.append("**分析指标：** 神奇九转序列 + MACD + RSI(14) + 成交量 + 均线(5/10/20/60) + 布林带")
    report_lines.append("\n---\n")

    all_results = []
    for code, info in STOCKS.items():
        print(f"分析中：{info['name']} ({code})...")
        res = analyze_stock(code, info['name'], info['tencent'])
        if res:
            all_results.append(res)
        else:
            print(f"  ⚠️ {info['name']} 数据获取失败")

    for r in all_results:
        report_lines.append(f"## {r['name']}（{r['code']}）")
        report_lines.append(f"\n**最新价：** {r['price']:.2f}  |  **涨跌：** {r['change_pct']:+.2f}%  |  **数据日期：** {r['date']}")
        report_lines.append(f"\n### 一、神奇九转序列（TD Sequential）")
        report_lines.append(f"- **当前状态：** {r['td_state']}")
        if r['td_buy_count'] > 0 and r['td_buy_count'] < 9:
            report_lines.append(f"- 下跌九转进度：{r['td_buy_count']}/9")
        if r['td_sell_count'] > 0 and r['td_sell_count'] < 9:
            report_lines.append(f"- 上涨九转进度：{r['td_sell_count']}/9")
        report_lines.append(f"\n### 二、MACD")
        report_lines.append(f"- **DIF：** {r['macd_dif']:.3f}")
        report_lines.append(f"- **DEA：** {r['macd_dea']:.3f}")
        report_lines.append(f"- **柱状体：** {r['macd_bar']:.3f}（{r['macd_trend']}）")
        report_lines.append(f"- **状态：** {r['macd_cross']}")
        report_lines.append(f"\n### 三、RSI（14日）")
        report_lines.append(f"- **RSI值：** {r['rsi']:.2f}")
        report_lines.append(f"- **区域：** {r['rsi_state']}")
        report_lines.append(f"\n### 四、成交量")
        report_lines.append(f"- **当日成交量：** {r['vol']:,.0f} 手")
        report_lines.append(f"- **5日均量：** {r['vol']/r['vol_vs_5d']:,.0f} 手")
        report_lines.append(f"- **量比（vs 5日）：** {r['vol_vs_5d']:.2f}x")
        report_lines.append(f"- **量比（vs 20日）：** {r['vol_vs_20d']:.2f}x")
        report_lines.append(f"- **趋势判断：** {r['vol_trend']}")
        report_lines.append(f"\n### 五、均线位置（5/10/20/60日线）")
        report_lines.append(f"- **5日线：** {r['ma5']:.2f}")
        report_lines.append(f"- **10日线：** {r['ma10']:.2f}")
        report_lines.append(f"- **20日线：** {r['ma20']:.2f}")
        report_lines.append(f"- **60日线：** {r['ma60']:.2f}")
        report_lines.append(f"- **位置关系：** {' / '.join(r['ma_position'])}")
        report_lines.append(f"- **排列形态：** {r['ma_arrange']}")
        report_lines.append(f"\n### 六、布林带（20日, 2σ）")
        report_lines.append(f"- **上轨：** {r['boll_up']:.2f}")
        report_lines.append(f"- **中轨：** {r['boll_mid']:.2f}")
        report_lines.append(f"- **下轨：** {r['boll_down']:.2f}")
        report_lines.append(f"- **当前位置：** {r['boll_pos']}")
        report_lines.append(f"- **带宽：** {r['boll_width']:.2f}%")
        report_lines.append(f"\n### 七、关键支撑与阻力位")
        if r['supports']:
            report_lines.append(f"- **支撑位：** {' > '.join(r['supports'])}")
        else:
            report_lines.append(f"- **支撑位：** 暂无（价格位于所有均线下方）")
        if r['resistances']:
            report_lines.append(f"- **阻力位：** {' < '.join(r['resistances'])}")
        else:
            report_lines.append(f"- **阻力位：** 暂无（价格位于所有均线上方）")
        report_lines.append(f"\n### 八、综合评级")
        report_lines.append(f"- **技术评分：** {r['score']:.0f}/100")
        report_lines.append(f"- **评级：** {'🟢' if r['rating']=='看多' else ('🔴' if r['rating']=='看空' else '⚪')} **{r['rating']}**")
        report_lines.append(f"- **操作建议：** {r['action']}")

        if r['code'] in HOLDINGS:
            h = HOLDINGS[r['code']]
            profit_pct = (r['price'] - h['cost']) / h['cost'] * 100
            report_lines.append(f"\n### 📌 持仓特别提醒")
            report_lines.append(f"- **持仓：** {h['shares']:,}股  |  **成本：** {h['cost']:.2f}")
            report_lines.append(f"- **当前盈亏：** {profit_pct:+.2f}%")
            if r['code'] in TARGETS:
                t = TARGETS[r['code']]
                report_lines.append(f"- **目标价：** {'/'.join(map(str, t['target']))}  |  **止损：** {t['stop']}")
                if r['price'] >= min(t['target']):
                    report_lines.append(f"- ⚠️ **已触及目标价区间，建议分批减仓兑现利润**")
                elif r['price'] <= t['stop']:
                    report_lines.append(f"- 🚨 **已跌破止损线，建议严格执行止损**")

            if r['code'] == '688485.SH':
                report_lines.append(f"\n> **九州一轨专项分析：**")
                report_lines.append(f"> - 成本44，现价{r['price']:.2f}，浮盈约 **{profit_pct:.1f}%**")
                if r['td_sell_count'] >= 9:
                    report_lines.append(f"> - ⚠️ 顶部九转延续中（计数{r['td_sell_count']}），高9已完成，短期回调风险加大")
                elif r['td_sell_count'] >= 6:
                    report_lines.append(f"> - ⚠️ 上涨九转计数已达 **{r['td_sell_count']}**，接近高9，短期回调风险加大")
                if r['rsi'] > 65:
                    report_lines.append(f"> - ⚠️ RSI进入{r['rsi_state']}，动能可能衰竭")
                if r['price'] > r['boll_up']:
                    report_lines.append(f"> - ⚠️ 价格突破布林上轨，短期过热")
                if profit_pct > 40:
                    report_lines.append(f"> - 💡 **建议：已大幅盈利，可考虑分批减仓锁定利润。若MACD死叉，减仓信号更强。**")
                else:
                    report_lines.append(f"> - 💡 **建议：继续持有，关注高9和MACD变化。**")

            elif r['code'] == '002158.SZ':
                report_lines.append(f"\n> **汉钟精机专项分析：**")
                report_lines.append(f"> - 成本31.8，现价{r['price']:.2f}，浮亏约 **{profit_pct:.2f}%**")
                if r['td_buy_count'] >= 6:
                    report_lines.append(f"> - 📌 下跌九转计数已达 **{r['td_buy_count']}**，接近低9，可能接近短期底部")
                if r['rsi'] < 35:
                    report_lines.append(f"> - 📌 RSI处于{r['rsi_state']}，超卖反弹概率存在")
                if r['price'] < r['boll_down']:
                    report_lines.append(f"> - 📌 价格跌破布林下轨，技术性反弹需求")
                if r['rating'] == '看多' or r['td_buy_count'] >= 7:
                    report_lines.append(f"> - 💡 **建议：技术面显示接近底部区域，若低9完成且MACD金叉，可考虑补仓摊低成本。当前亏损较小，也可观望等待更明确信号。**")
                elif r['rating'] == '看空':
                    report_lines.append(f"> - 🚨 **建议：技术面偏弱，若继续下跌建议严格止损，避免深套。**")
                else:
                    report_lines.append(f"> - 💡 **建议：技术面中性，持仓观望，等待低9或MACD金叉确认。**")

        report_lines.append("\n---\n")

    report_lines.append("## 📊 五朵金花技术状态汇总对比")
    report_lines.append("")
    report_lines.append("| 股票 | 现价 | 日涨跌 | TD序列 | MACD | RSI | 均线排列 | 布林带 | 评级 | 操作建议 |")
    report_lines.append("|------|------|--------|--------|------|-----|----------|--------|------|----------|")
    for r in all_results:
        td_short = r['td_state'].replace("下跌九转计数中：", "跌").replace("上涨九转计数中：", "涨").replace("底部九转完成(低9)", "低9").replace("顶部九转完成(高9)", "高9").replace("（近期出现低9，已重置）", "").replace("（近期出现高9，已重置）", "")
        macd_short = r['macd_cross']
        rsi_short = f"{r['rsi']:.1f}({r['rsi_state'][:2]})"
        boll_short = r['boll_pos'].replace("上轨与中轨之间（强势区）", "强势").replace("中轨与下轨之间（弱势区）", "弱势").replace("突破上轨（超买）", "超买").replace("跌破下轨（超卖）", "超卖")
        report_lines.append(f"| {r['name']} | {r['price']:.2f} | {r['change_pct']:+.2f}% | {td_short} | {macd_short} | {rsi_short} | {r['ma_arrange']} | {boll_short} | {r['rating']} | {r['action']} |")

    report_lines.append("\n---")
    report_lines.append(f"\n*报告自动生成，数据仅供参考，不构成投资建议。投资有风险，入市需谨慎。*")

    return "\n".join(report_lines)


if __name__ == '__main__':
    report = generate_markdown()
    output_path = '/Users/hf/.kimi_openclaw/workspace/五朵金花技术分析报告.md'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n✅ 报告已生成：{output_path}")
