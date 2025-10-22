## 居民消费价格指数

接口：cn_cpi

描述：获取CPI居民消费价格数据，包括全国、城市和农村的数据

限量：单次最大5000行，一次可以提取全部数据

权限：用户积累600积分可以使用，具体请参阅积分获取办法 

输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| m | str | N | 月份（YYYYMM，下同），支持多个月份同时输入，逗号分隔 |
| start_m | str | N | 开始月份 |
| end_m | str | N | 结束月份 |

输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| month | str | Y | 月份YYYYMM |
| nt_val | float | Y | 全国当月值 |
| nt_yoy | float | Y | 全国同比（%） |
| nt_mom | float | Y | 全国环比（%） |
| nt_accu | float | Y | 全国累计值 |
| town_val | float | Y | 城市当月值 |
| town_yoy | float | Y | 城市同比（%） |
| town_mom | float | Y | 城市环比（%） |
| town_accu | float | Y | 城市累计值 |
| cnt_val | float | Y | 农村当月值 |
| cnt_yoy | float | Y | 农村同比（%） |
| cnt_mom | float | Y | 农村环比（%） |
| cnt_accu | float | Y | 农村累计值 |

接口调用

```python
pro = ts.pro_api()

df = pro.cn_cpi(start_m='201801', end_m='201903')


#获取指定字段
df = pro.cn_cpi(start_q='201801', end_q='201903', fields='month,nt_val,nt_yoy')
```

数据样例

```python
month  nt_val nt_yoy nt_mom nt_accu town_val town_yoy town_mom town_accu cnt_val cnt_yoy cnt_mom cnt_accu
0   201903  102.30   2.30  -0.40  101.80   102.30     2.30    -0.40    101.90  102.30    2.30   -0.30   101.80
```