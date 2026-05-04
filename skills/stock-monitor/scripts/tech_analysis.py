#!/usr/bin/env python3
"""
技术分析主脚本 - KDJ/MACD/RSI计算与买卖点提示

用法:
    python3 tech_analysis.py --code 688485.SH --indicators kdj,macd,rsi
    python3 tech_analysis.py --code 688485.SH --days 60 --signal
    python3 tech_analysis.py --portfolio  # 分析全部持仓股

指标:
    kdj     - KDJ随机指标（9,3,3）
    macd    - MACD（12,26,9）
    rsi     - RSI相对强弱（6,12,24）
    ma      - 移动平均线（5/10/20/60日）
    boll    - 布林带（20,2）

信号:
    --signal  - 输出买卖建议
"""
import argparse
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tushare as ts
import numpy as np
from datetime import datetime, timedelta
from utils import (
    ALL_STOCK_CODES, HOLDINGS, STOCK_KEYWORDS,
    get_tushare_token, format_change, print_section
)


def init_tushare():
    token = get_tushare_token()
    if not token:
        print("[ERR] Tushare Token not found")
        sys.exit(1)
    ts.set_token(token)
    return ts.pro_api()


def fetch_history(pro, code, days=60):
    """获取历史K线数据"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days + 20)
    try:
        df = pro.daily(ts_code=code,
                       start_date=start_date.strftime('%Y%m%d'),
                       end_date=end_date.strftime('%Y%m%d'))
        if df is None or df.empty:
            return None
        # 按日期倒序→正序
        df = df.sort_values('trade_date').reset_index(drop=True)
        return df
    except Exception as e:
        print(f"[WARN] {code} history fetch failed: {e}")
        return None


def calc_kdj(df, n=9, m1=3, m2=3):
    """计算KDJ指标"""
    low_list = df['low'].rolling(window=n, min_periods=n).min()
    high_list = df['high'].rolling(window=n, min_periods=n).max()
    rsv = (df['close'] - low_list) / (high_list - low_list) * 100
    
    K = rsv.ewm(com=m1-1, adjust=False).mean()
    D = K.ewm(com=m2-1, adjust=False).mean()
    J = 3 * K - 2 * D
    
    return {
        'K': round(K.iloc[-1], 2) if not K.empty else None,
        'D': round(D.iloc[-1], 2) if not D.empty else None,
        'J': round(J.iloc[-1], 2) if not J.empty else None,
        'gold_cross': K.iloc[-1] > D.iloc[-1] and K.iloc[-2] <= D.iloc[-2] if len(K) >= 2 else False,
        'dead_cross': K.iloc[-1] < D.iloc[-1] and K.iloc[-2] >= D.iloc[-2] if len(K) >= 2 else False
    }


def calc_macd(df, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    macd = (dif - dea) * 2
    
    return {
        'DIF': round(dif.iloc[-1], 3) if not dif.empty else None,
        'DEA': round(dea.iloc[-1], 3) if not dea.empty else None,
        'MACD': round(macd.iloc[-1], 3) if not macd.empty else None,
        'gold_cross': dif.iloc[-1] > dea.iloc[-1] and dif.iloc[-2] <= dea.iloc[-2] if len(dif) >= 2 else False,
        'dead_cross': dif.iloc[-1] < dea.iloc[-1] and dif.iloc[-2] >= dea.iloc[-2] if len(dif) >= 2 else False
    }


def calc_rsi(df, periods=[6, 12, 24]):
    """计算RSI指标"""
    results = {}
    for period in periods:
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        results[f'RSI{period}'] = round(rsi.iloc[-1], 2) if not rsi.empty else None
    
    results['overbought'] = results.get('RSI6', 0) > 80
    results['oversold'] = results.get('RSI6', 0) < 20
    return results


def calc_ma(df):
    """计算移动平均线"""
    ma5 = df['close'].rolling(window=5).mean().iloc[-1]
    ma10 = df['close'].rolling(window=10).mean().iloc[-1]
    ma20 = df['close'].rolling(window=20).mean().iloc[-1]
    ma60 = df['close'].rolling(window=60).mean().iloc[-1]
    
    return {
        'MA5': round(ma5, 2) if not np.isnan(ma5) else None,
        'MA10': round(ma10, 2) if not np.isnan(ma10) else None,
        'MA20': round(ma20, 2) if not np.isnan(ma20) else None,
        'MA60': round(ma60, 2) if not np.isnan(ma60) else None,
        'bull_arrange': ma5 > ma10 > ma20 if not any(np.isnan([ma5, ma10, ma20])) else False
    }


def calc_boll(df, n=20, k=2):
    """计算布林带"""
    ma = df['close'].rolling(window=n).mean()
    std = df['close'].rolling(window=n).std()
    upper = ma + k * std
    lower = ma - k * std
    
    return {
        'UPPER': round(upper.iloc[-1], 2) if not upper.empty else None,
        'MID': round(ma.iloc[-1], 2) if not ma.empty else None,
        'LOWER': round(lower.iloc[-1], 2) if not lower.empty else None,
        'break_upper': df['close'].iloc[-1] > upper.iloc[-1] if not upper.empty else False,
        'break_lower': df['close'].iloc[-1] < lower.iloc[-1] if not lower.empty else False
    }


def generate_signal(code, kdj, macd, rsi, ma, boll, price_info):
    """生成买卖信号"""
    signals = []
    score = 0
    
    # KDJ 信号
    if kdj.get('gold_cross'):
        signals.append("🟢 KDJ金叉（买入信号）")
        score += 2
    elif kdj.get('dead_cross'):
        signals.append("🔴 KDJ死叉（卖出信号）")
        score -= 2
    
    if kdj.get('J', 0) < 0:
        signals.append("🟢 KDJ J值<0（超卖）")
        score += 1
    elif kdj.get('J', 0) > 100:
        signals.append("🔴 KDJ J值>100（超买）")
        score -= 1
    
    # MACD 信号
    if macd.get('gold_cross'):
        signals.append("🟢 MACD金叉")
        score += 2
    elif macd.get('dead_cross'):
        signals.append("🔴 MACD死叉")
        score -= 2
    
    if macd.get('MACD', 0) > 0:
        signals.append("🟢 MACD红柱（多头）")
        score += 1
    else:
        signals.append("🔴 MACD绿柱（空头）")
        score -= 1
    
    # RSI 信号
    if rsi.get('oversold'):
        signals.append("🟢 RSI超卖（<20）")
        score += 1
    elif rsi.get('overbought'):
        signals.append("🔴 RSI超买（>80）")
        score -= 1
    
    # MA 信号
    if ma.get('bull_arrange'):
        signals.append("🟢 均线多头排列")
        score += 1
    
    # 布林带
    if boll.get('break_lower'):
        signals.append("🟢 跌破布林带下轨（反弹机会）")
        score += 1
    elif boll.get('break_upper'):
        signals.append("🔴 突破布林带上轨（可能回调）")
        score -= 1
    
    # 止损检查
    stop_price = STOCK_KEYWORDS.get(code, {}).get('stop')
    current_price = price_info.get('close', 0)
    if stop_price and current_price < float(stop_price):
        signals.append(f"⚠️ 跌破止损线 {stop_price}！")
        score -= 3
    
    # 综合建议
    if score >= 3:
        signals.append("\n📌 综合建议：强烈买入")
    elif score >= 1:
        signals.append("\n📌 综合建议：考虑买入")
    elif score <= -3:
        signals.append("\n📌 综合建议：强烈卖出/止损")
    elif score <= -1:
        signals.append("\n📌 综合建议：考虑减仓")
    else:
        signals.append("\n📌 综合建议：观望")
    
    return signals, score


def analyze_stock(pro, code, indicators='kdj,macd,rsi', days=60, show_signal=False):
    """分析单只股票"""
    name = STOCK_KEYWORDS.get(code, {}).get('name', code)
    print_section(f"{name} ({code})")
    
    df = fetch_history(pro, code, days)
    if df is None or len(df) < 30:
        print(f"[ERR] {code} 数据不足（需至少30天，实际{len(df) if df is not None else 0}天）")
        return None
    
    result = {'code': code, 'name': name, 'last_close': float(df['close'].iloc[-1])}
    indicator_list = [i.strip() for i in indicators.split(',')]
    
    if 'kdj' in indicator_list:
        result['kdj'] = calc_kdj(df)
        print(f"  KDJ: K={result['kdj']['K']} D={result['kdj']['D']} J={result['kdj']['J']}")
    
    if 'macd' in indicator_list:
        result['macd'] = calc_macd(df)
        print(f"  MACD: DIF={result['macd']['DIF']} DEA={result['macd']['DEA']} MACD={result['macd']['MACD']}")
    
    if 'rsi' in indicator_list:
        result['rsi'] = calc_rsi(df)
        print(f"  RSI: 6日={result['rsi']['RSI6']} 12日={result['rsi']['RSI12']} 24日={result['rsi']['RSI24']}")
    
    if 'ma' in indicator_list:
        result['ma'] = calc_ma(df)
        print(f"  MA: 5日={result['ma']['MA5']} 10日={result['ma']['MA10']} 20日={result['ma']['MA20']} 60日={result['ma']['MA60']}")
    
    if 'boll' in indicator_list:
        result['boll'] = calc_boll(df)
        print(f"  BOLL: 上轨={result['boll']['UPPER']} 中轨={result['boll']['MID']} 下轨={result['boll']['LOWER']}")
    
    if show_signal and all(k in result for k in ['kdj', 'macd', 'rsi', 'ma', 'boll']):
        signals, score = generate_signal(code, result['kdj'], result['macd'], result['rsi'], result['ma'], result['boll'], result)
        print("\n  信号:")
        for s in signals:
            print(f"    {s}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Technical Analysis')
    parser.add_argument('--code', help='Stock code (e.g., 688485.SH)')
    parser.add_argument('--portfolio', action='store_true', help='Analyze all holdings')
    parser.add_argument('--indicators', default='kdj,macd,rsi', help='Comma-separated indicators')
    parser.add_argument('--days', type=int, default=60, help='History days')
    parser.add_argument('--signal', action='store_true', help='Show buy/sell signals')
    parser.add_argument('--output', help='Output JSON file')
    
    args = parser.parse_args()
    
    pro = init_tushare()
    results = []
    
    if args.portfolio:
        codes = HOLDINGS
    elif args.code:
        codes = [args.code]
    else:
        print("[ERR] Specify --code or --portfolio")
        sys.exit(1)
    
    for code in codes:
        r = analyze_stock(pro, code, args.indicators, args.days, args.signal)
        if r:
            results.append(r)
    
    if args.output:
        import json
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] Saved to {args.output}")


if __name__ == '__main__':
    main()
