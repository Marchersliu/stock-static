# 插入到 stock_service.py 中 _send_commodities 之前的位置

def fetch_commodity_prices():
    """通过Tushare期货接口抓取原材料期货价格"""
    # 原料 → 期货合约映射（主力合约：最近月份）
    commodity_futures = {
        '铝锭': {'code': 'AL2605.SHF', 'unit': '元/吨', 'source': '沪铝期货'},
        '铜': {'code': 'CU2605.SHF', 'unit': '元/吨', 'source': '沪铜期货'},
        '镍': {'code': 'NI2605.SHF', 'unit': '元/吨', 'source': '沪镍期货'},
        '锌': {'code': 'ZN2605.SHF', 'unit': '元/吨', 'source': '沪锌期货'},
        '铅': {'code': 'PB2605.SHF', 'unit': '元/吨', 'source': '沪铅期货'},
        '锡': {'code': 'SN2605.SHF', 'unit': '元/吨', 'source': '沪锡期货'},
        '聚丙烯': {'code': 'PP2605.DCE', 'unit': '元/吨', 'source': 'PP期货'},
        '焦煤': {'code': 'JM2605.DCE', 'unit': '元/吨', 'source': '焦煤期货'},
        '焦炭': {'code': 'J2605.DCE', 'unit': '元/吨', 'source': '焦炭期货'},
        '原油': {'code': 'SC2606.INE', 'unit': '元/桶', 'source': '原油期货'},
        '纸浆': {'code': 'SP2605.SHF', 'unit': '元/吨', 'source': '纸浆期货'},
    }
    
    prices = {}
    for name, info in commodity_futures.items():
        try:
            df = pro.fut_daily(ts_code=info['code'])
            if df is not None and not df.empty:
                row = df.iloc[0]
                pre_close = float(row['pre_close']) if row['pre_close'] else 0
                change1 = float(row['change1']) if row['change1'] else 0
                pct = round(change1 / pre_close * 100, 2) if pre_close else 0
                prices[name] = {
                    'latest': round(float(row['close']), 2),
                    'change_pct': pct,
                    'unit': info['unit'],
                    'source': info['source'],
                    'trade_date': str(row['trade_date']),
                }
                print(f"[Commodity] {name}: {prices[name]['latest']} ({pct:+.2f}%) @ {prices[name]['trade_date']}")
        except Exception as e:
            print(f"[ERR] 期货 {name} ({info['code']}): {e}")
    
    return prices
