# Tushare库基础用法

- 使用环境变量 TUSHARE_API_TOKEN 获取 token。基础用法如下：
    ```python
    import tushare as ts
    pro = ts.pro_api(os.getenv("TUSHARE_API_TOKEN"))
    df = pro.income(ts_code='600000.SH', fields='ts_code,end_date,revenue')
    ```
- 可以通过 tushare_docs_catalog 获取文档目录，再通过 tushare_docs 获取具体接口文档。
- tushare库主要提供中国股市相关数据，无特殊说明时，接口数据范围为中国股市即相关上市公司。
- tushare接口通用规范如下：
    - 所有接口的返回类型都是 `pandas.Dataframe`。
    - 所有接口的入参都支持 `fields` 参数，可控制需要获取的指标字段，即 dataframe 的列。多个字段使用英文逗号分隔。
    - 股票代码 或 指数代码参数都叫ts_code，每种代码都有规范的后缀：
        - 上海证券交易所: 后缀是 .SH 例如 600000.SH(股票) 000001.SH(0开头指数)。
        - 深圳证券交易所: 后缀是 .SZ 例如 000001.SZ(股票) 399005.SZ(3开头指数)。
        - 北京证券交易所: 后缀是 .BJ 例如 920819.BJ(9、8和4开头的股票)。
        - 香港证券交易所: 后缀是 .HK 例如 00001.HK。
    - 日期相关字段如无特殊说明都使用 YYYYMMDD 格式。
    - 股票报告期使用的都是该季度最后一天的日期，例如，20170331=一季度，20170630=二季度，20170930=三季度 20171231=四季度。