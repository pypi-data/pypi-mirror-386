## 同花顺概念板块资金流向（THS）

接口：moneyflow_cnt_ths

描述：获取同花顺概念板块每日资金流向

限量：单次最大可调取5000条数据，可以根据日期和代码循环提取全部数据

积分：5000积分可以调取，具体请参阅积分获取办法 

输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 代码 |
| trade_date | str | N | 交易日期(格式：YYYYMMDD，下同) |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| trade_date | str | Y | 交易日期 |
| ts_code | str | Y | 板块代码 |
| name | str | Y | 板块名称 |
| lead_stock | str | Y | 领涨股票名称 |
| close_price | float | Y | 最新价 |
| pct_change | float | Y | 行业涨跌幅 |
| industry_index | float | Y | 板块指数 |
| company_num | int | Y | 公司数量 |
| pct_change_stock | float | Y | 领涨股涨跌幅 |
| net_buy_amount | float | Y | 流入资金(亿元) |
| net_sell_amount | float | Y | 流出资金(亿元) |
| net_amount | float | Y | 净额(亿元) |

接口示例

```python
#获取当日同花顺板块资金流向
df = pro.moneyflow_cnt_ths(trade_date='20250320')
```

数据示例

```python
trade_date    ts_code     name lead_stock close_price pct_change industry_index  company_num pct_change_stock net_buy_amount net_sell_amount net_amount
0     20250320  885748.TI      可燃冰       海默科技        7.99       4.76        1307.56           12             4.76          21.00           19.00       1.00
```