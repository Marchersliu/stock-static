# Tushare Pro API 文档

## 基础配置

```python
import tushare as ts
ts.set_token('你的Tushare Pro Token')
pro = ts.pro_api()
```

## 常用接口

### 1. 个股日行情 pro.daily()

```python
df = pro.daily(ts_code='688485.SH', trade_date='20260504')
# 返回字段：ts_code, trade_date, open, high, low, close, pre_close,
#           change, pct_chg, vol, amount
```

### 2. 资金流向 pro.moneyflow()

```python
df = pro.moneyflow(ts_code='688485.SH', trade_date='20260504')
# 返回字段：ts_code, trade_date, buy_sm_amount, sell_sm_amount,
#           buy_md_amount, sell_md_amount, buy_lg_amount, sell_lg_amount,
#           buy_elg_amount, sell_elg_amount, net_mf_amount
# 关键字段：net_mf_amount = 主力净流入（万元）
```

### 3. 新闻快讯 pro.major_news()

```python
df = pro.major_news(src='sina', start_date='20260501', end_date='20260504')
# src参数：sina, 10jqka, eastmoney, cls, yicai, wallstreetcn
# 返回字段：datetime, title, content, channels
# 独立权限：1000元/年，每分钟400次，总量不限
```

### 4. 期货日行情 pro.fut_daily()

```python
# 碳酸锂期货（广期所）
df = pro.fut_daily(ts_code='LC2605.GFE', trade_date='20260504')
# 返回字段：ts_code, trade_date, open, high, low, close, pre_close,
#           change, pct_chg, vol, amount
```

### 5. 指数行情 pro.index_daily()

```python
df = pro.index_daily(ts_code='000001.SH', trade_date='20260504')
# 返回字段：ts_code, trade_date, open, high, low, close, pre_close,
#           change, pct_chg, vol, amount
```

### 6. 日历 pro.trade_cal()

```python
df = pro.trade_cal(exchange='SSE', start_date='20260501', end_date='20260506')
# 返回字段：exchange, cal_date, is_open（1=开市，0=休市）
```

### 7. 个股基本面 pro.daily_basic()

```python
df = pro.daily_basic(ts_code='688485.SH', trade_date='20260504')
# 返回字段：ts_code, trade_date, close, turnover_rate, turnover_rate_f,
#           volume_ratio, pe, pe_ttm, pb, ps, ps_ttm, dv_ratio, dv_ttm,
#           total_share, float_share, free_share, total_mv, circ_mv
```

## 接口限制

| 接口 | 免费版 | 独立权限 |
|------|--------|----------|
| `daily` | 5000次/分钟 | 不限 |
| `moneyflow` | 5000次/分钟 | 不限 |
| `major_news` | 30次/小时 | 400次/分钟 |
| `news` | 2次/天 | 400次/分钟 |
| `fut_daily` | 5000次/分钟 | 不限 |
| `index_daily` | 5000次/分钟 | 不限 |

## 期货交易所代码

| 交易所 | 代码 | 品种示例 |
|--------|------|----------|
| 上海期货交易所 | SHF | 铜CU、铝AL、锌ZN、镍NI |
| 大连商品交易所 | DCE | 聚丙烯PP、焦煤JM、焦炭J |
| 郑州商品交易所 | ZCE | 甲醇MA、锰硅SM、纯碱SA |
| 广州期货交易所 | GFE | 碳酸锂LC |

## 腾讯接口（备用）

```python
# 港股实时行情
import requests
resp = requests.get('https://qt.gtimg.cn/q=hkHSI')
# 返回格式：v_hkHSI="100~恒生指数~HSI~26199.9~..."
# 字段分隔：~
# parts[3]=当前价, parts[4]=昨收, parts[31]=涨跌额, parts[32]=涨跌幅%
```
