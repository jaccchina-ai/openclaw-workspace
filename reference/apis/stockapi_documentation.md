# StockAPI 股票数据接口完整文档

> 本文档基于 [stockapi.com.cn](https://www.stockapi.com.cn/) 官方网站的接口文档整理而成，
> 作为后续股票策略任务（T01龙头战法选股策略）的数据接口参考手册。

---

## 认证信息与权限说明

| 项目 | 内容 |
|------|------|
| **Token** | `516f4946db85f3f172e8ed29c6ad32f26148c58a38b33c74` |
| **Token级别** | 金刚钻5W次（含实时数据） |
| **每日调用次数** | 50,000次 |
| **Level2数据** | 不可获取 |
| **Token使用方式** | 在请求URL中添加参数 `&token=你的token` |
| **基础域名** | `https://www.stockapi.com.cn` |

**可用接口范围（18个分类）：** 策略回测、基础数据、实时数据、技术指标、大盘指数、基金、涨停股池、概念板块、异动数据、龙虎游资、附加增值接口、竞价专题、竞价专题增强版、竞价抢筹、风险预警、资金流向、AI智能选股、板块龙头股

---

## 目录

1. [策略回测](#策略回测)（1个接口）
2. [基础数据](#基础数据)（5个接口）
3. [实时数据](#实时数据)（10个接口）
4. [技术指标](#技术指标)（9个接口）
5. [大盘指数](#大盘指数)（5个接口）
6. [基金](#基金)（2个接口）
7. [涨停股池](#涨停股池)（5个接口）
8. [概念板块](#概念板块)（4个接口）
9. [异动数据](#异动数据)（2个接口）
10. [龙虎游资](#龙虎游资)（4个接口）
11. [附加增值接口](#附加增值接口)（2个接口）
12. [竞价专题](#竞价专题)（2个接口）
13. [竞价专题增强版](#竞价专题增强版)（3个接口）
14. [竞价抢筹](#竞价抢筹)（8个接口）
15. [风险预警](#风险预警)（4个接口）
16. [资金流向](#资金流向)（1个接口）
17. [AI智能选股](#ai智能选股)（1个接口）
18. [板块龙头股](#板块龙头股)（3个接口）

---

## 策略回测

### 收益回测接口

接口说明：
接口说明文字：可以回测买入股票后次日竞价开盘收益，次日收盘收益，次日涨停价收益（若涨停则按涨停价计算，若无涨停则按照收盘价计算）,白银以上可用
更新时间：随时
接口地址URL：https://www.stockapi.com.cn/v1/base/huice
请求方式：GET
请求频率：40次/秒

请求参数表格：
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
| --- | --- | --- | --- | --- | --- |
| strategyId | string | 是 | | 策略id，在策略回测下面先创建您的策略，将生成的策略id传入此处接口 | 99999999 |
| buyDate | string | 是 | 2024-03-25 | 买入时间，格式：2024-03-25 | 2024-03-25 |
| codes | string | 是 | 600006 | 股票代码集合,至少传一只票，多只票必须用英文逗号拼接，格式：600004,000901 | 600004 |
| price | string | 是 | | 买入价格 | 10 |

响应参数表格：
| 参数名 | 类型 | 说明 | 示例 |
| --- | --- | --- | --- |
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - api_code | string | 股票代码 | 000001.SH |
| - time | Object[] | 交易日期 | 2021-10-10 |
| - t1Open | Object[] | 买入后第一个交易日开盘收益涨幅 | |
| - t1Close | Object[] | 买入后第一个交易日收盘收益涨幅 | |
| - t1Ht | Object[] | 买入后第一个交易日如果盘中触及涨停价时的收益涨幅，如果盘中未触及涨停，以收盘收益涨幅为准 | |

请求URL示例：
https://www.stockapi.com.cn/v1/base/huice?strategyId=99999999&codes=600004&price=10.0&buyDate=2024-03-27

响应JSON示例：
```json
{
  "msg": "success",
  "code": 20000,
  "data": {
    "msg": "success",
    "code": 20000,
    "data": {
      "code": "600004",
      "name": "白云机场",
      "time": "2024-03-27",
      "t1Ht": "0.7",
      "t1Open": "-1.1",
      "t2Ht": "0.8"
    }
  }
}
```

---

## 基础数据

### A股列表数据查询

接口说明:
接口说明文字: 查询所有A股股票数据，包括股票名称、股票代码，建议用户自己本地保留一份，每天请求一次即可
更新时间: 交易日收盘后30分钟更新
接口地址URL: https://www.stockapi.com.cn/v1/base/all
请求方式: GET
请求频率: 2次/天

请求参数:
页面未提供

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
| --- | --- | --- | --- |
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - api_code | int | 股票代码 | 603176 |
| - jys | string | 交易所 | SH |
| - name | string | 名称 | 通灵股份 |
| - gl | string | 概念 | 光伏设备,江苏版块 |

请求URL示例:
https://www.stockapi.com.cn/v1/base/all?token=你的token

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "api_code": "603176",
      "jys": "SH",
      "name": "N汇通"
    },
    {
      "api_code": "301168",
      "jys": "SZ",
      "name": "通灵股份"
    }
  ]
}
```

---

### 所有st股列表数据查询

#### 接口说明
接口说明: 所有st股列表数据查询
更新时间: 交易日15:30分更新
接口地址: https://www.stockapi.com.cn/v1/base/st
请求方式: GET
请求频率: 40次/秒

#### 请求参数
No Data

#### 响应参数
| 参数名 | 类型 | 说明 | 示例 |
| --- | --- | --- | --- |
| code | String | 股票代码 | 300795.SZ |
| name | String | 股票名称 | **ST米奥 |

#### 请求URL示例
普通请求URL: https://www.stockapi.com.cn/v1/base/st
带Token请求URL: https://www.stockapi.com.cn/v1/base/st?token=你的token

#### 响应JSON示例
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "code": "300795.SZ",
      "name": "**ST米奥"
    }
  ]
}
```

---

### 查询当日是不是交易日

接口说明:
接口说明：交易日日历
更新时间：交易日上午9点
接口地址：https://www.stockapi.com.cn/v1/base/tradeDate
请求方式：GET
请求频率：40次/秒

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| tradeDate | string | 是 | 页面未提供 | 交易时间 | 2021-11-09 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | 页面未提供 | 页面未提供 |
| - isTradeDate | int | 是否为交易日：0:否，1:是 | 1 |

请求URL示例:
https://www.stockapi.com.cn/v1/base/tradeDate?tradeDate=2021-10-20

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": {
    "isTradeDate": 1
  }
}
```

---

### 股票/板块日,周，月K线行情

接口说明:
可以查询所有A股股票历史日线，周线，月线行情，数据都是前复权的
更新时间: 交易日16:00分更新
接口地址: https://www.stockapi.com.cn/v1/base/day
请求方式: GET
请求频率: 40次/秒

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| code | string | 是 | 600004 | 股票/板块/概念K线; 股票：600004; 板块：BK0733 | 600004 |
| startDate | string | 是 | | 交易开始时间 | 2021-11-09 |
| endDate | string | 是 | | 交易截止时间 | 2021-11-09 |
| calculationCycle | string | 是 | 100 | 周期：100-日，101-周,102-月 | 100 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - turnoverRatio | Object[] | 换手率 | |
| - amount | Object[] | 成交额 | |
| - totalCapital | Object[] | 总市值 | |
| - avgPrice | Object[] | 均价 | |
| - change | Object[] | 涨跌 | |
| - totalShares | Object[] | 总股本 | |
| - high | Object[] | 最高价 | |
| - low | Object[] | 最低价 | |
| - changeRatio | Object[] | 涨跌幅 | |
| - close | Object[] | 收盘价 | |
| - open | Object[] | 开盘价 | |
| - volume | Object | 成交量，单位(股) | |

请求URL示例:
https://www.stockapi.com.cn/v1/base/day?code=600004&endDate=2021-10-15&startDate=2021-10-10&calculationCycle=100

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": {
    "turnoverRatio": [],
    "amount": [],
    "totalCapital": [],
    "avgPrice": [],
    "change": [],
    "totalShares": [],
    "volume": [],
    "pb": [],
    "pcf": [],
    "high": [],
    "preClose": [],
    "pe": [],
    "low": [],
    "transactionAmount": [],
    "changeRatio": [],
    "pe_ttm": [],
    "close": [],
    "open": []
  }
}
```

---

### 龙虎榜查询

接口说明:
接口说明：龙虎榜查询
更新时间: 交易日15:30分更新
接口地址：https://www.stockapi.com.cn/v1/base/dragonTiger
请求方式：GET
请求频率：40次/秒

请求参数:
| 参数名 | 类型   | 是否必须 | 默认值 | 说明 | 示例 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| date | string | 是 | 页面未提供 | 交易时间 | 2021-11-09 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
| :--- | :--- | :--- | :--- |
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | 页面未提供 | 页面未提供 |
| - totalVolume | string | 总成交量 | 页面未提供 |
| - reason | string | 上榜原因 | 页面未提供 |
| - chg | string | 涨跌幅% | 页面未提供 |
| - endDate | string | 截至日期 | 页面未提供 |
| - sellAmountRatio | string | 占总成交比列% | 页面未提供 |
| - topAmount | string | 龙虎榜成交额（万元） | 页面未提供 |
| - buyAmountRatio | string | 占总成交额比列% | 页面未提供 |
| - totalAmount | string | 总成交额（万元） | 页面未提供 |
| - thsCode | string | 股票代码 | 页面未提供 |
| - buyAmount | string | 买入额（万元） | 页面未提供 |
| - sellAmount | string | 卖出额(万元) | 页面未提供 |
| - name | string | 名称 | 页面未提供 |
| - close | string | 收盘价 | 页面未提供 |
| - turnover | string | 换手率 | 页面未提供 |

请求URL示例:
https://www.stockapi.com.cn/v1/base/dragonTiger?date=2022-09-02

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": {
    "totalVolume": [],
    "reason": [],
    "chg": [],
    "endDate": [],
    "sellAmountRatio": [],
    "topAmount": [],
    "buyAmountRatio": [],
    "totalAmount": [],
    "thsCode": [],
    "buyAmount": [],
    "sellAmount": [],
    "name": [],
    "close": [],
    "turnover": []
  }
}
```

---

## 实时数据

### bias实时数据

接口说明:
接口说明文字: 查询实时5分钟，15分钟，30分钟，60分钟，120分钟bias数据。全刚钻可用
更新时间: 周期同隔内更新，只在9点30至15点之间有数据
接口地址URL: https://www.stockapi.com.cn/v1/base/minBias
请求方式: GET
请求频率: 1次/5分钟起

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
| --- | --- | --- | --- | --- | --- |
| code | string | 是 | | 股票代码 | 601088 |
| cycle1 | int | 是 | 6 | 周期1 | 6 |
| cycle2 | int | 是 | 12 | 周期2 | 12 |
| cycle3 | int | 是 | 24 | 周期3 | 24 |
| interval | string | 是 | 5 | 时间间隔：5分钟，15分钟，30分钟，60分钟，120分钟 | 5 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
| --- | --- | --- | --- |
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - api_code | string | 代码 | 600004 |
| - date | Onject[] | 时间 | 2025-11-04 11:00:00 |
| - bias12 | objec[] | bias12 | 0.39 |
| - bias6 | obejc[] | bias6 | 0.46 |
| - bias24 | object[] | bias24 | 0.18 |

请求URL示例:
https://www.stockapi.com.cn/v1/base/minBias?code=600004&cycle1=6&cycle2=12&cycle3=24&interval=5

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": {
    "date": [
      "2025-11-04 11:10:00"
    ],
    "api_code": "600004",
    "bias12": [
      3.45
    ],
    "bias6": [
      1.34
    ],
    "bias24": [
      4.56
    ]
  }
}
```

---

### kdj实时数据

# kdj实时数据

**所属分类:** 实时数据

#### 接口说明

- **接口说明:** 查询实时5分钟, 15分钟, 30分钟, 60分钟, 120分钟kdj数据, 金刚钻可用
- **更新时间:** 间隔周期内更新, 只在9点30至15点之间有数据
- **接口地址:** https://www.stockapi.com.cn/v1/base/minKdj
- **请求方式:** GET
- **请求频率:** 1次/5分钟起

#### 请求参数

| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| code | string | 是 | | 股票代码 | 601088 |
| cycle | int | 是 | 9 | 周期 | 9 |
| cycle1 | int | 是 | 3 | 周期1 | 3 |
| cycle2 | int | 是 | 3 | 周期2 | 3 |
| interval | string | 是 | 5 | 时间间隔：5分钟，15分钟，30分钟，60分钟，120分钟 | 5 |

#### 响应参数

| 参数名 | 类型 | 说明 | 示例 |
| :--- | :--- | :--- | :--- |
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - api_code | string | 代码 | 600004 |
| - date | Onject[] | 时间 | 2025-11-04 11:00:00 |
| - k | objec[] | k | 0.39 |
| - d | obejc[] | d | 0.46 |
| - j | object[] | j | 0.138 |

#### 请求URL示例

https://www.stockapi.com.cn/v1/base/minMacd?code=600004&cycle=9&cycle1=3&cycle2=3&interval=5

#### 响应JSON示例

```json
{
  "msg": "success",
  "code": 20000,
  "data": {
    "date": [
      "2025-11-04 11:10:00"
    ],
    "api_code": "600004",
    "d": [
      1.34
    ],
    "j": [
      3.45
    ],
    "k": [
      4.56
    ]
  }
}
```

---

### k线实时5/15/30分钟数据

接口说明:
接口说明文字: 可以查询所有A股股票5分钟K线，15分钟K线，30分钟K线，60分钟K线，120分钟K线，数据都是前复权的，金刚钻可用
更新时间: 在K线间隔周期内更新，只在9点30至15点之间有数据
接口地址URL: https://www.stockapi.com.cn/v1/base/kline
请求方式: GET
请求频率: 1次/5分钟起

请求参数:
| 参数名 | 类型   | 是否必须 | 默认值 | 说明                                   | 示例   |
|--------|--------|----------|--------|----------------------------------------|--------|
| code   | string | 是       | 600004 | 股票代码：如：600004;                  | 600004 |
| type   | string | 是       | 5      | 周期：5分钟，15分钟，30分钟，60分钟，120分钟 | 5      |

响应参数:
| 参数名   | 类型   | 说明             | 示例    |
|----------|--------|------------------|---------|
| code     | int    | 返回码           | 20000   |
| msg      | string | 状态             | success |
| data     | Object |                  |         |
| - amount | Object | 成交额           |         |
| - high   | Object | 最高价           |         |
| - low    | Object | 最低价           |         |
| - close  | Object | 收盘价           |         |
| - open   | Object | 开盘价           |         |
| - volume | Object | 成交量，单位(股) |         |
| - time   | Object | 时间             |         |

请求URL示例:
https://www.stockapi.com.cn/v1/base/kline?code=600004&type=5

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "volume": "220800",
      "high": "9.910",
      "amount": "2185391.9739",
      "code": "600004",
      "low": "9.890",
      "time": "2025-11-04 10:40:00",
      "close": "9.900",
      "open": "9.910"
    }
  ]
}
```

---

### macd实时数据

接口说明：
接口说明：查询实时5分钟，15分钟，30分钟，60分钟，120分钟macd数据，金刚钻可用
更新时间：间隔周期内更新，只在9点30至15点之间有数据
接口地址：https://www.stockapi.com.cn/v1/base/minMacd
请求方式：GET
请求频率: 1次/5分钟起

请求参数：
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| code | string | 是 | - | 股票代码 | 601088 |
| cycle | int | 是 | 9 | 周期 | 9 |
| longCycle | int | 是 | 26 | 长期周期 | 26 |
| shortCycle | int | 是 | 12 | 短期周期 | 12 |
| interval | string | 是 | 5 | 时间间隔:5分钟;15分钟;30分钟，60分钟，120分钟 | 5 |

响应参数：
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - api_code | string | 代码 | 600004 |
| - date | object[] | 时间 | 2025-11-04 11:00:00 |
| - dea | object[] | dea | 0.39 |
| - dif | string | dif值 | 0.46 |
| - macd | object[] | macd值 | 0.138 |

请求URL示例：
https://www.stockapi.com.cn/v1/base/minMacd?code=600004&cycle=9&longCycle=26&shortCycle=12&interval=5

响应JSON示例：
```json
{
  "msg": "success",
  "code": 20000,
  "data": {
    "dif": [
      0.01
    ],
    "date": [
      "2025-11-04 11:00:00"
    ],
    "api_code": "600004",
    "dea": [
      0.01
    ],
    "macd": [
      0.01
    ]
  }
}
```

---

### rsi实时数据

接口说明:
查询实时5分钟，15分钟，30分钟，60分钟，120分钟RSI数据。金刚钻可用
更新时间: 间隔周期内更新,只在9点30至15点之间有数据
接口地址: https://www.stockapi.com.cn/v1/base/minRsi
请求方式: GET
请求频率: 1次/5分钟起

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| code | string | 是 | | 股票代码 | 601088 |
| cycle1 | int | 是 | 6 | 周期1 | 6 |
| cycle2 | int | 是 | 12 | 周期2 | 12 |
| cycle3 | int | 是 | 24 | 周期3 | 24 |
| interval | string | 是 | 5 | 时间间隔：5分钟，15分钟，30分钟，60分钟，120分钟 | 5 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
| :--- | :--- | :--- | :--- |
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - api_code | string | 代码 | 600004 |
| - date | Onject[] | 时间 | 2025-11-04 11:00:00 |
| - rsi1 | objec[] | rsi1 | 0.39 |
| - rsi2 | obejc[] | rsi2 | 0.46 |
| - rsi3 | object[] | rsi3 | 0.18 |

请求URL示例:
https://www.stockapi.com.cn/v1/base/minRsi?code=600004&cycle1=6&cycle2=12&cycle3=24&interval=5

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": {
    "date": [
      "2025-11-04 11:10:00"
    ],
    "api_code": "600004",
    "rsi1": [
      1.34
    ],
    "rsi3": [
      4.56
    ],
    "rsi2": [
      3.45
    ]
  }
}
```

---

### wr实时数据

接口说明:
查询实时5分钟，15分钟，30分钟，60分钟，120分钟WR数据，金刚钻可用
更新时间: 周期间隔内更新，只在9点30至15点之间有数据
接口地址: https://www.stockapi.com.cn/v1/base/minWr
请求方式: GET
请求频率: 1次/5分钟起

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
| --- | --- | --- | --- | --- | --- |
| code | string | 是 | | 股票代码 | 601088 |
| cycle1 | int | 是 | 10 | 周期1 | 10 |
| cycle2 | int | 是 | 6 | 周期2 | 6 |
| interval | string | 是 | 5 | 时间间隔：5分钟，15分钟，30分钟，60分钟，120分钟 | 5 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
| --- | --- | --- | --- |
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - api_code | string | 代码 | 600004 |
| - date | Onject[] | 时间 | 2025-11-04 11:00:00 |
| - wr1 | objec[] | wr1 | 0.39 |
| - wr2 | obejc[] | wr2 | 0.46 |

请求URL示例:
https://www.stockapi.com.cn/v1/base/minWr?code=600004&cycle1=10&cycle2=6&interval=5

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": {
    "date": [
      "2025-11-04 11:10:00"
    ],
    "api_code": "600004",
    "wr2": [
      3.45
    ],
    "wr1": [
      3.45
    ]
  }
}
```

---

### 一分钟K线实时数据

接口说明：
接口说明文字：查询每分钟实时K线数据。仅在9点30到15点有数据，金刚钻可用
更新时间：实时更新
接口地址URL：https://www.stockapi.com.cn/v1/base/minkLine
请求方式：GET
请求频率：1次/一分钟

请求参数表格：
| 参数名 | 类型   | 是否必须 | 默认值 | 说明                                       | 示例   |
|--------|--------|----------|--------|--------------------------------------------|--------|
| code   | string | 是       |        | 传股票代码                                 | 600004 |
| all    | string | 是       | 1      | 返回全部数据， 1-返回全部数据， 0-返回最近一条 | 1      |

响应参数表格：
| 参数名 | 类型     | 说明     | 示例        |
|--------|----------|----------|-------------|
| code   | int      | 返回码   | 20000       |
| msg    | string   | 状态     | success     |
| data   | Object[] |          |             |
| - amount| Object[] | 成交额   |             |
| - high | Object[] | 最高价   |             |
| - low  | Object[] | 最低价   |             |
| - volume| Object[] | 成交量   |             |
| - close| Object[] | 收盘价   |             |
| - open | Object[] | 开盘价   |             |
| - time | Object[] | 时间     |             |

请求URL示例：
https://www.stockapi.com.cn/v1/base/minkLine?code=000001&all=1

响应JSON示例：
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "volume": "4748635",
      "high": "3069.53",
      "amount": "4791384832.00",
      "low": "3069.30",
      "time": "2024-04-03 15:00:00",
      "close": "3069.30",
      "open": "3069.50"
    }
  ]
}
```

---

### 分时成交量

接口说明:
接口说明：分时成交量，分析竞价爆量比较方便,，仅在9点15到15点有数据，金刚钻可用
更新时间: 实时更新
接口地址：https://www.stockapi.com.cn/v1/base/minList
请求方式：GET
请求频率: 1次/一分钟

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
| --- | --- | --- | --- | --- | --- |
| code | string | 是 | | 股票代码 | 600004 |
| all | string | 是 | 1 | 返回全部数据， 1-返回全部数据， 0-返回最近一条 | 1 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
| --- | --- | --- | --- |
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - time | int | 时间 | 1 |
| - price | int | 价格 | 1 |
| - shoushu | int | 手数 | 1 |
| - danShu | int | 单数 | 1 |
| - bsbz | int | 涨跌标志：1-跌，2-涨,4-竞价阶段 | 1 |

请求URL示例:
https://www.stockapi.com.cn/v1/base/minList?code=600004&all=1

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "shoushu": "889",
      "price": "29.55",
      "bsbz": "4",
      "time": "09:16:00"
    }
  ]
}
```

---

### 实时五档委托单

接口说明:
接口说明文字: 实时获取买卖五档数据，仅在9点25至15点有数据，金刚钻可用
更新时间: 实时更新
接口地址URL: https://www.stockapi.com.cn/v1/base/wudang
请求方式: GET
请求频率: 10次/秒

请求参数:
| 参数名 | 类型   | 是否必须 | 默认值 | 说明     | 示例   |
| :----- | :----- | :------- | :----- | :------- | :----- |
| code   | string | 是       |        | 股票代码 | 601088 |

响应参数:
| 参数名    | 类型     | 说明     | 示例     |
| :-------- | :------- | :------- | :------- |
| code      | int      | 返回码   | 20000    |
| msg       | string   | 状态     | success  |
| data      | Object[] |          |          |
| - code    | string   | 股票代码 | 600004   |
| - name    | string   | 股票名称 | 白云机场 |
| - current | string   | 当前价   | 10.27    |
| - totalV  | string   | 总成交   | 2000000  |
| - insideV | string   | 内盘     | 2000000  |
| - outerV  | string   | 外盘     | 2000000  |
| - buy1    | string   | 买1价    | 10.27    |
| - buyV1   | string   | 买1量    | 20003    |
| - buyAmt1 | string   | 买1金额  | 20003333 |
| - buy2    | string   | 买2价    | 10.27    |
| - buyV2   | string   | 买2量    | 20003    |
| - buyAmt2 | string   | 买2金额  | 20003333 |
| - buy3    | string   | 买3价    | 10.27    |
| - buyV3   | string   | 买3量    | 20003    |
| - buyAmt3 | string   | 买3金额  | 20003333 |
| - buy4    | string   | 买4价    | 10.27    |
| - buyV4   | string   | 买4量    | 20003    |
| - buyAmt4 | string   | 买4金额  | 20003333 |
| - buy5    | string   | 买5价    | 10.27    |
| - buyV5   | string   | 买5量    | 20003    |
| - buyAmt5 | string   | 买5金额  | 20003333 |
| - sell1   | string   | 卖1价    | 10.27    |
| - sellV1  | string   | 卖1量    | 20003    |
| - sellAmt1| string   | 卖1金额  | 20003333 |
| - sell2   | string   | 卖2价    | 10.27    |
| - sellV2  | string   | 卖2量    | 20003    |
| - sellAmt2| string   | 卖2金额  | 20003333 |
| - sell3   | string   | 卖3价    | 10.27    |
| - sellV3  | string   | 卖3量    | 20003    |
| - sellAmt3| string   | 卖3金额  | 20003333 |
| - sell4   | string   | 卖4价    | 10.27    |
| - sellV4  | string   | 卖4量    | 20003    |
| - sellAmt4| string   | 卖4金额  | 20003333 |
| - sell5   | string   | 卖5价    | 10.27    |
| - sellV5  | string   | 卖5量    | 20003    |
| - sellAmt5| string   | 卖5金额  | 20003333 |

请求URL示例:
https://www.stockapi.com.cn/v1/base/wudang?code=600004

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": {
    "buy4": "10.24",
    "buyAmt3": "1515975",
    "buy5": "10.23",
    "buyAmt2": "1966842",
    "buy2": "10.26",
    "buyAmt5": "356004",
    "sellAmt1": "739132",
    "buy3": "10.25",
    "code": "600004",
    "buyAmt4": "601088",
    "sellAmt3": "333720",
    "buy1": "10.27",
    "sellAmt2": "13377",
    "sellAmt5": "269352",
    "sellAmt4": "377346",
    "sellV5": "261",
    "sellV4": "366",
    "sellV3": "324",
    "sellV2": "13",
    "sellV1": "719",
    "current": "10.28",
    "totalV": "332404",
    "sell1": "10.28",
    "buyAmt1": "3226834",
    "sell2": "10.29",
    "sell3": "10.30",
    "sell4": "10.31",
    "sell5": "10.32",
    "outerV": "211106",
    "insideV": "121298",
    "name": "白云机场",
    "buyV3": "1479",
    "buyV2": "1917",
    "buyV1": "3142",
    "buyV5": "348",
    "buyV4": "587"
  }
}
```

---

### 逐笔明细

接口说明：
接口说明文字：逐笔明细，分析竞价爆量比较方便，仅在9点15到15点有数据，金刚钻可用
更新时间：实时更新
接口地址URL：https://www.stockapi.com.cn/v1/base/secondList
请求方式：GET
请求频率：1次/3秒

请求参数表格：
| 参数名 | 类型   | 是否必须 | 默认值 | 说明                                                 | 示例   |
|--------|--------|----------|--------|------------------------------------------------------|--------|
| code   | string | 是       |        | 股票代码                                             | 600004 |
| all    | string | 是       | 1      | 返回全部数据， 1-返回全部数据， 0-返回最近一条       | 1      |

响应参数表格：
| 参数名  | 类型     | 说明                               | 示例    |
|---------|----------|------------------------------------|---------|
| code    | int      | 返回码                             | 20000   |
| msg     | string   | 状态                               | success |
| data    | Object[] |                                    |         |
| - time  | int      | 时间                               | 1       |
| - price | int      | 价格                               | 1       |
| - shoushu| int      | 手数                               | 1       |
| - danShu| int      | 单数                               | 1       |
| - bsbz  | int      | 涨跌标志：1-跌，2-涨,4-竞价阶段     | 1       |

请求URL示例：
https://www.stockapi.com.cn/v1/base/secondList?code=600004&all=1

响应JSON示例：
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "shoushu": "889",
      "price": "29.55",
      "bsbz": "4",
      "time": "09:16:00"
    }
  ]
}

---

## 技术指标

### 5,10,20...日ma均线数据查询

---

#### 接口说明

- **接口说明**：日、周、月5,10,20...ma均线数据查询
- **更新时间**：交易日15:30分更新
- **接口地址**：https://www.stockapi.com.cn/v1/quota/ma2
- **请求方式**：GET
- **请求频率**：40次/秒

---

#### 请求参数

| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| code | string | 是 | | 可传股票、板块、概念代码 | 601088 |
| ma | int | 是 | 5,10,20 | 周期,逗号分隔符必须为英文 | 5,10,20... |
| startDate | string | 是 | 2021-10-22 | 开始时间 | 2021-10-22 |
| endDate | string | 是 | 2021-10-22 | 结束时间 | 2021-10-22 |
| calculationCycle | string | 是 | 100 | 周期：100-日，101-周,102-月 | 100 |

---

#### 响应参数

| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - api_code | string | 代码 | 600004.SH |
| - date | string | 时间 | 2021-10-10 |
| - ma5 | string | ma5 | 74 |
| - ma10 | string | ma10 | 74 |
| - ma20 | string | ma20 | 75.97 |

---

#### 请求URL示例

```
https://www.stockapi.com.cn/v1/quota/ma2?token=你的token&code=600004&startDate=2021-10-22&endDate=2021-10-22&ma=5,10,20&calculationCycle=100
```

---

#### 响应JSON示例

```json
{
  "msg": "success",
  "code": 20000,
  "data": {
    "ma5": [
      11.426
    ],
    "date": [
      "2021-10-22"
    ],
    "ma20": [
      11.023
    ],
    "api_code": "600004",
    "ma10": [
      11.421
    ]
  }
}
```

---

### 乖离率BIAS指标

接口说明:
接口说明: 日、周、月乖离率BIAS指标
更新时间: 交易日15:30分更新
接口地址: https://www.stockapi.com.cn/v1/quota/bias2
请求方式: GET
请求频率: 40次/秒

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| code | string | 是 | | 可传股票、板块、概念 | 601088 |
| cycle1 | int | 是 | 6 | 周期1 | 6 |
| cycle2 | int | 是 | 12 | 周期2 | 12 |
| cycle3 | int | 是 | 12 | 周期3 | 12 |
| startDate | string | 是 | 2021-10-22 | 开始时间 | 2021-10-22 |
| endDate | string | 是 | 2021-10-22 | 结束时间 | 2021-10-22 |
| calculationCycle | string | 是 | 100 | 周期：100-日，101-周,102-月 | 100 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
| :--- | :--- | :--- | :--- |
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - bias1 | string | bias1值 | 3.7532289925543 |
| - bias2 | string | bias2值 | 5.6066816178177 |
| - bias3 | string | bias3值 | 8.8734752451567 |

请求URL示例:
https://www.stockapi.com.cn/v1/quota/bias2?code=600004&cycle1=6&cycle2=12&cycle3=24&startDate=2021-10-22&endDate=2021-10-22&calculationCycle=100

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "date": "2021-10-10",
      "api_code": "600004.SH",
      "bias3": "8.8734752451567",
      "bias1": "3.7532289925543",
      "bias2": "5.6066816178177"
    }
  ]
}
```

---

### 布林带boll数据查询

接口说明:
接口说明文字: 日、周、月布林带boll数据查询
更新时间: 交易日15:30分更新
接口地址URL: https://www.stockapi.com.cn/v1/quota/boll2
请求方式: GET
请求频率: 40次/秒

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| code | string | 是 | | 可传股票、板块、概念代码 | 601088 |
| bandwidth | int | 是 | 2 | 带宽 | 2 |
| cycle | int | 是 | 26 | 周期 | 26 |
| startDate | string | 是 | 2021-10-22 | 开始时间 | 2021-10-22 |
| endDate | string | 是 | 2021-10-22 | 结束时间 | 2021-10-22 |
| calculationCycle | string | 是 | 100 | 周期：100-日，101-周,102-月 | 100 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - api_code | string | 代码 | 600004.SH |
| - date | string | 时间 | 2021-10-10 |
| - UPPER | string | 上轨 | 3.7532289925543 |
| - LOWER | string | 下轨 | 5.6066816178177 |
| - MID | string | 中轨 | 8.8734752451567 |

请求URL示例:
https://www.stockapi.com.cn/v1/quota/boll2?bandwidth=2&code=600004&cycle=26&startDate=2021-10-22&endDate=2021-10-22&calculationCycle=100

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "date": "2021-10-10",
      "api_code": "600004.SH",
      "UPPER": "8.8734752451567",
      "LOWER": "3.7532289925543",
      "MID": "5.6066816178177"
    }
  ]
}
```

---

### 日线cci数据查询

接口说明：
接口说明文字：日、周、月cci数据查询
更新时间：交易日15:30分更新
接口地址URL：https://www.stockapi.com.cn/v1/quota/cci2
请求方式：GET
请求频率：40次/秒

请求参数表格：
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| code | string | 是 | | 可传股票、板块、概念代码 | 601088 |
| cycle | int | 是 | 26 | 周期 | 26 |
| startDate | string | 是 | 2021-10-22 | 开始时间 | 2021-10-22 |
| endDate | string | 是 | 2021-10-22 | 结束时间 | 2021-10-22 |
| calculationCycle | string | 是 | 100 | 周期：100-日，101-周,102-月 | 100 |

响应参数表格：
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - api_code | string | 代码 | 600004.SH |
| - date | string | 时间 | 2021-10-10 |
| - cci | string | 上轨 | 3.7532289925543 |

请求URL示例：
https://www.stockapi.com.cn/v1/quota/cci2?code=600004&cycle=14&startDate=2021-10-22&endDate=2021-10-22&calculationCycle=...

响应JSON示例：
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "date": "2021-10-10",
      "api_code": "600004.SH",
      "cci": "8.8734752451567"
    }
  ]
}
```

---

### 日线kdj数据查询

接口说明：
接口说明：日、周、月kdj数据查询
更新时间：交易日15:30分更新
接口地址：https://www.stockapi.com.cn/v1/quota/kdj2
请求方式：GET
请求频率: 40次/秒

请求参数：
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| code | string | 是 | | 可传股票、板块、概念代码 | 601088 |
| cycle | int | 是 | 9 | 周期 | 9 |
| cycle1 | int | 是 | 3 | 周期1 | 3 |
| cycle2 | int | 是 | 3 | 周期2 | 3 |
| startDate | string | 是 | 2021-10-22 | 开始时间 | 2021-10-22 |
| endDate | string | 是 | 2021-10-22 | 结束时间 | 2021-10-22 |
| calculationCycle | string | 是 | 100 | 周期：100-日，101-周,102-月 | 100 |

响应参数：
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - api_code | string | 代码 | 600004.SH |
| - date | string | 时间 | 2021-10-10 |
| - k | string | k值 | 74.026411185765 |
| - d | string | d值 | 74.026411185765 |
| - j | string | j值 | 75.970593695305 |

请求URL示例：
https://www.stockapi.com.cn/v1/quota/kdj2?calculationCycle=100&code=600004&cycle=9&cycle1=3&cycle2=3&startDate=2021-10-2...

响应JSON示例：
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "date": "2021-10-10",
      "api_code": "600004.SH",
      "d": "75.970593695305",
      "j": "74.674472022278",
      "k": "74.026411185765"
    }
  ]
}
```

---

### 日线macd数据查询

接口说明:
接口说明: 日、周、月线macd数据查询
更新时间: 交易日15:30分更新
接口地址: https://www.stockapi.com.cn/v1/quota/macd2
请求方式: GET
请求频率: 40次/秒

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
| --- | --- | --- | --- | --- | --- |
| code | string | 是 | | 可传股票、板块、概念代码 | 601088 |
| cycle | int | 是 | 9 | 周期 | 9 |
| longCycle | int | 是 | 26 | 长期周期 | 26 |
| shortCycle | int | 是 | 12 | 短期周期 | 12 |
| startDate | string | 是 | 2021-10-22 | 开始时间 | 2021-10-22 |
| endDate | string | 是 | 2021-10-22 | 结束时间 | 2021-10-22 |
| calculationCycle | string | 是 | 100 | 周期：100-日，101-周,102-月 | 100 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
| --- | --- | --- | --- |
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - api_code | string | 代码 | 600004.SH |
| - date | string | 时间 | 2021-10-10 |
| - DEA | string | DEA值 | 0.39808748104648 |
| - DIFF | string | DIFF值 | 0.46470061143322 |
| - MACD | string | MACD值 | 0.13322626077348 |

请求URL示例:
https://www.stockapi.com.cn/v1/quota/macd2?code=600004&cycle=9&startDate=2021-10-22&endDate=2021-10-22&longCycle=26&shortCycle=12

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "date": "2021-10-10",
      "api_code": "600004.SH",
      "DEA": "74.026411185765",
      "DIFF": "75.970593695305",
      "MACD": "74.674472022278"
    }
  ]
}
```

---

### 日线rsi指标

接口说明:
接口说明文字: 日、周、月线RSI指标
更新时间: 交易日收盘后30分钟更新
接口地址URL: https://www.stockapi.com.cn/v1/quota/rsi2
请求方式: GET
请求频率: 40次/秒

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| code | string | 是 | | 可传股票、板块、概念代码 | 601088 |
| cycle1 | int | 是 | 6 | 周期1 | 6 |
| cycle2 | int | 是 | 12 | 周期2 | 12 |
| cycle3 | int | 是 | 24 | 周期3 | 24 |
| startDate | string | 是 | 2021-10-22 | 开始时间 | 2021-10-22 |
| endDate | string | 是 | 2021-10-22 | 结束时间 | 2021-10-22 |
| calculationCycle | string | 是 | 100 | 周期：100-日，101-周,102-月 | 100 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - api_code | string | 代码 | 600004.SH |
| - date | string | 时间 | 2021-10-10 |
| - rsi1 | string | rsi1值 | 29.770992366412 |
| - rsi2 | string | rsi2值 | 29.770992366412 |
| - rsi3 | string | rsi3值 | 29.770992366412 |

请求URL示例:
https://www.stockapi.com.cn/v1/quota/rsi2?code=601088&cycle1=6&cycle2=12&cycle3=24&startDate=2021-10-22&endDate=2021-10-22&calculationCycle=100

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "date": "2021-10-10",
      "api_code": "600004.SH",
      "rsi1": 29.770992366412,
      "rsi3": 29.770992366412,
      "rsi2": 29.770992366412
    }
  ]
}
```

---

### 日线wr数据查询

接口说明:
接口说明文字: 日、周、月线wr数据查询
更新时间: 交易日15:30分更新
接口地址URL: https://www.stockapi.com.cn/v1/quota/wr2
请求方式: GET
请求频率: 40次/秒

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| code | string | 是 | | 可传股票、板块、概念代码 | 601088 |
| cycle1 | int | 是 | 10 | 周期1 | 10 |
| cycle2 | int | 是 | 6 | 周期2 | 6 |
| startDate | string | 是 | 2021-10-22 | 开始时间 | 2021-10-22 |
| endDate | string | 是 | 2021-10-22 | 结束时间 | 2021-10-22 |
| calculationCycle | string | 是 | 100 | 周期：100-日，101-周,102-月 | 100 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - api_code | string | 代码 | 600004.SH |
| - date | string | 时间 | 2021-10-10 |
| - wr2 | string | wr2值 | 29.770992366412 |
| - wr1 | string | wr1值 | 29.770992366412 |

请求URL示例:
https://www.stockapi.com.cn/v1/quota/wr2?code=600004&cycle1=10&cycle2=6&startDate=2021-10-22&endDate=2021-10-22&calculationCycle=100

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "date": "2021-10-10",
      "api_code": "600004.SH",
      "wr2": 29.770992366412,
      "wr1": 29.770992366412
    }
  ]
}
```

---

### 神奇九转指标

接口说明:
接口说明文字: 日、周、月神奇九转指标
更新时间: 交易日15:30分更新
接口地址URL: https://www.stockapi.com.cn/v1/quota/nineTurn
请求方式: GET
请求频率: 40次/秒

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| code | string | 是 | | 可传股票、板块、概念代码 | 601088 |
| date | string | 是 | 2021-10-22 | 时间 | 2021-10-22 |
| calculationCycle | string | 是 | 100 | 周期：100-日，101-周,102-月 | 100 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - api_code | string | 代码 | 600004.SH |
| - date | string | 时间 | 2021-10-10 |
| - lowNine | int | 低位九转：0:否，1:是 | 0 |
| - highNine | int | 高位九转：0:否，1:是 | 1 |

请求URL示例:
https://www.stockapi.com.cn/v1/quota/nineTurn?code=600004&date=2021-10-15&calculationCycle=100

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "date": "2021-10-10",
      "api_code": "600004.SH",
      "lowNine": 0,
      "highNine": 1
    }
  ]
}
```

---

## 大盘指数

### 查询上证指数

接口说明:
接口说明文字: 查询上证指数
更新时间: 交易日15:30分更新
接口地址URL: https://www.stockapi.com.cn/v1/index/sh
请求方式: GET
请求频率: 40次/秒

请求参数表格:
| 参数名    | 类型   | 是否必须 | 默认值     | 说明                           | 示例       |
|-----------|--------|----------|------------|--------------------------------|------------|
| startDate | string | 是       | 2021-10-22 | 交易开始时间，格式：2021-10-20 | 2021-10-22 |
| endDate   | string | 是       | 2021-10-22 | 交易结束时间，格式：2021-10-20 | 2021-10-22 |

响应参数表格:
| 参数名      | 类型     | 说明     | 示例      |
|-------------|----------|----------|-----------|
| code        | int      | 返回码   | 20000     |
| msg         | string   | 状态     | success   |
| data        | Object[] |          |           |
| - api_code  | string   | 股票代码 | 000001.SH |
| - time      | Object[] | 交易日期 | 2021-10-10|
| - volume    | Object[] | 成交量   |           |
| - high      | Object[] | 最高价   |           |
| - amount    | Object[] | 成交额   |           |
| - low       | Object[] | 最低价   |           |
| - avgPrice  | Object[] | 均价     |           |
| - change    | Object[] | 涨跌     |           |
| - changeRatio| Object[] | 涨跌幅   |           |
| - close     | Object[] | 收盘价   |           |
| - open      | Object[] | 开盘价   |           |

请求URL示例:
普通请求URL: https://www.stockapi.com.cn/v1/index/sh?startDate=2021-10-20&endDate=2021-10-30
带Token请求URL: https://www.stockapi.com.cn/v1/index/sh?token=你的token&startDate=2021-10-20&endDate=2021-10-30

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": {
    "api_code": "000001.SH",
    "thscode": "",
    "time": "Object[242]",
    "table": {
      "volume": "Object[242]",
      "high": "Object[242]",
      "amount": "Object[242]",
      "low": "Object[242]",
      "avgPrice": "Object[242]",
      "change": "Object[242]",
      "changeRatio": "Object[242]",
      "close": "Object[242]",
      "open": "Object[242]"
    }
  }
}
```

---

### 查询创业板指

接口说明:
接口说明文字: 查询创业板指
更新时间: 交易日15:30分更新
接口地址URL: https://www.stockapi.com.cn/v1/index/cyb
请求方式: GET
请求频率: 40次/秒

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| startDate | string | 是 | 2021-10-22 | 交易开始时间，格式：2021-10-20 | 2021-10-22 |
| endDate | string | 是 | 2021-10-22 | 交易结束时间，格式：2021-10-20 | 2021-10-22 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - api_code | string | 股票代码 | 000001.SH |
| - time | Object[] | 交易日期 | 2021-10-10 |
| - volume | Object[] | 成交量 | |
| - high | Object[] | 最高价 | |
| - amount | Object[] | 成交额 | |
| - low | Object[] | 最低价 | |
| - avgPrice | Object[] | 均价 | |
| - change | Object[] | 涨跌 | |
| - changeRatio | Object[] | 涨跌幅 | |
| - close | Object[] | 收盘价 | |
| - open | Object[] | 开盘价 | |

请求URL示例:
https://www.stockapi.com.cn/v1/index/cyb?startDate=2021-10-20&endDate=2021-10-30

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": {
    "api_code": "000001.SH",
    "thscode": "",
    "time": "Object[242]",
    "table": {
      "volume": "Object[242]",
      "high": "Object[242]",
      "amount": "Object[242]",
      "low": "Object[242]",
      "avgPrice": "Object[242]",
      "change": "Object[242]",
      "changeRatio": "Object[242]",
      "close": "Object[242]",
      "open": "Object[242]"
    }
  }
}
```

---

### 查询沪深300

接口说明:
接口说明：查询沪深300
更新时间：交易日收盘后30分钟更新
接口地址：https://www.stockapi.com.cn/v1/index/sh300
请求方式：GET
请求频率: 40次/秒

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| startDate | string | 是 | 2021-10-22 | 交易开始时间，格式：2021-10-20 | 2021-10-22 |
| endDate | string | 是 | 2021-10-22 | 交易结束时间，格式：2021-10-20 | 2021-10-22 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - api_code | string | 股票代码 | 000001.SH |
| - time | Object[] | 交易日期 | 2021-10-10 |
| - volume | Object[] | 成交量 | 页面未提供 |
| - high | Object[] | 最高价 | 页面未提供 |
| - amount | Object[] | 成交额 | 页面未提供 |
| - low | Object[] | 最低价 | 页面未提供 |
| - avgPrice | Object[] | 均价 | 页面未提供 |
| - change | Object[] | 涨跌 | 页面未提供 |
| - changeRatio | Object[] | 涨跌幅 | 页面未提供 |
| - close | Object[] | 收盘价 | 页面未提供 |
| - open | Object[] | 开盘价 | 页面未提供 |

请求URL示例:
普通请求URL，每日免费1000次: https://www.stockapi.com.cn/v1/index/sh300?startDate=2021-10-20&endDate=2021-10-30
带Token请求URL： https://www.stockapi.com.cn/v1/index/sh300?token=你的token&startDate=2021-10-20&endDate=2021-10-30

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": {
    "api_code": "000001.SH",
    "thscode": "",
    "time": "Object[242]",
    "table": {
      "volume": "Object[242]",
      "high": "Object[242]",
      "amount": "Object[242]",
      "low": "Object[242]",
      "avgPrice": "Object[242]",
      "change": "Object[242]",
      "changeRatio": "Object[242]",
      "close": "Object[242]",
      "open": "Object[242]"
    }
  }
}
```

---

### 查询深圳成指

接口说明:
接口说明文字: 查询深圳成指
更新时间: 交易日15:30分更新
接口地址URL: https://www.stockapi.com.cn/v1/index/sz
请求方式: GET
请求频率: 40次/秒

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| startDate | string | 是 | 2021-10-22 | 交易开始时间，格式：2021-10-20 | 2021-10-22 |
| endDate | string | 是 | 2021-10-22 | 交易结束时间，格式：2021-10-20 | 2021-10-22 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - api_code | string | 股票代码 | 000001.SH |
| - time | Object[] | 交易日期 | 2021-10-10 |
| - volume | Object[] | 成交量 | |
| - high | Object[] | 最高价 | |
| - amount | Object[] | 成交额 | |
| - low | Object[] | 最低价 | |
| - avgPrice | Object[] | 均价 | |
| - change | Object[] | 涨跌 | |
| - changeRatio | Object[] | 涨跌幅 | |
| - close | Object[] | 收盘价 | |
| - open | Object[] | 开盘价 | |

请求URL示例:
https://www.stockapi.com.cn/v1/index/sz?startDate=2021-10-20&endDate=2021-10-30

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": {
    "api_code": "000001.SH",
    "thscode": "",
    "time": "Object[242]",
    "table": {
      "volume": "Object[242]",
      "high": "Object[242]",
      "amount": "Object[242]",
      "low": "Object[242]",
      "avgPrice": "Object[242]",
      "change": "Object[242]",
      "changeRatio": "Object[242]",
      "close": "Object[242]",
      "open": "Object[242]"
    }
  }
}
```

---

### 获取所有指数代码

接口说明:
接口说明文字: 获取所有指数代码
更新时间: 交易日15:30分更新
接口地址URL: https://www.stockapi.com.cn/v1/base/ZSCode
请求方式: GET
请求频率: 40次/秒

请求参数:
页面未提供

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
| :--- | :--- | :--- | :--- |
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - code | string | 指数代码 | 600004.SH |
| - name | string | 指数名称 | 2021-10-10 |

请求URL示例:
https://www.stockapi.com.cn/v1/base/ZSCode?token=你的token

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "code": "zs000001",
      "name": "上证指数"
    }
  ]
}
```

---

## 基金

### 所有ETF代码

接口说明：
接口说明：所有ETF代码
更新时间：交易日15点30
接口地址：https://www.stockapi.com.cn/v1/fund/etf
请求方式：GET
请求频率: 40次/秒

请求参数：
页面未提供

响应参数：
| 参数名 | 类型     | 说明   | 示例    |
|--------|----------|--------|---------|
| code   | int      | 返回码 | 20000   |
| msg    | string   | 状态   | success |
| data   | Object[] |        |         |
| - code | string   | 代码   | 159707  |
| - name | string   | ETF名称| 地产ETF |

请求URL示例：
https://www.stockapi.com.cn/v1/fund/etf?token=你的token

响应JSON示例：
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "code": "159707",
      "name": "地产ETF"
    }
  ]
}
```

---

### 查询基金列表

接口说明:
接口说明文字: 查询基金列表
更新时间: 交易日15点30
接口地址URL: https://www.stockapi.com.cn/v1/fund/all
请求方式: GET
请求频率: 40次/秒

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| keyWords | string | 否 | 页面未提供 | 支持基金代码和名称模糊查询(非必填) | 159713 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - code | string | 代码 | 000031 |
| - type | string | 基金类型 | 混合型-偏股 |
| - name | string | 基金名称 | 华夏复兴混合 |

请求URL示例:
https://www.stockapi.com.cn/v1/fund/all?token=你的token

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "code": "000031",
      "name": "华夏复兴混合",
      "type": "混合型-偏股"
    }
  ]
}
```

---

## 涨停股池

### 强势股池

接口说明：
接口说明：强势股池
更新时间：交易日15点30
接口地址：https://www.stockapi.com.cn/v1/base/QSPool
请求方式：GET
请求频率: 40次/秒

请求参数：
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
| --- | --- | --- | --- | --- | --- |
| date | string | 是 | | 交易时间，格式：2022-09-16 | 2022-09-16 |

响应参数：
| 参数名 | 类型 | 说明 | 示例 |
| --- | --- | --- | --- |
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - code | string | 代码 | 000419 |
| - name | string | 名称 | 通程控股 |
| - changeRatio | string | 涨跌幅% | 10.01 |
| - lastPrice | string | 最新价 | 5.91 |
| - amount | string | 成交额 | 142304401 |
| - flowCapital | string | 流通市值 | 3210902084 |
| - totalCapital | string | 总市值 | 3212573497 |
| - turnoverRatio | string | 换手率% | 4.610971 |
| - zttj | string | 涨停统计 | {'days':3,'ct':2}1 |
| - zs | string | 涨速 | 0.0 |
| - nh | string | 是否新高，0-否，1-是 | 0 |
| - lb | string | 量比 | 1.2846934795379639 |
| - industry | string | 所属行业 | 商业百货 |
| - time | string | 时间 | 2022-09-16 |
| - gl | string | 概念 | 光伏设备,江苏版块 |

请求URL示例：
https://www.stockapi.com.cn/v1/base/QSPool?date=2022-09-16

响应JSON示例：
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "turnoverRatio": 4.610971,
      "amount": 142304401,
      "code": "000419",
      "totalCapital": 3212573497,
      "zttj": "{'days':0,'ct':0}",
      "industry": "商业百货",
      "flowCapital": 3210902084,
      "name": "通程控股",
      "changeRatio": 10.055866,
      "zs": "0.0",
      "nh": 1,
      "time": "2022-09-16",
      "lastPrice": 5.91
    }
  ]
}
```

---

### 次新股池

接口说明:
接口说明文字: 次新股池
更新时间: 交易日15点30
接口地址URL: https://www.stockapi.com.cn/v1/base/CXPool
请求方式: GET
请求频率: 40次/秒

请求参数:
| 参数名 | 类型   | 是否必须 | 默认值 | 说明 | 示例 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| date | string | 是 | | 交易时间，格式：2022-09-16 | 2022-09-16 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
| :--- | :--- | :--- | :--- |
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - code | string | 代码 | 000419 |
| - name | string | 名称 | 通程控股 |
| - changeRatio | string | 涨跌幅% | 10.01 |
| - lastPrice | string | 最新价 | 5.91 |
| - amount | string | 成交额 | 142304401 |
| - flowCapital | string | 流通市值 | 3210902084 |
| - totalCapital | string | 总市值 | 3212573497 |
| - turnoverRatio | string | 换手率% | 4.610971 |
| - zttj | string | 涨停统计 | [object Object] |
| - ipod | string | 上市日期 | 20211019 |
| - ods | string | 开板几日 | 226 |
| - nh | string | 是否新高，0-否，1-是 | 0 |
| - od | string | 开板日期 | 20211019 |
| - industry | string | 所属行业 | 商业百货 |
| - time | string | 时间 | 2022-09-16 |
| - gl | string | 概念 | 光伏设备,江苏版块 |

请求URL示例:
https://www.stockapi.com.cn/v1/base/CXPool?date=2022-09-08

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "turnoverRatio": 4.610971,
      "amount": 142304401,
      "code": "000419",
      "totalCapital": 3212573497,
      "zttj": {
        "ct": 0,
        "days": 0
      },
      "industry": "商业百货",
      "flowCapital": 3210902084,
      "ipod": "20211019",
      "od": "20211019",
      "name": "通程控股",
      "changeRatio": 10.055866,
      "nh": 1,
      "time": "2022-09-16",
      "ods": 226,
      "lastPrice": 5.91
    }
  ]
}
```

---

### 涨停股池

接口说明:
接口说明文字: 涨停股池
更新时间: 交易日15点30
接口地址URL: https://www.stockapi.com.cn/v1/base/ZTPool
请求方式: GET
请求频率: 40次/秒

请求参数:
| 参数名 | 类型   | 是否必须 | 默认值 | 说明 | 示例 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| date | string | 是 | 页面未提供 | 交易时间，格式：2022-09-16 | 2022-09-16 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
| :--- | :--- | :--- | :--- |
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - code | string | 代码 | 000419 |
| - name | string | 名称 | 通程控股 |
| - changeRatio | string | 涨跌幅% | 10.01 |
| - lastPrice | string | 最新价 | 5.91 |
| - amount | string | 成交额 | 142304401 |
| - flowCapital | string | 流通市值 | 3210902084 |
| - totalCapital | string | 总市值 | 3212573497 |
| - turnoverRatio | string | 换手率% | 4.610971 |
| - ceilingAmount | string | 封板资金 | 102224679 |
| - firstCeilingTime | string | 首次封板时间 | 134027 |
| - lastCeilingTime | string | 最后封板时间 | 134027 |
| - bombNum | string | 炸板次数 | 0 |
| - lbNum | string | 连扳数量 | 1 |
| - industry | string | 所属行业 | 商业百货 |
| - time | string | 时间 | 2022-09-16 |
| - gl | string | 概念 | 光伏设备,江苏版块 |
| - stock_reason | string | 股票涨停原因 | 页面未提供 |
| - plate_reason | string | 主题上涨原因 | 页面未提供 |
| - plate_name | string | 涨停主题 | 页面未提供 |

请求URL示例:
https://www.stockapi.com.cn/v1/base/ZTPool?date=2022-09-16

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "turnoverRatio": 4.610971,
      "amount": 142304401,
      "code": "000419",
      "totalCapital": 3212573497,
      "lastCeilingTime": "134027",
      "industry": "商业百货",
      "ceilingAmount": 102224679,
      "flowCapital": 3210902084,
      "firstCeilingTime": "134027",
      "lbNum": 1,
      "name": "通程控股",
      "changeRatio": 10.055866,
      "time": "2022-09-16",
      "bombNum": 0,
      "lastPrice": 5.91
    }
  ]
}
```

---

### 炸板股池

接口说明:
- 接口说明文字: 炸板股池
- 更新时间: 交易日15点30
- 接口地址URL: https://www.stockapi.com.cn/v1/base/ZBPool
- 请求方式: GET
- 请求频率: 40次/秒

请求参数:
| 参数名 | 类型   | 是否必须 | 默认值 | 说明 | 示例 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| date | string | 是 | 页面未提供 | 交易时间，格式：2022-09-16 | 2022-09-16 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
| :--- | :--- | :--- | :--- |
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - code | string | 代码 | 000419 |
| - name | string | 名称 | 通程控股 |
| - changeRatio | string | 涨跌幅% | 10.01 |
| - lastPrice | string | 最新价 | 5.91 |
| - amount | string | 成交额 | 142304401 |
| - flowCapital | string | 流通市值 | 3210902084 |
| - totalCapital | string | 总市值 | 3212573497 |
| - turnoverRatio | string | 换手率% | 4.610971 |
| - ceilingAmount | string | 封板资金 | 102224679 |
| - firstCeilingTime | string | 首次封板时间 | 134027 |
| - bombNum | string | 炸板次数 | 0 |
| - zttj | string | 涨停统计 | [object Object] |
| - ipod | string | 上市日期 | 20211019 |
| - zs | string | 涨速% | 0 |
| - nh | string | 是否新高，0-否，1-是 | 0 |
| - industry | string | 所属行业 | 商业百货 |
| - time | string | 时间 | 2022-09-16 |
| - gl | string | 概念 | 光伏设备,江苏版块 |

请求URL示例:
https://www.stockapi.com.cn/v1/base/ZBPool?date=2022-09-16

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "turnoverRatio": 4.610971,
      "amount": 142304401,
      "code": "000419",
      "totalCapital": 3212573497,
      "zttj": {
        "ct": 0,
        "days": 0
      },
      "industry": "商业百货",
      "flowCapital": 3210902084,
      "ipod": "20211019",
      "name": "通程控股",
      "changeRatio": 10.055866,
      "zs": -0.1,
      "time": "2022-09-16",
      "lastPrice": 5.91
    }
  ]
}
```

---

### 跌停股池

接口说明:
接口说明文字: 跌停股池
更新时间: 交易日15点30
接口地址URL: https://www.stockapi.com.cn/v1/base/DTPool
请求方式: GET
请求频率: 40次/秒

请求参数表格:
| 参数名 | 类型   | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| date | string | 是 | 页面未提供 | 交易时间，格式：2022-09-16 | 2022-09-16 |

响应参数表格:
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - code | string | 代码 | 000419 |
| - name | string | 名称 | 通程控股 |
| - changeRatio | string | 涨跌幅% | 10.01 |
| - lastPrice | string | 最新价 | 5.91 |
| - amount | string | 成交额 | 142304401 |
| - flowCapital | string | 流通市值 | 3210902084 |
| - totalCapital | string | 总市值 | 3212573497 |
| - turnoverRatio | string | 换手率% | 4.610971 |
| - ceilingAmount | string | 封板资金 | 102224679 |
| - firstCeilingTime | string | 首次封板时间 | 134027 |
| - lastCeilingTime | string | 最后封板时间 | 134027 |
| - pe | string | 动态市盈率 | 27 |
| - fba | string | 板上成交额 | 33023498 |
| - days | string | 连续跌停天数 | 1 |
| - oc | string | 开板次数 | 2 |
| - industry | string | 所属行业 | 商业百货 |
| - time | string | 时间 | 2022-09-16 |
| - gl | string | 概念 | 光伏设备,江苏版块 |

请求URL示例:
https://www.stockapi.com.cn/v1/base/DTPool?token=你的token&date=2022-09-16

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "turnoverRatio": 4.610971,
      "amount": 142304401,
      "code": "000419",
      "fba": 33023498,
      "totalCapital": 3212573497,
      "industry": "商业百货",
      "flowCapital": 3210902084,
      "oc": 2,
      "pe": 27,
      "name": "通程控股",
      "changeRatio": 10.055866,
      "days": 1,
      "time": "2022-09-16",
      "lastPrice": 5.91
    }
  ]
}
```

---

## 概念板块

### 板块、概念历史资金流

接口说明:
接口说明：概念代码
更新时间：交易日15点30
接口地址：https://www.stockapi.com.cn/v1/base/bkFlowHistory
请求方式：GET
请求频率: 40次/秒

请求参数:
| 参数名  | 类型   | 是否必须 | 默认值 | 说明         | 示例   |
| :------- | :----- | :------- | :----- | :----------- | :----- |
| bkCode   | string | 是       |        | 板块、概念代码 | BK1036 |

响应参数:
| 参数名                      | 类型     | 说明              | 示例        |
| :-------------------------- | :------- | :---------------- | :---------- |
| code                        | int      | 返回码            | 20000       |
| msg                         | string   | 状态              | success     |
| data                        | Object[] |                   |             |
| - time                      | string   | 时间              | 2022-07-04  |
| - mainAmount                | string   | 主力净流入净额    | -4138475280 |
| - minAmount                 | string   | 小单净流入净额    | 3404481792  |
| - middleAmount              | string   | 中单净流入净额    | 733993728   |
| - bigAmount                 | string   | 大单净流入净额    | -4138475280 |
| - supperBigAmount           | string   | 超大单净流入净额  | -4138475280 |
| - mainAmountPercentage      | string   | 主力净流入净占比  | -4138475280 |
| - minAmountPercentage       | string   | 小单净流入净占比  | -4138475280 |
| - middleAmountPercentage    | string   | 中单净流入净占比  | -4138475280 |
| - bigAmountPercentage       | string   | 大单净流入净占比  | -4138475280 |
| - supperBigAmountPercentage | string   | 超大单净流入净占比| -4138475280 |

请求URL示例:
https://www.stockapi.com.cn/v1/base/bkFlowHistory?bkCode=BK1036

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "supperBigAmount": -1615579152,
      "minAmount": 3404481792,
      "middleAmount": 733993728,
      "minAmountPercentage": "6.39%",
      "bigAmount": -2522896128,
      "supperBigAmountPercentage": "-3.03%",
      "mainAmountPercentage": "-7.77%",
      "mainAmount": -4138475280,
      "time": "2022-07-04",
      "bigAmountPercentage": "-4.74%",
      "middleAmountPercentage": "1.38%"
    }
  ]
}
```

---

### 板块、概念成分股列表

接口说明:
接口说明文字: 板块、概念个股列表
更新时间: 交易日15:30
接口地址URL: https://www.stockapi.com.cn/v1/base/bkList
请求方式: GET
请求频率: 1次/秒

请求参数:
| 参数名  | 类型   | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| bkCode | string | 是 | 页面未提供 | 板块、概念代码 | BK1036 |
| pageNo | string | 是 | 1 | 页码 | 1 |
| pageSize | string | 是 | 50 | 每页行数 | 50 |

响应参数:
| 参数名  | 类型   | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | 页面未提供 | 页面未提供 |
| - f1 | string | 序号 | 2 |
| - f2 | string | 最新价 | 90.8 |
| - f3 | string | 今日涨跌幅 | -0.69% |
| - f12 | string | 股票代码 | 300223 |
| - f13 | string | 0 | 页面未提供 |
| - f14 | string | 股票名称 | 北京君正 |
| - f62 | string | 今日主力净流入净额 | 42552789 |
| - f66 | string | 今日超大单净流入净额 | 5038315 |
| - f69 | string | 今日超大单净流入占比 | 0.6% |
| - f72 | string | 今日大单净流入净额 | 37514474 |
| - f75 | string | 今日大单净流入占比 | 4.49% |
| - f78 | string | 今日中单净流入净额 | 22833456 |
| - f81 | string | 今日中单净流入占比 | 2.73% |
| - f84 | string | 今日小单净流入净额 | -65386248 |
| - f87 | string | 今日小单净流入占比 | -7.83% |
| - f184 | string | 今日主力净流入净额占比 | 2% |

请求URL示例:
https://www.stockapi.com.cn/v1/base/bkList?bkCode=BK1036&pageNo=1&pageSize=50

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "f72": 37514474,
      "f124": 1653464073,
      "f62": 42552789,
      "f84": -65386248,
      "f87": -7.83,
      "f75": 4.49,
      "f12": "300223",
      "f78": 22833456,
      "f66": 5038315,
      "f14": "北京君正",
      "f69": 0.6,
      "f184": 5.1,
      "f13": 0,
      "f1": 2,
      "f2": 90.8,
      "f3": -0.69,
      "f81": 2.73
    }
  ]
}
```

---

### 板块代码

接口说明:
接口说明文字: 板块代码
更新时间: 交易日15点30
接口地址URL: https://www.stockapi.com.cn/v1/base/bk
请求方式: GET
请求频率: 40次/秒

请求参数表格:
页面未提供

响应参数表格:
| 参数名 | 类型 | 说明 | 示例 |
| :--- | :--- | :--- | :--- |
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - name | string | 板块名称 | 包装材料 |
| - plateCode | string | 板块代码 | BK0733 |

请求URL示例:
https://www.stockapi.com.cn/v1/base/bk?token=你的token

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "name": "包装材料",
      "plateCode": "BK0733"
    }
  ]
}
```

---

### 概念代码

接口说明:
接口说明文字: 概念代码
更新时间: 交易日15点30
接口地址URL: https://www.stockapi.com.cn/v1/base/gn
请求方式: GET
请求频率: 40次/秒

请求参数:
页面未提供

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
| :--- | :--- | :--- | :--- |
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - name | string | 板块名称 | 包装材料 |
| - plateCode | string | 板块代码 | BK0733 |

请求URL示例:
普通请求URL，每日免费1000次: https://www.stockapi.com.cn/v1/base/gn
带Token请求URL: https://www.stockapi.com.cn/v1/base/gn?token=你的token

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "name": "包装材料",
      "plateCode": "BK0733"
    }
  ]
}
```

---

## 异动数据

### 全量异动数据历史

接口说明:
接口说明: 全量异动数据历史
更新时间: 交易日下午4点30分
接口地址: https://www.stockapi.com.cn/v1/change/allHistory
请求方式: GET
请求频率: 40次/秒

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| startDate | string | 是 | | 开始时间 | 2023-03-21 |
| endDate | string | 是 | | 结束时间 | 2023-03-21 |
| type | string | 是 | 8201 | 异动类型 | 8201:火箭发射, 8202:快速反弹, 8207:竞价上涨, 8209:高开5日线, 8211:向上缺口, 8215:60日大幅上涨, 8204:加速下跌, 8203:高台跳水, 8208:竞价下跌, 8210:低开5日线, 8212:向下缺口, 8216:60日大幅下跌, 8193:大笔买入, 8194:大笔卖出, 64:有大买盘, 128:有大卖盘, 4:封涨停板, 32:打开跌停板, 8213:60日新高, 8:封跌停板, 16:打开涨停板, 8214:60日新低 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - time | string | 异动时间 | 145553 |
| - code | string | 股票代码 | 873152 |
| - name | string | 股票名称 | 天宏锂电 |
| - type | string | 异动类型 | 8201 |
| - info | string | 异动信息 | 26.13% |
| - typeName | string | 异动名称 | 火箭发射 |
| - dateId | string | 日期 | 2023-03-21 |

请求URL示例:
https://www.stockapi.com.cn/v1/change/allHistory?endDate=2023-03-22&startDate=2023-03-21&type=8201

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "code": "000419",
      "name": "通程控股",
      "dateId": "2023-03-21",
      "typeName": "火箭发射",
      "time": 145553,
      "type": 8201,
      "info": "26.13%"
    }
  ]
}
```

---

### 股票异动数据历史

# 股票异动数据历史

#### 所属分类
异动数据

#### 接口说明

- **接口说明**: 股票异动数据历史
- **更新时间**: 交易日下午4点30分
- **接口地址**: https://www.stockapi.com.cn/v1/change/codeHistory
- **请求方式**: GET
- **请求频率**: 40次/秒

#### 请求参数

| 参数名    | 类型   | 是否必须 | 默认值 | 说明     | 示例       |
| --------- | ------ | -------- | ------ | -------- | ---------- |
| code      | string | 是       |        | 股票代码 | 300688     |
| startDate | string | 是       |        | 开始时间 | 2023-03-21 |
| endDate   | string | 是       |        | 结束时间 | 2023-03-24 |

#### 响应参数

| 参数名   | 类型     | 说明     | 示例       |
| -------- | -------- | -------- | ---------- |
| code     | int      | 返回码   | 20000      |
| msg      | string   | 状态     | success    |
| data     | Object[] |          |            |
| - time   | string   | 异动时间 | 145553     |
| - code   | string   | 股票代码 | 873152     |
| - name   | string   | 股票名称 | 天宏锂电   |
| - type   | string   | 异动类型 | 8201       |
| - info   | string   | 异动信息 | 26.13%     |
| - typeName | string   | 异动名称 | 火箭发射   |
| - dateId | string   | 日期     | 2023-03-21 |

#### 请求URL示例

```
https://www.stockapi.com.cn/v1/change/codeHistory?endDate=2023-12-22&startDate=2023-12-21&code=300688
```

#### 响应JSON示例

```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "code": "000419",
      "name": "通程控股",
      "dateId": "2023-03-21",
      "typeName": "火箭发射",
      "time": 145553,
      "type": 8201,
      "info": "26.13%"
    }
  ]
}
```

---

## 龙虎游资

### 个股游资上榜交割单

接口说明:
接口说明文字: 个股游资上榜交割单
更新时间: 交易日下午5点40
接口地址URL: https://www.stockapi.com.cn/v1/youzi/gegu
请求方式: GET
请求频率: 40次/秒

请求参数表格:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| code | string | 是 | | 股票代码 | 001337 |
| startDate | string | 是 | | 开始时间 | 2023-03-21 |
| endDate | string | 是 | | 结束时间 | 2023-03-24 |

响应参数表格:
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - yzmc | string | 游资名称 | 92科比 |
| - yyb | string | 营业部 | 兴业证券股份有限公司南京天元东路证券营业部 |
| - sblx | string | 单日榜或三日榜 | 1 |
| - gpdm | string | 股票代码 | 001337 |
| - gpmc | string | 股票名称 | 四川黄金 |
| - mrje | string | 买入金额 | 14470401 |
| - mcje | string | 卖出金额 | 15080 |
| - jlrje | string | 净流入金额 | 14455321 |
| - rq | string | 日期 | 2023-03-22 |
| - gl | string | 概念 | 贵金属,四川板块,昨日连板_含一字,昨日涨停_含一字,黄金概念,次新股 |

请求URL示例:
https://www.stockapi.com.cn/v1/youzi/gegu?code=001337&endDate=2023-03-24&startDate=2023-03-21

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "gpdm": "001337",
      "mcje": "15080",
      "yyb": "兴业证券股份有限公司南京天元东路证券营业部",
      "mrje": "14470401",
      "jlrje": "14455321",
      "gl": "贵金属,四川板块,昨日连板_含一字,昨日涨停_含一字,黄金概念,次新股",
      "rq": "2023-03-22",
      "gpmc": "四川黄金",
      "yzmc": "92科比"
    }
  ]
}
```

---

### 全量游资上榜交割单历史

接口说明:
接口说明: 全量游资上榜交割单历史
更新时间: 交易日下午5点40
接口地址: https://www.stockapi.com.cn/v1/youzi/all
请求方式: GET
请求频率: 40次/秒

请求参数:
| 参数名 | 类型   | 是否必须 | 默认值 | 说明 | 示例       |
| ------ | ------ | -------- | ------ | ---- | ---------- |
| date   | string | 是       |        | 时间 | 2023-03-21 |

响应参数:
| 参数名 | 类型     | 说明         | 示例                                       |
| ------ | -------- | ------------ | ------------------------------------------ |
| code   | int      | 返回码       | 20000                                      |
| msg    | string   | 状态         | success                                    |
| data   | Object[] |              |                                            |
| - yzmc | string   | 游资名称     | 92科比                                     |
| - yyb  | string   | 营业部       | 兴业证券股份有限公司南京天元东路证券营业部 |
| - sblx | string   | 单日榜或三日榜 | 1                                          |
| - gpdm | string   | 股票代码     | 001337                                     |
| - gpmc | string   | 股票名称     | 四川黄金                                   |
| - mrje | string   | 买入金额     | 14470401                                   |
| - mcje | string   | 卖出金额     | 15080                                      |
| - jlrje| string   | 净流入金额   | 14455321                                   |
| - rq   | string   | 日期         | 2023-03-22                                 |
| - gl   | string   | 概念         | 贵金属,四川板块,昨日连板_含一字,昨日涨停_含一字,黄金概念,次新股 |

请求URL示例:
https://www.stockapi.com.cn/v1/youzi/all?date=2023-03-24

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "gpdm": "001337",
      "mcje": "15080",
      "yyb": "兴业证券股份有限公司南京天元东路证券营业部",
      "mrje": "14470401",
      "jlrje": "14455321",
      "gl": "贵金属,四川板块,昨日连板_含一字,昨日涨停_含一字,黄金概念,次新股",
      "rq": "2023-03-22",
      "gpmc": "四川黄金",
      "yzmc": "92科比"
    }
  ]
}
```

---

### 单个游资上榜交割单历史

接口说明：
接口说明文字：单个游资上榜交割单历史
更新时间：交易日下午5点40
接口地址URL：https://www.stockapi.com.cn/v1/youzi/jgdhis
请求方式：GET
请求频率：40次/秒

请求参数：
| 参数名 | 类型   | 是否必须 | 默认值 | 说明     | 示例       |
|--------|--------|----------|--------|----------|------------|
| yzmc   | string | 是       |        | 游资名称 | 上塘路     |
| date   | string | 是       |        | 时间     | 2023-03-21 |

响应参数：
| 参数名 | 类型     | 说明                                       | 示例                                         |
|--------|----------|--------------------------------------------|----------------------------------------------|
| code   | int      | 返回码                                     | 20000                                        |
| msg    | string   | 状态                                       | success                                      |
| data   | Object[] |                                            |                                              |
| - yzmc | string   | 游资名称                                   | 92科比                                       |
| - yyb  | string   | 营业部                                     | 兴业证券股份有限公司南京天元东路证券营业部 |
| - sblx | string   | 单日榜或三日榜                             | 1                                            |
| - gpdm | string   | 股票代码                                   | 001337                                       |
| - gpmc | string   | 股票名称                                   | 四川黄金                                     |
| - mrje | string   | 买入金额                                   | 14470401                                     |
| - mcje | string   | 卖出金额                                   | 15080                                        |
| - jlrje| string   | 净流入金额                                 | 14455321                                     |
| - rq   | string   | 日期                                       | 2023-03-22                                   |
| - gl   | string   | 概念                                       | 贵金属,四川板块,昨日连板_含一字,昨日涨停_含一字,黄金概念,次新股 |

请求URL示例：
https://www.stockapi.com.cn/v1/youzi/jgdhis?yzmc=上塘路&date=2023-03-24

响应JSON示例：
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "gpdm": "001337",
      "mcje": "15080",
      "yyb": "兴业证券股份有限公司南京天元东路证券营业部",
      "mrje": "14470401",
      "jlrje": "14455321",
      "gl": "贵金属,四川板块,昨日连板_含一字,昨日涨停_含一字,黄金概念,次新股",
      "rq": "2023-03-22",
      "gpmc": "四川黄金",
      "yzmc": "92科比"
    }
  ]
}
```

---

### 获取游资名称

接口说明:
接口说明文字: 获取游资名称
更新时间: 交易日下午5点40
接口地址URL: https://www.stockapi.com.cn/v1/youzi/name
请求方式: GET
请求频率: 40次/秒

请求参数表格:
页面未提供

响应参数表格:
| 参数名 | 类型 | 说明 | 示例 |
| --- | --- | --- | --- |
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - youziName | string | 游资名称 | 章盟主 |
| - cpfg | string | 操盘风格 | 页面未提供 |

请求URL示例:
https://www.stockapi.com.cn/v1/youzi/name

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "cpfg": "说到中国最早的游资，只有两个人有这个资格，一个就是“敢死队总舵主”徐翔，另一个就是我们今天说的被称为游资“盟主”的章建平，章盟主是“60后”的老大，短线手法非常犀利，更厉害的是据说他没有任何助手，所有东西都是自己一个人做。",
      "youziName": "章盟主"
    }
  ]
}
```

---

## 附加增值接口

### 次日涨停价/新股涨停价

接口说明：
接口说明文字：计算次日/新股上市涨停价
更新时间：任意时间都可调用
接口地址URL：https://www.stockapi.com.cn/v1/chrome/limitUp
请求方式：GET
请求频率：40次/秒

请求参数表格：
| 参数名 | 类型   | 是否必须 | 默认值 | 说明                                       | 示例  |
|--------|--------|----------|--------|--------------------------------------------|-------|
| flag   | string | 是       | 页面未提供 | 1-涨停5%，2-涨停10%，3-涨停44%，4-涨停20% | 2     |
| close  | string | 是       | 页面未提供 | 昨日收盘价                                 | 10.01 |

响应参数表格：
| 参数名 | 类型   | 说明   | 示例    |
|--------|--------|--------|---------|
| code   | int    | 返回码 | 20000   |
| msg    | string | 状态   | success |
| data   | string | 涨停价 | 11.01   |

请求URL示例：
https://www.stockapi.com.cn/v1/chrome/limitUp?flag=2&close=10.01

响应JSON示例：
```json
{
  "msg": "success",
  "code": 20000,
  "data": "2.32"
}
```

---

### 股票人气排行榜

接口说明:
接口说明：股票人气排名
更新时间：每隔30分钟一次
接口地址：https://www.stockapi.com.cn/v1/change/renQi
请求方式：GET
请求频率: 40次/秒

请求参数:
页面未提供

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
| --- | --- | --- | --- |
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - code | string | 股票代码 | 002261 |
| - price | string | 价格 | 17.63 |
| - changeRatio | string | 涨幅 | 9.98 |
| - name | string | 股票名称 | 拓维信息 |

请求URL示例:
普通请求URL: https://www.stockapi.com.cn/v1/change/renQi
带Token请求URL: https://www.stockapi.com.cn/v1/change/renQi?token=你的token

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "code": "002261",
      "price": "17.63",
      "name": "拓维信息",
      "changeRatio": "9.98"
    }
  ]
}
```

---

## 竞价专题

### 早盘热点板块竞价

接口说明：
接口说明文字：早盘热点板块or极速下跌板块竞价，方便提前发现资金今日的方向
更新时间：交易日上午9点26分更新
接口地址URL：https://www.stockapi.com.cn/v1/base/bkjj
请求方式：GET
请求频率：40次/秒

请求参数：
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| startDate | string | 是 | | 开始时间 | 2023-09-01 |
| endDate | string | 是 | | 结束时间 | 2023-09-01 |
| type | string | 是 | | 0-看空，1-看多 | 1 |

响应参数：
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - bkCode | string | 板块代码 | 880482 |
| - bkName | string | 板块名称 | 房地产 |
| - ld | string | 看多or看空力度，数值越大越好 | 97.9798 |
| - jjzf | string | 竞价涨幅 | 1.5307 |
| - szjs | string | 上涨家数 | 29 |
| - xdjs | string | 下跌家数 | 72 |
| - type | string | 1-看多，0-看空 | 1 |
| - date | string | 时间 | 2023-09-01 |

请求URL示例：
https://www.stockapi.com.cn/v1/base/bkjj?endDate=2023-09-01&startDate=2023-09-01&type=1

响应JSON示例：
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "date": "2023-09-01",
      "szjs": 29,
      "bkName": "房地产",
      "ld": "97.9798",
      "bkCode": "880482",
      "type": 1,
      "jjzf": "1.5307",
      "xdjs": 72
    }
  ]
}
```

---

### 早盘热点板块竞价所属个股

接口说明：
接口说明文字：早盘热点板块竞价所属个股, 有助于将挖掘涨停潜力个股
更新时间：交易日上午9点26分更新
接口地址URL：https://www.stockapi.com.cn/v1/base/bkCodeList
请求方式：GET
请求频率：40次/秒

请求参数：
| 参数名    | 类型   | 是否必须 | 默认值 | 说明       | 示例       |
| --------- | ------ | -------- | ------ | ---------- | ---------- |
| startDate | string | 是       | 页面未提供 | 开始时间   | 2023-09-01 |
| endDate   | string | 是       | 页面未提供 | 结束时间   | 2023-09-01 |
| bkCode    | string | 是       | 页面未提供 | 热点板块代码 | 880431     |

响应参数：
| 参数名   | 类型     | 说明                 | 示例       |
| -------- | -------- | -------------------- | ---------- |
| code     | int      | 返回码               | 20000      |
| msg      | string   | 状态                 | success    |
| data     | Object[] |                      |            |
| - bkCode | string   | 板块代码             | 880482     |
| - bkName | string   | 板块名称             | 房地产     |
| - type   | string   | 1：看多，0看空       | 97.9798    |
| - code   | string   | 代码                 | 600685     |
| - name   | string   | 名称                 | 中船防务   |
| - jjzf   | string   | 竞价涨幅             | 0.2925     |
| - date   | string   | 时间                 | 2023-09-01 |
| - preLbNum| string   | 上一个交易日连板数   | 1          |
| - preZttj| string   | 上一个交易日几天几板 | 1          |
| - preDate| string   | 上一个涨停交易日     | 2023-08-31 |

请求URL示例：
https://www.stockapi.com.cn/v1/base/bkCodeList?endDate=2023-09-01&startDate=2023-09-01&bkCode=880431

响应JSON示例：
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "date": "2023-09-01",
      "code": "300589",
      "preDate": "",
      "bkName": "船舶",
      "name": "江龙船艇",
      "bkCode": "880431",
      "type": 0,
      "jjzf": "-0.2926",
      "preLbNum": "0",
      "preZttj": ""
    }
  ]
}
```

---

## 竞价专题增强版

### 增强版热点板块竞价

接口说明：
接口说明文字：早盘热点板块or极速下跌板块竞价，方便提前发现资金今日的方向
更新时间：交易日上午9点26分更新
接口地址URL：https://www.stockapi.com.cn/v1/base/bkjjzq
请求方式：GET
请求频率：40次/秒

请求参数表格：
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| tradeDate | string | 是 | 页面未提供 | 时间 | 2023-11-08 |

响应参数表格：
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - bkCode | string | 板块代码 | 880482 |
| - bkName | string | 板块名称 | 房地产 |
| - jjzf | string | 竞价涨幅 | 1.5307 |
| - szjs | string | 上涨家数 | 29 |
| - xdjs | string | 下跌家数 | 72 |
| - date | string | 时间 | 2023-09-01 |

请求URL示例：
https://www.stockapi.com.cn/v1/base/bkjjzq?tradeDate=2023-11-08

响应JSON示例：
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "date": "2023-09-01",
      "szjs": 29,
      "bkName": "房地产",
      "bkCode": "880482",
      "jjzf": "1.5307",
      "xdjs": 72
    }
  ]
}
```

---

### 增强版热点板块竞价所属个股

接口说明：
接口说明文字：早盘热点板块竞价所属个股，有助于将挖掘涨停潜力个股
更新时间：交易日上午9点26分更新
接口地址URL：https://www.stockapi.com.cn/v1/base/zqbkCodeList
请求方式：GET
请求频率：40次/秒

请求参数表格：
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| tradeDate | string | 是 | 页面未提供 | 开始时间 | 2023-11-03 |
| bkCode | string | 是 | 页面未提供 | 热点板块代码 | 880431 |

响应参数表格：
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - bkCode | string | 板块代码 | 880482 |
| - bkName | string | 板块名称 | 房地产 |
| - type | string | 1：看多，0看空 | 97.9798 |
| - code | string | 代码 | 600685 |
| - name | string | 名称 | 中船防务 |
| - jjzf | string | 竞价涨幅 | 0.2925 |
| - date | string | 时间 | 2023-09-01 |
| - preLbNum | string | 上一个交易日连板数 | 1 |
| - preZttj | string | 上一个交易日几天几板 | 1 |
| - preDate | string | 上一个涨停交易日 | 2023-08-31 |

请求URL示例：
https://www.stockapi.com.cn/v1/base/zqbkCodeList?tradeDate=2023-11-17&bkCode=37112745

响应JSON示例：
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "date": "2023-09-01",
      "code": "300589",
      "preDate": "",
      "bkName": "船舶",
      "name": "江龙船艇",
      "bkCode": "880431",
      "type": 0,
      "jjzf": "-0.2926",
      "preLbNum": "0",
      "preZttj": ""
    }
  ]
}
```

---

### 竞价一字板

接口说明:
接口说明：竞价一字板，黄金可用
更新时间: 交易日9：27
接口地址：https://www.stockapi.com.cn/v1/jjyizi/list
请求方式：GET
请求频率：40次/秒

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
| --- | --- | --- | --- | --- | --- |
| tradeDate | string | 是 | | 时间 | 2025-08-22 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
| --- | --- | --- | --- |
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - dtCount | int | 跌停数量 | |
| - zt1Count | int | 涨停一板数量 | |
| - zt2Count | String | 涨停二板以上数量 | |
| - todayList | int | 涨停列表 | |
| -- code | String | 股票代码 | |
| -- fde | String | 今日封单额 | |
| -- fdeDiff | String | 增减单额，，昨日竞价一字板才有这个值，是于昨日比较的增减单额 | |
| -- jjPrice | String | 价格 | |
| -- lb | String | 连板 | |
| -- ltsz | String | 流通市值 | |
| -- name | String | 股票名称 | |
| -- time | String | 时间 | |
| -- 涨停板块 | String | ztyy | |

请求URL示例:
普通请求URL，每日免费1000次: https://www.stockapi.com.cn/v1/jjyizi/list?tradeDate=2025-08-22
带Token请求URL： https://www.stockapi.com.cn/v1/jjyizi/list?tradeDate=2025-08-22&token=你的token

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": {
    "todayList": [
      {
        "code": "300192",
        "ztyy": "东数西算/算力",
        "lb": 1,
        "fde": 1126816644,
        "name": "科德教育",
        "id": 885,
        "time": "2025-08-22",
        "jjPrice": "21.590000",
        "type": 1,
        "fdeDiff": 1126816644,
        "ltsz": 6976502548
      }
    ],
    "dtCount": 0,
    "zt1Count": 3,
    "zt2Count": 3
  }
}
```

---

## 竞价抢筹

### 尾盘抢筹委托金额排序

接口说明：
接口说明文字：尾盘抢筹委托金额排序，黄金可用
更新时间：交易日15：10
接口地址URL：https://www.stockapi.com.cn/v1/base/jjqc
请求方式：GET
请求频率：40次/秒

请求参数表格：
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| tradeDate | string | 是 | | 时间 | 2025-03-04 |
| period | string | 是 | 1 | 抢筹类型，0-竞价抢筹，1-尾盘抢筹 | 1 |
| type | string | 是 | 1 | 尾盘抢筹委托金额排序 | 1 |

响应参数表格：
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - name | String | 股票名称 | |
| - code | String | 代码 | |
| - openAmt | Long | 开盘金额 | |
| - qczf | Double | 抢筹涨幅 | |
| - qccje | String | 抢筹成交额 | |
| - qcwtje | Long | 抢筹委托金额 | |
| - type | int | 排序类型：1-按照抢筹委托金额排序，2-按照抢筹成交金额排序，3-按照收盘金额顺序排序，4-按照抢筹涨幅排序 | |
| - period | int | 抢筹类型，0-早盘竞价抢筹，1-尾盘抢筹 | |
| - time | String | 时间 | |

请求URL示例：
https://www.stockapi.com.cn/v1/base/jjqc?tradeDate=2025-03-04&period=1&type=1

响应JSON示例：
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "period": 0,
      "code": "002725",
      "qcwtje": 729434002,
      "name": "跃岭股份",
      "qczf": 9.98,
      "qccje": 5730304,
      "openAmt": 5730304,
      "time": "2025-03-04",
      "type": 1
    },
    {
      "period": 0,
      "code": "002227",
      "qcwtje": 5296440,
      "name": "奥 特 迅",
      "qczf": 10.02,
      "qccje": 5296440,
      "openAmt": 45699975,
      "time": "2025-03-04",
      "type": 1
    }
  ]
}
```

---

### 尾盘抢筹成交金额排序

接口说明:
接口说明文字: 尾盘抢筹成交金额排序。黄金100w可用
更新时间: 交易日15：10
接口地址URL: https://www.stockapi.com.cn/v1/base/jjqc
请求方式: GET
请求频率: 40次/秒

请求参数表格:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| tradeDate | string | 是 | | 时间 | 2025-03-04 |
| period | string | 是 | 1 | 抢筹类型，0-竞价抢筹，1-尾盘抢筹 | 1 |
| type | string | 是 | 2 | 尾盘抢筹成交金额排序 | 2 |

响应参数表格:
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - name | String | 股票名称 | |
| - code | String | 代码 | |
| - openAmt | Long | 开盘金额 | |
| - qczf | Double | 抢筹涨幅 | |
| - qccje | String | 抢筹成交额 | |
| - qcwtje | Long | 抢筹委托金额 | |
| - type | int | 排序类型：1-按照抢筹委托金额排序，2-按照抢筹成交金额排序，3-按照收盘金额顺序排序，4-按照抢筹涨幅排序 | |
| - period | int | 抢筹类型，0-早盘竞价抢筹，1-尾盘抢筹 | |
| - time | String | 时间 | |

请求URL示例:
https://www.stockapi.com.cn/v1/base/jjqc?tradeDate=2025-03-04&period=1&type=2

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "period": 0,
      "code": "002725",
      "qcwtje": 729434002,
      "name": "跃岭股份",
      "qczf": 9.98,
      "qccje": 5730304,
      "openAmt": 5730304,
      "time": "2025-03-04",
      "type": 1
    },
    {
      "period": 0,
      "code": "002227",
      "qcwtje": 5296440,
      "name": "奥 特 迅",
      "qczf": 10.02,
      "qccje": 5296440,
      "openAmt": 45699975,
      "time": "2025-03-04",
      "type": 1
    }
  ]
}
```

---

### 尾盘抢筹收盘金额排序

接口说明:
接口说明：尾盘抢筹收盘金额排序，黄金100w可用
更新时间: 交易日15：10
接口地址：https://www.stockapi.com.cn/v1/base/jjqc
请求方式：GET
请求频率：40次/秒

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| tradeDate | string | 是 | | 时间 | 2025-03-04 |
| period | string | 是 | 1 | 抢筹类型，0-竞价抢筹，1-尾盘抢筹 | 1 |
| type | string | 是 | 3 | 尾盘抢筹成交金额排序 | 3 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - name | String | 股票名称 | |
| - code | String | 代码 | |
| - openAmt | Long | 开盘金额 | |
| - qczf | Double | 抢筹涨幅 | |
| - qccje | String | 抢筹成交额 | |
| - qcwtje | Long | 抢筹委托金额 | |
| - type | int | 排序类型：1-按照抢筹委托金额排序，2-按照抢筹成交金额排序，3-按照收盘金额顺序排序，4-按照抢筹涨幅排序 | |
| - period | int | 抢筹类型，0-早盘竞价抢筹，1-尾盘抢筹 | |
| - time | String | 时间 | |

请求URL示例:
https://www.stockapi.com.cn/v1/base/jjqc?tradeDate=2025-03-04&period=1&type=3

响应JSON示例:
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "period": 0,
      "code": "002725",
      "qcwtje": 729434002,
      "name": "跃岭股份",
      "qczf": 9.98,
      "qccje": 5730304,
      "openAmt": 5730304,
      "time": "2025-03-04",
      "type": 1
    },
    {
      "period": 0,
      "code": "002227",
      "qcwtje": 5296440,
      "name": "奥 特 迅",
      "qczf": 10.02,
      "qccje": 5296440,
      "openAmt": 45699975,
      "time": "2025-03-04",
      "type": 1
    }
  ]
}

---

### 尾盘抢筹涨幅排序

接口说明：
接口说明文字：尾盘抢筹涨幅排序，黄金可用
更新时间：交易日15：10
接口地址URL：https://www.stockapi.com.cn/v1/base/jjqc
请求方式：GET
请求频率：40次/秒

请求参数：
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| tradeDate | string | 是 | | 时间 | 2025-03-04 |
| period | string | 是 | 1 | 抢筹类型，0-竞价抢筹，1-尾盘抢筹 | 1 |
| type | string | 是 | 4 | 尾盘抢筹成交金额排序 | 4 |

响应参数：
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - name | String | 股票名称 | |
| - code | String | 代码 | |
| - openAmt | Long | 开盘金额 | |
| - qczf | Double | 抢筹涨幅 | |
| - qccje | String | 抢筹成交额 | |
| - qcwtje | Long | 抢筹委托金额 | |
| - type | int | 排序类型：1-按照抢筹委托金额排序，2-按照抢筹成交金额排序，3-按照收盘金额顺序排序，4-按照抢筹涨幅排序 | |
| - period | int | 抢筹类型，0-早盘竞价抢筹，1-尾盘抢筹 | |
| - time | String | 时间 | |

请求URL示例：
https://www.stockapi.com.cn/v1/base/jjqc?tradeDate=2025-03-04&period=1&type=4

响应JSON示例：
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "period": 0,
      "code": "002725",
      "qcwtje": 729434002,
      "name": "跃岭股份",
      "qczf": 9.98,
      "qccje": 5730304,
      "openAmt": 5730304,
      "time": "2025-03-04",
      "type": 1
    },
    {
      "period": 0,
      "code": "002227",
      "qcwtje": 5296440,
      "name": "奥 特 迅",
      "qczf": 10.02,
      "qccje": 5296440,
      "openAmt": 45699975,
      "time": "2025-03-04",
      "type": 1
    }
  ]
}
```

---

### 早盘抢筹委托金额排序

接口说明:
接口说明：早盘抢筹委托金额排序，黄金可用
更新时间: 交易日9：26
接口地址：https://www.stockapi.com.cn/v1/base/jjqc
请求方式：GET
请求频率：40次/秒

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| tradeDate | string | 是 | | 时间 | 2025-03-04 |
| period | string | 是 | 0 | 抢筹类型，0-竞价抢筹，1-尾盘抢筹 | 0 |
| type | string | 是 | 1 | 按照抢筹委托金额排序 | 1 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - name | String | 股票名称 | |
| - code | String | 代码 | |
| - openAmt | Long | 开盘金额 | |
| - qczf | Double | 抢筹涨幅 | |
| - qccje | String | 抢筹成交额 | |
| - qcwtje | Long | 抢筹委托金额 | |
| - type | int | 排序类型：1-按照抢筹委托金额排序，2-按照抢筹成交金额排序，3-按照开盘金额顺序排序，4-按照抢筹涨幅排序 | |
| - period | int | 抢筹类型，0-早盘竞价抢筹，1-尾盘抢筹 | |
| - time | String | 时间 | |

请求URL示例:
https://www.stockapi.com.cn/v1/base/jjqc?tradeDate=2025-03-04&period=0&type=1

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "period": 0,
      "code": "002725",
      "qcwtje": 729434002,
      "name": "跃岭股份",
      "qczf": 9.98,
      "qccje": 5730304,
      "openAmt": 5730304,
      "time": "2025-03-04",
      "type": 1
    },
    {
      "period": 0,
      "code": "002227",
      "qcwtje": 5296440,
      "name": "奥 特 迅",
      "qczf": 10.02,
      "qccje": 5296440,
      "openAmt": 45699975,
      "time": "2025-03-04",
      "type": 1
    }
  ]
}
```

---

### 早盘抢筹开盘金额排序

接口说明：
接口说明：早盘抢筹开盘金额排序，黄金可用
更新时间: 交易日9：26
接口地址：https://www.stockapi.com.cn/v1/base/jjqc
请求方式：GET
请求频率：40次/秒

请求参数：
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| tradeDate | string | 是 | | 时间 | 2025-03-04 |
| period | string | 是 | 0 | 抢筹类型，0-竞价抢筹，1-尾盘抢筹 | 0 |
| type | string | 是 | 3 | 早盘抢筹开盘金额排序 | 3 |

响应参数：
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - name | String | 股票名称 | |
| - code | String | 代码 | |
| - openAmt | Long | 开盘金额 | |
| - qczf | Double | 抢筹涨幅 | |
| - qccje | String | 抢筹成交额 | |
| - qcwtje | Long | 抢筹委托金额 | |
| - type | int | 排序类型：1-按照抢筹委托金额排序，2-按照抢筹成交金额排序，3-按照开盘金额顺序排序，4-按照抢筹涨幅排序 | |
| - period | int | 抢筹类型，0-早盘竞价抢筹，1-尾盘抢筹 | |
| - time | String | 时间 | |

请求URL示例：
https://www.stockapi.com.cn/v1/base/jjqc?tradeDate=2025-03-04&period=0&type=3

响应JSON示例：
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "period": 0,
      "code": "002725",
      "qcwtje": 729434002,
      "name": "跃岭股份",
      "qczf": 9.98,
      "qccje": 5730304,
      "openAmt": 5730304,
      "time": "2025-03-04",
      "type": 1
    },
    {
      "period": 0,
      "code": "002227",
      "qcwtje": 5296440,
      "name": "奥 特 迅",
      "qczf": 10.02,
      "qccje": 5296440,
      "openAmt": 45699975,
      "time": "2025-03-04",
      "type": 1
    }
  ]
}
```

---

### 早盘抢筹成交金额排序

接口说明:
接口说明文字: 早盘抢筹成交金额排序，黄金可用
更新时间: 交易日9：26
接口地址URL: https://www.stockapi.com.cn/v1/base/jjqc
请求方式: GET
请求频率: 40次/秒

请求参数表格:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| tradeDate | string | 是 | | 时间 | 2025-03-04 |
| period | string | 是 | 0 | 抢筹类型，0-竞价抢筹，1-尾盘抢筹 | 0 |
| type | string | 是 | 2 | 早盘抢筹成交金额排序 | 2 |

响应参数表格:
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - name | String | 股票名称 | |
| - code | String | 代码 | |
| - openAmt | Long | 开盘金额 | |
| - qczf | Double | 抢筹涨幅 | |
| - qccje | String | 抢筹成交额 | |
| - qcwtje | Long | 抢筹委托金额 | |
| - type | int | 排序类型：1-按照抢筹委托金额排序，2-按照抢筹成交金额排序，3-按照开盘金额顺序排序，4-按照抢筹涨幅排序 | |
| - period | int | 抢筹类型，0-早盘竞价抢筹，1-尾盘抢筹 | |
| - time | String | 时间 | |

请求URL示例:
https://www.stockapi.com.cn/v1/base/jjqc?tradeDate=2025-03-04&period=0&type=2

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "period": 0,
      "code": "002725",
      "qcwtje": 729434002,
      "name": "跃岭股份",
      "qczf": 9.98,
      "qccje": 5730304,
      "openAmt": 5730304,
      "time": "2025-03-04",
      "type": 1
    },
    {
      "period": 0,
      "code": "002227",
      "qcwtje": 5296440,
      "name": "奥 特 迅",
      "qczf": 10.02,
      "qccje": 5296440,
      "openAmt": 45699975,
      "time": "2025-03-04",
      "type": 1
    }
  ]
}
```

---

### 早盘抢筹涨幅排序

接口说明:
接口说明文字: 早盘抢筹涨幅排序, 黄金可用
更新时间: 交易日9:26
接口地址URL: https://www.stockapi.com.cn/v1/base/jjqc
请求方式: GET
请求频率: 40次/秒

请求参数:
| 参数名    | 类型   | 是否必须 | 默认值 | 说明                               | 示例       |
|-----------|--------|----------|--------|------------------------------------|------------|
| tradeDate | string | 是       |        | 时间                               | 2025-03-04 |
| period    | string | 是       | 0      | 抢筹类型，0-竞价抢筹，1-尾盘抢筹     | 0          |
| type      | string | 是       | 4      | 早盘抢筹涨幅排序                   | 4          |

响应参数:
| 参数名   | 类型     | 说明                                                                               | 示例    |
|----------|----------|------------------------------------------------------------------------------------|---------|
| code     | int      | 返回码                                                                             | 20000   |
| msg      | string   | 状态                                                                               | success |
| data     | Object[] |                                                                                    |         |
| - name   | String   | 股票名称                                                                           |         |
| - code   | String   | 代码                                                                               |         |
| - openAmt| Long     | 开盘金额                                                                           |         |
| - qczf   | Double   | 抢筹涨幅                                                                           |         |
| - qccje  | String   | 抢筹成交额                                                                         |         |
| - qcwtje | Long     | 抢筹委托金额                                                                       |         |
| - type   | int      | 排序类型：1-按照抢筹委托金额排序，2-按照抢筹成交金额排序，3-按照开盘金额顺序排序，4-按照抢筹涨幅排序 |         |
| - period | int      | 抢筹类型，0-早盘竞价抢筹，1-尾盘抢筹                                                 |         |
| - time   | String   | 时间                                                                               |         |

请求URL示例:
https://www.stockapi.com.cn/v1/base/jjqc?tradeDate=2025-03-04&period=0&type=4

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "period": 0,
      "code": "002725",
      "qcwtje": 729434002,
      "name": "跃岭股份",
      "qczf": 9.98,
      "qccje": 5730304,
      "openAmt": 5730304,
      "time": "2025-03-04",
      "type": 1
    },
    {
      "period": 0,
      "code": "002227",
      "qcwtje": 5296440,
      "name": "奥 特 迅",
      "qczf": 10.02,
      "qccje": 5296440,
      "openAmt": 45699975,
      "time": "2025-03-04",
      "type": 1
    }
  ]
}
```

---

## 风险预警

### 严重异动提醒

接口说明：
接口说明：严重异动提醒，黄金可用
更新时间: 交易日9：26
接口地址：https://www.stockapi.com.cn/v1/alarmData
请求方式：GET
请求频率：40次/秒

请求参数：
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| tradeDate | string | 是 | | 时间 | 2025-03-13 |
| type | string | 是 | 4 | 严重异动提醒 | 4 |

响应参数：
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - name | String | 股票名称 | |
| - code | String | 代码 | |
| - content | String | 异动详情 | |
| - type | int | 1-股东减持，2-大比列解禁，3-风险监控，4-严重异动提醒 | |
| - time | String | 时间 | |

请求URL示例：
https://www.stockapi.com.cn/v1/alarmData?tradeDate=2025-03-04&type=4

响应JSON示例：
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "code": "688213",
      "name": "思特威",
      "time": "2025-03-13",
      "type": 1,
      "content": "国家集成电路基金二期等股东拟合计减持不超2.99%公司股份"
    },
    {
      "code": "301085",
      "name": "亚康股份",
      "time": "2025-03-13",
      "type": 1,
      "content": "多名股东拟合计减持不超3.81%公司股份"
    }
  ]
}
```

---

### 大比列解禁

接口说明:
接口说明文字: 大比列解禁, 黄金可用
更新时间: 交易日9:26
接口地址URL: https://www.stockapi.com.cn/v1/alarmData
请求方式: GET
请求频率: 40次/秒

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| tradeDate | string | 是 | | 时间 | 2025-03-13 |
| type | string | 是 | 2 | 大比列解禁 | 2 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - name | String | 股票名称 | |
| - code | String | 代码 | |
| - content | String | 异动详情 | |
| - type | int | 1-股东减持，2-大比列解禁，3-风险监控，4-严重异动提醒 | |
| - time | String | 时间 | |

请求URL示例:
https://www.stockapi.com.cn/v1/alarmData?tradeDate=2025-03-04&type=2

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "code": "688213",
      "name": "思特威",
      "time": "2025-03-13",
      "type": 1,
      "content": "国家集成电路基金二期等股东拟合计减持不超2.99%公司股份"
    },
    {
      "code": "301085",
      "name": "亚康股份",
      "time": "2025-03-13",
      "type": 1,
      "content": "多名股东拟合计减持不超3.81%公司股份"
    }
  ]
}
```

---

### 大股东减持

接口说明:
接口说明文字: 大股东减持，黄金可用
更新时间: 交易日9：26
接口地址URL: https://www.stockapi.com.cn/v1/alarmData
请求方式: GET
请求频率: 40次/秒

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| tradeDate | string | 是 | | 时间 | 2025-03-13 |
| type | string | 是 | 1 | 大股东减持 | 1 |

响应参数:
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - name | String | 股票名称 | |
| - code | String | 代码 | |
| - content | String | 异动详情 | |
| - type | int | 1-股东减持，2-大比列解禁，3-风险监控，4-严重异动提醒 | |
| - time | String | 时间 | |

请求URL示例:
https://www.stockapi.com.cn/v1/alarmData?tradeDate=2025-03-04&type=1

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "code": "688213",
      "name": "思特威",
      "time": "2025-03-13",
      "type": 1,
      "content": "国家集成电路基金二期等股东拟合计减持不超2.99%公司股份"
    },
    {
      "code": "301085",
      "name": "亚康股份",
      "time": "2025-03-13",
      "type": 1,
      "content": "多名股东拟合计减持不超3.81%公司股份"
    }
  ]
}
```

---

### 风险监控

接口说明：
接口说明：风险监控，黄金可用
更新时间: 交易日9：26
接口地址：https://www.stockapi.com.cn/v1/alarmData
请求方式：GET
请求频率：40次/秒

请求参数：
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| tradeDate | string | 是 | | 时间 | 2025-03-13 |
| type | string | 是 | 3 | 风险监控 | 3 |

响应参数：
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - name | String | 股票名称 | |
| - code | String | 代码 | |
| - content | String | 异动详情 | |
| - type | int | 1-股东减持，2-大比列解禁，3-风险监控，4-严重异动提醒 | |
| - time | String | 时间 | |

请求URL示例：
https://www.stockapi.com.cn/v1/alarmData?tradeDate=2025-03-04&type=3

响应JSON示例：
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "code": "688213",
      "name": "思特威",
      "time": "2025-03-13",
      "type": 1,
      "content": "国家集成电路基金二期等股东拟合计减持不超2.99%公司股份"
    },
    {
      "code": "301085",
      "name": "亚康股份",
      "time": "2025-03-13",
      "type": 1,
      "content": "多名股东拟合计减持不超3.81%公司股份"
    }
  ]
}

---

## 资金流向

### 个股资金流向

接口说明：
接口说明文字：股票历史资金流
更新时间：交易日15: 30
接口地址URL：https://www.stockapi.com.cn/v1/base/codeFlow
请求方式：GET
请求频率：40次/秒

请求参数：
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
| --- | --- | --- | --- | --- | --- |
| code | string | 是 | | 代码 | 600004 |
| startDate | string | 是 | | 开始时间 | 2023-10-16 |
| endDate | string | 是 | | 结束时间 | 2023-10-17 |
| pageNo | string | 是 | 1 | 页码 | 1 |
| pageSize | string | 是 | 50 | 每页行数 | 50 |

响应参数：
| 参数名 | 类型 | 说明 | 示例 |
| --- | --- | --- | --- |
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | | |
| - code | string | 代码 | 600004 |
| - name | string | 名称 | 白云机场 |
| - changeRatio | string | 涨跌幅 | -1.38 |
| - lastPrice | string | 最新价 | 10.73 |
| - mainAmount | string | 主力净流入净额 | -1.5245291E7 |
| - mainAmountPercentage | string | 主力净流入净额占比 | -17.6 |
| - supperBigAmount | string | 超大单净流入净额 | -8549201.0 |
| - supperBigAmountPercentage | string | 超大单净流入占比 | -9.87 |
| - bigAmount | string | 大单净流入净额 | -6696090.0 |
| - bigAmountPercentage | string | 大单净流入占比 | -7.73 |
| - middleAmount | string | 中单净流入净额 | 7128325.0 |
| - middleAmountPercentage | string | 中单净流入占比 | 8.23 |
| - minAmount | string | 小单净流入净额 | 8116966.0 |
| - minAmountPercentage | string | 小单净流入净占比 | 9.37 |
| - date | string | 时间 | 2023-09-01 |

请求URL示例：
https://www.stockapi.com.cn/v1/base/codeFlow?code=600004&startDate=2023-10-16&endDate=2023-10-17&pageNo=1&pageSize=50

响应JSON示例：
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "date": "2023-10-13",
      "supperBigAmount": "-8549201.0",
      "minAmount": "8116966.0",
      "middleAmount": "7128325.0",
      "code": "600004",
      "mainAmountPercentage": "-17.6",
      "mainAmount": "-1.5245291E7",
      "bigAmountPercentage": "-7.73",
      "minAmountPercentage": "9.37",
      "bigAmount": "-6696090.0",
      "name": "白云机场",
      "changeRatio": "-1.38",
      "supperBigAmountPercentage": "-9.87",
      "middleAmountPercentage": "8.23",
      "lastPrice": "10.73"
    }
  ]
}
```

---

## AI智能选股

### AI智能选股

接口说明:
接口说明文字: AI智能选股，使用自然语言，白话文的形式选股，随时选出你想要的的好股，本接口特殊，不能直接调用，需要本地安装我们提供的一个软件和咨询技术
更新时间: 实时更新
接口地址URL: https://www.stockapi.com.cn/v1/base/xuangu
请求方式: GET
请求频率: 10次/秒

请求参数:
| 参数名 | 类型 | 是否必须 | 默认值 | 说明 | 示例 |
| --- | --- | --- | --- | --- | --- |
| strategy | string | 是 | 页面未提供 | 策略详情，比如：创业板，今日涨停，换手率大于10 | 创业板，今日涨停，换手率大于10 |

响应参数:
页面未提供

请求URL示例:
https://www.stockapi.com.cn/v1/base/xuangu?strategy=创业板，今日涨停，换手率大于10，竞价涨幅大于1

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "涨停明细数据[20240704]": "[{\\\"code\\\":\\\"300486.SZ\\\",\\\"time\\\":1720056811552,\\\"openTime\\\":1720058177117,\\\"duration\\\":1365565,\\\"updatedTime\\\":1720058177117,\\\"firstVol\\\":7.39147E7,\\\"highestVol\\\":9.7456075E7,\\\"firstVolDivLTGB\\\":0.18670637910502347,\\\"firstVolDivVol\\\":5.464993217806095,\\\"highestVolDivLTGB\\\":0.24617120660758415,\\\"highestVolDivVol\\\":6.129873063242823},{\\\"code\\\":\\\"300486.SZ\\\",\\\"time\\\":1720058267118,\\\"openTime\\\":1720058282118,\\\"duration\\\":15000,\\\"updatedTime\\\":1720058282118,\\\"firstVol\\\":374900.0,\\\"highestVol\\\":374900.0,\\\"firstVolDivLTGB\\\":9.469864793670717E-4,\\\"firstVolDivVol\\\":0.009097983805249078,\\\"highestVolDivLTGB\\\":9.469864793670717E-4,\\\"firstVolDivVol\\\":0.009097983805249078},{\\\"code\\\":\\\"300486.SZ\\\",\\\"time\\\":1720075892245,\\\"openTime\\\":1720075967245,\\\"duration\\\":75000,\\\"updatedTime\\\":1720075967245,\\\"firstVol\\\":9162725.0,\\\"highestVol\\\":9162725.0,\\\"firstVolDivLTGB\\\":0.023144776444808356,\\\"firstVolDivVol\\\":0.10518119907984638,\\\"highestVolDivLTGB\\\":0.023144776444808356,\\\"highestVolDivVol\\\":0.10518119907984638},{\\\"code\\\":\\\"300486.SZ\\\",\\\"time\\\":1720075982245,\\\"openTime\\\":null,\\\"duration\\\":417755,\\\"updatedTime\\\":1720076400000,\\\"firstVol\\\":75500.0,\\\"highestVol\\\":2494575.0,\\\"firstVolDivLTGB\\\":1.907108007260974E-4,\\\"firstVolDivVol\\\":8.561368113428262E-4,\\\"highestVolDivLTGB\\\":0.006301223784388138,\\\"highestVolDivVol\\\":0.028151291063805248}]",
      "经营范围": "物流设备、自动化生产线、输送线、仓储设备、涂装设备、自动监控系统、自动化配送中心、立体停车库、电气设备、工业机器人的设计、制造、安装、调试；自有房屋经营租赁；电力业务：太阳能光伏发电；电力供应：售电业务；机电设备安装工程；进出口：自营和代理各类商品和技术的进出口（但国家限定公司经营或禁止进出口的商品和技术除外）。（依法须经批准的项目，经相关部门批准后方可开展经营活动）。",
      "code": "300486",
      "涨停[20240704]": "涨停",
      "连续涨停天数[20240704]": 1,
      "涨停封单额[20240704]": "2509724.25",
      "最新价": "5.93",
      "注册地址": "山西省太原市尖草坪区中北高新技术产业开发区丰源路59号",
      "最新涨跌幅": "20.041",
      "最终涨停时间[20240704]": " 14:53:02",
      "涨停原因类别[20240704]": "曾向国电高科支付预付款+智能物流+机器人+国企",
      "market_code": "33",
      "涨停封单量[20240704]": "423225.0",
      "股票代码": "300486.SZ",
      "a股市值(不含限售股)[20240704]": "2347612200.000",
      "涨停开板次数[20240704]": "3",
      "首次涨停时间[20240704]": " 09:33:31",
      "上市板块": "创业板",
      "股票简称": "东杰智能",
      "涨停类型[20240704]": "放量涨停",
      "涨停封单量占成交量比[20240704]": 0.4721479560921645,
      "几天几板[20240704]": "首板涨停",
      "涨停封单量占流通a股比[20240704]": 0.10690540216861266
    }
  ]
}
```

---

## 板块龙头股

### 强势股多日涨幅累计

接口说明:
接口说明文字: 可查询当前5日,10日累计涨幅最靠前的前50只强势票。金刚钻可用
更新时间: 交易日下午16点
接口地址URL: https://www.stockapi.com.cn/v1/base/kplZhangfuRanking
请求方式: GET
请求频率: 10次/秒

请求参数表格:
| 参数名 | 类型   | 是否必须 | 默认值 | 说明 | 示例 |
|---|---|---|---|---|---|
| date | string | 是 | 页面未提供 | 时间 | 2025-11-14 |
| days | string | 是 | 页面未提供 | 天数(5或10) | 5 |

响应参数表格:
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 返回码 | 20000 |
| msg | string | 状态 | success |
| data | Object[] | 页面未提供 | 页面未提供 |
| - code | String | 股票代码 | 002083 |
| - name | String | 股票名称 | 孚日股份 |
| - zf | String | 5日或10日区间涨幅 | 61.23 |
| - bk | String | 板块 | 电解液、服装家纺 |
| - price | String | 股价 | 3 |
| - jlrts | String | 5日或10日资金净流入天数 | 2 |
| - je | String | 5日或10日净额 | 39999999 |
| - hsl换手率 | String | 换手率 | 119 |
| - time | String | 时间 | 2025-11-14 |
| - zl | String | 主力 | 游资 |
| - type | String | 类型 | 5日或者10日 |

请求URL示例:
https://www.stockapi.com.cn/v1/base/kplZhangfuRanking?date=2025-11-14&days=5

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "hsl": 4016167939,
      "zl": "游资",
      "code": "002083",
      "price": 11.56,
      "jlrts": 4,
      "name": "孚日股份",
      "bk": "电解液、服装家纺",
      "je": 239811665,
      "zf": 61.23,
      "type": 5
    }
  ]
}
```

---

### 热点板块

接口说明：
接口说明：可查询当前主力聚焦的热点板块排行。金刚钻可用
更新时间：交易日下午16点
接口地址：https://www.stockapi.com.cn/v1/hotBkJlrDr
请求方式：GET
请求频率: 10次/秒

请求参数：
| 参数名 | 类型   | 是否必须 | 默认值 | 说明 | 示例       |
| ------ | ------ | -------- | ------ | ---- | ---------- |
| date   | string | 是       |        | 时间 | 2025-11-14 |

响应参数：
| 参数名      | 类型     | 说明           | 示例    |
| ----------- | -------- | -------------- | ------- |
| code        | int      | 返回码         | 20000   |
| msg         | string   | 状态           | success |
| data        | Object[] |                |         |
| - bkCode    | string   | 板块代码       | 801004  |
| - bkName    | String   | 板块名称       | 锂电池  |
| - qjzf      | String   | 涨幅           | 0.4     |
| - diffQjzf  | String   | 涨幅差         | 0.4     |
| - qjje      | String   | 净额           | 0.4     |
| - diffQjje  | String   | 净额差         | 0.4     |
| - jlrts     | String   | 资金净流入天数 | 2       |
| - qiangdu   | String   | 板块强度       | 29576   |
| - diffQiangdu | String | 板块强度差 | 576 |
| - time      | String   | 时间           | 2025-11-14 |

请求URL示例：
普通请求URL：https://www.stockapi.com.cn/v1/hotBkJlrDr?date=2025-11-14
带Token请求URL：https://www.stockapi.com.cn/v1/hotBkJlrDr?date=2025-11-14&token=你的token

响应JSON示例：
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "qjje": 4987191157,
      "qjzf": 1.53,
      "qiangdu": 29576.2,
      "jlrts": 1,
      "bkName": "锂电池",
      "bkCode": "801004",
      "id": 211,
      "time": "2025-11-14",
      "diffQjje": -3653424711,
      "diffQjzf": -1.49,
      "diffQiangdu": 1059.9000000000017
    }
  ]
}
```

---

### 热点板块龙头股

接口说明:
接口说明：可查询当前板块下的龙头股，别的都不要，只要龙头。金刚钻可用
更新时间：交易日下午16点
接口地址：https://www.stockapi.com.cn/v1/hotBkJlrLongTou
请求方式：GET
请求频率: 10次/秒

请求参数:
| 参数名  | 类型   | 是否必须 | 默认值 | 说明   | 示例       |
|---------|--------|----------|--------|--------|------------|
| date    | string | 是       |        | 时间   | 2025-11-14 |
| plateId | string | 是       |        | 板块id | 87983      |

响应参数:
| 参数名           | 类型     | 说明         | 示例          |
|------------------|----------|--------------|---------------|
| code             | int      | 返回码       | 20000         |
| msg              | string   | 状态         | success       |
| data             | Object[] |              |               |
| - bkCode         | string   | 板块代码     | 801004        |
| - code           | String   | 股票代码     | 002083        |
| - name           | String   | 股票名称     | 孚日股份      |
| - qjzf           | String   | 5日区间涨幅  | 61.23         |
| - bk             | String   | 板块         | 电解液、服装家纺 |
| - jlrts          | String   | 资金净流入天数 | 2             |
| - time           | String   | 时间         | 2025-11-14    |

请求URL示例:
https://www.stockapi.com.cn/v1/hotBkJlrLongTou?date=2025-11-14&plateId=801004

响应JSON示例:
```json
{
  "msg": "success",
  "code": 20000,
  "data": [
    {
      "qjzf": 61.23,
      "code": "002083",
      "jlrts": 4,
      "name": "孚日股份",
      "bkCode": "801004",
      "bk": "电解液、服装家纺",
      "id": 388,
      "time": "2025-11-14"
    }
  ]
}
```

---

## 附录：接口统计

本文档共收录 **71** 个API接口，分布在 **18** 个分类中。

| 分类 | 接口数量 |
|------|----------|
| 策略回测 | 1 |
| 基础数据 | 5 |
| 实时数据 | 10 |
| 技术指标 | 9 |
| 大盘指数 | 5 |
| 基金 | 2 |
| 涨停股池 | 5 |
| 概念板块 | 4 |
| 异动数据 | 2 |
| 龙虎游资 | 4 |
| 附加增值接口 | 2 |
| 竞价专题 | 2 |
| 竞价专题增强版 | 3 |
| 竞价抢筹 | 8 |
| 风险预警 | 4 |
| 资金流向 | 1 |
| AI智能选股 | 1 |
| 板块龙头股 | 3 |

---

*文档生成时间：2026年2月24日*

*数据来源：[stockapi.com.cn](https://www.stockapi.com.cn/)*
