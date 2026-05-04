#!/usr/bin/env python3
"""K线图技术分析 - MA/MACD/KDJ/RSI/BOLL信号"""
import argparse, json, numpy as np

def ma(data, n):
    return np.convolve(data, np.ones(n)/n, mode='valid')

def macd(data, fast=12, slow=26, signal=9):
    ema_fast = data[0]
    ema_slow = data[0]
    emaf, emas, dif, dea, macd_hist = [], [], [], [], []
    for p in data:
        ema_fast = ema_fast + (p - ema_fast) * 2/(fast+1)
        ema_slow = ema_slow + (p - ema_slow) * 2/(slow+1)
        emaf.append(ema_fast); emas.append(ema_slow)
        dif.append(ema_fast - ema_slow)
    dea0 = dif[0]
    for d in dif:
        dea0 = dea0 + (d - dea0) * 2/(signal+1)
        dea.append(dea0)
        macd_hist.append(2*(d - dea0))
    return dif, dea, macd_hist

def kdj(highs, lows, closes, n=9):
    k, d = [50], [50]
    for i in range(len(closes)):
        h = max(highs[max(0,i-n+1):i+1]) if i >= n-1 else highs[i]
        l = min(lows[max(0,i-n+1):i+1]) if i >= n-1 else lows[i]
        c = closes[i]
        rsv = (c-l)/(h-l)*100 if h != l else 50
        k.append(k[-1]*2/3 + rsv/3)
        d.append(d[-1]*2/3 + k[-1]/3)
    return k[1:], d[1:]

def rsi(data, n=14):
    gains, losses = [], []
    for i in range(1, len(data)):
        delta = data[i] - data[i-1]
        gains.append(max(delta, 0)); losses.append(abs(min(delta, 0)))
    rsis = []
    for i in range(n, len(gains)+1):
        avg_g = np.mean(gains[i-n:i]) if i >= n else np.mean(gains[:i])
        avg_l = np.mean(losses[i-n:i]) if i >= n else np.mean(losses[:i])
        rsis.append(100 - 100/(1+avg_g/avg_l) if avg_l else 100)
    return rsis

def analyze(closes, highs=None, lows=None):
    highs = highs or closes; lows = lows or closes
    sig = {'buy': 0, 'sell': 0, 'hold': 0, 'details': []}
    
    # MA
    if len(closes) >= 20:
        ma5, ma10, ma20 = ma(closes,5)[-1], ma(closes,10)[-1], ma(closes,20)[-1]
        if ma5 > ma10 > ma20: sig['buy'] += 20; sig['details'].append(f'MA金叉排列 5>10>20')
        elif ma5 < ma10 < ma20: sig['sell'] += 20; sig['details'].append(f'MA死叉排列 5<10<20')
        else: sig['hold'] += 20
    
    # MACD
    if len(closes) >= 26:
        dif, dea, hist = macd(closes)
        if hist[-1] > hist[-2] > 0: sig['buy'] += 25; sig['details'].append('MACD红柱放大')
        elif hist[-1] < hist[-2] < 0: sig['sell'] += 25; sig['details'].append('MACD绿柱放大')
        else: sig['hold'] += 25
    
    # KDJ
    if len(closes) >= 9 and highs and lows:
        k, d = kdj(highs, lows, closes)
        if k[-1] > d[-1] and k[-2] <= d[-2]: sig['buy'] += 20; sig['details'].append('KDJ金叉')
        elif k[-1] < d[-1] and k[-2] >= d[-2]: sig['sell'] += 20; sig['details'].append('KDJ死叉')
        else: sig['hold'] += 20
    
    # RSI
    if len(closes) >= 14:
        r = rsi(closes)
        if r[-1] < 30: sig['buy'] += 15; sig['details'].append(f'RSI超卖 {r[-1]:.1f}')
        elif r[-1] > 70: sig['sell'] += 15; sig['details'].append(f'RSI超买 {r[-1]:.1f}')
        else: sig['hold'] += 15
    
    sig['signal'] = 'BUY' if sig['buy'] > sig['sell'] else 'SELL' if sig['sell'] > sig['buy'] else 'HOLD'
    sig['score'] = sig['buy'] - sig['sell']
    return sig

def main():
    parser = argparse.ArgumentParser(description='Chart Analysis')
    parser.add_argument('stock', help='Stock code')
    parser.add_argument('--days', type=int, default=60)
    parser.add_argument('--signal', action='store_true')
    parser.add_argument('--data', help='JSON file with [closes, highs, lows]')
    args = parser.parse_args()
    
    if args.data:
        with open(args.data, 'r') as f: d = json.load(f)
        closes, highs, lows = d['closes'], d.get('highs'), d.get('lows')
    else:
        # Demo data
        closes = [100 + np.sin(i/5)*5 + np.random.randn()*2 for i in range(args.days)]
        highs = [c + abs(np.random.randn()*2) for c in closes]
        lows = [c - abs(np.random.randn()*2) for c in closes]
    
    result = analyze(closes, highs, lows)
    result['stock'] = args.stock
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
