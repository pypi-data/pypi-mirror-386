## 同花顺热榜

接口：ths_hot

描述：获取同花顺App热榜数据，包括热股、概念板块、ETF、可转债、港美股等等，每日盘中提取4次，收盘后4次，最晚22点提取一次。

限量：单次最大2000条，可根据日期等参数循环获取全部数据

积分：用户积5000积分可调取使用，积分获取办法请参阅积分获取办法







注意：本接口只限个人学习和研究使用，如需商业用途，请自行联系同花顺解决数据采购问题。









输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| trade_date | str | N | 交易日期 |
| ts_code | str | N | TS代码 |
| market | str | N | 热榜类型(热股、ETF、可转债、行业板块、概念板块、期货、港股、热基、美股) |
| is_new | str | N | 是否最新（默认Y，如果为N则为盘中和盘后阶段采集，具体时间可参考rank_time字段，状态N每小时更新一次，状态Y更新时间为22：30） |

输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| trade_date | str | Y | 交易日期 |
| data_type | str | Y | 数据类型 |
| ts_code | str | Y | 股票代码 |
| ts_name | str | Y | 股票名称 |
| rank | int | Y | 排行 |
| pct_change | float | Y | 涨跌幅% |
| current_price | float | Y | 当前价格 |
| concept | str | Y | 标签 |
| rank_reason | str | Y | 上榜解读 |
| hot | float | Y | 热度值 |
| rank_time | str | Y | 排行榜获取时间 |

接口示例

```python
#获取查询月份券商金股
df = pro.ths_hot(trade_date='20240315', market='热股', fields='ts_code,ts_name,hot,concept')
```

数据示例

```python
ts_code ts_name       hot                  concept
0   300750.SZ    宁德时代  214462.0    ["钠离子电池", "同花顺漂亮100"]
```

数据来源