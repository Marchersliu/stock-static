import urllib.request, json, re, sys

def get_eastmoney_funds(code):
    """通过东方财富API抓取资金流向"""
    prefix = '1.' if code.endswith('.SH') else '0.'
    num = code.replace('.SH','').replace('.SZ','')
    secid = prefix + num
    
    # f88=主力净流入 f89=超大单净流入 f90=大单净流入 f91=中单 f92=小单
    # f93=主力流入 f94=主力流出 f95=超大单流入 f96=超大单流出 f97=大单流入 f98=大单流出
    fields = 'f57,f88,f89,f90,f91,f92,f93,f94,f95,f96,f97,f98'
    url = f'https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields={fields}'
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://quote.eastmoney.com/',
            'Accept': '*/*'
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            text = resp.read().decode('utf-8')
            m = re.search(r'\(({.*})\)', text, re.DOTALL)
            if m:
                data = json.loads(m.group(1))
                d = data.get('data', {})
                return {
                    'name': d.get('f57'),
                    'main_net': d.get('f88'),
                    'elg_net': d.get('f89'),
                    'lg_net': d.get('f90'),
                    'md_net': d.get('f91'),
                    'sm_net': d.get('f92'),
                    'main_in': d.get('f93'),
                    'main_out': d.get('f94'),
                }
    except Exception as e:
        return {'error': str(e)}
    return {}

for code in ['688485.SH', '002158.SZ', '688693.SH', '002484.SZ', '002364.SZ', '002439.SZ']:
    result = get_eastmoney_funds(code)
    print(f"{code}: {json.dumps(result, ensure_ascii=False)}")
