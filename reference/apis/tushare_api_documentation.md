# Tushare Pro API 接口参考手册

> 本手册详细记录了 [Tushare Pro](https://tushare.pro) 平台主要数据接口的完整调用文档，涵盖接口名称、接口说明、调用方法、输入参数、输出参数及调用示例。所有信息均来自 Tushare 官网真实文档内容，可作为量化投资策略开发（如 T01 龙头战法选股策略）的数据接口参考。

## 目录

| 序号 | 主题 | 接口数量 |
| --- | --- | --- |
| 1 | 股票数据 | 106 |
| 2 | ETF专题 | 8 |
| 3 | 指数专题 | 19 |
| 4 | 债券专题 | 15 |
| 5 | 外汇数据 | 2 |
| 6 | 美股数据 | 9 |
| 7 | 行业经济 | 8 |
| 8 | 宏观经济 | 18 |
| 9 | 大模型语料专题数据 | 8 |

**共计 193 个接口**

---

# 1. 股票数据

## 基础数据

### IPO新股列表 (new_share)

#### 接口说明

获取新股上市列表数据。

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api("YOUR_TOKEN")
df = pro.new_share(start_date="", end_date="")
```

#### 权限要求

用户需要至少120积分才可以调取。

#### 输入参数

| 名称        | 类型 | 是否必填 | 说明             |
| :---------- | :--- | :------- | :--------------- |
| start_date  | str  | N        | 上网发行开始日期 |
| end_date    | str  | N        | 上网发行结束日期 |

#### 输出参数

| 名称           | 类型  | 说明               |
| :------------- | :---- | :----------------- |
| ts_code        | str   | TS股票代码         |
| sub_code       | str   | 申购代码           |
| name           | str   | 名称               |
| ipo_date       | str   | 上网发行日期       |
| issue_date     | str   | 上市日期           |
| amount         | float | 发行总量（万股）   |
| market_amount  | float | 上网发行总量（万股） |
| price          | float | 发行价格           |
| pe             | float | 市盈率             |
| limit_amount   | float | 个人申购上限（万股） |
| funds          | float | 募集资金（亿元）   |
| ballot         | float | 中签率             |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.new_share(start_date='20180901', end_date='20181018')
```

---

### ST股票列表

**接口标识**：`stock_st`

**接口说明**：获取ST股票列表，可根据交易日期获取历史上每天的ST列表。

**调用方法**：`pro.stock_st()`

**权限要求**：3000积分起

**提示**：每天上午9:20更新，单次请求最大返回1000行数据，可循环提取,本接口数据从20160101开始,太早历史无法补齐

#### 输入参数

| 名称 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 股票代码 |
| trade_date | str | N | 交易日期（格式：YYYYMMDD下同） |
| start_date | str | N | 开始时间 |
| end_date | str | N | 结束时间 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 股票代码 |
| name | str | Y | 股票名称 |
| trade_date | str | Y | 交易日期 |
| type | str | Y | 类型 |
| type_name | str | Y | 类型名称 |

#### 调用示例

```python
pro = ts.pro_api()

#获取20250813日所有的ST股票
df = pro.stock_st(trade_date='20250813')
```

---

### ST风险警示板股票

#### 接口信息

- **接口名称**: ST风险警示板股票
- **接口标识**: st
- **接口说明**: 获取ST风险警示板股票列表。
- **调用方法**: `pro.st()`
- **权限要求**: 6000积分

#### 输入参数

| 参数名称 | 类型 | 是否必选 | 描述 |
|---|---|---|---|
| ts_code | str | N | 股票代码 |
| pub_date | str | N | 发布日期 |
| imp_date | str | N | 实施日期 |

#### 输出参数

| 字段名称 | 类型 | 默认显示 | 描述 |
|---|---|---|---|
| ts_code | str | Y | 股票代码 |
| name | str | Y | 股票名称 |
| pub_date | str | Y | 发布日期 |
| imp_date | str | Y | 实施日期 |
| st_tpye | str | Y | 类型 |
| st_reason | str | Y | st变更原因 |
| st_explain | str | Y | st变更详细原因 |

#### 调用示例

```python
### 拉取接口st数据
df = pro.st(**{
    "ts_code": "300125.SZ",
    "pub_date": "",
    "imp_date": ""
}, fields=[
    "ts_code",
    "name",
    "pub_date",
    "imp_date",
    "st_tpye",
    "st_reason",
    "st_explain"
])
print(df)
```

---

### 上市公司基本信息

**接口标识**：`stock_company`

**接口说明**：获取上市公司基础信息，单次提取4500条，可以根据交易所分批提取。

**调用方法**：
```python
pro = ts.pro_api()

#或者
#pro = ts.pro_api('your token')

df = pro.stock_company(exchange='SZSE', fields='ts_code,chairman,manager,secretary,reg_capital,setup_date,province')
```

**权限要求**：用户需要至少120积分才可以调取。

**输入参数**：

| 名称 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 股票代码 |
| exchange | str | N | 交易所代码 ，SSE上交所 SZSE深交所 BSE北交所 |

**输出参数**：

| 名称 | 类型 | 描述 |
| --- | --- | --- |
| ts_code | str | 股票代码 |
| com_name | str | 公司全称 |
| com_id | str | 统一社会信用代码 |
| exchange | str | 交易所代码 |
| chairman | str | 法人代表 |
| manager | str | 总经理 |
| secretary | str | 董秘 |
| reg_capital | float | 注册资本(万元) |
| setup_date | str | 注册日期 |
| province | str | 所在省份 |
| city | str | 所在城市 |
| introduction | str | 公司介绍 |
| website | str | 公司主页 |
| email | str | 电子邮件 |
| office | str | 办公室 |
| employees | int | 员工人数 |
| main_business | str | 主要业务及产品 |
| business_scope | str | 经营范围 |

**调用示例**：

```python
pro = ts.pro_api()

#或者
#pro = ts.pro_api('your token')

df = pro.stock_company(exchange='SZSE', fields='ts_code,chairman,manager,secretary,reg_capital,setup_date,province')
```

---

### 中央结算系统持股明细

#### 接口信息

- **接口名称**: 中央结算系统持股明细
- **接口标识**: ccass_hold_detail
- **接口说明**: 获取中央结算系统机构席位持股明细，数据覆盖全历史，根据交易所披露时间，当日数据在下一交易日早上9点前完成。
- **调用方法**: `pro.ccass_hold_detail()`
- **权限要求**: 用户积8000积分可调取，每分钟可以请求300次。

#### 输入参数

| 参数名称 | 类型 | 是否必填 | 说明 |
|---|---|---|---|
| ts_code | str | N | 股票代码 (e.g. 605009.SH) |
| hk_code | str | N | 港交所代码 （e.g. 95009） |
| trade_date | str | N | 交易日期(YYYYMMDD格式，下同) |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 字段名称 | 类型 | 说明 |
|---|---|---|
| trade_date | str | 交易日期 (默认输出) |
| ts_code | str | 股票代号 (默认输出) |
| name | str | 股票名称 (默认输出) |
| col_participant_id | str | 参与者编号 (默认输出) |
| col_participant_name | str | 机构名称 (默认输出) |
| col_shareholding | str | 持股量(股) (默认输出) |
| col_shareholding_percent | str | 占已发行股份/权证/单位百分比(%) (默认输出) |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.ccass_hold_detail(ts_code='00960.HK', trade_date='20211101', fields='trade_date,ts_code,col_participant_id,col_participant_name,col_shareholding')
```

---

### 交易日历 (trade_cal)

#### 接口描述

获取各大交易所交易日历数据,默认提取的是上交所。

#### 调用方法

```python
pro.trade_cal(exchange='', start_date='20180101', end_date='20181231')
```

或者

```python
pro.query('trade_cal', start_date='20180101', end_date='20181231')
```

#### 权限要求

需2000积分

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| exchange | str | N | 交易所 SSE上交所,SZSE深交所,CFFEX 中金所,SHFE 上期所,CZCE 郑商所,DCE 大商所,INE 上能源 |
| start_date | str | N | 开始日期 （格式：YYYYMMDD 下同） |
| end_date | str | N | 结束日期 |
| is_open | str | N | 是否交易 '0'休市 '1'交易 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| exchange | str | Y | 交易所 SSE上交所 SZSE深交所 |
| cal_date | str | Y | 日历日期 |
| is_open | str | Y | 是否交易 0休市 1交易 |
| pretrade_date | str | Y | 上一个交易日 |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.trade_cal(exchange='', start_date='20180101', end_date='20181231')
print(df)
```

---

### 北交所新旧代码对照

#### 接口标识

bse_mapping

#### 接口说明

获取北交所股票代码变更后新旧代码映射表数据。

#### 调用方法

```python
df = pro.bse_mapping(o_code='838163.BJ')
```

#### 权限要求

- 限量：单次最大1000条（本接口总数据量300以内）
- 积分：120分即可调取

#### 输入参数

| 名称 | 类型 | 是否必填 | 描述 |
| :--- | :--- | :--- | :--- |
| o_code | str | N | 旧代码 |
| n_code | str | N | 新代码 |

#### 输出参数

| 字段 | 类型 | 默认显示 | 描述 |
| :--- | :--- | :--- | :--- |
| name | str | Y | 股票名称 |
| o_code | str | Y | 原代码 |
| n_code | str | Y | 新代码 |
| list_date | str | Y | 上市日期 |

#### 调用示例

```python
### 获取方大新材新旧代码对照数据
df = pro.bse_mapping(o_code='838163.BJ')

### 获取全部变更的股票代码对照表
df = pro.bse_mapping()
```

---

### 每日股本（盘前） (stk_premarket)

#### 接口说明

每日开盘前获取当日股票的股本情况，包括总股本和流通股本，涨跌停价格等。

#### 调用方法

```python
pro.stk_premarket(ts_code, trade_date, start_date, end_date)
```

#### 权限要求

与积分无关，可以在线开通权限。

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 股票代码 |
| trade_date | str | N | 交易日期(YYYYMMDD格式，下同) |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 字段名称 | 字段类型 | 描述 |
| --- | --- | --- |
| trade_date | str | 交易日期 |
| ts_code | str | TS股票代码 |
| total_share | float | 总股本（万股） |
| float_share | float | 流通股本（万股） |
| pre_close | float | 昨日收盘价 |
| up_limit | float | 今日涨停价 |
| down_limit | float | 今日跌停价 |

#### 调用示例

```python
pro = ts.pro_api()
#获取某一日盘前所有股票当日的最新股本
df = pro.stk_premarket(trade_date='20240603')
```

---

### 沪深港通股票列表 (stock_hsgt)

#### 接口说明

获取沪深港通股票列表。

- **接口标识**：stock_hsgt
- **权限要求**：3000积分起
- **提示**：每天上午9:20更新，单次请求最大返回2000行数据，可根据类型循环提取,本接口数据从20250812开始

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api()

#获取20250813日深股通的股票列表
df = pro.stock_hsgt(trade_date='20250813',type='HK_SZ')
```

#### 输入参数

| 名称       | 类型 | 必选 | 描述                     |
| ---------- | ---- | ---- | ------------------------ |
| ts_code    | str  | N    | 股票代码                 |
| trade_date | str  | N    | 交易日期（格式：YYYYMMDD） |
| type       | str  | Y    | 类型（参考下表）         |
| start_date | str  | N    | 开始时间                 |
| end_date   | str  | N    | 结束时间                 |

**类型说明如下：**

| 类型   | 类型名称       |
| ------ | -------------- |
| HK_SZ  | 深股通(港>深) |
| SZ_HK  | 港股通(深>港) |
| HK_SH  | 沪股通(港>沪) |
| SH_HK  | 港股通(沪>港) |

#### 输出参数

| 名称       | 类型 | 描述     |
| ---------- | ---- | -------- |
| ts_code    | str  | 股票代码 |
| trade_date | str  | 交易日期 |
| type       | str  | 类型     |
| name       | str  | 股票名称 |
| type_name  | str  | 类型名称 |

#### 调用示例

```python
pro = ts.pro_api()

#获取20250813日深股通的股票列表
df = pro.stock_hsgt(trade_date='20250813',type='HK_SZ')
```

**数据样例**

```
                 ts_code trade_date   type     name type_name
    0    001258.SZ   20250813  HK_SZ     立新能源  深股通(港>深)
    1     00019.HK   20250813  SZ_HK  太古股份公司A  港股通(深>港)
    2    000513.SZ   20250813  HK_SZ     丽珠集团  深股通(港>深)
    3    002044.SZ   20250813  HK_SZ     美年健康  深股通(港>深)
    4    000338.SZ   20250813  HK_SZ     潍柴动力  深股通(港>深)
    ..         ...        ...    ...      ...       ...
    995  300206.SZ   20250813  HK_SZ     理邦仪器  深股通(港>深)
    996   02331.HK   20250813  SH_HK       李宁  港股通(沪>港)
    997   01855.HK   20250813  SH_HK     中庆股份  港股通(沪>港)
    998  300726.SZ   20250813  HK_SZ     宏达电子  深股通(港>深)
    999   06127.HK   20250813  SH_HK     昭衍新药  港股通(沪>港)
```

---

### 沪深股通十大成交股

**接口名称**: 沪深股通十大成交股

**接口标识**: hsgt_top10

**接口说明**: 获取沪股通、深股通每日前十大成交详细数据，每天18~20点之间完成当日更新

**调用方法**:
```python
pro = ts.pro_api()

### 获取20180725的沪市十大成交股
pro.hsgt_top10(trade_date='20180725', market_type='1')

### 查询贵州茅台在20180701到20180725期间的十大成交股情况
pro.query('hsgt_top10', ts_code='600519.SH', start_date='20180701', end_date='20180725')
```

**权限要求**: 

**输入参数**:

| 名称 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| ts_code | str | N | 股票代码（二选一） |
| trade_date | str | N | 交易日期（二选一） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |
| market_type | str | N | 市场类型（1：沪市 3：深市） |

**输出参数**:

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| trade_date | str | 交易日期 |
| ts_code | str | 股票代码 |
| name | str | 股票名称 |
| close | float | 收盘价 |
| change | float | 涨跌额 |
| rank | int | 资金排名 |
| market_type | str | 市场类型（1：沪市 3：深市） |
| amount | float | 成交金额（元） |
| net_amount | float | 净成交金额（元） |
| buy | float | 买入金额（元） |
| sell | float | 卖出金额（元） |

**调用示例**:

```python
pro = ts.pro_api()

df = pro.hsgt_top10(trade_date='20180725', market_type='1')
```

```
      trade_date    ts_code  name       close  change  rank  market_type  \
    0   20180725  600009.SH  上海机场   62.69    2.0677     9            1   
    1   20180725  600019.SH  宝钢股份    8.62    0.9368     7            1   
    2   20180725  600036.SH  招商银行   28.22    1.6937    10            1   
    3   20180725  600276.SH  恒瑞医药   71.89    1.2393     5            1   
    4   20180725  600519.SH  贵州茅台  743.81   -0.2133     2            1   
    5   20180725  600585.SH  海螺水泥   38.23   -0.4427     3            1   
    6   20180725  600690.SH  青岛海尔   18.09    0.0000     8            1   
    7   20180725  600887.SH  伊利股份   27.54   -1.7131     6            1   
    8   20180725  601318.SH  中国平安   62.16    0.6803     1            1   
    9   20180725  601888.SH  中国国旅   74.19    5.5184     4            1   
    
            amount   net_amount          buy         sell  
    0  240958518.0   31199144.0  136078831.0  104879687.0  
    1   245582396.0   81732606.0  163657501.0   81924895.0  
    2  240655550.0  142328622.0  191492086.0   49163464.0  
    3  329472455.0  -71519443.0  128976506.0  200495949.0  
    4  508590993.0  226149667.0  367370330.0  141220663.0  
    5  357946144.0   51215890.0  204581017.0  153365127.0  
    6  243840019.0  -55595149.0   94122435.0  149717584.0  
    7  296552611.0  -40273759.0  128139426.0  168413185.0  
    8  534002916.0  287838388.0  410920652.0  123082264.0  
    9  342115066.0  -63262966.0  139426050.0  202689016.0
```

---

### 管理层薪酬和持股 (stk_rewards)

#### 接口说明

获取上市公司管理层薪酬和持股

#### 调用方法

```python
pro.stk_rewards()
```

#### 权限要求

用户需要2000积分才可以调取，5000积分以上频次相对较高

#### 输入参数

| 名称      | 类型 | 必选 | 描述                               |
| --------- | ---- | ---- | ---------------------------------- |
| ts_code   | str  | Y    | TS股票代码，支持单个或多个代码输入 |
| end_date  | str  | N    | 报告期                             |

#### 输出参数

| 名称      | 类型  | 默认显示 | 描述       |
| --------- | ----- | -------- | ---------- |
| ts_code   | str   | Y        | TS股票代码 |
| ann_date  | str   | Y        | 公告日期   |
| end_date  | str   | Y        | 截止日期   |
| name      | str   | Y        | 姓名       |
| title     | str   | Y        | 职务       |
| reward    | float | Y        | 报酬       |
| hold_vol  | float | Y        | 持股数     |

#### 调用示例

```python
pro = ts.pro_api()

#获取单个公司高管全部数据
df = pro.stk_rewards(ts_code='000001.SZ')

#获取多个公司高管全部数据
df = pro.stk_rewards(ts_code='000001.SZ,600000.SH')
```

---

### 股票列表 (stock_basic)

#### 接口描述

获取基础信息数据，包括股票代码、名称、上市日期、退市日期等。

#### 接口标识

stock_basic

#### 调用方法

```python
pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
```

或者

```python
pro.query('stock_basic', exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
```

#### 权限要求

2000积分起。此接口是基础信息，调取一次就可以拉取完，建议保存到本地存储后使用。

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | TS股票代码 |
| name | str | N | 名称 |
| market | str | N | 市场类别 （主板/创业板/科创板/CDR/北交所） |
| list_status | str | N | 上市状态 L上市 D退市 P暂停上市 G过会未交易，默认是L |
| exchange | str | N | 交易所 SSE上交所 SZSE深交所 BSE北交所 |
| is_hs | str | N | 是否沪深港通标的，N否 H沪股通 S深股通 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | TS代码 |
| symbol | str | Y | 股票代码 |
| name | str | Y | 股票名称 |
| area | str | Y | 地域 |
| industry | str | Y | 所属行业 |
| fullname | str | N | 股票全称 |
| enname | str | N | 英文全称 |
| cnspell | str | Y | 拼音缩写 |
| market | str | Y | 市场类型（主板/创业板/科创板/CDR） |
| exchange | str | N | 交易所代码 |
| curr_type | str | N | 交易货币 |
| list_status | str | N | 上市状态 L上市 D退市 G过会未交易 P暂停上市 |
| list_date | str | Y | 上市日期 |
| delist_date | str | N | 退市日期 |
| is_hs | str | N | 是否沪深港通标的，N否 H沪股通 S深股通 |
| act_name | str | Y | 实控人名称 |
| act_ent_type | str | Y | 实控人企业性质 |

#### 调用示例

```python
pro = ts.pro_api()

#查询当前所有正常上市交易的股票列表
data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')

#或者
#查询当前所有正常上市交易的股票列表
data = pro.query('stock_basic', exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
```

---

### 股票曾用名 (namechange)

#### 接口描述

历史名称变更记录

#### 接口信息

- **接口标识**：namechange
- **接口说明**：历史名称变更记录
- **调用方法**：
  ```python
  pro = ts.pro_api()
  df = pro.namechange(ts_code='600848.SH', fields='ts_code,name,start_date,end_date,change_reason')
  ```
- **权限要求**：免费

#### 输入参数

| 参数名称    | 参数类型 | 是否必填 | 参数描述     |
| :---------- | :------- | :------- | :----------- |
| ts_code     | str      | N        | TS代码       |
| start_date  | str      | N        | 公告开始日期 |
| end_date    | str      | N        | 公告结束日期 |

#### 输出参数

| 字段名称      | 字段类型 | 描述         |
| :------------ | :------- | :----------- |
| ts_code       | str      | TS代码       |
| name          | str      | 证券名称     |
| start_date    | str      | 开始日期     |
| end_date      | str      | 结束日期     |
| ann_date      | str      | 公告日期     |
| change_reason | str      | 变更原因     |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.namechange(ts_code='600848.SH', fields='ts_code,name,start_date,end_date,change_reason')
```

---

## 行情数据

### A股实时分钟 (rt_min)

#### 接口说明

获取全A股票实时分钟数据，包括1~60min。

#### 接口标识

rt_min

#### 调用方法

```python
pro = ts.pro_api()
#获取浦发银行60000.SH的实时分钟数据
df = pro.rt_min(ts_code='600000.SH', freq='1MIN')
```

#### 权限要求

正式权限请参阅 [权限说明](https://tushare.pro/document/1?doc_id=108)。

注：支持股票当日开盘以来的所有历史分钟数据提取，接口名：rt_min_daily（仅支持一个个股票提取，不同同时提取多个），可以[在线开通](https://tushare.pro/user/token)权限。

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| freq | str | Y | 1MIN,5MIN,15MIN,30MIN,60MIN （大写） |
| ts_code | str | Y | 支持单个和多个：600000.SH 或者 600000.SH,000001.SZ |

##### freq参数说明

| freq | 说明 |
| --- | --- |
| 1MIN | 1分钟 |
| 5MIN | 5分钟 |
| 15MIN | 15分钟 |
| 30MIN | 30分钟 |
| 60MIN | 60分钟 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 股票代码 |
| time | None | Y | 交易时间 |
| open | float | Y | 开盘价 |
| close | float | Y | 收盘价 |
| high | float | Y | 最高价 |
| low | float | Y | 最低价 |
| vol | float | Y | 成交量(股） |
| amount | float | Y | 成交额（元） |

---

### 股票历史分钟行情 (stk_mins)

#### 接口说明

获取A股分钟数据，支持1min/5min/15min/30min/60min行情，提供Python SDK和 http Restful API两种方式。

#### 调用方法

```python
pro = ts.pro_api()
df = pro.stk_mins(ts_code='600000.SH', freq='1min', start_date='2023-08-25 09:00:00', end_date='2023-08-25 19:00:00')
```

#### 权限要求

需单独开权限，正式权限请参阅 [权限说明](https://tushare.pro/document/1?doc_id=108) ，可以[在线开通](https://tushare.pro/user/min_subscribe)分钟权限。

#### 输入参数

| 名称       | 类型     | 是否必填 | 说明                                      |
| ---------- | -------- | -------- | ----------------------------------------- |
| ts_code    | str      | Y        | 股票代码，e.g. 600000.SH                  |
| freq       | str      | Y        | 分钟频度（1min/5min/15min/30min/60min）   |
| start_date | datetime | N        | 开始日期 格式：2023-08-25 09:00:00        |
| end_date   | datetime | N        | 结束时间 格式：2023-08-25 19:00:00        |

##### freq参数说明

| freq  | 说明   |
| ----- | ------ |
| 1min  | 1分钟  |
| 5min  | 5分钟  |
| 15min | 15分钟 |
| 30min | 30分钟 |
| 60min | 60分钟 |

#### 输出参数

| 名称       | 类型  | 描述         |
| ---------- | ----- | ------------ |
| ts_code    | str   | 股票代码     |
| trade_time | str   | 交易时间     |
| open       | float | 开盘价       |
| close      | float | 收盘价       |
| high       | float | 最高价       |
| low        | float | 最低价       |
| vol        | int   | 成交量(股)   |
| amount     | float | 成交金额（元） |

#### 调用示例

```python
pro = ts.pro_api()

#获取浦发银行60000.SH的历史分钟数据
df = pro.stk_mins(ts_code='600000.SH', freq='1min', start_date='2023-08-25 09:00:00', end_date='2023-08-25 19:00:00')
```

##### 数据样例

```
     ts_code             trade_time  close  open  high   low       vol     amount
0    600000.SH  2023-08-25 15:00:00   7.05  7.05  7.05  7.05  235500.0  1660275.0
1    600000.SH  2023-08-25 14:59:00   7.05  7.05  7.05  7.05       0.0        0.0
2    600000.SH  2023-08-25 14:58:00   7.05  7.05  7.05  7.05       0.0        0.0
3    600000.SH  2023-08-25 14:57:00   7.05  7.06  7.06  7.05   51800.0   365491.0
4    600000.SH  2023-08-25 14:56:00   7.05  7.05  7.06  7.04   92700.0   653831.0
..         ...                  ...    ...   ...   ...   ...       ...        ...
236  600000.SH  2023-08-25 09:34:00   7.01  7.02  7.02  7.00  120500.0   845311.0
237  600000.SH  2023-08-25 09:33:00   7.01  7.01  7.02  7.00  126000.0   883188.0
238  600000.SH  2023-08-25 09:32:00   7.01  7.02  7.02  6.99  236699.0  1659260.0
239  600000.SH  2023-08-25 09:31:00   7.02  6.99  7.02  6.97  807500.0  5649956.0
240  600000.SH  2023-08-25 09:30:00   6.99  6.99  6.99  6.99  103700.0   724863.0
```

---

### 股票周/月线行情(复权--每日更新)

#### 接口信息

- **接口名称**：股票周/月线行情(复权--每日更新)
- **接口标识**：`stk_week_month_adj`
- **接口说明**：获取股票周/月线复权行情，每日更新。
- **限量**：单次最大6000条，可使用交易日期循环提取，总量不限制。
- **权限要求**：用户需要至少2000积分才可以调取。

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api("YOUR_TOKEN")

df = pro.stk_week_month_adj(ts_code='000001.SZ', freq='week')
```

#### 输入参数

| 名称       | 类型 | 必选 | 描述                                                 |
| ---------- | ---- | ---- | ---------------------------------------------------- |
| ts_code    | str  | N    | TS代码                                               |
| trade_date | str  | N    | 交易日期（格式：YYYYMMDD，每周或每月最后一天的日期） |
| start_date | str  | N    | 开始交易日期                                         |
| end_date   | str  | N    | 结束交易日期                                         |
| freq       | str  | Y    | 频率：'week' (周), 'month' (月)                      |

#### 输出参数

| 名称      | 类型  | 描述                                                                 |
| --------- | ----- | -------------------------------------------------------------------- |
| ts_code   | str   | 股票代码                                                             |
| trade_date| str   | 交易日期（每周五或者月末日期）                                       |
| end_date  | str   | 计算截至日期                                                         |
| freq      | str   | 频率(周week,月month)                                                 |
| open      | float | (周/月)开盘价                                                        |
| high      | float | (周/月)最高价                                                        |
| low       | float | (周/月)最低价                                                        |
| close     | float | (周/月)收盘价                                                        |
| pre_close | float | 上一(周/月)收盘价【除权价，前复权】                                  |
| open_qfq  | float | 前复权(周/月)开盘价                                                  |
| high_qfq  | float | 前复权(周/月)最高价                                                  |
| low_qfq   | float | 前复权(周/月)最低价                                                  |
| close_qfq | float | 前复权(周/月)收盘价                                                  |
| open_hfq  | float | 后复权(周/月)开盘价                                                  |
| high_hfq  | float | 后复权(周/月)最高价                                                  |
| low_hfq   | float | 后复权(周/月)最低价                                                  |
| close_hfq | float | 后复权(周/月)收盘价                                                  |
| vol       | float | (周/月)成交量                                                        |
| amount    | float | (周/月)成交额                                                        |
| change    | float | (周/月)涨跌额                                                        |
| pct_chg   | float | (周/月)涨跌幅 【基于除权后的昨收计算的涨跌幅：（今收-除权昨收）/除权昨收 】 |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.stk_week_month_adj(ts_code='000001.SZ', freq='week')
```

**数据样例**

```
           ts_code  trade_date  freq   open   high    low  close  pre_close  open_qfq  high_qfq  low_qfq  close_qfq  open_hfq  high_hfq  low_hfq  close_hfq         vol      amount  change  pct_chg
0     000001.SZ   20250117  week  11.25  11.59  11.08  11.45      11.30     11.25     11.59    11.08      11.45   1437.57   1481.02  1415.85    1463.13  4353954.80  4963695.53    0.15     0.01
1     000001.SZ   20250110  week  11.38  11.63  11.22  11.30      11.38     11.38     11.63    11.22      11.30   1454.18   1486.13  1433.74    1443.96  4445402.00  5079074.95   -0.08    -0.01
2     000001.SZ   20250103  week  11.78  11.99  11.36  11.38      11.83     11.78     11.99    11.36      11.38   1505.30   1532.13  1451.63    1454.18  5801491.12  6781578.23   -0.45    -0.04
3     000001.SZ   20241227  week  11.64  12.02  11.64  11.83      11.62     11.64     12.02    11.64      11.83   1487.41   1535.96  1487.41    1511.69  6775611.59  8011303.78    0.21     0.02
4     000001.SZ   20241220  week  11.56  11.74  11.52  11.62      11.56     11.56     11.74    11.52      11.62   1477.18   1500.19  1472.07    1484.85  4036452.70  4689640.57    0.06     0.01
```

---

### 周线行情 (weekly)

#### 接口说明

获取A股周线行情，本接口每周最后一个交易日更新，如需要使用每天更新的周线数据，请使用日度更新的周线行情接口。

#### 调用方法

```python
pro = ts.pro_api()
df = pro.weekly(ts_code='000001.SZ', start_date='20180101', end_date='20181101', fields='ts_code,trade_date,open,high,low,close,vol,amount')
```

#### 权限要求

用户需要至少2000积分才可以调取。

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 参数描述 |
|---|---|---|---|
| ts_code | str | N | TS代码 （ts_code,trade_date两个参数任选一） |
| trade_date | str | N | 交易日期 （每周最后一个交易日期，YYYYMMDD格式） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 字段名称 | 字段类型 | 默认显示 | 字段描述 |
|---|---|---|---|
| ts_code | str | Y | 股票代码 |
| trade_date | str | Y | 交易日期 |
| close | float | Y | 周收盘价 |
| open | float | Y | 周开盘价 |
| high | float | Y | 周最高价 |
| low | float | Y | 周最低价 |
| pre_close | float | Y | 上一周收盘价 |
| change | float | Y | 周涨跌额 |
| pct_chg | float | Y | 周涨跌 （未复权，未*100，如果是复权请用通用行情接口，如需%单位请*100） |
| vol | float | Y | 周成交量 |
| amount | float | Y | 周成交额 |

#### 调用示例

```python
pro = ts.pro_api()

### 示例1：按代码和日期范围获取
df = pro.weekly(ts_code='000001.SZ', start_date='20180101', end_date='20181101', fields='ts_code,trade_date,open,high,low,close,vol,amount')

### 示例2：按交易日期获取
df = pro.weekly(trade_date='20181123', fields='ts_code,trade_date,open,high,low,close,vol,amount')
```

---

### 周线行情 (weekly)

#### 接口说明

获取A股周线行情，本接口每周最后一个交易日更新，如需要使用每天更新的周线数据，请使用日度更新的周线行情接口。

#### 调用方法

```python
pro = ts.pro_api()
df = pro.weekly(ts_code='000001.SZ', start_date='20180101', end_date='20181101', fields='ts_code,trade_date,open,high,low,close,vol,amount')

### 或者

df = pro.weekly(trade_date='20181123', fields='ts_code,trade_date,open,high,low,close,vol,amount')
```

#### 权限要求

用户需要至少2000积分才可以调取。

#### 输入参数

| 名称 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | TS代码 （ts_code,trade_date两个参数任选一） |
| trade_date | str | N | 交易日期 （每周最后一个交易日期，YYYYMMDD格式） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| ts_code | str | 股票代码 |
| trade_date | str | 交易日期 |
| close | float | 周收盘价 |
| open | float | 周开盘价 |
| high | float | 周最高价 |
| low | float | 周最低价 |
| pre_close | float | 上一周收盘价 |
| change | float | 周涨跌额 |
| pct_chg | float | 周涨跌 （未复权，未*100，如果是复权请用通用行情接口，如需%单位请*100 ） |
| vol | float | 周成交量 |
| amount | float | 周成交额 |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.weekly(ts_code='000001.SZ', start_date='20180101', end_date='20181101', fields='ts_code,trade_date,open,high,low,close,vol,amount')
print(df)
```

```text
        ts_code   trade_date  close   open   high    low          vol  \
    0   000001.SZ   20181026  11.18  10.81  11.46  10.71   9062500.14   
    1   000001.SZ   20181019  10.76  10.39  10.78   9.92   7235319.55   
    2   000001.SZ   20181012  10.30  10.70  10.79   9.70   7257596.97   
    3   000001.SZ   20180928  11.05  10.52  11.27  10.48   5458134.13   
    4   000001.SZ   20180921  10.67   9.80  10.70   9.68   5120305.29   
    5   000001.SZ   20180914   9.84  10.01  10.10   9.81   3534261.76   
    6   000001.SZ   20180907  10.01  10.09  10.55   9.93   4708303.81   
    7   000001.SZ   20180831  10.13  10.02  10.43   9.97   6715867.92   
    8   000001.SZ   20180824  10.03   8.90  10.28   8.87   6697713.52   
    9   000001.SZ   20180817   8.81   9.12   9.16   8.64   3206923.44   
    10  000001.SZ   20180810   9.23   8.94   9.35   8.88   3054338.56   
    11  000001.SZ   20180803   8.91   9.32   9.50   8.88   3648566.35   
    12  000001.SZ   20180727   9.25   9.04   9.59   9.00   5170189.41   
    13  000001.SZ   20180720   9.11   8.85   9.20   8.61   3806004.47   
    14  000001.SZ   20180713   8.88   8.69   9.03   8.58   4901983.84   
    15  000001.SZ   20180706   8.66   9.05   9.05   8.45   5125563.53   
    16  000001.SZ   20180629   9.09   9.91   9.92   8.87   5150575.93 
    
              amount  
    0   1.002282e+07  
    1   7.482596e+06  
    2   7.483906e+06  
    3   5.904901e+06  
    4   5.225262e+06  
    5   3.501724e+06  
    6   4.796533e+06  
    7   6.858804e+06  
    8   6.358840e+06  
    9   2.854248e+06  
    10  2.787629e+06  
    11  3.363448e+06  
    12  4.826484e+06  
    13  3.371040e+06  
    14  4.346872e+06  
    15  4.446723e+06  
    16  4.764107e+06
```

---

### 备用行情 (bak_daily)

#### 接口说明

获取备用行情，包括特定的行情指标(数据从2017年中左右开始，早期有几天数据缺失，近期正常)。

#### 调用方法

通过Tushare Pro的Python SDK进行调用。

```python
import tushare as ts

### 初始化pro接口
pro = ts.pro_api("YOUR_TOKEN")

### 调用接口
df = pro.bak_daily(**params)
```

#### 权限要求

单次最大7000行数据，可以根据日期参数循环获取，正式权限需要5000积分。

#### 输入参数

| 名称       | 类型 | 必选 | 描述     |
| ---------- | ---- | ---- | -------- |
| ts_code    | str  | N    | 股票代码 |
| trade_date | str  | N    | 交易日期 |
| start_date | str  | N    | 开始日期 |
| end_date   | str  | N    | 结束日期 |
| offset     | str  | N    | 开始行数 |
| limit      | str  | N    | 最大行数 |

#### 输出参数

| 名称         | 类型  | 描述             |
| ------------ | ----- | ---------------- |
| ts_code      | str   | 股票代码         |
| trade_date   | str   | 交易日期         |
| name         | str   | 股票名称         |
| pct_change   | float | 涨跌幅           |
| close        | float | 收盘价           |
| change       | float | 涨跌额           |
| open         | float | 开盘价           |
| high         | float | 最高价           |
| low          | float | 最低价           |
| pre_close    | float | 昨收价           |
| vol_ratio    | float | 量比             |
| turn_over    | float | 换手率           |
| swing        | float | 振幅             |
| vol          | float | 成交量           |
| amount       | float | 成交额           |
| selling      | float | 内盘（主动卖，手） |
| buying       | float | 外盘（主动买，手） |
| total_share  | float | 总股本(亿)       |
| float_share  | float | 流通股本(亿)     |
| pe           | float | 市盈(动)         |
| industry     | str   | 所属行业         |
| area         | str   | 所属地域         |
| float_mv     | float | 流通市值         |
| total_mv     | float | 总市值           |
| avg_price    | float | 平均价           |
| strength     | float | 强弱度(%)        |
| activity     | float | 活跃度(%)        |
| avg_turnover | float | 笔换手           |
| attack       | float | 攻击波(%)        |
| interval_3   | float | 近3月涨幅        |
| interval_6   | float | 近6月涨幅        |

#### 调用示例

```python
pro = ts.pro_api()

df = pro.bak_daily(trade_date='20211012', fields='trade_date,ts_code,name,close,open')
```

---

_# 复权因子 (adj_factor)

#### 接口描述

本接口由Tushare自行生产，获取股票复权因子，可提取单只股票全部历史复权因子，也可以提取单日全部股票的复权因子。

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api("YOUR_TOKEN")

### 提取000001全部复权因子
df = pro.adj_factor(ts_code='000001.SZ', trade_date='')

### 提取2018年7月18日复权因子
df = pro.adj_factor(ts_code='', trade_date='20180718')

### 或者
df = pro.query('adj_factor',  trade_date='20180718')
```

#### 权限要求

2000积分起，5000以上可高频调取

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 股票代码 |
| trade_date | str | N | 交易日期(YYYYMMDD，下同) |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

**注：日期都填YYYYMMDD格式，比如20181010**

#### 输出参数

| 名称 | 类型 | 描述 |
| --- | --- | --- |
| ts_code | str | 股票代码 |
| trade_date | str | 交易日期 |
| adj_factor | float | 复权因子 |

#### 调用示例

```python
pro = ts.pro_api()

#提取000001全部复权因子
df = pro.adj_factor(ts_code='000001.SZ', trade_date='')


#提取2018年7月18日复权因子
df = pro.adj_factor(ts_code='', trade_date='20180718')
```

或者

```python
df = pro.query('adj_factor',  trade_date='20180718')
```

---

### 复权因子 (adj_factor)

#### 接口说明

本接口由Tushare自行生产，获取股票复权因子，可提取单只股票全部历史复权因子，也可以提取单日全部股票的复权因子。

**更新时间：** 盘前9点15~20分完成当日复权因子入库

#### 调用方法

```python
pro.adj_factor(ts_code='...', trade_date='...')
### 或者
pro.query('adj_factor', trade_date='...')
```

#### 权限要求

2000积分起，5000以上可高频调取

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 股票代码 |
| trade_date | str | N | 交易日期(YYYYMMDD，下同) |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

**注：** 日期都填YYYYMMDD格式，比如20181010

#### 输出参数

| 名称 | 类型 | 描述 |
| --- | --- | --- |
| ts_code | str | 股票代码 |
| trade_date | str | 交易日期 |
| adj_factor | float | 复权因子 |

#### 调用示例

```python
pro = ts.pro_api()

#提取000001全部复权因子
df = pro.adj_factor(ts_code='000001.SZ', trade_date='')


#提取2018年7月18日复权因子
df = pro.adj_factor(ts_code='', trade_date='20180718')

### 或者

df = pro.query('adj_factor',  trade_date='20180718')
```

---

### 实时盘口TICK快照(爬虫版)

#### 接口信息

- **接口名称**：实时盘口TICK快照(爬虫版)
- **接口标识**：realtime_quote
- **接口说明**：本接口是tushare org版实时接口的顺延，数据来自网络，且不进入tushare服务器，属于爬虫接口，请将tushare升级到1.3.3版本以上。
- **权限要求**：0积分完全开放，但需要有tushare账号。

#### 调用方法

```python
import tushare as ts

#设置你的token，登录tushare在个人用户中心里拷贝
ts.set_token("你的token")

#sina数据
df = ts.realtime_quote(ts_code="600000.SH,000001.SZ,000001.SH")

#东财数据
df = ts.realtime_quote(ts_code="600000.SH", src="dc")
```

#### 输入参数

| 名称     | 类型 | 必选 | 描述                                                                         |
|----------|------|------|------------------------------------------------------------------------------|
| ts_code  | str  | N    | 股票代码，需按tushare股票和指数标准代码输入，比如：000001.SZ表示平安银行，000001.SH表示上证指数 |
| src      | str  | N    | 数据源 （sina-新浪 dc-东方财富，默认sina）                                   |

##### src数据源说明

| src源 | 说明     | 描述                                                                       |
|-------|----------|----------------------------------------------------------------------------|
| sina  | 新浪财经 | 支持多个多个股票同时输入，举例：ts_code='600000.SH,000001.SZ'），一次最多不能超过50个股票 |
| dc    | 东方财富 | 只支持单个股票提取                                                         |

#### 输出参数

| 名称     | 类型  | 描述                               |
|----------|-------|------------------------------------|
| name     | str   | 股票名称                           |
| ts_code  | str   | 股票代码                           |
| date     | str   | 交易日期                           |
| time     | str   | 交易时间                           |
| open     | float | 开盘价                             |
| pre_close| float | 昨收价                             |
| price    | float | 现价                               |
| high     | float | 今日最高价                         |
| low      | float | 今日最低价                         |
| bid      | float | 竞买价，即“买一”报价（元）         |
| ask      | float | 竞卖价，即“卖一”报价（元）         |
| volume   | int   | 成交量（src=sina时是股，src=dc时是手） |
| amount   | float | 成交金额（元 CNY）                 |
| b1_v     | float | 委买一（量，单位：手，下同）       |
| b1_p     | float | 委买一（价，单位：元，下同）       |
| b2_v     | float | 委买二（量）                       |
| b2_p     | float | 委买二（价）                       |
| b3_v     | float | 委买三（量）                       |
| b3_p     | float | 委买三（价）                       |
| b4_v     | float | 委买四（量）                       |
| b4_p     | float | 委买四（价）                       |
| b5_v     | float | 委买五（量）                       |
| b5_p     | float | 委买五（价）                       |
| a1_v     | float | 委卖一（量，单位：手，下同）       |
| a1_p     | float | 委卖一（价，单位：元，下同）       |
| a2_v     | float | 委卖二（量）                       |
| a2_p     | float | 委卖二（价）                       |
| a3_v     | float | 委卖三（量）                       |
| a3_p     | float | 委卖三（价）                       |
| a4_v     | float | 委卖四（量）                       |
| a4_p     | float | 委卖四（价）                       |
| a5_v     | float | 委卖五（量）                       |
| a5_p     | float | 委卖五（价）                       |

#### 调用示例

```python
import tushare as ts

#设置你的token，登录tushare在个人用户中心里拷贝
ts.set_token("你的token")

#sina数据
df = ts.realtime_quote(ts_code="600000.SH,000001.SZ,000001.SH")

#东财数据
df = ts.realtime_quote(ts_code="600000.SH", src="dc")
```

---

### 实时成交（爬虫） (realtime_tick)

#### 接口说明

本接口是tushare org版实时接口的顺延，数据来自网络，且不进入tushare服务器，属于爬虫接口，数据包括该股票当日开盘以来的所有分笔成交数据。

#### 调用方法

接口：realtime_tick

#### 权限要求

0积分完全开放，但需要有tushare账号。

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 股票代码，需按tushare股票代码标准输入，比如：000001.SZ表示平安银行，600000.SH表示浦发银行，单次只能输入一个股票 |
| src | str | N | 数据源 （sina-新浪 dc-东方财富，默认sina） |

#### 输出参数

| 名称 | 类型 | 描述 |
| --- | --- | --- |
| time | str | 交易时间 |
| price | float | 现价 |
| change | float | 价格变动 |
| volume | int | 成交量（单位：手） |
| amount | int | 成交金额（元） |
| type | str | 类型：买入/卖出/中性 |

#### 调用示例

```python
import tushare as ts

#设置你的token，登录tushare在个人用户中心里拷贝
ts.set_token('你的token')

#sina数据
df = ts.realtime_tick(ts_code='600000.SH')


#东财数据
df = ts.realtime_tick(ts_code='600000.SH', src='dc')
```

---

### 实时涨跌幅排名(爬虫版)

#### 接口信息

- **接口名称**: 实时涨跌幅排名(爬虫版)
- **接口标识**: realtime_list
- **接口说明**: 本接口是tushare org版实时接口的顺延，数据来自网络，且不进入tushare服务器，属于爬虫接口，数据包括该股票当日开盘以来的所有分笔成交数据。
- **权限要求**: 0积分完全开放，但需要有tushare账号。

#### 输入参数

| 名称 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| src | str | N | 数据源 （sina-新浪 dc-东方财富，默认dc） |

#### 输出参数 (东财数据)

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| ts_code | str | 股票代码 |
| name | str | 股票名称 |
| price | float | 当前价格 |
| pct_change | float | 涨跌幅 |
| change | float | 涨跌额 |
| volume | int | 成交量（单位：手） |
| amount | int | 成交金额（元） |
| swing | float | 振幅 |
| low | float | 今日最低价 |
| high | float | 今日最高价 |
| open | float | 今日开盘价 |
| close | float | 今日收盘价 |
| vol_ratio | int | 量比 |
| turnover_rate | float | 换手率 |
| pe | int | 市盈率PE |
| pb | float | 市净率PB |
| total_mv | float | 总市值（元） |
| float_mv | float | 流通市值（元） |
| rise | float | 涨速 |
| 5min | float | 5分钟涨幅 |
| 60day | float | 60天涨幅 |
| 1tyear | float | 1年涨幅 |

#### 输出参数 (新浪数据)

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| ts_code | str | 股票代码 |
| name | str | 股票名称 |
| price | float | 当前价格 |
| pct_change | float | 涨跌幅 |
| change | float | 涨跌额 |
| buy | float | 买入价 |
| sale | float | 卖出价 |
| close | float | 今日收盘价 |
| open | float | 今日开盘价 |
| high | float | 今日最高价 |
| low | float | 今日最低价 |
| volume | int | 成交量（单位：股） |
| amount | int | 成交金额（元） |
| time | str | 当前时间 |

#### 调用示例

```python
import tushare as ts

#东财数据
df = ts.realtime_list(src='dc')


#sina数据
df = ts.realtime_list(src='sina')
```

---

### 月线行情

**接口标识**：monthly

**接口说明**：获取A股月线数据

**调用方法**：
```python
import tushare as ts

pro = ts.pro_api("YOUR_TOKEN")

df = pro.monthly(ts_code='000001.SZ', start_date='20180101', end_date='20181101', fields='ts_code,trade_date,open,high,low,close,vol,amount')
```

**权限要求**：用户需要至少2000积分才可以调取

**输入参数**：

| 名称 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | TS代码 （ts_code,trade_date两个参数任选一） |
| trade_date | str | N | 交易日期 （每月最后一个交易日日期，YYYYMMDD格式） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

**输出参数**：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| ts_code | str | 股票代码 |
| trade_date | str | 交易日期 |
| close | float | 月收盘价 |
| open | float | 月开盘价 |
| high | float | 月最高价 |
| low | float | 月最低价 |
| pre_close | float | 上月收盘价 |
| change | float | 月涨跌额 |
| pct_chg | float | 月涨跌幅 （未复权，如果是复权请用通用行情接口） |
| vol | float | 月成交量 |
| amount | float | 月成交额 |

**调用示例**：

```python
pro = ts.pro_api()

#示例1
df = pro.monthly(ts_code='000001.SZ', start_date='20180101', end_date='20181101', fields='ts_code,trade_date,open,high,low,close,vol,amount')

#示例2
df = pro.monthly(trade_date='20181031', fields='ts_code,trade_date,open,high,low,close,vol,amount')
```

---

### 每日停复牌信息 (suspend_d)

#### 接口说明

按日期方式获取股票每日停复牌信息。

#### 调用方法

```python
pro = ts.pro_api()
df = pro.suspend_d(**kwargs)
```

#### 权限要求

本文档未明确提及特定的权限或积分要求。

#### 输入参数

| 参数名称 | 类型 | 是否必填 | 描述 |
|---|---|---|---|
| ts_code | str | N | 股票代码(可输入多值) |
| trade_date | str | N | 交易日日期 |
| start_date | str | N | 停复牌查询开始日期 |
| end_date | str | N | 停复牌查询结束日期 |
| suspend_type | str | N | 停复牌类型：S-停牌,R-复牌 |

#### 输出参数

| 字段名称 | 类型 | 描述 |
|---|---|---|
| ts_code | str | TS代码 |
| trade_date | str | 停复牌日期 |
| suspend_timing | str | 日内停牌时间段 |
| suspend_type | str | 停复牌类型：S-停牌，R-复牌 |

#### 调用示例

```python
pro = ts.pro_api()

#提取2020-03-12的停牌股票
df = pro.suspend_d(suspend_type='S', trade_date='20200312')
```

---

### 每日指标 (daily_basic)

#### 接口说明

获取全部股票每日重要的基本面指标，可用于选股分析、报表展示等。单次请求最大返回6000条数据，可按日线循环提取全部历史。

**更新时间：** 交易日每日15点～17点之间

#### 调用方法

```python
pro.daily_basic()
```

#### 权限要求

至少2000积分才可以调取，5000积分无总量限制。

#### 输入参数

| 名称       | 类型 | 是否必填 | 描述             |
| ---------- | ---- | -------- | ------------------ |
| ts_code    | str  | Y        | 股票代码（二选一）   |
| trade_date | str  | N        | 交易日期 （二选一） |
| start_date | str  | N        | 开始日期(YYYYMMDD) |
| end_date   | str  | N        | 结束日期(YYYYMMDD) |

*注：日期都填YYYYMMDD格式，比如20181010*

#### 输出参数

| 名称            | 类型  | 描述                     |
| --------------- | ----- | ------------------------ |
| ts_code         | str   | TS股票代码               |
| trade_date      | str   | 交易日期                 |
| close           | float | 当日收盘价               |
| turnover_rate   | float | 换手率（%）              |
| turnover_rate_f | float | 换手率（自由流通股）     |
| volume_ratio    | float | 量比                     |
| pe              | float | 市盈率（总市值/净利润）  |
| pe_ttm          | float | 市盈率（TTM）            |
| pb              | float | 市净率（总市值/净资产）  |
| ps              | float | 市销率                   |
| ps_ttm          | float | 市销率（TTM）            |
| dv_ratio        | float | 股息率 （%）             |
| dv_ttm          | float | 股息率（TTM）（%）       |
| total_share     | float | 总股本 （万股）          |
| float_share     | float | 流通股本 （万股）        |
| free_share      | float | 自由流通股本 （万）      |
| total_mv        | float | 总市值 （万元）          |
| circ_mv         | float | 流通市值（万元）         |

#### 调用示例

```python
import tushare as ts

pro = ts.pro_api()

### 查询单日全部
df = pro.daily_basic(trade_date='20180726', fields='ts_code,trade_date,turnover_rate,volume_ratio,pe,pb')

### 查询单个股票
df = pro.daily_basic(ts_code='000001.SZ', start_date='20180101', end_date='20181011', fields='ts_code,trade_date,turnover_rate,volume_ratio,pe,pb')
```

---

### 沪深京实时日线 (rt_k)

#### 接口说明

获取实时日k线行情，支持按股票代码及股票代码通配符一次性提取全部股票实时日k线行情。

#### 调用方法

```python
pro.rt_k()
```

#### 权限要求

本接口是单独开权限的数据，单独申请权限请参考权限列表，可以在线开通权限。

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| :--- | :--- | :--- | :--- |
| ts_code | str | Y | 支持通配符方式，e.g. 所有上交所股票：6*.SH、所有创业板股票3*.SZ、所有科创板股票688*.SH，或单个股票600000.SH |

**注：** ts_code代码一定要带.SH/.SZ/.BJ后缀

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| :--- | :--- | :--- | :--- |
| ts_code | str | Y | 股票代码 |
| name | None | Y | 股票名称 |
| pre_close | float | Y | 昨收价 |
| high | float | Y | 最高价 |
| open | float | Y | 开盘价 |
| low | float | Y | 最低价 |
| close | float | Y | 收盘价（最新价） |
| vol | int | Y | 成交量（股） |
| amount | int | Y | 成交金额（元） |
| num | int | Y | 开盘以来成交笔数 |
| ask_price1 | float | N | 委托卖盘（元） |
| ask_volume1 | int | N | 委托卖盘（股） |
| bid_price1 | float | N | 委托买盘（元） |
| bid_volume1 | int | N | 委托买盘（股） |
| trade_time | str | N | 交易时间 |

#### 调用示例

```python
#获取今日开盘以来所有创业板实时日线和成交笔数
df = pro.rt_k(ts_code='3*.SZ')

#获取今日开盘以来全市场所有股票实时日线和成交笔数（不建议一次提取全市场，可分批提取性能更好）
df = pro.rt_k(ts_code='3*.SZ,6*.SH,0*.SZ,9*.BJ')

#获取当日开盘以来单个股票实时日线和成交笔数
df = pro.rt_k(ts_code='600000.SH,000001.SZ')
```

---

### 沪深股通十大成交股

#### 接口信息

- **接口名称**：沪深股通十大成交股
- **接口标识**：hsgt_top10
- **接口说明**：获取沪股通、深股通每日前十大成交详细数据，每天18~20点之间完成当日更新。
- **调用方法**：
  ```python
  pro.hsgt_top10(trade_date='20180725', market_type='1')
  ```
  或者
  ```python
  pro.query('hsgt_top10', ts_code='600519.SH', start_date='20180701', end_date='20180725')
  ```
- **权限要求**：未在文档中明确提及。

#### 输入参数

| 名称       | 类型 | 必选 | 描述                 |
| ---------- | ---- | ---- | -------------------- |
| ts_code    | str  | N    | 股票代码（二选一）   |
| trade_date | str  | N    | 交易日期（二选一）   |
| start_date | str  | N    | 开始日期             |
| end_date   | str  | N    | 结束日期             |
| market_type| str  | N    | 市场类型（1：沪市 3：深市） |

#### 输出参数

| 名称         | 类型  | 描述                       |
| ------------ | ----- | -------------------------- |
| trade_date   | str   | 交易日期                   |
| ts_code      | str   | 股票代码                   |
| name         | str   | 股票名称                   |
| close        | float | 收盘价                     |
| change       | float | 涨跌额                     |
| rank         | int   | 资金排名                   |
| market_type  | str   | 市场类型（1：沪市 3：深市） |
| amount       | float | 成交金额（元）             |
| net_amount   | float | 净成交金额（元）           |
| buy          | float | 买入金额（元）             |
| sell         | float | 卖出金额（元）             |

#### 调用示例

```python
pro = ts.pro_api()

### 获取2018年7月25日沪市的十大成交股
pro.hsgt_top10(trade_date='20180725', market_type='1')

### 获取贵州茅台在2018年7月1日至25日期间的十大成交股情况
pro.query('hsgt_top10', ts_code='600519.SH', start_date='20180701', end_date='20180725')
```

---

### 港股交易日历 (hk_tradecal)

#### 接口描述

获取港股交易日历信息。

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api("YOUR_TOKEN")
df = pro.hk_tradecal(start_date='20200101', end_date='20201231')
```

#### 权限要求

用户需要至少300积分才可以调取，基础积分每分钟内最多调取500次，每次5000条数据，超过5000积分无限制。 

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 描述 |
|---|---|---|---|
| start_date | str | N | 开始日期 (YYYYMMDD) |
| end_date | str | N | 结束日期 (YYYYMMDD) |
| is_open | str | N | 是否交易 '0'休市 '1'交易 |

#### 输出参数

| 字段名称 | 字段类型 | 默认显示 | 描述 |
|---|---|---|---|
| cal_date | str | Y | 日历日期 |
| is_open | str | Y | 是否交易 '0'休市 '1'交易 |
| pretrade_date | str | Y | 上一个交易日 |

#### 调用示例

```python
### 获取2020年港股交易日历
df = pro.hk_tradecal(start_date='20200101', end_date='20201231')
```

---

### 港股通十大成交股 (ggt_top10)

#### 接口说明

获取港股通每日成交数据，其中包括沪市、深市详细数据，每天18~20点之间完成当日更新

#### 调用方法

```python
pro = ts.pro_api()
pro.ggt_top10(trade_date='20180727')
```

或者

```python
pro.query('ggt_top10', ts_code='00700', start_date='20180701', end_date='20180727')
```

#### 权限要求

文档中未明确提及权限要求（积分要求）。

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 股票代码（二选一） |
| trade_date | str | N | 交易日期（二选一） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |
| market_type | str | N | 市场类型 2：港股通（沪） 4：港股通（深） |

#### 输出参数

| 名称 | 类型 | 描述 |
| --- | --- | --- |
| trade_date | str | 交易日期 |
| ts_code | str | 股票代码 |
| name | str | 股票名称 |
| close | float | 收盘价 |
| p_change | float | 涨跌幅 |
| rank | int | 资金排名 |
| market_type | str | 市场类型 2：港股通（沪） 4：港股通（深） |
| amount | float | 累计成交金额（元） |
| net_amount | float | 净买入金额（元） |
| sh_amount | float | 沪市成交金额（元） |
| sh_net_amount | float | 沪市净买入金额（元） |
| sh_buy | float | 沪市买入金额（元） |
| sh_sell | float | 沪市卖出金额 |
| sz_amount | float | 深市成交金额（元） |
| sz_net_amount | float | 深市净买入金额（元） |
| sz_buy | float | 深市买入金额（元） |
| sz_sell | float | 深市卖出金额（元） |

#### 调用示例

```python
pro = ts.pro_api()

df = pro.ggt_top10(trade_date='20180727')
```

或者

```python
df = pro.query('ggt_top10', ts_code='00700', start_date='20180701', end_date='20180727')
```

##### 数据样例

```
   trade_date ts_code       name   close   p_change  rank   market_type  \
0    20180727   00175    吉利汽车   18.42   -3.2563   4.0            2   
1    20180727   00175    吉利汽车   18.42   -3.2563   4.0            4   
2    20180727   00581  中国东方集团    6.60    5.9390   NaN          4   
3    20180727   00607    丰盛控股    3.48   -2.5210   NaN            4   
4    20180727   00700    腾讯控股  373.00   -0.4803   1.0            2   
5    20180727   00700    腾讯控股  373.00   -0.4803   1.0            4   

       amount   net_amount    sh_amount  sh_net_amount       sh_buy  \
0   476991220.0  -71294840.0  182183940.0    -30957820.0   75613060.0   
1   294807280.0  -71294840.0  182183940.0    -30957820.0   75613060.0   
2    49196800.0   23544640.0          NaN            NaN          NaN   
3    44903050.0  -36431000.0          NaN            NaN          NaN   
4   519061900.0 -219372420.0  383183900.0   -189541460.0   96821220.0   
5   654939900.0 -219372420.0  383183900.0   -189541460.0   96821220.0   

       sh_sell    sz_amount  sh_net_amount      sz_buy     sz_sell
0   106570880.0  112623340.0    -40337020.0  36143160.0  76480180.0
1   106570880.0  112623340.0    -40337020.0  36143160.0  76480180.0
2           NaN   49196800.0     23544640.0  36370720.0  12826080.0
3           NaN   44903050.0    -36431000.0   4236025.0  40667025.0
4   286362680.0  135878000.0    -29830960.0  53023520.0  82854480.0
5   286362680.0  135878000.0    -29830960.0  53023520.0  82854480.0
```

---

### 港股通每日成交统计 (ggt_daily)

#### 接口说明

获取港股通每日成交信息，数据从2014年开始。

**调用方法**

```python
pro.ggt_daily()
```

**权限要求**

用户积2000积分可调取，5000积分以上频次相对较高。

#### 输入参数

| 名称 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| trade_date | str | N | 交易日期 （格式YYYYMMDD，下同。支持单日和多日输入） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| trade_date | str | Y | 交易日期 |
| buy_amount | float | Y | 买入成交金额（亿元） |
| buy_volume | float | Y | 买入成交笔数（万笔） |
| sell_amount | float | Y | 卖出成交金额（亿元） |
| sell_volume | float | Y | 卖出成交笔数（万笔） |

#### 调用示例

```python
pro = ts.pro_api()

#获取单日全部统计
df = pro.ggt_daily(trade_date='20190625')

#获取多日统计信息
df = pro.ggt_daily(trade_date='20190925,20180924,20170925')

#获取时间段统计信息
df = pro.ggt_daily(start_date='20180925', end_date='20190925')
```

---

### 港股通每月成交统计 (ggt_monthly)

#### 接口说明

- **接口标识**：`ggt_monthly`
- **接口名称**：港股通每月成交统计
- **功能描述**：港股通每月成交信息，数据从2014年开始。
- **调用方法**：`pro.ggt_monthly()`
- **权限要求**：用户积5000积分可调取。

#### 输入参数

| 参数名称 | 类型 | 是否必填 | 描述 |
|---|---|---|---|
| month | str | N | 月度（格式YYYYMM，下同，支持多个输入） |
| start_month | str | N | 开始月度 |
| end_month | str | N | 结束月度 |

#### 输出参数

| 字段名称 | 类型 | 描述 |
|---|---|---|
| month | str | 交易日期 |
| day_buy_amt | float | 当月日均买入成交金额（亿元） |
| day_buy_vol | float | 当月日均买入成交笔数（万笔） |
| day_sell_amt | float | 当月日均卖出成交金额（亿元） |
| day_sell_vol | float | 当月日均卖出成交笔数（万笔） |
| total_buy_amt | float | 总买入成交金额（亿元） |
| total_buy_vol | float | 总买入成交笔数（万笔） |
| total_sell_amt | float | 总卖出成交金额（亿元） |
| total_sell_vol | float | 总卖出成交笔数（万笔） |

#### 调用示例

```python
pro = ts.pro_api()

#获取单月全部统计
df = pro.ggt_monthly(trade_date='201906')

#获取多月统计信息
df = pro.ggt_monthly(trade_date='201906,201907,201709')

#获取时间段统计信息
df = pro.ggt_monthly(start_date='201809', end_date='201908')
```

---

### 股票周/月线行情(每日更新)

#### 接口信息

- **接口名称**: 股票周/月线行情(每日更新)
- **接口标识**: stk_weekly_monthly
- **接口说明**: 股票周/月线行情(每日更新)
- **限量**: 单次最大6000,可使用交易日期循环提取，总量不限制
- **权限要求**: 用户需要至少2000积分才可以调取

#### 调用方法

```python
pro = ts.pro_api()

#获取20251024这周周线数据
df=pro.stk_weekly_monthly(trade_date='20251024',freq='week')

#获取202510月月线数据
df=pro.stk_weekly_monthly(trade_date='20251031',freq='month')
```

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | TS代码 |
| trade_date | str | N | 交易日期(格式：YYYYMMDD，每周或每月最后一天的日期） |
| start_date | str | N | 开始交易日期 |
| end_date | str | N | 结束交易日期 |
| freq | str | Y | 频率week周，month月 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 股票代码 |
| trade_date | str | Y | 交易日期 |
| end_date | str | Y | 计算截至日期 |
| freq | str | Y | 频率(周week,月month) |
| open | float | Y | (周/月)开盘价 |
| high | float | Y | (周/月)最高价 |
| low | float | Y | (周/月)最低价 |
| close | float | Y | (周/月)收盘价 |
| pre_close | float | Y | 上一(周/月)收盘价 |
| vol | float | Y | (周/月)成交量 |
| amount | float | Y | (周/月)成交额 |
| change | float | Y | (周/月)涨跌额 |
| pct_chg | float | Y | (周/月)涨跌幅(未复权,如果是复权请用 通用行情接口) |

---

### 股票曾用名 (namechange)

#### 接口说明

历史名称变更记录

#### 调用方法

```python
pro = ts.pro_api()
df = pro.namechange(ts_code='600848.SH', fields='ts_code,name,start_date,end_date,change_reason')
```

#### 权限要求

无

#### 输入参数

| 名称      | 类型 | 是否必填 | 说明         |
| --------- | ---- | -------- | ------------ |
| ts_code   | str  | N        | TS代码       |
| start_date| str  | N        | 公告开始日期 |
| end_date  | str  | N        | 公告结束日期 |

#### 输出参数

| 名称          | 类型 | 默认输出 | 说明     |
| ------------- | ---- | -------- | -------- |
| ts_code       | str  | Y        | TS代码   |
| name          | str  | Y        | 证券名称 |
| start_date    | str  | Y        | 开始日期 |
| end_date      | str  | Y        | 结束日期 |
| ann_date      | str  | Y        | 公告日期 |
| change_reason | str  | Y        | 变更原因 |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.namechange(ts_code='600848.SH', fields='ts_code,name,start_date,end_date,change_reason')
```

---

## 财务数据

### 业绩快报 (express)

#### 接口说明

获取上市公司业绩快报。

**权限要求**

用户需要至少2000积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)。

**提示**

当前接口只能按单只股票获取其历史数据，如果需要获取某一季度全部上市公司数据，请使用express_vip接口（参数一致），需积攒5000积分。

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api()

df = pro.express(ts_code='600000.SH', start_date='20180101', end_date='20180701', fields='ts_code,ann_date,end_date,revenue,operate_profit,total_profit,n_income,total_assets')
```

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 股票代码 |
| ann_date | str | N | 公告日期 |
| start_date | str | N | 公告开始日期 |
| end_date | str | N | 公告结束日期 |
| period | str | N | 报告期(每个季度最后一天的日期,比如20171231表示年报，20170630半年报，20170930三季报) |

#### 输出参数

| 名称 | 类型 | 描述 |
| --- | --- | --- |
| ts_code | str | TS股票代码 |
| ann_date | str | 公告日期 |
| end_date | str | 报告期 |
| revenue | float | 营业收入(元) |
| operate_profit | float | 营业利润(元) |
| total_profit | float | 利润总额(元) |
| n_income | float | 净利润(元) |
| total_assets | float | 总资产(元) |
| total_hldr_eqy_exc_min_int | float | 股东权益合计(不含少数股东权益)(元) |
| diluted_eps | float | 每股收益(摊薄)(元) |
| diluted_roe | float | 净资产收益率(摊薄)(%) |
| yoy_net_profit | float | 去年同期修正后净利润 |
| bps | float | 每股净资产 |
| yoy_sales | float | 同比增长率:营业收入 |
| yoy_op | float | 同比增长率:营业利润 |
| yoy_tp | float | 同比增长率:利润总额 |
| yoy_dedu_np | float | 同比增长率:归属母公司股东的净利润 |
| yoy_eps | float | 同比增长率:基本每股收益 |
| yoy_roe | float | 同比增减:加权平均净资产收益率 |
| growth_assets | float | 比年初增长率:总资产 |
| yoy_equity | float | 比年初增长率:归属母公司的股东权益 |
| growth_bps | float | 比年初增长率:归属于母公司股东的每股净资产 |
| or_last_year | float | 去年同期营业收入 |
| op_last_year | float | 去年同期营业利润 |
| tp_last_year | float | 去年同期利润总额 |
| np_last_year | float | 去年同期净利润 |
| eps_last_year | float | 去年同期每股收益 |
| open_net_assets | float | 期初净资产 |
| open_bps | float | 期初每股净资产 |
| perf_summary | str | 业绩简要说明 |
| is_audit | int | 是否审计： 1是 0否 |
| remark | str | 备注 |

#### 调用示例

##### 获取单只股票的业绩快报

```python
pro = ts.pro_api()

df = pro.express(ts_code='600000.SH', start_date='20180101', end_date='20180701', fields='ts_code,ann_date,end_date,revenue,operate_profit,total_profit,n_income,total_assets')
```

##### 获取某一季度全部股票数据

```python
df = pro.express_vip(period='20181231',fields='ts_code,ann_date,end_date,revenue,operate_profit,total_profit,n_income,total_assets')
```

##### 数据样例

```
         ts_code  ann_date  end_date       revenue  operate_profit  total_profit      n_income  total_assets  \
0  603535.SH  20180411  20180331  2.064659e+08    3.345047e+07  3.340047e+07  2.672643e+07  1.682111e+09   
1  603535.SH  20180208  20171231  1.034262e+09    1.323373e+08  1.440493e+08  1.188325e+08  1.710466e+09   
2  603535.SH  20171016  20170930  7.064117e+08    9.509520e+07  9.931530e+07  8.202480e+07  1.672986e+09
```

---

### 业绩预告 (forecast)

#### 接口描述

获取上市公司发布的业绩预告、修正公告及业绩快报。

**接口名称**：forecast
**接口说明**：获取业绩预告数据
**调用方法**：pro.forecast()
**权限要求**：用户需要至少2000积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)

**提示**：当前接口只能按单只股票获取其历史数据，如果需要获取某一季度全部上市公司数据，请使用forecast_vip接口（参数一致），需积攒5000积分。

#### 输入参数

| 参数名称 | 类型 | 是否必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 股票代码(二选一) |
| ann_date | str | N | 公告日期 (二选一) |
| start_date | str | N | 公告开始日期 |
| end_date | str | N | 公告结束日期 |
| period | str | N | 报告期(每个季度最后一天的日期，比如20171231表示年报，20170630半年报，20170930三季报) |
| type | str | N | 预告类型(预增/预减/扭亏/首亏/续亏/续盈/略增/略减) |

#### 输出参数

| 字段名称 | 类型 | 描述 |
| --- | --- | --- |
| ts_code | str | TS股票代码 |
| ann_date | str | 公告日期 |
| end_date | str | 报告期 |
| type | str | 业绩预告类型(预增/预减/扭亏/首亏/续亏/续盈/略增/略减) |
| p_change_min | float | 预告净利润变动幅度下限（%） |
| p_change_max | float | 预告净利润变动幅度上限（%） |
| net_profit_min | float | 预告净利润下限（万元） |
| net_profit_max | float | 预告净利润上限（万元） |
| last_parent_net | float | 上年同期归属母公司净利润 |
| first_ann_date | str | 首次公告日 |
| summary | str | 业绩预告摘要 |
| change_reason | str | 业绩变动原因 |

#### 调用示例

```python
pro = ts.pro_api()

### 获取单个股票的业绩预告
pro.forecast(ann_date='20190131', fields='ts_code,ann_date,end_date,type,p_change_min,p_change_max,net_profit_min')

### 获取某一季度全部股票数据
df = pro.forecast_vip(period='20181231',fields='ts_code,ann_date,end_date,type,p_change_min,p_change_max,net_profit_min')
```

---

### 个股资金流向

#### 接口信息

- **接口名称**: 个股资金流向
- **接口标识**: moneyflow
- **接口说明**: 获取沪深A股和港股每日资金流向数据，每次请求最多返回300条记录，可通过设置日期多次请求获取更多数据。
- **调用方法**: `pro.moneyflow()`
- **权限要求**: 2000积分

#### 输入参数

| 名称 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| ts_code | str | N | TS代码，支持A股和港股，为空则返回全部 |
| trade_date | str | N | 交易日期（YYYYMMDD） |
| start_date | str | N | 开始日期（YYYYMMDD） |
| end_date | str | N | 结束日期（YYYYMMDD） |

#### 输出参数

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| ts_code | str | TS代码 |
| trade_date | str | 交易日期 |
| buy_sm_vol | int | 小单买入量（手） |
| buy_sm_amount | float | 小单买入金额（万元） |
| sell_sm_vol | int | 小单卖出量（手） |
| sell_sm_amount | float | 小单卖出金额（万元） |
| buy_md_vol | int | 中单买入量（手） |
| buy_md_amount | float | 中单买入金额（万元） |
| sell_md_vol | int | 中单卖出量（手） |
| sell_md_amount | float | 中单卖出金额（万元） |
| buy_lg_vol | int | 大单买入量（手） |
| buy_lg_amount | float | 大单买入金额（万元） |
| sell_lg_vol | int | 大单卖出量（手） |
| sell_lg_amount | float | 大单卖出金额（万元） |
| buy_elg_vol | int | 特大单买入量（手） |
| buy_elg_amount | float | 特大单买入金额（万元） |
| sell_elg_vol | int | 特大单卖出量（手） |
| sell_elg_amount | float | 特大单卖出金额（万元） |
| net_mf_vol | int | 净流入量（手） |
| net_mf_amount | float | 净流入额（万元） |

#### 调用示例

```python
import tushare as ts

pro = ts.pro_api()

### 获取单只股票资金流向
df = pro.moneyflow(ts_code='600000.SH', start_date='20180101', end_date='20180105')

### 获取多只股票资金流向
df = pro.moneyflow(ts_code='600000.SH,000001.SZ', start_date='20180101', end_date='20180105')

### 获取单日全部股票资金流向
df = pro.moneyflow(trade_date='20180104')
```

---

### 主营业务构成 (fina_mainbz)

#### 接口说明

- **接口标识**：`fina_mainbz`
- **功能描述**：获得上市公司主营业务构成，分地区和产品两种方式。
- **权限要求**：用户需要至少2000积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)，单次最大提取100行，总量不限制，可循环获取。
- **提示**：当前接口只能按单只股票获取其历史数据，如果需要获取某一季度全部上市公司数据，请使用`fina_mainbz_vip`接口（参数一致），需积攒5000积分。

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api("YOUR_TOKEN")

### 单只股票
df = pro.fina_mainbz(ts_code='000627.SZ', type='P')

### 某一季度全部股票
df_vip = pro.fina_mainbz_vip(period='20181231', type='P', fields='ts_code,end_date,bz_item,bz_sales')
```

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 描述 |
|---|---|---|---|
| ts_code | str | Y | 股票代码 |
| period | str | N | 报告期(每个季度最后一天的日期,比如20171231表示年报) |
| type | str | N | 类型：P按产品 D按地区 I按行业（请输入大写字母P或者D） |
| start_date | str | N | 报告期开始日期 |
| end_date | str | N | 报告期结束日期 |

#### 输出参数

| 字段名称 | 字段类型 | 描述 |
|---|---|---|
| ts_code | str | TS代码 |
| end_date | str | 报告期 |
| bz_item | str | 主营业务来源 |
| bz_sales | float | 主营业务收入(元) |
| bz_profit | float | 主营业务利润(元) |
| bz_cost | float | 主营业务成本(元) |
| curr_type | str | 货币代码 |
| update_flag | str | 是否更新 |

#### 调用示例

##### 获取单只股票的主营业务构成

```python
pro = ts.pro_api()
df = pro.fina_mainbz(ts_code='000627.SZ', type='P')
print(df)
```

##### 获取某一季度全部股票的主营业务构成 (VIP)

```python
df = pro.fina_mainbz_vip(period='20181231', type='P' ,fields='ts_code,end_date,bz_item,bz_sales')
print(df)
```

##### 数据样例

```
     ts_code  end_date    bz_item       bz_sales       bz_profit bz_cost curr_type
0  000627.SZ  20171231    其他产品      1.847507e+08      None    None       CNY
1  000627.SZ  20171231    其他主营业务  1.847507e+08      None    None       CNY
2  000627.SZ  20171231    聚丙烯        6.629111e+07      None    None       CNY
3  000627.SZ  20171231    原料药产品    2.685909e+08      None    None       CNY
4  000627.SZ  20171231    保险业务      5.288595e+10      None    None       CNY
```

---

### 分红送股 (dividend)

#### 接口描述

分红送股数据

#### 调用方法

```python
pro = ts.pro_api()

df = pro.dividend(ts_code='600848.SH', fields='ts_code,div_proc,stk_div,record_date,ex_date')
```

#### 权限要求

用户需要至少2000积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | TS代码 |
| ann_date | str | N | 公告日 |
| record_date | str | N | 股权登记日期 |
| ex_date | str | N | 除权除息日 |
| imp_ann_date | str | N | 实施公告日 |

**注意：** 以上参数至少有一个不能为空

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | TS代码 |
| end_date | str | Y | 分红年度 |
| ann_date | str | Y | 预案公告日 |
| div_proc | str | Y | 实施进度 |
| stk_div | float | Y | 每股送转 |
| stk_bo_rate | float | Y | 每股送股比例 |
| stk_co_rate | float | Y | 每股转增比例 |
| cash_div | float | Y | 每股分红（税后） |
| cash_div_tax | float | Y | 每股分红（税前） |
| record_date | str | Y | 股权登记日 |
| ex_date | str | Y | 除权除息日 |
| pay_date | str | Y | 派息日 |
| div_listdate | str | Y | 红股上市日 |
| imp_ann_date | str | Y | 实施公告日 |
| base_date | str | N | 基准日 |
| base_share | float | N | 基准股本（万） |

#### 调用示例

```python
pro = ts.pro_api()

df = pro.dividend(ts_code='600848.SH', fields='ts_code,div_proc,stk_div,record_date,ex_date')
```

##### 数据样例

```
             ts_code div_proc  stk_div record_date   ex_date
    0  600848.SH       实施     0.10    19950606  19950607
    1  600848.SH       实施     0.10    19970707  19970708
    2  600848.SH       实施     0.15    19960701  19960702
    3  600848.SH       实施     0.10    19980706  19980707
    4  600848.SH       预案     0.00        None      None
    5  600848.SH       实施     0.00    20180522  20180523
```

---

### 利润表 (income)

#### 接口描述
获取上市公司财务利润表数据。

#### 接口标识
`income`

#### 调用方法
```python
import tushare as ts

pro = ts.pro_api('YOUR_TOKEN')
df = pro.income(ts_code='600000.SH', start_date='20180101', end_date='20180730', fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,basic_eps,diluted_eps')
```

#### 权限要求
用户需要至少2000积分才可以调取。

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 股票代码 |
| ann_date | str | N | 公告日期（YYYYMMDD格式，下同） |
| f_ann_date | str | N | 实际公告日期 |
| start_date | str | N | 公告日开始日期 |
| end_date | str | N | 公告日结束日期 |
| period | str | N | 报告期(每个季度最后一天的日期，比如20171231表示年报，20170630半年报，20170930三季报) |
| report_type | str | N | 报告类型，参考文档最下方说明 |
| comp_type | str | N | 公司类型（1一般工商业2银行3保险4证券） |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | TS代码 |
| ann_date | str | Y | 公告日期 |
| f_ann_date | str | Y | 实际公告日期 |
| end_date | str | Y | 报告期 |
| report_type | str | Y | 报告类型 见底部表 |
| comp_type | str | Y | 公司类型(1一般工商业2银行3保险4证券) |
| basic_eps | float | Y | 基本每股收益 |
| diluted_eps | float | Y | 稀释每股收益 |
| total_revenue | float | Y | 营业总收入 |
| revenue | float | Y | 营业收入 |
| n_income | float | Y | 净利润(含少数股东损益) |
| n_income_attr_p | float | Y | 净利润(不含少数股东损益) |
| total_profit | float | Y | 利润总额 |
| income_tax | float | Y | 所得税费用 |
| operate_profit | float | Y | 营业利润 |
| non_oper_income | float | Y | 加:营业外收入 |
| non_oper_exp | float | Y | 减:营业外支出 |
| total_opcost | float | N | 营业总成本（二） |
| assets_impair_loss | float | Y | 减:资产减值损失 |
| ebit | float | Y | 息税前利润 |
| ebitda | float | Y | 息税折旧摊销前利润 |
| update_flag | str | Y | 更新标识 |
| int_income | float | Y | 利息收入 |
| prem_earned | float | Y | 已赚保费 |
| comm_income | float | Y | 手续费及佣金收入 |
| n_commis_income | float | Y | 手续费及佣金净收入 |
| n_oth_income | float | Y | 其他经营净收益 |
| n_oth_b_income | float | Y | 加:其他业务净收益 |
| prem_income | float | Y | 保险业务收入 |
| out_prem | float | Y | 减:分出保费 |
| une_prem_reser | float | Y | 提取未到期责任准备金 |
| reins_income | float | Y | 其中:分保费收入 |
| n_sec_tb_income | float | Y | 代理买卖证券业务净收入 |
| n_sec_uw_income | float | Y | 证券承销业务净收入 |
| n_asset_mg_income | float | Y | 受托客户资产管理业务净收入 |
| oth_b_income | float | Y | 其他业务收入 |
| fv_value_chg_gain | float | Y | 加:公允价值变动净收益 |
| invest_income | float | Y | 加:投资净收益 |
| ass_invest_income | float | Y | 其中:对联营企业和合营企业的投资收益 |
| forex_gain | float | Y | 加:汇兑净收益 |
| total_cogs | float | Y | 营业总成本 |
| oper_cost | float | Y | 减:营业成本 |
| int_exp | float | Y | 减:利息支出 |
| comm_exp | float | Y | 减:手续费及佣金支出 |
| biz_tax_surchg | float | Y | 减:营业税金及附加 |
| sell_exp | float | Y | 减:销售费用 |
| admin_exp | float | Y | 减:管理费用 |
| fin_exp | float | Y | 减:财务费用 |
| prem_refund | float | Y | 退保金 |
| compens_payout | float | Y | 赔付总支出 |
| reser_insur_liab | float | Y | 提取保险责任准备金 |
| div_payt | float | Y | 保户红利支出 |
| reins_exp | float | Y | 分保费用 |
| oper_exp | float | Y | 营业支出 |
| compens_payout_refu | float | Y | 减:摊回赔付支出 |
| insur_reser_refu | float | Y | 减:摊回保险责任准备金 |
| reins_cost_refund | float | Y | 减:摊回分保费用 |
| other_bus_cost | float | Y | 其他业务成本 |
| nca_disploss | float | Y | 其中:减:非流动资产处置净损失 |
| minority_gain | float | Y | 少数股东损益 |
| oth_compr_income | float | Y | 其他综合收益 |
| t_compr_income | float | Y | 综合收益总额 |
| compr_inc_attr_p | float | Y | 归属于母公司(或股东)的综合收益总额 |
| compr_inc_attr_m_s | float | Y | 归属于少数股东的综合收益总额 |
| insurance_exp | float | Y | 保险业务支出 |
| undist_profit | float | Y | 年初未分配利润 |
| distable_profit | float | Y | 可分配利润 |
| rd_exp | float | Y | 研发费用 |
| fin_exp_int_exp | float | Y | 财务费用:利息费用 |
| fin_exp_int_inc | float | Y | 财务费用:利息收入 |
| transfer_surplus_rese | float | Y | 盈余公积转入 |
| transfer_housing_imprest | float | Y | 住房周转金转入 |
| transfer_oth | float | Y | 其他转入 |
| adj_lossgain | float | Y | 调整以前年度损益 |
| withdra_legal_surplus | float | Y | 提取法定盈余公积 |
| withdra_legal_pubfund | float | Y | 提取法定公益金 |
| withdra_biz_devfund | float | Y | 提取企业发展基金 |
| withdra_rese_fund | float | Y | 提取储备基金 |
| withdra_oth_ersu | float | Y | 提取任意盈余公积金 |
| workers_welfare | float | Y | 职工奖金福利 |
| distr_profit_shrhder | float | Y | 可供股东分配的利润 |
| prfshare_payable_dvd | float | Y | 应付优先股股利 |
| comshare_payable_dvd | float | Y | 应付普通股股利 |
| capit_comstock_div | float | Y | 转作股本的普通股股利 |
| net_after_nr_lp_correct | float | N | 扣除非经常性损益后的净利润（更正前） |
| credit_impa_loss | float | N | 信用减值损失 |
| net_expo_hedging_benefits | float | N | 净敞口套期收益 |
| oth_impair_loss_assets | float | N | 其他资产减值损失 |
| amodcost_fin_assets | float | N | 以摊余成本计量的金融资产终止确认收益 |
| oth_income | float | N | 其他收益 |
| asset_disp_income | float | N | 资产处置收益 |
| continued_net_profit | float | N | 持续经营净利润 |
| end_net_profit | float | N | 终止经营净利润 |

#### 调用示例

##### 获取单只股票的利润表数据
```python
pro = ts.pro_api()
df = pro.income(ts_code='600000.SH', start_date='20180101', end_date='20180730', fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,basic_eps,diluted_eps')
```

##### 获取某一季度全部股票数据
```python
df = pro.income_vip(period='20181231',fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,basic_eps,diluted_eps')
```

---

### 现金流量表 (cashflow)

#### 接口说明

获取上市公司现金流量表。

#### 调用方法

```python
pro.cashflow(ts_code=\'600000.SH\', start_date=\'20180101\', end_date=\'20180730\')
```

#### 权限要求

用户需要至少2000积分才可以调取。

提示：当前接口只能按单只股票获取其历史数据，如果需要获取某一季度全部上市公司数据，请使用cashflow_vip接口（参数一致），需积攒5000积分。

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 股票代码 |
| ann_date | str | N | 公告日期（YYYYMMDD格式，下同） |
| f_ann_date | str | N | 实际公告日期 |
| start_date | str | N | 公告日开始日期 |
| end_date | str | N | 公告日结束日期 |
| period | str | N | 报告期(每个季度最后一天的日期，比如20171231表示年报，20170630半年报，20170930三季报) |
| report_type | str | N | 报告类型：见下方详细说明 |
| comp_type | str | N | 公司类型：1一般工商业 2银行 3保险 4证券 |
| is_calc | int | N | 是否计算报表 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | TS股票代码 |
| ann_date | str | Y | 公告日期 |
| f_ann_date | str | Y | 实际公告日期 |
| end_date | str | Y | 报告期 |
| comp_type | str | Y | 公司类型(1一般工商业2银行3保险4证券) |
| report_type | str | Y | 报表类型 |
| end_type | str | Y | 报告期类型 |
| net_profit | float | Y | 净利润 |
| finan_exp | float | Y | 财务费用 |
| c_fr_sale_sg | float | Y | 销售商品、提供劳务收到的现金 |
| recp_tax_rends | float | Y | 收到的税费返还 |
| n_depos_incr_fi | float | Y | 客户存款和同业存放款项净增加额 |
| n_incr_loans_cb | float | Y | 向中央银行借款净增加额 |
| n_inc_borr_oth_fi | float | Y | 向其他金融机构拆入资金净增加额 |
| prem_fr_orig_contr | float | Y | 收到原保险合同保费取得的现金 |
| n_incr_insured_dep | float | Y | 保户储金净增加额 |
| n_reinsur_prem | float | Y | 收到再保业务现金净额 |
| n_incr_disp_tfa | float | Y | 处置交易性金融资产净增加额 |
| ifc_cash_incr | float | Y | 收取利息和手续费净增加额 |
| n_incr_disp_faas | float | Y | 处置可供出售金融资产净增加额 |
| n_incr_loans_oth_bank | float | Y | 拆入资金净增加额 |
| n_cap_incr_repur | float | Y | 回购业务资金净增加额 |
| c_fr_oth_operate_a | float | Y | 收到其他与经营活动有关的现金 |
| c_inf_fr_operate_a | float | Y | 经营活动现金流入小计 |
| c_paid_goods_s | float | Y | 购买商品、接受劳务支付的现金 |
| c_paid_to_for_empl | float | Y | 支付给职工以及为职工支付的现金 |
| c_paid_for_taxes | float | Y | 支付的各项税费 |
| n_incr_clt_loan_adv | float | Y | 客户贷款及垫款净增加额 |
| n_incr_dep_cbob | float | Y | 存放央行和同业款项净增加额 |
| c_pay_claims_orig_inco | float | Y | 支付原保险合同赔付款项的现金 |
| pay_handling_chrg | float | Y | 支付手续费的现金 |
| pay_comm_insur_plcy | float | Y | 支付保单红利的现金 |
| oth_cash_pay_oper_act | float | Y | 支付其他与经营活动有关的现金 |
| st_cash_out_act | float | Y | 经营活动现金流出小计 |
| n_cashflow_act | float | Y | 经营活动产生的现金流量净额 |
| oth_recp_ral_inv_act | float | Y | 收到其他与投资活动有关的现金 |
| c_disp_withdrwl_invest | float | Y | 收回投资收到的现金 |
| c_recp_return_invest | float | Y | 取得投资收益收到的现金 |
| n_recp_disp_fiolta | float | Y | 处置固定资产、无形资产和其他长期资产收回的现金净额 |
| n_recp_disp_sobu | float | Y | 处置子公司及其他营业单位收到的现金净额 |
| stot_inflows_inv_act | float | Y | 投资活动现金流入小计 |
| c_pay_acq_const_fiolta | float | Y | 购建固定资产、无形资产和其他长期资产支付的现金 |
| c_paid_invest | float | Y | 投资支付的现金 |
| n_disp_subs_oth_biz | float | Y | 取得子公司及其他营业单位支付的现金净额 |
| oth_pay_ral_inv_act | float | Y | 支付其他与投资活动有关的现金 |
| n_incr_pledge_loan | float | Y | 质押贷款净增加额 |
| stot_out_inv_act | float | Y | 投资活动现金流出小计 |
| n_cashflow_inv_act | float | Y | 投资活动产生的现金流量净额 |
| c_recp_borrow | float | Y | 取得借款收到的现金 |
| proc_issue_bonds | float | Y | 发行债券收到的现金 |
| oth_cash_recp_ral_fnc_act | float | Y | 收到其他与筹资活动有关的现金 |
| stot_cash_in_fnc_act | float | Y | 筹资活动现金流入小计 |
| free_cashflow | float | Y | 企业自由现金流量 |
| c_prepay_amt_borr | float | Y | 偿还债务支付的现金 |
| c_pay_dist_dpcp_int_exp | float | Y | 分配股利、利润或偿付利息支付的现金 |
| incl_dvd_profit_paid_sc_ms | float | Y | 其中:子公司支付给少数股东的股利、利润 |
| oth_cashpay_ral_fnc_act | float | Y | 支付其他与筹资活动有关的现金 |
| stot_cashout_fnc_act | float | Y | 筹资活动现金流出小计 |
| n_cash_flows_fnc_act | float | Y | 筹资活动产生的现金流量净额 |
| eff_fx_flu_cash | float | Y | 汇率变动对现金的影响 |
| n_incr_cash_cash_equ | float | Y | 现金及现金等价物净增加额 |
| c_cash_equ_beg_period | float | Y | 期初现金及现金等价物余额 |
| c_cash_equ_end_period | float | Y | 期末现金及现金等价物余额 |
| c_recp_cap_contrib | float | Y | 吸收投资收到的现金 |
| incl_cash_rec_saims | float | Y | 其中:子公司吸收少数股东投资收到的现金 |
| uncon_invest_loss | float | Y | 未确认投资损失 |
| prov_depr_assets | float | Y | 加:资产减值准备 |
| depr_fa_coga_dpba | float | Y | 固定资产折旧、油气资产折耗、生产性生物资产折旧 |
| amort_intang_assets | float | Y | 无形资产摊销 |
| lt_amort_deferred_exp | float | Y | 长期待摊费用摊销 |
| decr_deferred_exp | float | Y | 待摊费用减少 |
| incr_acc_exp | float | Y | 预提费用增加 |
| loss_disp_fiolta | float | Y | 处置固定、无形资产和其他长期资产的损失 |
| loss_scr_fa | float | Y | 固定资产报废损失 |
| loss_fv_chg | float | Y | 公允价值变动损失 |
| invest_loss | float | Y | 投资损失 |
| decr_def_inc_tax_assets | float | Y | 递延所得税资产减少 |
| incr_def_inc_tax_liab | float | Y | 递延所得税负债增加 |
| decr_inventories | float | Y | 存货的减少 |
| decr_oper_payable | float | Y | 经营性应收项目的减少 |
| incr_oper_payable | float | Y | 经营性应付项目的增加 |
| others | float | Y | 其他 |
| im_net_cashflow_oper_act | float | Y | 经营活动产生的现金流量净额(间接法) |
| conv_debt_into_cap | float | Y | 债务转为资本 |
| conv_copbonds_due_within_1y | float | Y | 一年内到期的可转换公司债券 |
| fa_fnc_leases | float | Y | 融资租入固定资产 |
| im_n_incr_cash_equ | float | Y | 现金及现金等价物净增加额(间接法) |
| net_dism_capital_add | float | Y | 拆出资金净增加额 |
| net_cash_rece_sec | float | Y | 代理买卖证券收到的现金净额(元) |
| credit_impa_loss | float | Y | 信用减值损失 |
| use_right_asset_dep | float | Y | 使用权资产折旧 |
| oth_loss_asset | float | Y | 其他资产减值损失 |
| end_bal_cash | float | Y | 现金的期末余额 |
| beg_bal_cash | float | Y | 减:现金的期初余额 |
| end_bal_cash_equ | float | Y | 加:现金等价物的期末余额 |
| beg_bal_cash_equ | float | Y | 减:现金等价物的期初余额 |
| update_flag | str | Y | 更新标志(1最新） |

#### 调用示例

##### 获取单只股票的现金流量表

```python
import tushare as ts

pro = ts.pro_api()

df = pro.cashflow(ts_code=\'600000.SH\', start_date=\'20180101\', end_date=\'20180730\')
```

##### 获取某一季度全部股票数据

```python
df2 = pro.cashflow_vip(period=\'20181231\',fields=\'\')
```

##### 数据样例

```
     ts_code  ann_date f_ann_date  end_date comp_type report_type    net_profit finan_exp  \
0  600000.SH  20180428   20180428  20180331         2           1           NaN      None   
1  600000.SH  20180428   20180428  20171231         2           1  5.500200e+10      None   
2  600000.SH  20180428   20180428  20171231         2           1  5.500200e+10      None
```

#### 主要报表类型说明

| 代码 | 类型 | 说明 |
| --- | --- | --- |
| 1 | 合并报表 | 上市公司最新报表（默认） |
| 2 | 单季合并 | 单一季度的合并报表 |
| 3 | 调整单季合并表 | 调整后的单季合并报表（如果有） |
| 4 | 调整合并报表 | 本年度公布上年同期的财务报表数据，报告期为上年度 |
| 5 | 调整前合并报表 | 数据发生变更，将原数据进行保留，即调整前的原数据 |
| 6 | 母公司报表 | 该公司母公司的财务报表数据 |
| 7 | 母公司单季表 | 母公司的单季度表 |
| 8 | 母公司调整单季表 | 母公司调整后的单季表 |
| 9 | 母公司调整表 | 该公司母公司的本年度公布上年同期的财务报表数据 |
| 10 | 母公司调整前报表 | 母公司调整之前的原始财务报表数据 |
| 11 | 目公司调整前合并报表 | 母公司调整之前合并报表原数据 |
| 12 | 母公司调整前报表 | 母公司报表发生变更前保留的原数据 |

---

### 股票技术面因子（专业版）

#### 接口信息

- **接口名称：** 股票技术面因子（专业版）
- **接口标识：** disclosure_date
- **接口说明：** 获取财报披露计划日期
- **调用方法：** `pro.disclosure_date()`
- **权限要求：** 用户需要至少500积分才可以调取，积分越多权限越大

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 参数描述 |
|---|---|---|---|
| ts_code | str | N | TS股票代码 |
| end_date | str | N | 财报周期（每个季度最后一天的日期，比如20181231表示2018年年报，20180630表示中报) |
| pre_date | str | N | 计划披露日期 |
| ann_date | str | N | 最新披露公告日 |
| actual_date | str | N | 实际披露日期 |

#### 输出参数

| 字段名称 | 字段类型 | 是否默认输出 | 字段描述 |
|---|---|---|---|
| ts_code | str | Y | TS代码 |
| ann_date | str | Y | 最新披露公告日 |
| end_date | str | Y | 报告期 |
| pre_date | str | Y | 预计披露日期 |
| actual_date | str | Y | 实际披露日期 |
| modify_date | str | N | 披露日期修正记录 |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.disclosure_date(end_date='20181231')
```

---

### 财务审计意见 (fina_audit)

#### 接口说明

获取上市公司定期财务审计意见数据。

#### 调用方法

```python
pro.fina_audit(ts_code, ann_date, start_date, end_date, period)
```

#### 权限要求

用户需要至少500积分才可以调取。

#### 输入参数

| 名称       | 类型 | 必选 | 描述                                                       |
| ---------- | ---- | ---- | ---------------------------------------------------------- |
| ts_code    | str  | Y    | 股票代码                                                   |
| ann_date   | str  | N    | 公告日期                                                   |
| start_date | str  | N    | 公告开始日期                                               |
| end_date   | str  | N    | 公告结束日期                                               |
| period     | str  | N    | 报告期(每个季度最后一天的日期,比如20171231表示年报) |

#### 输出参数

| 名称         | 类型  | 描述             |
| ------------ | ----- | ---------------- |
| ts_code      | str   | TS股票代码       |
| ann_date     | str   | 公告日期         |
| end_date     | str   | 报告期           |
| audit_result | str   | 审计结果         |
| audit_fees   | float | 审计总费用（元） |
| audit_agency | str   | 会计事务所       |
| audit_sign   | str   | 签字会计师       |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.fina_audit(ts_code='600000.SH', start_date='20100101', end_date='20180808')
```

---

### 资产负债表 (balancesheet)

#### 接口描述
获取上市公司资产负债表。

#### 调用方法
```python
pro.balancesheet(ts_code='600000.SH', start_date='20180101', end_date='20180730', fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,cap_rese')
```

#### 权限要求
用户需要至少2000积分才可以调取。

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 股票代码 |
| ann_date | str | N | 公告日期(YYYYMMDD格式，下同) |
| start_date | str | N | 公告日开始日期 |
| end_date | str | N | 公告日结束日期 |
| period | str | N | 报告期(每个季度最后一天的日期，比如20171231表示年报，20170630半年报，20170930三季报) |
| report_type | str | N | 报告类型：见下方详细说明 |
| comp_type | str | N | 公司类型：1一般工商业 2银行 3保险 4证券 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | TS股票代码 |
| ann_date | str | Y | 公告日期 |
| f_ann_date | str | Y | 实际公告日期 |
| end_date | str | Y | 报告期 |
| report_type | str | Y | 报表类型 |
| comp_type | str | Y | 公司类型(1一般工商业2银行3保险4证券) |
| end_type | str | Y | 报告期类型 |
| total_share | float | Y | 期末总股本 |
| cap_rese | float | Y | 资本公积金 |
| undistr_porfit | float | Y | 未分配利润 |
| surplus_rese | float | Y | 盈余公积金 |
| special_rese | float | Y | 专项储备 |
| money_cap | float | Y | 货币资金 |
| trad_asset | float | Y | 交易性金融资产 |
| notes_receiv | float | Y | 应收票据 |
| accounts_receiv | float | Y | 应收账款 |
| oth_receiv | float | Y | 其他应收款 |
| prepayment | float | Y | 预付款项 |
| div_receiv | float | Y | 应收股利 |
| int_receiv | float | Y | 应收利息 |
| inventories | float | Y | 存货 |
| amor_exp | float | Y | 待摊费用 |
| nca_within_1y | float | Y | 一年内到期的非流动资产 |
| sett_rsrv | float | Y | 结算备付金 |
| loanto_oth_bank_fi | float | Y | 拆出资金 |
| premium_receiv | float | Y | 应收保费 |
| reinsur_receiv | float | Y | 应收分保账款 |
| reinsur_res_receiv | float | Y | 应收分保合同准备金 |
| pur_resale_fa | float | Y | 买入返售金融资产 |
| oth_cur_assets | float | Y | 其他流动资产 |
| total_cur_assets | float | Y | 流动资产合计 |
| fa_avail_for_sale | float | Y | 可供出售金融资产 |
| htm_invest | float | Y | 持有至到期投资 |
| lt_eqt_invest | float | Y | 长期股权投资 |
| invest_real_estate | float | Y | 投资性房地产 |
| time_deposits | float | Y | 定期存款 |
| oth_assets | float | Y | 其他资产 |
| lt_rec | float | Y | 长期应收款 |
| fix_assets | float | Y | 固定资产 |
| cip | float | Y | 在建工程 |
| const_materials | float | Y | 工程物资 |
| fixed_assets_disp | float | Y | 固定资产清理 |
| produc_bio_assets | float | Y | 生产性生物资产 |
| oil_and_gas_assets | float | Y | 油气资产 |
| intan_assets | float | Y | 无形资产 |
| r_and_d | float | Y | 研发支出 |
| goodwill | float | Y | 商誉 |
| lt_amor_exp | float | Y | 长期待摊费用 |
| defer_tax_assets | float | Y | 递延所得税资产 |
| decr_in_disbur | float | Y | 发放贷款及垫款 |
| oth_nca | float | Y | 其他非流动资产 |
| total_nca | float | Y | 非流动资产合计 |
| cash_reser_cb | float | Y | 现金及存放中央银行款项 |
| depos_in_oth_bfi | float | Y | 存放同业和其它金融机构款项 |
| prec_metals | float | Y | 贵金属 |
| deriv_assets | float | Y | 衍生金融资产 |
| rr_reins_une_prem | float | Y | 应收分保未到期责任准备金 |
| rr_reins_outstd_cla | float | Y | 应收分保未决赔款准备金 |
| rr_reins_lins_liab | float | Y | 应收分保寿险责任准备金 |
| rr_reins_lthins_liab | float | Y | 应收分保长期健康险责任准备金 |
| refund_depos | float | Y | 存出保证金 |
| ph_pledge_loans | float | Y | 保户质押贷款 |
| refund_cap_depos | float | Y | 存出资本保证金 |
| indep_acct_assets | float | Y | 独立账户资产 |
| client_depos | float | Y | 其中：客户资金存款 |
| client_prov | float | Y | 其中：客户备付金 |
| transac_seat_fee | float | Y | 其中:交易席位费 |
| invest_as_receiv | float | Y | 应收款项类投资 |
| total_assets | float | Y | 资产总计 |
| lt_borr | float | Y | 长期借款 |
| st_borr | float | Y | 短期借款 |
| cb_borr | float | Y | 向中央银行借款 |
| depos_ib_deposits | float | Y | 吸收存款及同业存放 |
| loan_oth_bank | float | Y | 拆入资金 |
| trading_fl | float | Y | 交易性金融负债 |
| notes_payable | float | Y | 应付票据 |
| acct_payable | float | Y | 应付账款 |
| adv_receipts | float | Y | 预收款项 |
| sold_for_repur_fa | float | Y | 卖出回购金融资产款 |
| comm_payable | float | Y | 应付手续费及佣金 |
| payroll_payable | float | Y | 应付职工薪酬 |
| taxes_payable | float | Y | 应交税费 |
| int_payable | float | Y | 应付利息 |
| div_payable | float | Y | 应付股利 |
| oth_payable | float | Y | 其他应付款 |
| acc_exp | float | Y | 预提费用 |
| deferred_inc | float | Y | 递延收益 |
| st_bonds_payable | float | Y | 应付短期债券 |
| payable_to_reinsurer | float | Y | 应付分保账款 |
| rsrv_insur_cont | float | Y | 保险合同准备金 |
| acting_trading_sec | float | Y | 代理买卖证券款 |
| acting_uw_sec | float | Y | 代理承销证券款 |
| non_cur_liab_due_1y | float | Y | 一年内到期的非流动负债 |
| oth_cur_liab | float | Y | 其他流动负债 |
| total_cur_liab | float | Y | 流动负债合计 |
| bond_payable | float | Y | 应付债券 |
| lt_payable | float | Y | 长期应付款 |
| specific_payables | float | Y | 专项应付款 |
| estimated_liab | float | Y | 预计负债 |
| defer_tax_liab | float | Y | 递延所得税负债 |
| defer_inc_non_cur_liab | float | Y | 递延收益-非流动负债 |
| oth_ncl | float | Y | 其他非流动负债 |
| total_ncl | float | Y | 非流动负债合计 |
| depos_oth_bfi | float | Y | 同业和其它金融机构存放款项 |
| deriv_liab | float | Y | 衍生金融负债 |
| depos | float | Y | 吸收存款 |
| agency_bus_liab | float | Y | 代理业务负债 |
| oth_liab | float | Y | 其他负债 |
| prem_receiv_adva | float | Y | 预收保费 |
| depos_received | float | Y | 存入保证金 |
| ph_invest | float | Y | 保户储金及投资款 |
| reser_une_prem | float | Y | 未到期责任准备金 |
| reser_outstd_claims | float | Y | 未决赔款准备金 |
| reser_lins_liab | float | Y | 寿险责任准备金 |
| reser_lthins_liab | float | Y | 长期健康险责任准备金 |
| indept_acc_liab | float | Y | 独立账户负债 |
| pledge_borr | float | Y | 其中:质押借款 |
| indem_payable | float | Y | 应付赔付款 |
| policy_div_payable | float | Y | 应付保单红利 |
| total_liab | float | Y | 负债合计 |
| treasury_share | float | Y | 减:库存股 |
| ordin_risk_reser | float | Y | 一般风险准备 |
| forex_differ | float | Y | 外币报表折算差额 |
| invest_loss_unconf | float | Y | 未确认的投资损失 |
| minority_int | float | Y | 少数股东权益 |
| total_hldr_eqy_exc_min_int | float | Y | 股东权益合计(不含少数股东权益) |
| total_hldr_eqy_inc_min_int | float | Y | 股东权益合计(含少数股东权益) |
| total_liab_hldr_eqy | float | Y | 负债及股东权益总计 |
| lt_payroll_payable | float | Y | 长期应付职工薪酬 |
| oth_comp_income | float | Y | 其他综合收益 |
| oth_eqt_tools | float | Y | 其他权益工具 |
| oth_eqt_tools_p_shr | float | Y | 其他权益工具(优先股) |
| lending_funds | float | Y | 融出资金 |
| acc_receivable | float | Y | 应收款项 |
| st_fin_payable | float | Y | 应付短期融资款 |
| payables | float | Y | 应付款项 |
| hfs_assets | float | Y | 持有待售的资产 |
| hfs_sales | float | Y | 持有待售的负债 |
| cost_fin_assets | float | Y | 以摊余成本计量的金融资产 |
| fair_value_fin_assets | float | Y | 以公允价值计量且其变动计入其他综合收益的金融资产 |
| cip_total | float | Y | 在建工程(合计)(元) |
| oth_pay_total | float | Y | 其他应付款(合计)(元) |
| long_pay_total | float | Y | 长期应付款(合计)(元) |
| debt_invest | float | Y | 债权投资(元) |
| oth_debt_invest | float | Y | 其他债权投资(元) |
| oth_eq_invest | float | N | 其他权益工具投资(元) |
| oth_illiq_fin_assets | float | N | 其他非流动金融资产(元) |
| oth_eq_ppbond | float | N | 其他权益工具:永续债(元) |
| receiv_financing | float | N | 应收款项融资 |
| use_right_assets | float | N | 使用权资产 |
| lease_liab | float | N | 租赁负债 |
| contract_assets | float | Y | 合同资产 |
| contract_liab | float | Y | 合同负债 |
| accounts_receiv_bill | float | Y | 应收票据及应收账款 |
| accounts_pay | float | Y | 应付票据及应付账款 |
| oth_rcv_total | float | Y | 其他应收款(合计)（元） |
| fix_assets_total | float | Y | 固定资产(合计)(元) |
| update_flag | str | Y | 更新标识 |

#### 调用示例

##### 获取单只股票历史数据
```python
pro = ts.pro_api()
df = pro.balancesheet(ts_code='600000.SH', start_date='20180101', end_date='20180730', fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,cap_rese')
```

##### 获取某一季度全部股票数据
```python
df2 = pro.balancesheet_vip(period='20181231',fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,cap_rese')
```

##### 数据样例
```
         ts_code  ann_date f_ann_date  end_date report_type comp_type  \
0  600000.SH  20180830   20180830  20180630           1         2   
1  600000.SH  20180428   20180428  20180331           1         2

             cap_rese  
0  8.176000e+10  
1  8.176000e+10
```

#### 主要报表类型说明

| 代码 | 类型 | 说明 |
| ---- | ----- | ---- |
| 1 | 合并报表 | 上市公司最新报表（默认） |
| 2 | 单季合并 | 单一季度的合并报表 |
| 3 | 调整单季合并表 | 调整后的单季合并报表（如果有） |
| 4 | 调整合并报表 | 本年度公布上年同期的财务报表数据，报告期为上年度 |
| 5 | 调整前合并报表 | 数据发生变更，将原数据进行保留，即调整前的原数据 |
| 6 | 母公司报表 | 该公司母公司的财务报表数据 |
| 7 | 母公司单季表 | 母公司的单季度表 |
| 8 | 母公司调整单季表 | 母公司调整后的单季表 |
| 9 | 母公司调整表 | 该公司母公司的本年度公布上年同期的财务报表数据 |
| 10 | 母公司调整前报表 | 母公司调整之前的原始财务报表数据 |
| 11 | 母公司调整前合并报表 | 母公司调整之前合并报表原数据 |
| 12 | 母公司调整前报表 | 母公司报表发生变更前保留的原数据 |

---

## 参考数据

### API文档：前十大股东 (top10_holders)

#### 接口说明

获取上市公司前十大股东数据，包括持有数量和比例等信息。

#### 接口标识

`top10_holders`

#### 调用方法

```python
pro.top10_holders(ts_code='...', ...)
```

或者

```python
pro.query('top10_holders', ts_code='...', ...)
```

#### 权限要求

需要2000积分以上才可以调取本接口，5000积分以上频次会更高。

#### 输入参数

| 名称       | 类型 | 是否必填 | 描述                                         |
| ---------- | ---- | -------- | -------------------------------------------- |
| ts_code    | str  | Y        | TS代码                                       |
| period     | str  | N        | 报告期（YYYYMMDD格式，一般为每个季度最后一天） |
| ann_date   | str  | N        | 公告日期                                     |
| start_date | str  | N        | 报告期开始日期                               |
| end_date   | str  | N        | 报告期结束日期                               |

#### 输出参数

| 名称             | 类型  | 描述             |
| ---------------- | ----- | ---------------- |
| ts_code          | str   | TS股票代码       |
| ann_date         | str   | 公告日期         |
| end_date         | str   | 报告期           |
| holder_name      | str   | 股东名称         |
| hold_amount      | float | 持有数量（股）   |
| hold_ratio       | float | 占总股本比例(%)  |
| hold_float_ratio | float | 占流通股本比例(%)|
| hold_change      | float | 持股变动         |
| holder_type      | str   | 股东类型         |

#### 调用示例

```python
import tushare as ts

### 初始化pro接口
pro = ts.pro_api('YOUR_TOKEN')

### 拉取数据
df = pro.top10_holders(ts_code='600000.SH', start_date='20170101', end_date='20171231')

print(df)
```

或者

```python
df = pro.query('top10_holders', ts_code='600000.SH', start_date='20170101', end_date='20171231')
print(df)
```

##### 数据样例

```
         ts_code  ann_date  end_date                        holder_name   hold_amount  hold_ratio
0  600000.SH  20180428  20171231   富德生命人寿保险股份有限公司-传统  2.779437e+09        9.47
1  600000.SH  20180428  20171231        上海国鑫投资发展有限公司  9.455690e+08        3.22
2  600000.SH  20180428  20171231  富德生命人寿保险股份有限公司-万能H  1.270429e+09        4.33
3  600000.SH  20180428  20171231  富德生命人寿保险股份有限公司-资本金  1.763232e+09        6.01
4  600000.SH  20180428  20171231          上海国际集团有限公司  6.331323e+09       21.57
5  600000.SH  20180428  20171231      中国移动通信集团广东有限公司  5.334893e+09       18.18
6  600000.SH  20180428  20171231        中国证券金融股份有限公司  1.216979e+09        4.15
7  600000.SH  20180428  20171231       梧桐树投资平台有限责任公司  8.861313e+08        3.02
8  600000.SH  20180428  20171231      中央汇金资产管理有限责任公司  3.985214e+08        1.36
9  600000.SH  20180428  20171231       上海上国投资产管理有限公司  1.395571e+09        4.75
```

---

### 大宗交易 (block_trade)

#### 接口说明

获取大宗交易数据，包括交易日、成交价、成交量、成交金额、买方和卖方营业部等信息。

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api("YOUR_TOKEN")
df = pro.block_trade(trade_date="20181227")
```

#### 权限要求

- 积分：300积分可调取，每分钟内限制次数，超过5000积分频次相对较高。
- 限量：单次最大1000条，总量不限制。

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 参数描述 |
|---|---|---|---|
| ts_code | str | N | TS代码（股票代码和日期至少输入一个参数） |
| trade_date | str | N | 交易日期（格式：YYYYMMDD） |
| start_date | str | N | 开始日期（格式：YYYYMMDD） |
| end_date | str | N | 结束日期（格式：YYYYMMDD） |

#### 输出参数

| 字段名称 | 字段类型 | 默认显示 | 字段描述 |
|---|---|---|---|
| ts_code | str | Y | TS代码 |
| trade_date | str | Y | 交易日历 |
| price | float | Y | 成交价 |
| vol | float | Y | 成交量（万股） |
| amount | float | Y | 成交金额 |
| buyer | str | Y | 买方营业部 |
| seller | str | Y | 卖方营业部 |

#### 调用示例

```python
### 获取2018年12月27日的大宗交易数据
df = pro.block_trade(trade_date=\'20181227\')

### 获取指定股票代码在某期间的大宗交易数据
df = pro.block_trade(ts_code=\'600000.SH\', start_date=\'20230101\', end_date=\'20230331\')
```

##### 示例数据

```
      ts_code trade_date  price      vol     amount                                       buyer                                     seller
0   600436.SH   20181227  86.95     9.49     825.16        安信证券股份有限公司成都交子大道证券营业部        安信证券股份有限公司成都交子大道证券营业部
1   603160.SH   20181227  70.00    28.57    2000.00                中国银河证券股份有限公司总部        长江证券股份有限公司武汉巨龙大道证券营业部
2   601318.SH   20181227  55.76  1800.00  100368.00                      恒泰证券股份有限公司总部                                     机构专用
3   601318.SH   20181227  55.76   332.00   18512.32        华鑫证券有限责任公司合肥梅山路证券营业部                                     机构专用
4   601318.SH   20181227  55.76   288.00   16058.88  华泰证券股份有限公司上海徐汇区天钥桥路证券营业部                                     机构专用
```

---

### 月线行情

**接口名称：** 月线行情

**接口标识：** monthly

**接口说明：** 获取A股月线数据

**调用方法：**
```python
pro.monthly()
```

**权限要求：** 用户需要至少2000积分才可以调取

**输入参数：**

| 名称 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| ts_code | str | N | TS代码 （ts_code,trade_date两个参数任选一） |
| trade_date | str | N | 交易日期 （每月最后一个交易日日期，YYYYMMDD格式） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

**输出参数：**

| 名称 | 类型 | 默认显示 | 说明 |
| --- | --- | --- | --- |
| ts_code | str | Y | 股票代码 |
| trade_date | str | Y | 交易日期 |
| close | float | Y | 月收盘价 |
| open | float | Y | 月开盘价 |
| high | float | Y | 月最高价 |
| low | float | Y | 月最低价 |
| pre_close | float | Y | 上月收盘价 |
| change | float | Y | 月涨跌额 |
| pct_chg | float | Y | 月涨跌幅 （未复权，如果是复权请用 [通用行情接口]() ） |
| vol | float | Y | 月成交量 |
| amount | float | Y | 月成交额 |

**调用示例：**

```python
pro = ts.pro_api()
df = pro.monthly(ts_code='000001.SZ', start_date='20180101', end_date='20181101', fields='ts_code,trade_date,open,high,low,close,vol,amount')
```

或者

```python
df = pro.monthly(trade_date='20181031', fields='ts_code,trade_date,open,high,low,close,vol,amount')
```

---

### 股东人数 (stk_holdernumber)

#### 接口说明

获取上市公司股东户数数据，数据不定期公布

#### 调用方法

```python
pro.stk_holdernumber(ts_code='300199.SZ', start_date='20160101', end_date='20181231')
```

#### 权限要求

600积分可调取，基础积分每分钟调取100次，5000积分以上频次相对较高。

#### 输入参数

| 名称 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| ts_code | str | N | TS股票代码 |
| ann_date | str | N | 公告日期 |
| enddate | str | N | 截止日期 |
| start_date | str | N | 公告开始日期 |
| end_date | str | N | 公告结束日期 |

#### 输出参数

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| ts_code | str | TS股票代码 |
| ann_date | str | 公告日期 |
| end_date | str | 截止日期 |
| holder_num | int | 股东户数 |

#### 调用示例

```python
pro = ts.pro_api()

df = pro.stk_holdernumber(ts_code='300199.SZ', start_date='20160101', end_date='20181231')
```

---

### 股东增减持 (stk_holdertrade)

#### 接口说明

获取上市公司增减持数据，了解重要股东近期及历史上的股份增减变化。

#### 调用方法

```python
pro.stk_holdertrade(**kwargs)
```

#### 权限要求

用户需要至少2000积分才可以调取。基础积分有流量控制，积分越多权限越大，5000积分以上无明显限制。

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | TS股票代码 |
| ann_date | str | N | 公告日期 |
| start_date | str | N | 公告开始日期 |
| end_date | str | N | 公告结束日期 |
| trade_type | str | N | 交易类型IN增持DE减持 |
| holder_type | str | N | 股东类型C公司P个人G高管 |

#### 输出参数

| 字段名称 | 字段类型 | 描述 |
| --- | --- | --- |
| ts_code | str | TS代码 |
| ann_date | str | 公告日期 |
| holder_name | str | 股东名称 |
| holder_type | str | 股东类型G高管P个人C公司 |
| in_de | str | 类型IN增持DE减持 |
| change_vol | float | 变动数量 |
| change_ratio | float | 占流通比例（%） |
| after_share | float | 变动后持股 |
| after_ratio | float | 变动后占流通比例（%） |
| avg_price | float | 平均价格 |
| total_share | float | 持股总数 |
| begin_date | str | 增减持开始日期 |
| close_date | str | 增减持结束日期 |

*默认输出字段已在表格中列出*

#### 调用示例

```python
### 获取单日全部增减持数据
df = pro.stk_holdertrade(ann_date='20190426')

### 获取单个股票数据
df = pro.stk_holdertrade(ts_code='002149.SZ')

### 获取当日增持数据
df = pro.stk_holdertrade(ann_date='20190426', trade_type='IN')
```

---

### 股东增减持 (stk_holdertrade)

#### 接口说明

获取上市公司增减持数据，了解重要股东近期及历史上的股份增减变化。

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api("YOUR_TOKEN")

df = pro.stk_holdertrade(ts_code='002149.SZ')
```

#### 权限要求

用户需要至少2000积分才可以调取。基础积分有流量控制，积分越多权限越大，5000积分以上无明显限制。

#### 输入参数

| 名称 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | TS股票代码 |
| ann_date | str | N | 公告日期 |
| start_date | str | N | 公告开始日期 |
| end_date | str | N | 公告结束日期 |
| trade_type | str | N | 交易类型IN增持DE减持 |
| holder_type | str | N | 股东类型C公司P个人G高管 |

#### 输出参数

| 名称 | 类型 | 描述 |
| --- | --- | --- |
| ts_code | str | TS代码 |
| ann_date | str | 公告日期 |
| holder_name | str | 股东名称 |
| holder_type | str | 股东类型G高管P个人C公司 |
| in_de | str | 类型IN增持DE减持 |
| change_vol | float | 变动数量 |
| change_ratio | float | 占流通比例（%） |
| after_share | float | 变动后持股 |
| after_ratio | float | 变动后占流通比例（%） |
| avg_price | float | 平均价格 |
| total_share | float | 持股总数 |
| begin_date | str | 增减持开始日期 |
| close_date | str | 增减持结束日期 |

#### 调用示例

```python
#获取单日全部增减持数据
df = pro.stk_holdertrade(ann_date='20190426')

#获取单个股票数据
df = pro.stk_holdertrade(ts_code='002149.SZ')

#获取当日增持数据
df = pro.stk_holdertrade(ann_date='20190426', trade_type='IN')
```

---

_# 股权质押明细 (pledge_detail)

#### 接口说明

获取股票质押明细数据

#### 调用方法

```python
pro = ts.pro_api()
df = pro.pledge_detail(ts_code='000014.SZ')
```

#### 权限要求

用户需要至少500积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 股票代码 |

#### 输出参数

| 字段 | 类型 | 默认显示 | 说明 |
| --- | --- | --- | --- |
| ts_code | str | Y | TS股票代码 |
| ann_date | str | Y | 公告日期 |
| holder_name | str | Y | 股东名称 |
| pledge_amount | float | Y | 质押数量（万股） |
| start_date | str | Y | 质押开始日期 |
| end_date | str | Y | 质押结束日期 |
| is_release | str | Y | 是否已解押 |
| release_date | str | Y | 解押日期 |
| pledgor | str | Y | 质押方 |
| holding_amount | float | Y | 持股总数（万股） |
| pledged_amount | float | Y | 质押总数（万股） |
| p_total_ratio | float | Y | 本次质押占总股本比例 |
| h_total_ratio | float | Y | 持股总数占总股本比例 |
| is_buyback | str | Y | 是否回购（0否 1是） |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.pledge_detail(ts_code='000014.SZ')
```

_

---

### 股权质押统计数据

#### 接口信息

- **接口名称**: 股权质押统计数据
- **接口标识**: pledge_stat
- **接口说明**: 获取股票质押统计数据
- **调用方法**: `pro.pledge_stat()`
- **权限要求**: 用户需要至少500积分才可以调取

#### 输入参数

| 名称 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| ts_code | str | N | 股票代码 |
| end_date | str | N | 截止日期 |

#### 输出参数

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| ts_code | str | TS代码 (默认输出) |
| end_date | str | 截止日期 (默认输出) |
| pledge_count | int | 质押次数 (默认输出) |
| unrest_pledge | float | 无限售股质押数量（万） (默认输出) |
| rest_pledge | float | 限售股份质押数量（万） (默认输出) |
| total_share | float | 总股本 (默认输出) |
| pledge_ratio | float | 质押比例 (默认输出) |

#### 调用示例

```python
pro = ts.pro_api()

### 或者
### pro = ts.pro_api('your token')

df = pro.pledge_stat(ts_code='000014.SZ')
```

或者

```python
df = pro.query('pledge_stat', ts_code='000014.SZ')
```

---

### 股票回购 (repurchase)

#### 接口描述

获取上市公司回购股票数据。

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api("YOUR_TOKEN")
df = pro.repurchase(ann_date='', start_date='20180101', end_date='20180510')
```

#### 权限要求

用户需要至少600积分才可以调取。

#### 输入参数

| 名称      | 类型 | 必选 | 描述                                                 |
| --------- | ---- | ---- | ---------------------------------------------------- |
| ann_date  | str  | N    | 公告日期（任意填参数，如果都不填，单次默认返回2000条） |
| start_date| str  | N    | 公告开始日期                                         |
| end_date  | str  | N    | 公告结束日期                                         |

**日期格式**: YYYYMMDD, 例如 20181010

#### 输出参数

| 名称       | 类型  | 描述     |
| ---------- | ----- | -------- |
| ts_code    | str   | TS代码   |
| ann_date   | str   | 公告日期 |
| end_date   | str   | 截止日期 |
| proc       | str   | 进度     |
| exp_date   | str   | 过期日期 |
| vol        | float | 回购数量 |
| amount     | float | 回购金额 |
| high_limit | float | 回购最高价 |
| low_limit  | float | 回购最低价 |

#### 调用示例

```python
### 获取2018年1月1日至2018年5月10日之间公告的回购数据
df = pro.repurchase(start_date='20180101', end_date='20180510')

### 获取2018年10月10日公告的回购数据
df = pro.repurchase(ann_date='20181010')
```

---

### 股票账户开户数据（旧）

**接口名称**: 股票账户开户数据（旧）

**接口标识**: stk_account_old

**接口说明**: 获取股票账户开户数据旧版格式数据，数据从2008年1月开始，到2015年5月29，新数据请通过[股票开户数据](https://tushare.pro/document/2?doc_id=164)获取。

**调用方法**

```python
pro = ts.pro_api()
df = pro.stk_account_old(start_date='20140101', end_date='20141231')
```

**权限要求**: 600积分可调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)

**输入参数**

| 名称      | 类型 | 是否必填 | 说明     |
| --------- | ---- | -------- | -------- |
| start_date | str  | N        | 开始日期 |
| end_date  | str  | N        | 结束日期 |

**输出参数**

| 名称      | 类型  | 说明                   |
| --------- | ----- | ---------------------- |
| date      | str   | 统计周期               |
| new_sh    | int   | 本周新增（上海，户）   |
| new_sz    | int   | 本周新增（深圳，户）   |
| active_sh | float | 期末有效账户（上海，万户） |
| active_sz | float | 期末有效账户（深圳，万户） |
| total_sh  | float | 期末账户数（上海，万户）   |
| total_sz  | float | 期末账户数（深圳，万户）   |
| trade_sh  | float | 参与交易账户数（上海，万户） |
| trade_sz  | float | 参与交易账户数（深圳，万户） |

**调用示例**

```python
pro = ts.pro_api()
df = pro.stk_account_old(start_date='20140101', end_date='20141231')
print(df)
```

**数据示例**

```
                date   new_sh  new_sz  active_sh  active_sz  total_sh  total_sz  \
    0   20141229~0102  157871  152943    7187.12    7027.58   9269.40   9131.77   
    1   20141222~1226  279044  268562    7171.13    7011.97   9254.69   9117.34   
    2   20141215~1219  322400  310114    7142.80    6984.49   9228.68   9092.02   
    3   20141208~1212  454796  437448    7109.96    6952.60   9198.74   9062.83   
    4   20141201~1205  306085  292176    7063.30    6907.28   9156.27   9021.43   
    5   20141124~1128  190694  179377    7031.79    6876.74   9127.81   8993.78   
    6   20141117~1121  121884  112181    7012.31    6858.11   9110.03   8976.76   
    7   20141110~1114  125695  117912    7000.00    6846.61   9098.66   8966.15   
    8   20141103~1107  121205  114562    6987.25    6834.46   9086.97   8954.99   
    9   20141027~1031  111282  106319    6974.95    6822.66   9075.72   8944.18   
    10  20141020~1024  106926  103467    6963.70    6811.77   9065.35   8934.12   
    11  20141013~1017  122201  120783    6952.91    6801.17   9055.43   8924.35   
    12  20141008~1010   77637   77278    6940.49    6788.71   9044.10   8912.93   
    13  20140929~1003   48397   47825    6932.63    6780.71   9036.90   8905.59   
    14  20140922~0926  110845  108871    6927.75    6775.81   9032.46   8901.11   
    15  20140915~0919  109261  107790    6916.49    6764.56   9022.26   8890.85   
    16  20140909~0912   89155   88151    6905.34    6753.39   9012.24   8880.75   
    17  20140901~0905   82987   82151    6896.25    6744.24   9004.09   8872.48   
    18  20140825~0829   80279   79732    6887.85    6735.80   8996.52   8864.80   
    19  20140818~0822   87261   86458    6879.80    6727.66   8989.21   8857.35   
    20  20140811~0815   76158   75789    6871.01    6718.81   8981.23   8849.26

        trade_sh  trade_sz  
    0     962.11    770.00  
    1    1262.57   1010.97  
    2    1328.72   1118.42  
    3    1423.32   1209.22  
    4    1291.36   1142.27  
    5    1047.42    979.97  
    6     720.30    696.37  
    7     875.06    810.11  
    8     839.16    803.56  
    9     793.85    783.00  
    10    676.26    715.03  
    11    805.18    845.42  
    12    635.07    707.21  
    13    469.69    527.89  
    14    746.12    806.42  
    15    803.06    847.07  
    16    708.86    766.22  
    17    745.14    798.20  
    18    617.42    696.66  
    19    693.70    776.73  
    20    656.34    728.21
```

---

### 限售股解禁

#### 接口信息

- **接口名称**: 限售股解禁
- **接口标识**: `share_float`
- **接口说明**: 获取限售股解禁
- **调用方法**: `pro.share_float()`
- **权限要求**: 120分可调取，每分钟内限制次数，超过5000积分频次相对较高

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | TS股票代码 |
| ann_date | str | N | 公告日期（日期格式：YYYYMMDD，下同） |
| float_date | str | N | 解禁日期 |
| start_date | str | N | 解禁开始日期 |
| end_date | str | N | 解禁结束日期 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | TS代码 |
| ann_date | str | Y | 公告日期 |
| float_date | str | Y | 解禁日期 |
| float_share | float | Y | 流通股份(股) |
| float_ratio | float | Y | 流通股份占总股本比率 |
| holder_name | str | Y | 股东名称 |
| share_type | str | Y | 股份类型 |

#### 调用示例

```python
pro = ts.pro_api()

df = pro.share_float(ann_date='20181220')
```

---

## 特色数据

### AH股比价

#### 接口标识

stk_ah_comparison

#### 接口说明

AH股比价数据，可根据交易日期获取历史

#### 调用方法

##### HTTP

```json
{
    "api_name": "stk_ah_comparison",
    "token": "your token",
    "params": {},
    "fields": ""
}
```

##### Python

```python
import tushare as ts

pro = ts.pro_api()

df = pro.stk_ah_comparison(trade_date='20250812')
```

#### 权限要求

5000积分起

#### 输入参数

| 名称 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| hk_code | str | N | 港股股票代码（xxxxx.HK) |
| ts_code | str | N | A股票代码(xxxxxx.SH/SZ/BJ) |
| trade_date | str | N | 交易日期（格式：YYYYMMDD下同） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 名称 | 类型 | 描述 |
| --- | --- | --- |
| hk_code | str | 港股股票代码 |
| ts_code | str | A股股票代码 |
| trade_date | str | 交易日期 |
| hk_name | str | 港股股票名称 |
| hk_pct_chg | float | 港股股票涨跌幅 |
| hk_close | float | 港股股票收盘价 |
| name | str | A股股票名称 |
| close | float | A股股票收盘价 |
| pct_chg | float | A股股票涨跌幅 |
| ah_comparison | float | 比价(A/H) |
| ah_premium | float | 溢价(A/H)% |

#### 调用示例

```python
pro = ts.pro_api()

#获取20250812日所有的AH股比价数据
df = pro.stk_ah_comparison(trade_date='20250812')
```

---

### 中央结算系统持股明细

#### 接口信息

- **接口名称**: 中央结算系统持股明细
- **接口标识**: ccass_hold_detail
- **接口说明**: 获取中央结算系统机构席位持股明细，数据覆盖全历史，根据交易所披露时间，当日数据在下一交易日早上9点前完成。
- **调用方法**: 
```python
pro = ts.pro_api()
df = pro.ccass_hold_detail(ts_code='00960.HK', trade_date='20211101', fields='trade_date,ts_code,col_participant_id,col_participant_name,col_shareholding')
```
- **权限要求**: 用户积8000积分可调取，每分钟可以请求300次。

#### 输入参数

| 参数名称 | 类型 | 是否必填 | 描述 |
|---|---|---|---|
| ts_code | str | N | 股票代码 (e.g. 605009.SH) |
| hk_code | str | N | 港交所代码 （e.g. 95009） |
| trade_date | str | N | 交易日期(YYYYMMDD格式，下同) |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 字段名称 | 类型 | 描述 |
|---|---|---|
| trade_date | str | 交易日期 |
| ts_code | str | 股票代号 |
| name | str | 股票名称 |
| col_participant_id | str | 参与者编号 |
| col_participant_name | str | 机构名称 |
| col_shareholding | str | 持股量(股) |
| col_shareholding_percent | str | 占已发行股份/权证/单位百分比(%) |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.ccass_hold_detail(ts_code='00960.HK', trade_date='20211101', fields='trade_date,ts_code,col_participant_id,col_participant_name,col_shareholding')
```

---

### 中央结算系统持股汇总

#### 接口信息

- **接口名称**: 中央结算系统持股汇总
- **接口标识**: ccass_hold
- **接口说明**: 获取中央结算系统持股汇总数据，覆盖全部历史数据，根据交易所披露时间，当日数据在下一交易日早上9点前完成入库。
- **限量**: 单次最大5000条数据，可循环或分页提供全部。
- **权限要求**: 用户120积分可以试用看数据，5000积分每分钟可以请求300次，8000积分以上可以请求500次每分钟。

#### 输入参数

| 参数名称   | 参数类型 | 是否必填 | 参数描述                  |
| ---------- | -------- | -------- | ------------------------- |
| ts_code    | str      | N        | 股票代码 (e.g. 605009.SH) |
| hk_code    | str      | N        | 港交所代码 （e.g. 95009） |
| trade_date | str      | N        | 交易日期(YYYYMMDD格式)    |
| start_date | str      | N        | 开始日期                  |
| end_date   | str      | N        | 结束日期                  |

#### 输出参数

| 字段名称     | 字段类型 | 描述                                                                      |
| -------------- | -------- | ------------------------------------------------------------------------- |
| trade_date   | str      | 交易日期                                                                  |
| ts_code      | str      | 股票代号                                                                  |
| name         | str      | 股票名称                                                                  |
| shareholding | str      | 于中央结算系统的持股量(股) Shareholding in CCASS                            |
| hold_nums    | str      | 参与者数目（个）                                                          |
| hold_ratio   | str      | 占于上交所上市及交易的A股总数的百分比（%）                                |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.ccass_hold(ts_code='00960.HK')
```

---

### 券商每月荐股 (broker_recommend)

#### 接口描述

获取券商月度金股，一般1日~3日内更新当月数据。

#### 调用方法

```python
pro.broker_recommend(**kwargs)
```

#### 权限要求

积分达到6000即可调用，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 描述 |
| :--- | :--- | :--- | :--- |
| month | str | Y | 月度（YYYYMM） |

#### 输出参数

| 字段名称 | 字段类型 | 描述 |
| :--- | :--- | :--- |
| month | str | 月度 |
| broker | str | 券商 |
| ts_code | str | 股票代码 |
| name | str | 股票简称 |

#### 调用示例

```python
### 获取查询月份券商金股
df = pro.broker_recommend(month='202106')
```

---

### 券商盈利预测数据 (report_rc)

#### 接口说明

获取券商（卖方）每天研报的盈利预测数据，数据从2010年开始，每晚19~22点更新当日数据。

#### 调用方法

```python
pro = ts.pro_api()
df = pro.report_rc(ts_code='', report_date='20220429')
```

#### 权限要求

本接口120积分可以试用，每天10次请求，正式权限需8000积分，每天可请求100000次，10000积分以上无总量限制。

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 股票代码 |
| report_date | str | N | 报告日期 |
| start_date | str | N | 报告开始日期 |
| end_date | str | N | 报告结束日期 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 股票代码 |
| name | str | Y | 股票名称 |
| report_date | str | Y | 研报日期 |
| report_title | str | Y | 报告标题 |
| report_type | str | Y | 报告类型 |
| classify | str | Y | 报告分类 |
| org_name | str | Y | 机构名称 |
| author_name | str | Y | 作者 |
| quarter | str | Y | 预测报告期 |
| op_rt | float | Y | 预测营业收入（万元） |
| op_pr | float | Y | 预测营业利润（万元） |
| tp | float | Y | 预测利润总额（万元） |
| np | float | Y | 预测净利润（万元） |
| eps | float | Y | 预测每股收益（元） |
| pe | float | Y | 预测市盈率 |
| rd | float | Y | 预测股息率 |
| roe | float | Y | 预测净资产收益率 |
| ev_ebitda | float | Y | 预测EV/EBITDA |
| rating | str | Y | 卖方评级 |
| max_price | float | Y | 预测最高目标价 |
| min_price | float | Y | 预测最低目标价 |
| imp_dg | str | N | 机构关注度 |
| create_time | datetime | N | TS数据更新时间 |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.report_rc(ts_code='', report_date='20220429')
```

---

### 机构调研表 (stk_surv)

#### 接口说明

获取上市公司机构调研记录数据

#### 调用方法

```python
pro = ts.pro_api()
df = pro.stk_surv(ts_code='002223.SZ', trade_date='20211024', fields='ts_code,name,surv_date,fund_visitors,rece_place,rece_mode,rece_org')
```

#### 权限要求

用户积5000积分可使用

#### 输入参数

| 名称 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 股票代码 |
| trade_date | str | N | 调研日期 |
| start_date | str | N | 调研开始日期 |
| end_date | str | N | 调研结束日期 |

#### 输出参数

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| ts_code | str | 股票代码 |
| name | str | 股票名称 |
| surv_date | str | 调研日期 |
| fund_visitors | str | 机构参与人员 |
| rece_place | str | 接待地点 |
| rece_mode | str | 接待方式 |
| rece_org | str | 接待的公司 |
| org_type | str | 接待公司类型 |
| comp_rece | str | 上市公司接待人员 |
| content | None | 调研内容 |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.stk_surv(ts_code='002223.SZ', trade_date='20211024', fields='ts_code,name,surv_date,fund_visitors,rece_place,rece_mode,rece_org')
```

---

### 每日筹码分布 (cyq_chips)

#### 接口描述

获取A股每日的筹码分布情况，提供各价位占比，数据从2018年开始，每天18~19点之间更新当日数据。

**接口来源:** Tushare社区

**限量:** 单次最大2000条，可以按股票代码和日期循环提取

**积分:** 5000积分每天20000次，10000积分每天200000次，15000积分每天不限总量

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api('YOUR_TOKEN')

### 单次查询
df = pro.cyq_chips(ts_code='600000.SH', start_date='20220101', end_date='20220429')
```

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 参数描述 |
|---|---|---|---|
| ts_code | str | Y | 股票代码 |
| trade_date | str | N | 交易日期（YYYYMMDD） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 字段名称 | 字段类型 | 字段描述 |
|---|---|---|
| ts_code | str | 股票代码 |
| trade_date | str | 交易日期 |
| price | float | 成本价格 |
| percent | float | 价格占比（%） |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.cyq_chips(ts_code='600000.SH', start_date='20220101', end_date='20220429')
```

##### 示例数据

```
         ts_code trade_date price percent
0    600000.SH   20220429  8.96    0.56
1    600000.SH   20220429  8.94    0.40
2    600000.SH   20220429  8.92    0.34
3    600000.SH   20220429  8.90    0.32
4    600000.SH   20220429  8.88    0.27
..         ...        ...   ...     ...
995  600000.SH   20220418  7.26    0.01
996  600000.SH   20220418  7.24    0.01
997  600000.SH   20220418  7.22    0.01
998  600000.SH   20220418  7.20    0.01
999  600000.SH   20220418  7.18    0.01
```

---

### 每日筹码及胜率 (cyq_perf)

#### 接口说明

获取A股每日筹码平均成本和胜率情况，每天18~19点左右更新，数据从2018年开始。

#### 调用方法

```python
pro = ts.pro_api()
df = pro.cyq_perf(ts_code='600000.SH', start_date='20220101', end_date='20220429')
```

#### 权限要求

- 5000积分每天20000次
- 10000积分每天200000次
- 15000积分每天不限总量

#### 输入参数

| 名称 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| ts_code | str | Y | 股票代码 |
| trade_date | str | N | 交易日期（YYYYMMDD） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| ts_code | str | 股票代码 |
| trade_date | str | 交易日期 |
| his_low | float | 历史最低价 |
| his_high | float | 历史最高价 |
| cost_5pct | float | 5分位成本 |
| cost_15pct | float | 15分位成本 |
| cost_50pct | float | 50分位成本 |
| cost_85pct | float | 85分位成本 |
| cost_95pct | float | 95分位成本 |
| weight_avg | float | 加权平均成本 |
| winner_rate | float | 胜率 |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.cyq_perf(ts_code='600000.SH', start_date='20220101', end_date='20220429')
```

**数据样例**

```
      ts_code trade_date his_low his_high cost_5pct cost_95pct weight_avg winner_rate
0   600000.SH   20220429    0.72    12.16      8.18      11.34       9.76        3.52
1   600000.SH   20220428    0.72    12.16      8.24      11.34       9.76        3.08
2   600000.SH   20220427    0.72    12.16      8.30      11.34       9.76        1.71
3   600000.SH   20220426    0.72    12.16      8.34      11.34       9.76        2.02
4   600000.SH   20220425    0.72    12.16      8.36      11.34       9.77        1.44
..        ...        ...     ...      ...       ...        ...        ...         ...
72  600000.SH   20220110    0.72    12.16      8.60      11.36       9.89        7.62
73  600000.SH   20220107    0.72    12.16      8.60      11.36       9.89        7.59
74  600000.SH   20220106    0.72    12.16      8.60      11.36       9.89        3.92
75  600000.SH   20220105    0.72    12.16      8.60      11.36       9.89        5.65
76  600000.SH   20220104    0.72    12.16      8.60      11.36       9.89        3.93
```

---

### 沪深港股通持股明细

#### 接口信息

- **接口名称**: 沪深港股通持股明细
- **接口标识**: hk_hold
- **接口说明**: 获取沪深港股通持股明细，数据来源港交所。
- **调用方法**: `pro.hk_hold()`
- **权限要求**: 用户积120积分可调取试用，2000积分可正常使用，单位分钟有流控，积分越高流量越大，请自行提高积分。

#### 输入参数

| 名称       | 类型 | 是否必填 | 描述                                                         |
| ---------- | ---- | -------- | ------------------------------------------------------------ |
| code       | str  | N        | 交易所代码                                                   |
| ts_code    | str  | N        | TS股票代码                                                   |
| trade_date | str  | N        | 交易日期                                                     |
| start_date | str  | N        | 开始日期                                                     |
| end_date   | str  | N        | 结束日期                                                     |
| exchange   | str  | N        | 类型：SH沪股通（北向）SZ深股通（北向）HK港股通（南向持股） |

#### 输出参数

| 字段名称    | 类型  | 默认显示 | 描述                                       |
| ----------- | ----- | -------- | ------------------------------------------ |
| code        | str   | Y        | 原始代码                                   |
| trade_date  | str   | Y        | 交易日期                                   |
| ts_code     | str   | Y        | TS代码                                     |
| name        | str   | Y        | 股票名称                                   |
| vol         | int   | Y        | 持股数量(股)                               |
| ratio       | float | Y        | 持股占比（%），占已发行股份百分比          |
| exchange    | str   | Y        | 类型：SH沪股通SZ深股通HK港股通             |

#### 调用示例

```python
pro = ts.pro_api()

### 获取单日全部持股
df = pro.hk_hold(trade_date='20190625')

### 获取单日交易所所有持股
df = pro.hk_hold(trade_date='20190625', exchange='SH')
```

---

### 神奇九转指标 (stk_nineturn)

#### 接口说明

神奇九转（又称“九转序列”）是一种基于技术分析的股票趋势反转指标，其思想来源于技术分析大师汤姆·迪马克（Tom DeMark）的TD序列。该指标的核心功能是通过识别股价在上涨或下跌过程中连续9天的特定走势，来判断股价的潜在反转点，从而帮助投资者提高抄底和逃顶的成功率，日线级别配合60min的九转效果更好，数据从20230101开始。

#### 调用方法

```python
pro = ts.pro_api()
df = pro.stk_nineturn(**kwargs)
```

#### 权限要求

达到6000积分可以调用

#### 输入参数

| 名称       | 类型 | 必选 | 描述                                 |
| ---------- | ---- | ---- | ------------------------------------ |
| ts_code    | str  | N    | 股票代码                             |
| trade_date | str  | N    | 交易日期 （格式：YYYY-MM-DD HH:MM:SS) |
| freq       | str  | N    | 频率(日daily)                        |
| start_date | str  | N    | 开始时间                             |
| end_date   | str  | N    | 结束时间                             |

#### 输出参数

| 名称           | 类型     | 描述                     |
| -------------- | -------- | ------------------------ |
| ts_code        | str      | 股票代码                 |
| trade_date     | datetime | 交易日期                 |
| freq           | str      | 频率(日daily)            |
| open           | float    | 开盘价                   |
| high           | float    | 最高价                   |
| low            | float    | 最低价                   |
| close          | float    | 收盘价                   |
| vol            | float    | 成交量                   |
| amount         | float    | 成交额                   |
| up_count       | float    | 上九转计数               |
| down_count     | float    | 下九转计数               |
| nine_up_turn   | str      | 是否上九转)+9表示上九转  |
| nine_down_turn | str      | 是否下九转-9表示下九转   |

#### 调用示例

```python
pro = ts.pro_api()
df=pro.stk_nineturn(ts_code='000001.SZ',freq='daily',fields='ts_code,trade_date,freq,up_count,down_count,nine_up_turn,nine_down_turn')
```

---

### 股票开盘集合竞价数据 (stk_auction_o)

#### 接口描述

股票开盘9:30集合竞价数据，每天盘后更新

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api('YOUR_TOKEN')

df = pro.stk_auction_o(trade_date='20241122')
```

#### 权限要求

开通了股票分钟权限后可获得本接口权限，具体参考[权限说明](https://tushare.pro/document/1?doc_id=108)。

#### 输入参数

| 名称 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 股票代码 |
| trade_date | str | N | 交易日期(YYYYMMDD) |
| start_date | str | N | 开始日期(YYYYMMDD) |
| end_date | str | N | 结束日期(YYYYMMDD) |

#### 输出参数

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| ts_code | str | 股票代码 |
| trade_date | str | 交易日期 |
| close | float | 开盘集合竞价收盘价 |
| open | float | 开盘集合竞价开盘价 |
| high | float | 开盘集合竞价最高价 |
| low | float | 开盘集合竞价最低价 |
| vol | float | 开盘集合竞价成交量 |
| amount | float | 开盘集合竞价成交额 |
| vwap | float | 开盘集合竞价均价 |

#### 调用示例

```python
pro = ts.pro_api()

df=pro.stk_auction_o(trade_date='20241122')
```

---

### 股票技术面因子(专业版） (stk_factor_pro)

#### 接口说明

获取股票每日技术面因子数据，用于跟踪股票当前走势情况，数据由Tushare社区自产，覆盖全历史；输出参数_bfq表示不复权，_qfq表示前复权 _hfq表示后复权，描述中说明了因子的默认传参，如需要特殊参数或者更多因子可以联系管理员评估

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api("YOUR_TOKEN")

df = pro.stk_factor_pro(ts_code='000001.SZ', start_date='20230101', end_date='20230131')
```

#### 权限要求

5000积分每分钟可以请求30次，8000积分以上每分钟500次

#### 输入参数

| 名称 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 股票代码 |
| trade_date | str | N | 交易日期(格式：yyyymmdd，下同) |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 名称 | 类型 | 描述 |
| --- | --- | --- |
| ts_code | str | 股票代码 |
| trade_date | str | 交易日期 |
| open | float | 开盘价 |
| open_hfq | float | 开盘价（后复权） |
| open_qfq | float | 开盘价（前复权） |
| high | float | 最高价 |
| high_hfq | float | 最高价（后复权） |
| high_qfq | float | 最高价（前复权） |
| low | float | 最低价 |
| low_hfq | float | 最低价（后复权） |
| low_qfq | float | 最低价（前复权） |
| close | float | 收盘价 |
| close_hfq | float | 收盘价（后复权） |
| close_qfq | float | 收盘价（前复权） |
| pre_close | float | 昨收价(前复权)--为daily接口的pre_close,以当时复权因子计算值跟前一日close_qfq对不上，可不用 |
| change | float | 涨跌额 |
| pct_chg | float | 涨跌幅 （未复权，如果是复权请用 通用行情接口 ） |
| vol | float | 成交量 （手） |
| amount | float | 成交额 （千元） |
| turnover_rate | float | 换手率（%） |
| turnover_rate_f | float | 换手率（自由流通股） |
| volume_ratio | float | 量比 |
| pe | float | 市盈率（总市值/净利润， 亏损的PE为空） |
| pe_ttm | float | 市盈率（TTM，亏损的PE为空） |
| pb | float | 市净率（总市值/净资产） |
| ps | float | 市销率 |
| ps_ttm | float | 市销率（TTM） |
| dv_ratio | float | 股息率 （%） |
| dv_ttm | float | 股息率（TTM）（%） |
| total_share | float | 总股本 （万股） |
| float_share | float | 流通股本 （万股） |
| free_share | float | 自由流通股本 （万） |
| total_mv | float | 总市值 （万元） |
| circ_mv | float | 流通市值（万元） |
| adj_factor | float | 复权因子 |
| asi_bfq | float | 振动升降指标-OPEN, CLOSE, HIGH, LOW, M1=26, M2=10 |
| asi_hfq | float | 振动升降指标-OPEN, CLOSE, HIGH, LOW, M1=26, M2=10 |
| asi_qfq | float | 振动升降指标-OPEN, CLOSE, HIGH, LOW, M1=26, M2=10 |
| asit_bfq | float | 振动升降指标-OPEN, CLOSE, HIGH, LOW, M1=26, M2=10 |
| asit_hfq | float | 振动升降指标-OPEN, CLOSE, HIGH, LOW, M1=26, M2=10 |
| asit_qfq | float | 振动升降指标-OPEN, CLOSE, HIGH, LOW, M1=26, M2=10 |
| atr_bfq | float | 真实波动N日平均值-CLOSE, HIGH, LOW, N=20 |
| atr_hfq | float | 真实波动N日平均值-CLOSE, HIGH, LOW, N=20 |
| atr_qfq | float | 真实波动N日平均值-CLOSE, HIGH, LOW, N=20 |
| bbi_bfq | float | BBI多空指标-CLOSE, M1=3, M2=6, M3=12, M4=20 |
| bbi_hfq | float | BBI多空指标-CLOSE, M1=3, M2=6, M3=12, M4=21 |
| bbi_qfq | float | BBI多空指标-CLOSE, M1=3, M2=6, M3=12, M4=22 |
| bias1_bfq | float | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24 |
| bias1_hfq | float | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24 |
| bias1_qfq | float | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24 |
| bias2_bfq | float | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24 |
| bias2_hfq | float | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24 |
| bias2_qfq | float | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24 |
| bias3_bfq | float | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24 |
| bias3_hfq | float | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24 |
| bias3_qfq | float | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24 |
| boll_lower_bfq | float | BOLL指标，布林带-CLOSE, N=20, P=2 |
| boll_lower_hfq | float | BOLL指标，布林带-CLOSE, N=20, P=2 |
| boll_lower_qfq | float | BOLL指标，布林带-CLOSE, N=20, P=2 |
| boll_mid_bfq | float | BOLL指标，布林带-CLOSE, N=20, P=2 |
| boll_mid_hfq | float | BOLL指标，布林带-CLOSE, N=20, P=2 |
| boll_mid_qfq | float | BOLL指标，布林带-CLOSE, N=20, P=2 |
| boll_upper_bfq | float | BOLL指标，布林带-CLOSE, N=20, P=2 |
| boll_upper_hfq | float | BOLL指标，布林带-CLOSE, N=20, P=2 |
| boll_upper_qfq | float | BOLL指标，布林带-CLOSE, N=20, P=2 |
| brar_ar_bfq | float | BRAR情绪指标-OPEN, CLOSE, HIGH, LOW, M1=26 |
| brar_ar_hfq | float | BRAR情绪指标-OPEN, CLOSE, HIGH, LOW, M1=26 |
| brar_ar_qfq | float | BRAR情绪指标-OPEN, CLOSE, HIGH, LOW, M1=26 |
| brar_br_bfq | float | BRAR情绪指标-OPEN, CLOSE, HIGH, LOW, M1=26 |
| brar_br_hfq | float | BRAR情绪指标-OPEN, CLOSE, HIGH, LOW, M1=26 |
| brar_br_qfq | float | BRAR情绪指标-OPEN, CLOSE, HIGH, LOW, M1=26 |
| cci_bfq | float | 顺势指标又叫CCI指标-CLOSE, HIGH, LOW, N=14 |
| cci_hfq | float | 顺势指标又叫CCI指标-CLOSE, HIGH, LOW, N=14 |
| cci_qfq | float | 顺势指标又叫CCI指标-CLOSE, HIGH, LOW, N=14 |
| cr_bfq | float | CR价格动量指标-CLOSE, HIGH, LOW, N=20 |
| cr_hfq | float | CR价格动量指标-CLOSE, HIGH, LOW, N=20 |
| cr_qfq | float | CR价格动量指标-CLOSE, HIGH, LOW, N=20 |
| dfma_dif_bfq | float | 平行线差指标-CLOSE, N1=10, N2=50, M=10 |
| dfma_dif_hfq | float | 平行线差指标-CLOSE, N1=10, N2=50, M=10 |
| dfma_dif_qfq | float | 平行线差指标-CLOSE, N1=10, N2=50, M=10 |
| dfma_difma_bfq | float | 平行线差指标-CLOSE, N1=10, N2=50, M=10 |
| dfma_difma_hfq | float | 平行线差指标-CLOSE, N1=10, N2=50, M=10 |
| dfma_difma_qfq | float | 平行线差指标-CLOSE, N1=10, N2=50, M=10 |
| dmi_adx_bfq | float | 动向指标-CLOSE, HIGH, LOW, M1=14, M2=6 |
| dmi_adx_hfq | float | 动向指标-CLOSE, HIGH, LOW, M1=14, M2=6 |
| dmi_adx_qfq | float | 动向指标-CLOSE, HIGH, LOW, M1=14, M2=6 |
| dmi_adxr_bfq | float | 动向指标-CLOSE, HIGH, LOW, M1=14, M2=6 |
| dmi_adxr_hfq | float | 动向指标-CLOSE, HIGH, LOW, M1=14, M2=6 |
| dmi_adxr_qfq | float | 动向指标-CLOSE, HIGH, LOW, M1=14, M2=6 |
| dmi_mdi_bfq | float | 动向指标-CLOSE, HIGH, LOW, M1=14, M2=6 |
| dmi_mdi_hfq | float | 动向指标-CLOSE, HIGH, LOW, M1=14, M2=6 |
| dmi_mdi_qfq | float | 动向指标-CLOSE, HIGH, LOW, M1=14, M2=6 |
| dmi_pdi_bfq | float | 动向指标-CLOSE, HIGH, LOW, M1=14, M2=6 |
| dmi_pdi_hfq | float | 动向指标-CLOSE, HIGH, LOW, M1=14, M2=6 |
| dmi_pdi_qfq | float | 动向指标-CLOSE, HIGH, LOW, M1=14, M2=6 |
| downdays | float | 连跌天数 |
| updays | float | 连涨天数 |
| dpo_bfq | float | 区间震荡线-CLOSE, M1=20, M2=10, M3=6 |
| dpo_hfq | float | 区间震荡线-CLOSE, M1=20, M2=10, M3=6 |
| dpo_qfq | float | 区间震荡线-CLOSE, M1=20, M2=10, M3=6 |
| madpo_bfq | float | 区间震荡线-CLOSE, M1=20, M2=10, M3=6 |
| madpo_hfq | float | 区间震荡线-CLOSE, M1=20, M2=10, M3=6 |
| madpo_qfq | float | 区间震荡线-CLOSE, M1=20, M2=10, M3=6 |
| ema_bfq_10 | float | 指数移动平均-N=10 |
| ema_bfq_20 | float | 指数移动平均-N=20 |
| ema_bfq_250 | float | 指数移动平均-N=250 |
| ema_bfq_30 | float | 指数移动平均-N=30 |
| ema_bfq_5 | float | 指数移动平均-N=5 |
| ema_bfq_60 | float | 指数移动平均-N=60 |
| ema_bfq_90 | float | 指数移动平均-N=90 |
| ema_hfq_10 | float | 指数移动平均-N=10 |
| ema_hfq_20 | float | 指数移动平均-N=20 |
| ema_hfq_250 | float | 指数移动平均-N=250 |
| ema_hfq_30 | float | 指数移动平均-N=30 |
| ema_hfq_5 | float | 指数移动平均-N=5 |
| ema_hfq_60 | float | 指数移动平均-N=60 |
| ema_hfq_90 | float | 指数移动平均-N=90 |
| ema_qfq_10 | float | 指数移动平均-N=10 |
| ema_qfq_20 | float | 指数移动平均-N=20 |
| ema_qfq_250 | float | 指数移动平均-N=250 |
| ema_qfq_30 | float | 指数移动平均-N=30 |
| ema_qfq_5 | float | 指数移动平均-N=5 |
| ema_qfq_60 | float | 指数移动平均-N=60 |
| ema_qfq_90 | float | 指数移动平均-N=90 |
| emv_bfq | float | 简易波动指标-HIGH, LOW, VOL, N=14, M=9 |
| emv_hfq | float | 简易波动指标-HIGH, LOW, VOL, N=14, M=9 |
| emv_qfq | float | 简易波动指标-HIGH, LOW, VOL, N=14, M=9 |
| maemv_bfq | float | 简易波动指标-HIGH, LOW, VOL, N=14, M=9 |
| maemv_hfq | float | 简易波动指标-HIGH, LOW, VOL, N=14, M=9 |
| maemv_qfq | float | 简易波动指标-HIGH, LOW, VOL, N=14, M=9 |
| expma_12_bfq | float | EMA指数平均数指标-CLOSE, N1=12, N2=50 |
| expma_12_hfq | float | EMA指数平均数指标-CLOSE, N1=12, N2=50 |
| expma_12_qfq | float | EMA指数平均数指标-CLOSE, N1=12, N2=50 |
| expma_50_bfq | float | EMA指数平均数指标-CLOSE, N1=12, N2=50 |
| expma_50_hfq | float | EMA指数平均数指标-CLOSE, N1=12, N2=50 |
| expma_50_qfq | float | EMA指数平均数指标-CLOSE, N1=12, N2=50 |
| kdj_bfq | float | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3 |
| kdj_hfq | float | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3 |
| kdj_qfq | float | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3 |
| kdj_d_bfq | float | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3 |
| kdj_d_hfq | float | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3 |
| kdj_d_qfq | float | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3 |
| kdj_k_bfq | float | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3 |
| kdj_k_hfq | float | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3 |
| kdj_k_qfq | float | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3 |
| ktn_down_bfq | float | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10 |
| ktn_down_hfq | float | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10 |
| ktn_down_qfq | float | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10 |
| ktn_mid_bfq | float | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10 |
| ktn_mid_hfq | float | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10 |
| ktn_mid_qfq | float | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10 |
| ktn_upper_bfq | float | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10 |
| ktn_upper_hfq | float | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10 |
| ktn_upper_qfq | float | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10 |
| lowdays | float | LOWRANGE(LOW)表示当前最低价是近多少周期内最低价的最小值 |
| topdays | float | TOPRANGE(HIGH)表示当前最高价是近多少周期内最高价的最大值 |
| ma_bfq_10 | float | 简单移动平均-N=10 |
| ma_bfq_20 | float | 简单移动平均-N=20 |
| ma_bfq_250 | float | 简单移动平均-N=250 |
| ma_bfq_30 | float | 简单移动平均-N=30 |
| ma_bfq_5 | float | 简单移动平均-N=5 |
| ma_bfq_60 | float | 简单移动平均-N=60 |
| ma_bfq_90 | float | 简单移动平均-N=90 |
| ma_hfq_10 | float | 简单移动平均-N=10 |
| ma_hfq_20 | float | 简单移动平均-N=20 |
| ma_hfq_250 | float | 简单移动平均-N=250 |
| ma_hfq_30 | float | 简单移动平均-N=30 |
| ma_hfq_5 | float | 简单移动平均-N=5 |
| ma_hfq_60 | float | 简单移动平均-N=60 |
| ma_hfq_90 | float | 简单移动平均-N=90 |
| ma_qfq_10 | float | 简单移动平均-N=10 |
| ma_qfq_20 | float | 简单移动平均-N=20 |
| ma_qfq_250 | float | 简单移动平均-N=250 |
| ma_qfq_30 | float | 简单移动平均-N=30 |
| ma_qfq_5 | float | 简单移动平均-N=5 |
| ma_qfq_60 | float | 简单移动平均-N=60 |
| ma_qfq_90 | float | 简单移动平均-N=90 |
| macd_bfq | float | MACD指标-CLOSE, SHORT=12, LONG=26, M=9 |
| macd_hfq | float | MACD指标-CLOSE, SHORT=12, LONG=26, M=9 |
| macd_qfq | float | MACD指标-CLOSE, SHORT=12, LONG=26, M=9 |
| macd_dea_bfq | float | MACD指标-CLOSE, SHORT=12, LONG=26, M=9 |
| macd_dea_hfq | float | MACD指标-CLOSE, SHORT=12, LONG=26, M=9 |
| macd_dea_qfq | float | MACD指标-CLOSE, SHORT=12, LONG=26, M=9 |
| macd_dif_bfq | float | MACD指标-CLOSE, SHORT=12, LONG=26, M=9 |
| macd_dif_hfq | float | MACD指标-CLOSE, SHORT=12, LONG=26, M=9 |
| macd_dif_qfq | float | MACD指标-CLOSE, SHORT=12, LONG=26, M=9 |
| mass_bfq | float | 梅斯线-HIGH, LOW, N1=9, N2=25, M=6 |
| mass_hfq | float | 梅斯线-HIGH, LOW, N1=9, N2=25, M=6 |
| mass_qfq | float | 梅斯线-HIGH, LOW, N1=9, N2=25, M=6 |
| ma_mass_bfq | float | 梅斯线-HIGH, LOW, N1=9, N2=25, M=6 |
| ma_mass_hfq | float | 梅斯线-HIGH, LOW, N1=9, N2=25, M=6 |
| ma_mass_qfq | float | 梅斯线-HIGH, LOW, N1=9, N2=25, M=6 |
| mfi_bfq | float | MFI指标是成交量的RSI指标-CLOSE, HIGH, LOW, VOL, N=14 |
| mfi_hfq | float | MFI指标是成交量的RSI指标-CLOSE, HIGH, LOW, VOL, N=14 |
| mfi_qfq | float | MFI指标是成交量的RSI指标-CLOSE, HIGH, LOW, VOL, N=14 |
| mtm_bfq | float | 动量指标-CLOSE, N=12, M=6 |
| mtm_hfq | float | 动量指标-CLOSE, N=12, M=6 |
| mtm_qfq | float | 动量指标-CLOSE, N=12, M=6 |
| mtmma_bfq | float | 动量指标-CLOSE, N=12, M=6 |
| mtmma_hfq | float | 动量指标-CLOSE, N=12, M=6 |
| mtmma_qfq | float | 动量指标-CLOSE, N=12, M=6 |
| obv_bfq | float | 能量潮指标-CLOSE, VOL |
| obv_hfq | float | 能量潮指标-CLOSE, VOL |
| obv_qfq | float | 能量潮指标-CLOSE, VOL |
| psy_bfq | float | 投资者对股市涨跌产生心理波动的情绪指标-CLOSE, N=12, M=6 |
| psy_hfq | float | 投资者对股市涨跌产生心理波动的情绪指标-CLOSE, N=12, M=6 |
| psy_qfq | float | 投资者对股市涨跌产生心理波动的情绪指标-CLOSE, N=12, M=6 |
| psyma_bfq | float | 投资者对股市涨跌产生心理波动的情绪指标-CLOSE, N=12, M=6 |
| psyma_hfq | float | 投资者对股市涨跌产生心理波动的情绪指标-CLOSE, N=12, M=6 |
| psyma_qfq | float | 投资者对股市涨跌产生心理波动的情绪指标-CLOSE, N=12, M=6 |
| roc_bfq | float | 变动率指标-CLOSE, N=12, M=6 |
| roc_hfq | float | 变动率指标-CLOSE, N=12, M=6 |
| roc_qfq | float | 变动率指标-CLOSE, N=12, M=6 |
| maroc_bfq | float | 变动率指标-CLOSE, N=12, M=6 |
| maroc_hfq | float | 变动率指标-CLOSE, N=12, M=6 |
| maroc_qfq | float | 变动率指标-CLOSE, N=12, M=6 |
| rsi_bfq_12 | float | RSI指标-CLOSE, N=12 |
| rsi_bfq_24 | float | RSI指标-CLOSE, N=24 |
| rsi_bfq_6 | float | RSI指标-CLOSE, N=6 |
| rsi_hfq_12 | float | RSI指标-CLOSE, N=12 |
| rsi_hfq_24 | float | RSI指标-CLOSE, N=24 |
| rsi_hfq_6 | float | RSI指标-CLOSE, N=6 |
| rsi_qfq_12 | float | RSI指标-CLOSE, N=12 |
| rsi_qfq_24 | float | RSI指标-CLOSE, N=24 |
| rsi_qfq_6 | float | RSI指标-CLOSE, N=6 |
| taq_down_bfq | float | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20 |
| taq_down_hfq | float | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20 |
| taq_down_qfq | float | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20 |
| taq_mid_bfq | float | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20 |
| taq_mid_hfq | float | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20 |
| taq_mid_qfq | float | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20 |
| taq_up_bfq | float | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20 |
| taq_up_hfq | float | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20 |
| taq_up_qfq | float | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20 |
| trix_bfq | float | 三重指数平滑平均线-CLOSE, M1=12, M2=20 |
| trix_hfq | float | 三重指数平滑平均线-CLOSE, M1=12, M2=20 |
| trix_qfq | float | 三重指数平滑平均线-CLOSE, M1=12, M2=20 |
| trma_bfq | float | 三重指数平滑平均线-CLOSE, M1=12, M2=20 |
| trma_hfq | float | 三重指数平滑平均线-CLOSE, M1=12, M2=20 |
| trma_qfq | float | 三重指数平滑平均线-CLOSE, M1=12, M2=20 |
| vr_bfq | float | VR容量比率-CLOSE, VOL, M1=26 |
| vr_hfq | float | VR容量比率-CLOSE, VOL, M1=26 |
| vr_qfq | float | VR容量比率-CLOSE, VOL, M1=26 |
| wr_bfq | float | W&R 威廉指标-CLOSE, HIGH, LOW, N=10, N1=6 |
| wr_hfq | float | W&R 威廉指标-CLOSE, HIGH, LOW, N=10, N1=6 |
| wr_qfq | float | W&R 威廉指标-CLOSE, HIGH, LOW, N=10, N1=6 |
| wr1_bfq | float | W&R 威廉指标-CLOSE, HIGH, LOW, N=10, N1=6 |
| wr1_hfq | float | W&R 威廉指标-CLOSE, HIGH, LOW, N=10, N1=6 |
| wr1_qfq | float | W&R 威廉指标-CLOSE, HIGH, LOW, N=10, N1=6 |
| xsii_td1_bfq | float | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7 |
| xsii_td1_hfq | float | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7 |
| xsii_td1_qfq | float | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7 |
| xsii_td2_bfq | float | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7 |
| xsii_td2_hfq | float | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7 |
| xsii_td2_qfq | float | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7 |
| xsii_td3_bfq | float | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7 |
| xsii_td3_hfq | float | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7 |
| xsii_td3_qfq | float | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7 |
| xsii_td4_bfq | float | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7 |
| xsii_td4_hfq | float | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7 |
| xsii_td4_qfq | float | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7 |

---

### 股票收盘集合竞价数据 (stk_auction_c)

#### 接口描述

股票收盘15:00集合竞价数据，每天盘后更新。

#### 限量

单次请求最大返回10000行数据，可根据日期循环。

#### 权限

开通了股票分钟权限后可获得本接口权限。

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 股票代码 |
| trade_date | str | N | 交易日期(YYYYMMDD) |
| start_date | str | N | 开始日期(YYYYMMDD) |
| end_date | str | N | 结束日期(YYYYMMDD) |

#### 输出参数

| 名称 | 类型 | 描述 |
| --- | --- | --- |
| ts_code | str | 股票代码 |
| trade_date | str | 交易日期 |
| close | float | 收盘集合竞价收盘价 |
| open | float | 收盘集合竞价开盘价 |
| high | float | 收盘集合竞价最高价 |
| low | float | 收盘集合竞价最低价 |
| vol | float | 收盘集合竞价成交量 |
| amount | float | 收盘集合竞价成交额 |
| vwap | float | 收盘集合竞价均价 |

#### 调用示例

```python
import tushare as ts

pro = ts.pro_api()

df = pro.stk_auction_c(trade_date='20241122')
```

---

## 两融及转融通

### 做市借券交易汇总 (slb_len_mm)

#### 接口说明

- **接口名称**：做市借券交易汇总
- **接口标识**：slb_len_mm
- **功能描述**：做市借券交易汇总
- **限量**：单次最大可以提取5000行数据，可循环获取所有历史

#### 调用方法

使用Tushare Pro的Python SDK进行调用。

#### 权限要求

- 2000积分：每分钟请求200次
- 5000积分：每分钟请求500次

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| trade_date | str | N | 交易日期（YYYYMMDD格式，下同） |
| ts_code | str | N | 股票代码 |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 名称 | 类型 | 描述 |
| --- | --- | --- |
| trade_date | str | 交易日期（YYYYMMDD） |
| ts_code | str | 股票代码 |
| name | str | 股票名称 |
| ope_inv | float | 期初余量(万股) |
| lent_qnt | float | 融出数量(万股) |
| cls_inv | float | 期末余量(万股) |
| end_bal | float | 期末余额(万元) |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.slb_len_mm(trade_date='20240620')
```

---

### 前十大股东 (top10_holders)

#### 接口说明

获取上市公司前十大股东数据，包括持有数量和比例等信息。

#### 调用方法

```python
pro = ts.pro_api()
df = pro.top10_holders(ts_code='600000.SH', start_date='20170101', end_date='20171231')
```

或者

```python
df = pro.query('top10_holders', ts_code='600000.SH', start_date='20170101', end_date='20171231')
```

#### 权限要求

需要2000积分以上才能调用此接口，5000积分以上可以获得更高的调用频率。

#### 输入参数

| 参数名称 | 类型 | 是否必填 | 描述 |
|---|---|---|---|
| ts_code | str | Y | TS代码 |
| period | str | N | 报告期（YYYYMMDD格式，一般为每个季度最后一天） |
| ann_date | str | N | 公告日期 |
| start_date | str | N | 报告期开始日期 |
| end_date | str | N | 报告期结束日期 |

#### 输出参数

| 字段名称 | 类型 | 描述 |
|---|---|---|
| ts_code | str | TS股票代码 |
| ann_date | str | 公告日期 |
| end_date | str | 报告期 |
| holder_name | str | 股东名称 |
| hold_amount | float | 持有数量（股） |
| hold_ratio | float | 占总股本比例(%) |
| hold_float_ratio | float | 占流通股本比例(%) |
| hold_change | float | 持股变动 |
| holder_type | str | 股东类型 |

#### 调用示例

```python
import tushare as ts

pro = ts.pro_api('YOUR_TOKEN')

df = pro.top10_holders(ts_code='600000.SH', start_date='20170101', end_date='20171231')

print(df)
```

---

### 融资融券交易明细

#### 接口信息

- **接口名称**：融资融券交易明细
- **接口标识**：margin_detail
- **接口说明**：获取沪深两市每日融资融券明细
- **调用方法**：
  ```python
  pro.margin_detail(trade_date='20180802')
  ```
  或者
  ```python
  pro.query('margin_detail', trade_date='20180802')
  ```
- **权限要求**：2000积分可获得本接口权限，积分越高权限越大

#### 输入参数

| 名称       | 类型 | 是否必填 | 描述                             |
| ---------- | ---- | -------- | -------------------------------- |
| trade_date | str  | N        | 交易日期（格式：YYYYMMDD，下同） |
| ts_code    | str  | N        | TS代码                           |
| start_date | str  | N        | 开始日期                         |
| end_date   | str  | N        | 结束日期                         |

#### 输出参数

| 名称       | 类型  | 描述                         |
| ---------- | ----- | ---------------------------- |
| trade_date | str   | 交易日期                     |
| ts_code    | str   | TS股票代码                   |
| name       | str   | 股票名称 （20190910后有数据） |
| rzye       | float | 融资余额(元)                 |
| rqye       | float | 融券余额(元)                 |
| rzmre      | float | 融资买入额(元)               |
| rqyl       | float | 融券余量（股）               |
| rzche      | float | 融资偿还额(元)               |
| rqchl      | float | 融券偿还量(股)               |
| rqmcl      | float | 融券卖出量(股,份,手)         |
| rzrqye     | float | 融资融券余额(元)             |

#### 调用示例

```python
import tushare as ts

pro = ts.pro_api()

df = pro.margin_detail(trade_date='20180802')

### 或者
df = pro.query('margin_detail', trade_date='20180802')
```

---

### 融资融券标的（盘前更新）

#### 接口标识

`margin_secs`

#### 接口说明

获取沪深京三大交易所融资融券标的（包括ETF），每天盘前更新。

#### 调用方法

```python
pro = ts.pro_api()

#获取2024年4月17日上交所融资融券标的
df = pro.margin_secs(trade_date='20240417', exchange='SSE')
```

#### 权限要求

2000积分可调取，5000积分无总量限制，积分越高权限越大。

#### 输入参数

| 名称       | 类型 | 是否必填 | 说明                                     |
| ---------- | ---- | -------- | ---------------------------------------- |
| ts_code    | str  | N        | 标的代码                                 |
| trade_date | str  | N        | 交易日                                   |
| exchange   | str  | N        | 交易所（SSE上交所 SZSE深交所 BSE北交所） |
| start_date | str  | N        | 开始日期                                 |
| end_date   | str  | N        | 结束日期                                 |

#### 输出参数

| 字段名称    | 类型 | 说明     |
| ----------- | ---- | -------- |
| trade_date  | str  | 交易日期 |
| ts_code     | str  | 标的代码 |
| name        | str  | 标的名称 |
| exchange    | str  | 交易所   |

#### 调用示例

```python
pro = ts.pro_api()

#获取2024年4月17日上交所融资融券标的
df = pro.margin_secs(trade_date='20240417', exchange='SSE')
```

---

### 转融券交易明细(停）

**接口标识**：`slb_sec_detail`

**接口说明**：获取转融券交易明细，本接口从2024年8月16日起停止更新，请使用新接口：slb_sec_detail。

**调用方法**：

```python
import tushare as ts

pro = ts.pro_api("YOUR_TOKEN")
df = pro.slb_sec_detail(trade_date='20240620')
```

**权限要求**：2000积分，每分钟可请求200次；5000积分，每分钟可请求500次。

**输入参数**：

| 参数名称 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | --- | --- |
| trade_date | str | 否 | 交易日期（YYYYMMDD格式） |
| ts_code | str | 否 | 股票代码 |
| start_date | str | 否 | 开始日期（YYYYMMDD格式） |
| end_date | str | 否 | 结束日期（YYYYMMDD格式） |

**输出参数**：

| 字段名称 | 字段类型 | 字段描述 |
| --- | --- | --- |
| trade_date | str | 交易日期（YYYYMMDD） |
| ts_code | str | 股票代码 |
| name | str | 股票名称 |
| tenor | str | 期限(天) |
| fee_rate | float | 融出费率(%) |
| lent_qnt | float | 转融券融出数量(万股) |

**调用示例**：

```python
pro = ts.pro_api()
df = pro.slb_sec_detail(trade_date='20240620')
```

---

### 转融券交易汇总(停)

#### 接口标识

slb_sec

#### 接口说明

转融通转融券交易汇总

#### 调用方法

通过Tushare Pro SDK调用，示例如下：

```python
pro = ts.pro_api()
df = pro.slb_sec(trade_date='20240620')
```

#### 权限要求

- 2000积分每分钟请求200次
- 5000积分500次请求

#### 输入参数

| 名称        | 类型 | 必选 | 描述                      |
|-------------|------|------|---------------------------|
| trade_date  | str  | N    | 交易日期（YYYYMMDD格式） |
| ts_code     | str  | N    | 股票代码                  |
| start_date  | str  | N    | 开始日期                  |
| end_date    | str  | N    | 结束日期                  |

#### 输出参数

| 名称        | 类型  | 描述              |
|-------------|-------|-------------------|
| trade_date  | str   | 交易日期（YYYYMMDD） |
| ts_code     | str   | 股票代码          |
| name        | str   | 股票名称          |
| ope_inv     | float | 期初余量(万股)    |
| lent_qnt    | float | 转融券融出数量(万股)|
| cls_inv     | float | 期末余量(万股)    |
| end_bal     | float | 期末余额(万元)    |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.slb_sec(trade_date='20240620')
```

---

### 转融资交易汇总

#### 接口信息

- **接口名称**: 转融资交易汇总
- **接口标识**: slb_len
- **接口说明**: 获取转融通融资汇总数据
- **权限要求**: 2000积分每分钟请求200次，5000积分500次请求

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api("YOUR_TOKEN")

df = pro.slb_len(start_date='20240601', end_date='20240620')
```

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 参数描述 |
|---|---|---|---|
| trade_date | str | N | 交易日期（YYYYMMDD格式，下同） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 字段名称 | 字段类型 | 字段描述 |
|---|---|---|
| trade_date | str | 交易日期 |
| ob | float | 期初余额(亿元) |
| auc_amount | float | 竞价成交金额(亿元) |
| repo_amount | float | 再借成交金额(亿元) |
| repay_amount | float | 偿还金额(亿元) |
| cb | float | 期末余额(亿元) |

#### 调用示例

```python
pro = ts.pro_api()

df = pro.slb_len(start_date='20240601', end_date='20240620')
```

---

## 资金流向数据

### 个股资金流向 (moneyflow)

#### 接口描述

获取沪深A股票资金流向数据，分析大单小单成交情况，用于判别资金动向，数据开始于2010年。

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api('your token')

#获取单日全部股票数据
df = pro.moneyflow(trade_date='20190315')

#获取单个股票数据
df = pro.moneyflow(ts_code='002149.SZ', start_date='20190115', end_date='20190315')
```

#### 权限要求

用户需要至少2000积分才可以调取，基础积分有流量控制，积分越多权限越大，请自行提高积分。

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 股票代码 （股票和时间参数至少输入一个） |
| trade_date | str | N | 交易日期 |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 名称 | 类型 | 描述 |
| --- | --- | --- |
| ts_code | str | TS代码 |
| trade_date | str | 交易日期 |
| buy_sm_vol | int | 小单买入量（手） |
| buy_sm_amount | float | 小单买入金额（万元） |
| sell_sm_vol | int | 小单卖出量（手） |
| sell_sm_amount | float | 小单卖出金额（万元） |
| buy_md_vol | int | 中单买入量（手） |
| buy_md_amount | float | 中单买入金额（万元） |
| sell_md_vol | int | 中单卖出量（手） |
| sell_md_amount | float | 中单卖出金额（万元） |
| buy_lg_vol | int | 大单买入量（手） |
| buy_lg_amount | float | 大单买入金额（万元） |
| sell_lg_vol | int | 大单卖出量（手） |
| sell_lg_amount | float | 大单卖出金额（万元） |
| buy_elg_vol | int | 特大单买入量（手） |
| buy_elg_amount | float | 特大单买入金额（万元） |
| sell_elg_vol | int | 特大单卖出量（手） |
| sell_elg_amount | float | 特大单卖出金额（万元） |
| net_mf_vol | int | 净流入量（手） |
| net_mf_amount | float | 净流入额（万元） |

---

### 个股资金流向（DC） (moneyflow_dc)

#### 接口说明

- **接口标识：** moneyflow_dc
- **接口名称：** 个股资金流向（DC）
- **功能描述：** 获取东方财富个股资金流向数据，每日盘后更新，数据开始于20230911。
- **限量：** 单次最大获取6000条数据，可根据日期或股票代码循环提取数据。

#### 调用方法

通过Tushare Pro SDK调用，方法为`pro.moneyflow_dc()`。

#### 权限要求

用户需要至少5000积分才可以调取该接口。

#### 输入参数

| 参数名称   | 类型 | 是否必选 | 描述                               |
| ---------- | ---- | -------- | ---------------------------------- |
| ts_code    | str  | N        | 股票代码                           |
| trade_date | str  | N        | 交易日期（YYYYMMDD格式，下同）     |
| start_date | str  | N        | 开始日期                           |
| end_date   | str  | N        | 结束日期                           |

#### 输出参数

| 字段名称             | 类型  | 描述                       |
| -------------------- | ----- | -------------------------- |
| trade_date           | str   | 交易日期                   |
| ts_code              | str   | 股票代码                   |
| name                 | str   | 股票名称                   |
| pct_change           | float | 涨跌幅                     |
| close                | float | 最新价                     |
| net_amount           | float | 今日主力净流入额（万元）   |
| net_amount_rate      | float | 今日主力净流入净占比（%）  |
| buy_elg_amount       | float | 今日超大单净流入额（万元） |
| buy_elg_amount_rate  | float | 今日超大单净流入占比（%）  |
| buy_lg_amount        | float | 今日大单净流入额（万元）   |
| buy_lg_amount_rate   | float | 今日大单净流入占比（%）    |
| buy_md_amount        | float | 今日中单净流入额（万元）   |
| buy_md_amount_rate   | float | 今日中单净流入占比（%）    |
| buy_sm_amount        | float | 今日小单净流入额（万元）   |
| buy_sm_amount_rate   | float | 今日小单净流入占比（%）    |

#### 调用示例

```python
import tushare as ts

### 初始化pro接口
pro = ts.pro_api('YOUR_TOKEN')

### 获取单日全部股票数据
df = pro.moneyflow_dc(trade_date='20241011')
print(df)

### 获取单个股票数据
df = pro.moneyflow_dc(ts_code='002149.SZ', start_date='20240901', end_date='20240913')
print(df)
```

---

### 个股资金流向（THS）

#### 接口信息

- **接口名称:** 个股资金流向（THS）
- **接口标识:** moneyflow_ths
- **接口说明:** 获取同花顺个股资金流向数据，每日盘后更新
- **权限要求:** 用户需要至少5000积分才可以调取

#### 调用方法

通过Tushare Pro SDK调用，方法名为`moneyflow_ths`。

#### 输入参数

| 参数名称   | 类型 | 是否必填 | 说明                               |
| ---------- | ---- | -------- | ---------------------------------- |
| ts_code    | str  | N        | 股票代码                           |
| trade_date | str  | N        | 交易日期（YYYYMMDD格式，下同） |
| start_date | str  | N        | 开始日期                           |
| end_date   | str  | N        | 结束日期                           |

#### 输出参数

| 字段名称           | 类型  | 说明                   |
| ------------------ | ----- | ---------------------- |
| trade_date         | str   | 交易日期               |
| ts_code            | str   | 股票代码               |
| name               | str   | 股票名称               |
| pct_change         | float | 涨跌幅                 |
| latest             | float | 最新价                 |
| net_amount         | float | 资金净流入(万元)       |
| net_d5_amount      | float | 5日主力净额(万元)      |
| buy_lg_amount      | float | 今日大单净流入额(万元) |
| buy_lg_amount_rate | float | 今日大单净流入占比(%)  |
| buy_md_amount      | float | 今日中单净流入额(万元) |
| buy_md_amount_rate | float | 今日中单净流入占比(%)  |
| buy_sm_amount      | float | 今日小单净流入额(万元) |
| buy_sm_amount_rate | float | 今日小单净流入占比(%)  |

#### 调用示例

```python
pro = ts.pro_api()

#获取单日全部股票数据
df = pro.moneyflow_ths(trade_date='20241011')

#获取单个股票数据
df = pro.moneyflow_ths(ts_code='002149.SZ', start_date='20241001', end_date='20241011')
```

---

### 同花顺概念板块资金流向（THS）

#### 接口信息

- **接口名称**：同花顺概念板块资金流向（THS）
- **接口标识**：`moneyflow_cnt_ths`
- **接口说明**：获取同花顺概念板块每日资金流向
- **调用方法**：`pro.moneyflow_cnt_ths()`
- **权限要求**：5000积分可以调取

#### 输入参数

| 名称 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| ts_code | str | N | 代码 |
| trade_date | str | N | 交易日期(格式：YYYYMMDD，下同) |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

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

#### 调用示例

```python
#获取当日同花顺板块资金流向
df = pro.moneyflow_cnt_ths(trade_date='20250320')
```

---

### 大盘资金流向（DC）

#### 接口信息

- **接口名称**：大盘资金流向（DC）
- **接口标识**：moneyflow_mkt_dc
- **接口说明**：获取东方财富大盘资金流向数据，每日盘后更新。
- **调用方法**：

```python
import tushare as ts

pro = ts.pro_api("YOUR_TOKEN")

df = pro.moneyflow_mkt_dc(trade_date='20240930')
```

- **权限要求**：120积分可试用，5000积分可正式调取。

#### 输入参数

| 参数名称 | 类型 | 是否必填 | 描述 |
|---|---|---|---|
| trade_date | str | N | 交易日期(YYYYMMDD格式) |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 字段名称 | 类型 | 描述 |
|---|---|---|
| trade_date | str | 交易日期 |
| close_sh | float | 上证收盘价（点） |
| pct_change_sh | float | 上证涨跌幅(%) |
| close_sz | float | 深证收盘价（点） |
| pct_change_sz | float | 深证涨跌幅(%) |
| net_amount | float | 今日主力净流入 净额（元） |
| net_amount_rate | float | 今日主力净流入净占比% |
| buy_elg_amount | float | 今日超大单净流入 净额（元） |
| buy_elg_amount_rate | float | 今日超大单净流入 净占比% |
| buy_lg_amount | float | 今日大单净流入 净额（元） |
| buy_lg_amount_rate | float | 今日大单净流入 净占比% |
| buy_md_amount | float | 今日中单净流入 净额（元） |
| buy_md_amount_rate | float | 今日中单净流入 净占比% |
| buy_sm_amount | float | 今日小单净流入 净额（元） |
| buy_sm_amount_rate | float | 今日小单净流入 净占比% |

#### 调用示例

```python
### 获取指定日期范围的板块资金流向
df = pro.moneyflow_mkt_dc(start_date='20240901', end_date='20240930')
```

---

### 东财概念及行业板块资金流向（DC）

#### 接口信息

- **接口名称**：东财概念及行业板块资金流向（DC）
- **接口标识**：`moneyflow_ind_dc`
- **接口说明**：获取东方财富板块资金流向，每天盘后更新。
- **限量**：单次最大可调取5000条数据，可以根据日期和代码循环提取全部数据。
- **权限要求**：5000积分可以调取。

#### 输入参数

| 参数名称 | 类型 | 是否必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 代码 |
| trade_date | str | N | 交易日期（YYYYMMDD格式） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |
| content_type | str | N | 资金类型(行业、概念、地域) |

#### 输出参数

| 字段名称 | 类型 | 描述 |
| --- | --- | --- |
| trade_date | str | 交易日期 |
| content_type | str | 数据类型 |
| ts_code | str | DC板块代码（行业、概念、地域） |
| name | str | 板块名称 |
| pct_change | float | 板块涨跌幅（%） |
| close | float | 板块最新指数 |
| net_amount | float | 今日主力净流入 净额（元） |
| net_amount_rate | float | 今日主力净流入净占比% |
| buy_elg_amount | float | 今日超大单净流入 净额（元） |
| buy_elg_amount_rate | float | 今日超大单净流入 净占比% |
| buy_lg_amount | float | 今日大单净流入 净额（元） |
| buy_lg_amount_rate | float | 今日大单净流入 净占比% |
| buy_md_amount | float | 今日中单净流入 净额（元） |
| buy_md_amount_rate | float | 今日中单净流入 净占比% |
| buy_sm_amount | float | 今日小单净流入 净额（元） |
| buy_sm_amount_rate | float | 今日小单净流入 净占比% |
| buy_sm_amount_stock | str | 今日主力净流入最大股 |
| rank | int | 序号 |

#### 调用示例

```python
### 获取当日所有板块资金流向
df = pro.moneyflow_ind_dc(trade_date='20240927', fields='trade_date,name,pct_change, close, net_amount,net_amount_rate,rank')
```

---

### 沪深港通资金流向 (moneyflow_hsgt)

#### 接口说明

获取沪股通、深股通、港股通每日资金流向数据，每次最多返回300条记录，总量不限制。

#### 调用方法

```python
pro = ts.pro_api()
### E.g.
pro.moneyflow_hsgt(start_date='20180125', end_date='20180808')
### Or
pro.query('moneyflow_hsgt', trade_date='20180725')
```

#### 权限要求

2000积分起，5000积分每分钟可提取500次

#### 输入参数

| 参数名称 | 类型 | 是否必填 | 描述 |
|---|---|---|---|
| trade_date | str | N | 交易日期 (二选一) |
| start_date | str | N | 开始日期 (二选一) |
| end_date | str | N | 结束日期 |

#### 输出参数

| 字段名称 | 类型 | 描述 |
|---|---|---|
| trade_date | str | 交易日期 |
| ggt_ss | float | 港股通（上海） |
| ggt_sz | float | 港股通（深圳） |
| hgt | float | 沪股通（百万元） |
| sgt | float | 深股通（百万元） |
| north_money | float | 北向资金（百万元） |
| south_money | float | 南向资金（百万元） |

#### 调用示例

```python
import tushare as ts

pro = ts.pro_api('YOUR_TOKEN')

df = pro.moneyflow_hsgt(start_date='20180125', end_date='20180808')
print(df)
```

##### 示例数据

```
   trade_date  ggt_ss  ggt_sz      hgt      sgt  north_money  south_money
0    20180808  -476.0  -188.0   962.68   799.94      1762.62       -664.0
1    20180807  -261.0   177.0  2140.85  1079.82      3220.67        -84.0
2    20180803   667.0   -32.0  -436.99  1088.07       651.08        635.0
3    20180802 -1651.0  -366.0   874.97  -216.65       658.32      -2017.0
4    20180801 -1443.0  -443.0   544.36   542.79      1087.15      -1886.0
```

---

### 同花顺行业资金流向（THS）

#### 接口信息

- **接口名称：** 同花顺行业资金流向（THS）
- **接口标识：** `moneyflow_ind_ths`
- **接口说明：** 获取同花顺行业资金流向，每日盘后更新。
- **限量：** 单次最大可调取5000条数据，可以根据日期和代码循环提取全部数据。
- **权限要求：** 5000积分可以调取。

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api('YOUR_TOKEN')

### 获取当日所有同花顺行业资金流向
df = pro.moneyflow_ind_ths(trade_date='20240927')
```

#### 输入参数

| 名称       | 类型 | 是否必填 | 描述                           |
| ---------- | ---- | -------- | ------------------------------ |
| ts_code    | str  | N        | 代码                           |
| trade_date | str  | N        | 交易日期(YYYYMMDD格式，下同) |
| start_date | str  | N        | 开始日期                       |
| end_date   | str  | N        | 结束日期                       |

#### 输出参数

| 名称             | 类型  | 描述         |
| ---------------- | ----- | ------------ |
| trade_date       | str   | 交易日期     |
| ts_code          | str   | 板块代码     |
| industry         | str   | 板块名称     |
| lead_stock       | str   | 领涨股票名称 |
| close            | float | 收盘指数     |
| pct_change       | float | 指数涨跌幅   |
| company_num      | int   | 公司数量     |
| pct_change_stock | float | 领涨股涨跌幅 |
| close_price      | float | 领涨股最新价 |
| net_buy_amount   | float | 流入资金(亿元) |
| net_sell_amount  | float | 流出资金(亿元) |
| net_amount       | float | 净额(亿元)   |

#### 调用示例

```python
### 获取当日所有同花顺行业资金流向
df = pro.moneyflow_ind_ths(trade_date='20240927')
```

---

## 打板专题数据

### 上市公司基本信息 (stock_company)

#### 接口说明

获取上市公司基础信息，单次提取4500条，可以根据交易所分批提取。

#### 调用方法

```python
pro.stock_company(exchange='SZSE', fields='ts_code,chairman,manager,secretary,reg_capital,setup_date,province')
```

#### 权限要求

用户需要至少120积分才可以调取。

#### 输入参数

| 参数名称   | 参数类型 | 是否必填 | 参数描述                                 |
| ---------- | -------- | -------- | ---------------------------------------- |
| ts_code    | str      | N        | 股票代码                                 |
| exchange   | str      | N        | 交易所代码 ，SSE上交所 SZSE深交所 BSE北交所 |

#### 输出参数

| 字段名称      | 字段类型 | 是否默认显示 | 字段描述         |
| ------------- | -------- | ------------ | ---------------- |
| ts_code       | str      | Y            | 股票代码         |
| com_name      | str      | Y            | 公司全称         |
| com_id        | str      | Y            | 统一社会信用代码 |
| exchange      | str      | Y            | 交易所代码       |
| chairman      | str      | Y            | 法人代表         |
| manager       | str      | Y            | 总经理           |
| secretary     | str      | Y            | 董秘             |
| reg_capital   | float    | Y            | 注册资本(万元)   |
| setup_date    | str      | Y            | 注册日期         |
| province      | str      | Y            | 所在省份         |
| city          | str      | Y            | 所在城市         |
| introduction  | str      | N            | 公司介绍         |
| website       | str      | Y            | 公司主页         |
| email         | str      | Y            | 电子邮件         |
| office        | str      | N            | 办公室           |
| employees     | int      | Y            | 员工人数         |
| main_business | str      | N            | 主要业务及产品   |
| business_scope| str      | N            | 经营范围         |

#### 调用示例

```python
pro = ts.pro_api()

#或者
#pro = ts.pro_api('your token')

df = pro.stock_company(exchange='SZSE', fields='ts_code,chairman,manager,secretary,reg_capital,setup_date,province')
```

---

### 东方财富App热榜

#### 接口标识

dc_hot

#### 接口说明

获取东方财富App热榜数据，包括A股市场、ETF基金、港股市场、美股市场等等，每日盘中提取4次，收盘后4次，最晚22点提取一次。

#### 调用方法

通过Tushare Pro SDK调用，方法为`pro.dc_hot()`。

#### 权限要求

用户积分8000积分可调取使用。

#### 输入参数

| 名称 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| trade_date | str | N | 交易日期 |
| ts_code | str | N | TS代码 |
| market | str | N | 类型(A股市场、ETF基金、港股市场、美股市场) |
| hot_type | str | N | 热点类型(人气榜、飙升榜) |
| is_new | str | N | 是否最新（默认Y，如果为N则为盘中和盘后阶段采集，具体时间可参考rank_time字段，状态N每小时更新一次，状态Y更新时间为22：30） |

#### 输出参数

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| trade_date | str | 交易日期 |
| data_type | str | 数据类型 |
| ts_code | str | 股票代码 |
| ts_name | str | 股票名称 |
| rank | int | 排行或者热度 |
| pct_change | float | 涨跌幅% |
| current_price | float | 当前价 |
| rank_time | str | 排行榜获取时间 |

#### 调用示例

```python
#获取查询月份券商金股
df = pro.dc_hot(trade_date='20240415', market='A股市场',hot_type='人气榜',  fields='ts_code,ts_name,rank')
```

---

### 东方财富板块成分 (dc_member)

#### 接口描述
获取东方财富板块每日成分数据，可以根据概念板块代码和交易日期，获取历史成分。

**限量**：单次最大获取5000条数据，可以通过日期和代码循环获取。
**注意**：本接口只限个人学习和研究使用，如需商业用途，请自行联系东方财富解决数据采购问题。

#### 调用方法
```python
import tushare as ts

### 初始化pro接口
pro = ts.pro_api('YOUR_TOKEN')

### 调用接口
df = pro.dc_member(trade_date='20250102', ts_code='BK1184.DC')
```

#### 权限要求
用户积累6000积分可调取

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 板块指数代码 |
| con_code | str | N | 成分股票代码 |
| trade_date | str | N | 交易日期（YYYYMMDD格式） |

#### 输出参数

| 名称 | 类型 | 描述 |
| --- | --- | --- |
| trade_date | str | 交易日期 |
| ts_code | str | 概念代码 |
| con_code | str | 成分代码 |
| name | str | 成分股名称 |

#### 调用示例

```python
#获取东方财富2025年1月2日的人形机器人概念板块成分列表
df = pro.dc_member(trade_date='20250102', ts_code='BK1184.DC')
```

---

### 东方财富概念板块

#### 接口标识

dc_index

#### 接口说明

获取东方财富每个交易日的概念板块数据，支持按日期查询。

#### 调用方法

```python
df = pro.dc_index(trade_date='20250103', fields='ts_code,name,turnover_rate,up_num,down_num')
```

#### 权限要求

用户积累6000积分可调取。

#### 输入参数

| 名称 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 指数代码（支持多个代码同时输入，用逗号分隔） |
| name | str | N | 板块名称（例如：人形机器人） |
| trade_date | str | N | 交易日期（YYYYMMDD格式，下同） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 名称 | 类型 | 描述 |
| --- | --- | --- |
| ts_code | str | 概念代码 |
| trade_date | str | 交易日期 |
| name | str | 概念名称 |
| leading | str | 领涨股票名称 |
| leading_code | str | 领涨股票代码 |
| pct_change | float | 涨跌幅 |
| leading_pct | float | 领涨股票涨跌幅 |
| total_mv | float | 总市值（万元） |
| turnover_rate | float | 换手率 |
| up_num | int | 上涨家数 |
| down_num | int | 下降家数 |

#### 调用示例

```python
#获取东方财富2025年1月3日的概念板块列表
df = pro.dc_index(trade_date='20250103', fields='ts_code,name,turnover_rate,up_num,down_num')
```

---

### 东财概念和行业指数行情

#### 接口标识

dc_daily

#### 接口说明

获取东财概念板块、行业指数板块、地域板块行情数据，历史数据开始于2020年。

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api("YOUR_TOKEN")
df = pro.dc_daily(**kwargs)
```

#### 权限要求

用户积累6000积分可调取。

#### 输入参数

| 名称 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| ts_code | str | N | 板块代码（格式：xxxxx.DC) |
| trade_date | str | N | 交易日期(格式：YYYYMMDD下同） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |
| idx_type | str | N | 板块类型： 概念板块、行业板块、地域板块 |

#### 输出参数

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| ts_code | str | 板块代码 |
| trade_date | str | 交易日 |
| close | float | 收盘点位 |
| open | float | 开盘点位 |
| high | float | 最高点位 |
| low | float | 最低点位 |
| change | float | 涨跌点位 |
| pct_change | float | 涨跌幅 |
| vol | float | 成交量(股) |
| amount | float | 成交额(元) |
| swing | float | 振幅 |
| turnover_rate | float | 换手率 |

#### 调用示例

```python
### 获取东方财富2025年5月13日概念板块行情
df = pro.dc_daily(trade_date='20250513')
```

---

### 同花顺App热榜数 (ths_hot)

#### 接口说明

获取同花顺App热榜数据，包括热股、概念板块、ETF、可转债、港美股等等，每日盘中提取4次，收盘后4次，最晚22点提取一次。

**注意：** 本接口只限个人学习和研究使用，如需商业用途，请自行联系同花顺解决数据采购问题。

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api("YOUR_TOKEN")
df = pro.ths_hot(**kwargs)
```

#### 权限要求

用户积分6000积分可调取使用。

#### 输入参数

| 名称 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| trade_date | str | N | 交易日期 |
| ts_code | str | N | TS代码 |
| market | str | N | 热榜类型(热股、ETF、可转债、行业板块、概念板块、期货、港股、热基、美股) |
| is_new | str | N | 是否最新（默认Y，如果为N则为盘中和盘后阶段采集，具体时间可参考rank_time字段，状态N每小时更新一次，状态Y更新时间为22：30） |

#### 输出参数

| 名称 | 类型 | 描述 |
| --- | --- | --- |
| trade_date | str | 交易日期 |
| data_type | str | 数据类型 |
| ts_code | str | 股票代码 |
| ts_name | str | 股票名称 |
| rank | int | 排行 |
| pct_change | float | 涨跌幅% |
| current_price | float | 当前价格 |
| concept | str | 标签 |
| rank_reason | str | 上榜解读 |
| hot | float | 热度值 |
| rank_time | str | 排行榜获取时间 |

#### 调用示例

```python
### 获取查询月份券商金股
df = pro.ths_hot(trade_date='20240315', market='热股', fields='ts_code,ts_name,hot,concept')
```

---

### 接口：同花顺概念板块成分 (ths_member)

#### 接口说明

获取同花顺概念板块成分列表。数据版权归属同花顺，如做商业用途，请主动联系同花顺。

#### 调用方法

```python
pro.ths_member(**kwargs)
```

#### 权限要求

用户积累6000积分可调取，每分钟可调取200次，可按概念板块代码循环提取所有成分。

#### 输入参数

| 名称      | 类型 | 必选 | 描述         |
| --------- | ---- | ---- | ------------ |
| ts_code   | str  | N    | 板块指数代码 |
| con_code  | str  | N    | 股票代码     |

#### 输出参数

| 名称      | 类型  | 默认显示 | 描述           |
| --------- | ----- | -------- | -------------- |
| ts_code   | str   | Y        | 指数代码       |
| con_code  | str   | Y        | 股票代码       |
| con_name  | str   | Y        | 股票名称       |
| weight    | float | N        | 权重(暂无)     |
| in_date   | str   | N        | 纳入日期(暂无) |
| out_date  | str   | N        | 剔除日期(暂无) |
| is_new    | str   | N        | 是否最新Y是N否 |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.ths_member(ts_code='885800.TI')
```

---

### 涨跌停榜单（同花顺）

#### 接口标识

`limit_list_ths`

#### 接口说明

获取同花顺每日涨跌停榜单数据，历史数据从20231101开始提供，增量每天16点左右更新。

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api("YOUR_TOKEN")

df = pro.limit_list_ths(trade_date='20241125', limit_type='涨停池', fields='ts_code,trade_date,tag,status,lu_desc')
```

#### 权限要求

8000积分以上每分钟500次，每天总量不限制。

#### 输入参数

| 名称 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| trade_date | str | N | 交易日期 |
| ts_code | str | N | 股票代码 |
| limit_type | str | N | 涨停池、连扳池、冲刺涨停、炸板池、跌停池，默认：涨停池 |
| market | str | N | HS-沪深主板 GEM-创业板 STAR-科创板 |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 名称 | 类型 | 描述 |
| --- | --- | --- |
| trade_date | str | 交易日期 |
| ts_code | str | 股票代码 |
| name | str | 股票名称 |
| price | float | 收盘价(元) |
| pct_chg | float | 涨跌幅% |
| open_num | int | 打开次数 |
| lu_desc | str | 涨停原因 |
| limit_type | str | 板单类别 |
| tag | str | 涨停标签 |
| status | str | 涨停状态（N连板、一字板） |
| first_lu_time | str | 首次涨停时间 |
| last_lu_time | str | 最后涨停时间 |
| first_ld_time | str | 首次跌停时间 |
| last_ld_time | str | 最后跌停时间 |
| limit_order | float | 封单量(元) |
| limit_amount | float | 封单额(元) |
| turnover_rate | float | 换手率% |
| free_float | float | 实际流通(元) |
| lu_limit_order | float | 最大封单(元) |
| limit_up_suc_rate | float | 近一年涨停封板率 |
| turnover | float | 成交额 |
| rise_rate | float | 涨速 |
| sum_float | float | 总市值（亿元） |
| market_type | str | 股票类型：HS沪深主板、GEM创业板、STAR科创板 |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.limit_list_ths(trade_date='20241125', limit_type='涨停池', fields='ts_code,trade_date,tag,status,lu_desc')
```

---

### 市场游资最全名录 (hm_list)

#### 接口说明

获取游资分类名录信息。

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api('YOUR_TOKEN')

df = pro.hm_list(name='str')
```

#### 权限要求

需要 5000 积分才能调用，积分获取办法请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)。

#### 输入参数

| 名称 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| name | str | N | 游资名称 |

#### 输出参数

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| name | str | 游资名称 |
| desc | str | 说明 |
| orgs | None | 关联机构 |

#### 调用示例

```python
#代码示例
pro = ts.pro_api()
df = pro.hm_list()
```

---

### 开盘竞价成交（当日） (stk_auction)

#### 接口说明

获取当日个股和ETF的集合竞价成交情况，每天9点25~29分之间可以获取当日的集合竞价成交数据。

#### 调用方法

通过Tushare Pro SDK调用，方法为`stk_auction`。

#### 权限要求

本接口是单独开权限的数据，已经开通了股票分钟权限的用户可自动获得本接口权限，单独申请权限请参考权限列表。

#### 输入参数

| 参数名称   | 类型   | 是否必选 | 描述                               |
| ---------- | ------ | -------- | ---------------------------------- |
| ts_code    | str    | N        | 股票代码                           |
| trade_date | str    | N        | 交易日期（YYYYMMDD格式，下同)      |
| start_date | str    | N        | 开始日期                           |
| end_date   | str    | N        | 结束日期                           |

#### 输出参数

| 字段名称      | 类型  | 描述             |
| ------------- | ----- | ---------------- |
| ts_code       | str   | 股票代码         |
| trade_date    | str   | 数据日期         |
| vol           | int   | 成交量（股）     |
| price         | int   | 成交均价（元）   |
| amount        | float | 成交金额（元）   |
| pre_close     | float | 昨收价（元）     |
| turnover_rate | float | 换手率（%）      |
| volume_ratio  | float | 量比             |
| float_share   | float | 流通股本（万股） |

#### 调用示例

```python
#获取2025年2月18日开盘集合竞价成交情况
df = pro.stk_auction(trade_date='20250218',fields='ts_code, trade_date,vol,price,amount,turnover_rate,volume_ratio')
```

---

### 开盘啦榜单数据

**接口名称**: 开盘啦榜单数据

**接口标识**: kpl_list

**接口说明**: 获取开盘啦涨停、跌停、炸板等榜单数据

**调用方法**

```python
pro = ts.pro_api()
df = pro.kpl_list(trade_date='20240927', tag='涨停', fields='ts_code,name,trade_date,tag,theme,status')
```

**权限要求**: 5000积分每分钟可以请求200次每天总量1万次，8000积分以上每分钟500次每天总量不限制

**输入参数**

| 名称 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 股票代码 |
| trade_date | str | N | 交易日期 |
| tag | str | N | 板单类型（涨停/炸板/跌停/自然涨停/竞价，默认为涨停) |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

**输出参数**

| 字段 | 类型 | 描述 |
| --- | --- | --- |
| ts_code | str | 代码 |
| name | str | 名称 |
| trade_date | str | 交易时间 |
| lu_time | str | 涨停时间 |
| ld_time | str | 跌停时间 |
| open_time | str | 开板时间 |
| last_time | str | 最后涨停时间 |
| lu_desc | str | 涨停原因 |
| tag | str | 标签 |
| theme | str | 板块 |
| net_change | float | 主力净额(元) |
| bid_amount | float | 竞价成交额(元) |
| status | str | 状态（N连板） |
| bid_change | float | 竞价净额 |
| bid_turnover | float | 竞价换手% |
| lu_bid_vol | float | 涨停委买额 |
| pct_chg | float | 涨跌幅% |
| bid_pct_chg | float | 竞价涨幅% |
| rt_pct_chg | float | 实时涨幅% |
| limit_order | float | 封单 |
| amount | float | 成交额 |
| turnover_rate | float | 换手率% |
| free_float | float | 实际流通 |
| lu_limit_order | float | 最大封单 |

**调用示例**

```python
pro = ts.pro_api()
df = pro.kpl_list(trade_date='20240927', tag='涨停', fields='ts_code,name,trade_date,tag,theme,status')
```

**数据样例**

```
       ts_code  name      trade_date tag         theme         status
0    000762.SZ  西藏矿业   20240927  涨停       锂矿、盐湖提锂     首板
1    300399.SZ  天利科技   20240927  涨停    互联网金融、金融概念     首板
2    002673.SZ  西部证券   20240927  涨停      证券、控参股基金     首板
3    002050.SZ  三花智控   20240927  涨停  汽车热管理、比亚迪产业链     首板
4    600801.SH  华新水泥   20240927  涨停        水泥、地产链     首板
..         ...   ...        ...  ..           ...    ...
126  600696.SH  岩石股份   20240927  涨停         白酒、酿酒    2连板
127  600606.SH  绿地控股   20240927  涨停       房地产、地产链    2连板
128  000882.SZ  华联股份   20240927  涨停      零售、互联网金融    2连板
129  000069.SZ  华侨城Ａ   20240927  涨停       房地产、地产链    2连板
130  002570.SZ   贝因美   20240927  涨停       多胎概念、乳业     首板
```

---

### 沪深股通成份股 (hs_const)

#### 接口描述

获取沪股通、深股通成分股。

#### 调用方法

```python
pro.hs_const(hs_type='SH')
```

#### 权限要求

需要2000积分才可调用，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)。

#### 输入参数

| 参数名称  | 参数类型 | 是否必填 | 描述 |
| :-------- | :------- | :------- | :--- |
| hs_type   | str      | Y        | 交易类型(SH：沪股通 SZ：深股通) |
| is_new    | str      | N        | 是否最新 1 是 0 否 (默认是) |

#### 输出参数

| 字段名称   | 字段类型 | 默认显示 | 描述 |
| :--------- | :------- | :------- | :--- |
| ts_code    | str      | Y        | TS代码 |
| hs_type    | str      | Y        | 沪深港通类型SH沪SZ深 |
| in_date    | str      | Y        | 纳入日期 |
| out_date   | str      | Y        | 剔除日期 |
| is_new     | str      | Y        | 是否最新 1是 0否 |

#### 调用示例

```python
import tushare as ts

pro = ts.pro_api()

### 获取沪股通成分
df = pro.hs_const(hs_type='SH')

### 获取深股通成分
df = pro.hs_const(hs_type='SZ')
```

---

### 涨停最强板块统计 (limit_cpt_list)

#### 接口说明

获取每天涨停股票最多最强的概念板块，可以分析强势板块的轮动，判断资金动向。

#### 调用方法

```python
pro = ts.pro_api()
df = pro.limit_cpt_list(trade_date='20241127')
```

#### 权限要求

8000积分以上每分钟500次，每天总量不限制。

#### 输入参数

| 名称 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| trade_date | str | N | 交易日期（格式：YYYYMMDD，下同） |
| ts_code | str | N | 板块代码 |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| ts_code | str | 板块代码 |
| name | str | 板块名称 |
| trade_date | str | 交易日期 |
| days | int | 上榜天数 |
| up_stat | str | 连板高度 |
| cons_nums | int | 连板家数 |
| up_nums | int | 涨停家数 |
| pct_chg | float | 涨跌幅% |
| rank | str | 板块热点排名 |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.limit_cpt_list(trade_date='20241127')
```

**数据样例**

```
      ts_code    name      trade_date  days up_stat  cons_nums  up_nums pct_chg  rank
0   885728.TI    人工智能   20241127    18    9天7板         9       27  2.8608     1
1   885420.TI    电子商务   20241127     6    9天7板        11       25  1.8973     2
2   885806.TI    华为概念   20241127    34  18天14板         6       21  2.4648     3
3   885418.TI  文化传媒概念   20241127     2    9天7板         6       18  3.5207     4
4   885976.TI    数字经济   20241127     4    9天7板         6       17  2.8993     5
5   885788.TI    网络直播   20241127     6    9天7板         9       17  2.5367     6
6   886019.TI  AIGC概念   20241127     1    9天7板         5       16  4.3615     7
7   885756.TI    芯片概念   20241127     1    7天7板         7       16  2.4840     8
8   885642.TI    跨境电商   20241127     6    9天7板        10       16  2.1974     9
9   885517.TI   机器人概念   20241127    14    6天6板         7       16  2.1272    10
10  885929.TI    专精特新   20241127     8    7天7板         4       16  2.0335    11
11  885709.TI    虚拟现实   20241127     1    9天7板         4       15  3.4553    12
12  885934.TI     元宇宙   20241127     1    9天7板         4       14  3.9264    13
13  885757.TI     区块链   20241127     1  18天14板         5       14  3.1271    14
14  885413.TI      创投   20241127     3  18天14板         7       14  1.7311    15
15  885779.TI    腾讯概念   20241127     1    9天7板         4       13  3.3722    16
16  885876.TI    网红经济   20241127     1    9天7板         5       12  2.9002    17
17  885494.TI    一带一路   20241127     2    9天7板         1       12  1.3427    18
18  885950.TI   虚拟数字人   20241127     1    9天7板         3       11  4.1545    19
19  886013.TI      信创   20241127     2    9天7板         6       11  3.2298    20
```

---

### 涨停股票连板天梯 (limit_step)

#### 接口说明

获取每天连板个数晋级的股票，可以分析出每天连续涨停进阶个数，判断强势热度。

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api("YOUR_TOKEN")

df = pro.limit_step(trade_date='20241125')
```

#### 权限要求

8000积分以上每分钟500次，每天总量不限制。

#### 输入参数

| 名称 | 类型 | 是否必填 | 说明 |
|---|---|---|---|
| trade_date | str | N | 交易日期（格式：YYYYMMDD） |
| ts_code | str | N | 股票代码 |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |
| nums | str | N | 连板次数，支持多个输入，例如nums='2,3' |

#### 输出参数

| 字段 | 类型 | 说明 |
|---|---|---|
| ts_code | str | 代码 |
| name | str | 名称 |
| trade_date | str | 交易日期 |
| nums | str | 连板次数 |

#### 调用示例

```python
pro = ts.pro_api()

df = pro.limit_step(trade_date='20241125')
```

##### 数据样例

```
        ts_code        name trade_date nums
    0   000833.SZ  粤桂股份   20241125   11
    1   002611.SZ  东方精工   20241125    8
    2   600800.SH  渤海化学   20241125    7
    3   000801.SZ  四川九洲   20241125    6
    4   600889.SH  南京化纤   20241125    6
    5   000615.SZ  ST美谷   20241125    5
    6   001229.SZ  魅视科技   20241125    5
    7   002095.SZ   生意宝   20241125    5
    8   002403.SZ   爱仕达   20241125    5
    9   600470.SH  六国化工   20241125    5
    10  603015.SH  弘讯科技   20241125    5
    11  603527.SH  众源新材   20241125    5
    12  002103.SZ  广博股份   20241125    4
    13  002175.SZ  东方智造   20241125    4
    14  002467.SZ   二六三   20241125    4
    15  002741.SZ  光华科技   20241125    4
    16  002862.SZ  实丰文化   20241125    4
    17  003036.SZ  泰坦股份   20241125    4
    18  603377.SH  ST东时   20241125    4
    19  000573.SZ  粤宏远A   20241125    3
    20  002155.SZ  湖南黄金   20241125    3
    21  300822.SZ  贝仕达克   20241125    3
    22  600105.SH  永鼎股份   20241125    3
    23  600405.SH   动力源   20241125    3
    24  600410.SH  华胜天成   20241125    3
    25  600979.SH  广安爱众   20241125    3
    26  000548.SZ  湖南投资   20241125    2
    27  000695.SZ  滨海能源   20241125    2
    28  000803.SZ  山高环能   20241125    2
    29  002045.SZ  国光电器   20241125    2
    30  002054.SZ  德美化工   20241125    2
    31  002117.SZ  东港股份   20241125    2
    32  002638.SZ  勤上股份   20241125    2
    33  002640.SZ   跨境通   20241125    2
    34  002658.SZ   雪迪龙   20241125    2
    35  002820.SZ   桂发祥   20241125    2
    36  002877.SZ  智能自控   20241125    2
    37  003005.SZ   竞业达   20241125    2
    38  300220.SZ  金运激光   20241125    2
    39  600228.SH  返利科技   20241125    2
    40  600333.SH  长春燃气   20241125    2
    41  600615.SH  丰华股份   20241125    2
    42  600775.SH  南京熊猫   20241125    2
    43  601133.SH  柏诚股份   20241125    2
    44  603026.SH  石大胜华   20241125    2
    45  603359.SH  东珠生态   20241125    2
    46  603585.SH  苏利股份   20241125    2
    47  603655.SH  朗博科技   20241125    2
    48  603843.SH  正平股份   20241125    2
```

---

### 涨跌停和炸板数据

#### 接口信息

- **接口名称:** 涨跌停列表（新）
- **接口标识:** limit_list_d
- **接口说明:** 获取A股每日涨跌停、炸板数据情况，数据从2020年开始（不提供ST股票的统计）。
- **限量:** 单次最大可以获取2500条数据，可通过日期或者股票循环提取。
- **权限要求:** 5000积分每分钟可以请求200次每天总量1万次，8000积分以上每分钟500次每天总量不限制。

#### 输入参数

| 名称 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| trade_date | str | N | 交易日期 |
| ts_code | str | N | 股票代码 |
| limit_type | str | N | 涨跌停类型（U涨停D跌停Z炸板） |
| exchange | str | N | 交易所（SH上交所SZ深交所BJ北交所） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 名称 | 类型 | 描述 |
| --- | --- | --- |
| trade_date | str | 交易日期 |
| ts_code | str | 股票代码 |
| industry | str | 所属行业 |
| name | str | 股票名称 |
| close | float | 收盘价 |
| pct_chg | float | 涨跌幅 |
| amount | float | 成交额 |
| limit_amount | float | 板上成交金额(成交价格为该股票跌停价的所有成交额的总和，涨停无此数据) |
| float_mv | float | 流通市值 |
| total_mv | float | 总市值 |
| turnover_ratio | float | 换手率 |
| fd_amount | float | 封单金额（以涨停价买入挂单的资金总量） |
| first_time | str | 首次封板时间（跌停无此数据） |
| last_time | str | 最后封板时间 |
| open_times | int | 炸板次数(跌停为开板次数) |
| up_stat | str | 涨停统计（N/T T天有N次涨停） |
| limit_times | int | 连板数（个股连续封板数量） |
| limit | str | D跌停U涨停Z炸板 |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.limit_list_d(trade_date='20220615', limit_type='U', fields='ts_code,trade_date,industry,name,close,pct_chg,open_times,up_stat,limit_times')
```

---

### 游资每日明细 (hm_detail)

#### 接口说明

获取每日游资交易明细，数据开始于2022年8。

#### 调用方法

通过Tushare Pro SDK调用，方法名为`hm_detail`。

#### 权限要求

用户积10000积分可调取使用。

#### 输入参数

| 参数名称 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| trade_date | str | N | 交易日期(YYYYMMDD) |
| ts_code | str | N | 股票代码 |
| hm_name | str | N | 游资名称 |
| start_date | str | N | 开始日期(YYYYMMDD) |
| end_date | str | N | 结束日期(YYYYMMDD) |

#### 输出参数

| 字段名称 | 类型 | 说明 |
| --- | --- | --- |
| trade_date | str | 交易日期 |
| ts_code | str | 股票代码 |
| ts_name | str | 股票名称 |
| buy_amount | float | 买入金额（元） |
| sell_amount | float | 卖出金额（元） |
| net_amount | float | 净买卖（元） |
| hm_name | str | 游资名称 |
| hm_orgs | str | 关联机构（一般为营业部或机构专用） |
| tag | str | 标签 |

#### 调用示例

```python
import tushare as ts

### 设置token
### ts.set_token('YOUR_TOKEN_HERE')

### 初始化pro接口
pro = ts.pro_api()

### 获取单日全部明细
df = pro.hm_detail(trade_date='20230815')

print(df)
```

---

### 通达信板块信息 (tdx_index)

#### 接口说明

获取通达信板块基础信息，包括概念板块、行业、风格、地域等

#### 调用方法

获取Tushare Pro的token，然后用token初始化pro接口。

```python
import tushare as ts

### 设置token
ts.set_token('你的token')

### 初始化pro接口
pro = ts.pro_api()

### 调用接口
### df = pro.tdx_index(trade_date='20250513', fields='ts_code,name,idx_type,idx_count')
```

#### 权限要求

用户积累6000积分可调取

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 板块代码：xxxxxx.TDX |
| trade_date | str | N | 交易日期(格式：YYYYMMDD） |
| idx_type | str | N | 板块类型：概念板块、行业板块、风格板块、地区板块 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 板块代码 |
| trade_date | str | Y | 交易日期 |
| name | str | Y | 板块名称 |
| idx_type | str | Y | 板块类型 |
| idx_count | int | Y | 成分个数 |
| total_share | float | Y | 总股本(亿) |
| float_share | float | Y | 流通股(亿) |
| total_mv | float | Y | 总市值(亿) |
| float_mv | float | Y | 流通市值(亿) |

#### 调用示例

```python
#获取通达信2025年5月13日的概念板块列表
df = pro.tdx_index(trade_date='20250513', fields='ts_code,name,idx_type,idx_count')
```

---

### 通达信板块成分 (tdx_member)

#### 接口描述

获取通达信各板块成分股信息。

#### 调用方法

通过Tushare Pro SDK调用。

#### 权限要求

用户积累6000积分可调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)

#### 限量

单次最大3000条数据，可以根据日期和板块代码循环提取。

#### 输入参数

| 名称       | 类型 | 是否必选 | 描述                |
| ---------- | ---- | -------- | ------------------- |
| ts_code    | str  | N        | 板块代码：xxxxxx.TDX |
| trade_date | str  | N        | 交易日期：格式YYYYMMDD |

#### 输出参数

| 名称      | 类型 | 描述         |
| --------- | ---- | ------------ |
| ts_code   | str  | 板块代码     |
| trade_date| str  | 交易日期     |
| con_code  | str  | 成分股票代码 |
| con_name  | str  | 成分股票名称 |

#### 调用示例

```python
#获取通达信板块2025年5月13日的航运概念板块成分股
df = pro.tdx_member(trade_date='20250513', ts_code='880728.TDX')
```

---

### 通达信板块行情 (tdx_daily)

#### 接口描述

获取通达信各板块行情，包括成交和估值等数据。

**限量**：单次提取最大3000条数据，可根据板块代码和日期参数循环提取
**权限**：用户积累6000积分可调取

#### 调用方法

通过Tushare Pro SDK调用，方法名为`tdx_daily`。

```python
import tushare as ts

### 初始化pro接口
pro = ts.pro_api('YOUR_TOKEN')

### 调用接口
df = pro.tdx_daily(trade_date='20250513')
```

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 板块代码：xxxxxx.TDX |
| trade_date | str | N | 交易日期，格式YYYYMMDD,下同 |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 名称 | 类型 | 描述 |
| --- | --- | --- |
| ts_code | str | 板块代码 |
| trade_date | str | 交易日期 |
| close | float | 收盘点位 |
| open | float | 开盘点位 |
| high | float | 最高点位 |
| low | float | 最低点位 |
| pre_close | float | 昨日收盘点 |
| change | float | 涨跌点位 |
| pct_change | float | 涨跌幅% |
| vol | float | 成交量（手） |
| amount | float | 成交额（万元）, 对于期货指数，该字段存储持仓量 |
| rise | str | 收盘涨速% |
| vol_ratio | float | 量比 |
| turnover_rate | float | 换手% |
| swing | float | 振幅% |
| up_num | int | 上涨家数 |
| down_num | int | 下跌家数 |
| limit_up_num | int | 涨停家数 |
| limit_down_num | int | 跌停家数 |
| lu_days | int | 连涨天数 |
| 3day | float | 3日涨幅% |
| 5day | float | 5日涨幅% |
| 10day | float | 10日涨幅% |
| 20day | float | 20日涨幅% |
| 60day | float | 60日涨幅% |
| mtd | float | 月初至今% |
| ytd | float | 年初至今% |
| 1year | float | 一年涨幅% |
| pe | str | 市盈率 |
| pb | str | 市净率 |
| float_mv | float | 流通市值(亿) |
| ab_total_mv | float | AB股总市值（亿） |
| float_share | float | 流通股(亿) |
| total_share | float | 总股本(亿) |
| bm_buy_net | float | 主买净额(元) |
| bm_buy_ratio | float | 主买占比% |
| bm_net | float | 主力净额 |
| bm_ratio | float | 主力占比% |

#### 调用示例

```python
#获取通达信2025年5月13日概念板块行情
df = pro.tdx_daily(trade_date='20250513')
```

---

### 开盘啦题材成分

#### 接口信息

- **接口名称：** 开盘啦题材成分
- **接口标识：** kpl_concept_cons
- **接口说明：** 获取开盘啦概念题材的成分股
- **限量：** 单次最大3000条，可根据代码和日期循环获取全部数据
- **权限要求：** 5000积分可提取数据

**注：** 开盘啦是一个优秀的专业打板app，有兴趣的用户可以自行下载安装。本接口仅限用于量化研究，如需商业用途，请自行联系开盘APP官方。此接口因源站改版暂无新增数据

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| trade_date | str | N | 交易日期（YYYYMMDD格式） |
| ts_code | str | N | 题材代码（xxxxxx.KP格式） |
| con_code | str | N | 成分代码（xxxxxx.SH格式） |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 题材ID |
| name | str | Y | 题材名称 |
| con_name | str | Y | 股票名称 |
| con_code | str | Y | 股票代码 |
| trade_date | str | Y | 交易日期 |
| desc | str | Y | 描述 |
| hot_num | int | Y | 人气值 |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.kpl_concept_cons(trade_date='20241014')
```

#### 数据样例

```
        ts_code      name     ts_name con_code trade_date
0     000111.KP  化债概念    信达地产  600657.SH   20241014
1     000111.KP  化债概念    银宝山新  002786.SZ   20241014
2     000111.KP  化债概念    摩恩电气  002451.SZ   20241014
3     000111.KP  化债概念    光大嘉宝  600622.SH   20241014
4     000111.KP  化债概念    海德股份  000567.SZ   20241014
...         ...   ...     ...        ...        ...
2995  000229.KP    电力    特变电工  600089.SH   20241014
2996  000229.KP    电力    中国西电  601179.SH   20241014
2997  000229.KP    电力    金盘科技  688676.SH   20241014
2998  000229.KP    电力    思源电气  002028.SZ   20241014
2999  000229.KP    电力    明阳电气  301291.SZ   20241014
```

---

### 龙虎榜机构明细 (top_inst)

#### 接口说明

- **接口标识**：top_inst
- **接口名称**：龙虎榜机构明细
- **功能描述**：获取龙虎榜机构成交明细，单次请求最大返回10000行数据，可根据参数循环获取全部历史。
- **权限要求**：用户需要至少5000积分才可以调取。

#### 调用方法

```python
import tushare as ts

### 初始化pro接口
pro = ts.pro_api("YOUR_TOKEN")

### 调用方法1
df = pro.top_inst(trade_date=
'20210525
')

### 调用方法2
df = pro.query(
'top_inst
', trade_date=
'20210524
', ts_code=
'000592.SZ
', fields=
'trade_date,buy,sell,side,reason
')
```

#### 输入参数

| 参数名称   | 类型 | 是否必填 | 描述     |
| ---------- | ---- | -------- | -------- |
| trade_date | str  | Y        | 交易日期 |
| ts_code    | str  | N        | TS代码   |

#### 输出参数

| 字段名称   | 类型  | 描述                                       |
| ---------- | ----- | ------------------------------------------ |
| trade_date | str   | 交易日期                                   |
| ts_code    | str   | TS代码                                     |
| exalter    | str   | 营业部名称                                 |
| side       | str   | 买卖类型0：买入金额最大的前5名， 1：卖出金额最大的前5名 |
| buy        | float | 买入额（元）                               |
| buy_rate   | float | 买入占总成交比例                           |
| sell       | float | 卖出额（元）                               |
| sell_rate  | float | 卖出占总成交比例                           |
| net_buy    | float | 净成交额（元）                             |
| reason     | str   | 上榜理由                                   |

#### 调用示例

```python
### 获取2021年5月25日的龙虎榜机构明细
df = pro.top_inst(trade_date='20210525')
print(df)
```

##### 示例数据

```
   trade_date          buy         sell side                   reason
0    20210524  19627524.05  25593683.67    0              涨幅偏离值达7%的证券
1    20210524   9091252.00  18009704.00    0              涨幅偏离值达7%的证券
2    20210524  35168640.99  13344062.12    0              涨幅偏离值达7%的证券
3    20210524  18812912.60  12121352.00    0              涨幅偏离值达7%的证券
4    20210524   1684986.00  12076417.00    0              涨幅偏离值达7%的证券
5    20210524  37071259.81   3956982.00    1              涨幅偏离值达7%的证券
6    20210524  35168640.99  13344062.12    1              涨幅偏离值达7%的证券
7    20210524  21487772.44     84795.00    1              涨幅偏离值达7%的证券
8    20210524  19627524.05  25593683.67    1              涨幅偏离值达7%的证券
9    20210524  18812912.60  12121352.00    1              涨幅偏离值达7%的证券
10   20210524  28720777.05  53009929.06    0  连续三个交易日内，涨幅偏离值累计达20%的证券
11   20210524  35504648.99  46382533.92    0  连续三个交易日内，涨幅偏离值累计达20%的证券
12   20210524  35344119.44  46305551.88    0  连续三个交易日内，涨幅偏离值累计达20%的证券
13   20210524   9091252.00  26481086.00    0  连续三个交易日内，涨幅偏离值累计达20%的证券
14   20210524  23609443.87  23791701.41    0  连续三个交易日内，涨幅偏离值累计达20%的证券
15   20210524  49699663.21   3956982.00    1  连续三个交易日内，涨幅偏离值累计达20%的证券
16   20210524  35504648.99  46382533.92    1  连续三个交易日内，涨幅偏离值累计达20%的证券
17   20210524  35344119.44  46305551.88    1  连续三个交易日内，涨幅偏离值累计达20%的证券
18   20210524  29607924.52  19374138.00    1  连续三个交易日内，涨幅偏离值累计达20%的证券
19   20210524  28720777.05  53009929.06    1  连续三个交易日内，涨幅偏离值累计达20%的证券
```

---

### 龙虎榜每日明细 (top_list)

#### 接口说明

- **接口标识**：top_list
- **接口名称**：龙虎榜每日明细
- **功能描述**：获取龙虎榜每日交易明细数据，包括上榜股票的交易日期、代码、名称、收盘价、涨跌幅、换手率、总成交额、龙虎榜相关金额及上榜理由等。
- **数据历史**：2005年至今
- **限量**：单次请求返回最大10000行数据，可通过参数循环获取全部历史。

#### 权限要求

用户需要至少2000积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)。

#### 调用方法

```python
pro.top_list(trade_date=\'YYYYMMDD\', ts_code=\'xxxxxx.SH\')
```

或者

```python
pro.query(\'top_list\', trade_date=\'YYYYMMDD\', ts_code=\'xxxxxx.SH\')
```

#### 输入参数

| 参数名称   | 类型 | 是否必填 | 描述     |
| ---------- | ---- | -------- | -------- |
| trade_date | str  | Y        | 交易日期 |
| ts_code    | str  | N        | 股票代码 |

#### 输出参数

| 字段名称      | 类型  | 默认显示 | 描述             |
| ------------- | ----- | -------- | ---------------- |
| trade_date    | str   | Y        | 交易日期         |
| ts_code       | str   | Y        | TS代码           |
| name          | str   | Y        | 名称             |
| close         | float | Y        | 收盘价           |
| pct_change    | float | Y        | 涨跌幅           |
| turnover_rate | float | Y        | 换手率           |
| amount        | float | Y        | 总成交额         |
| l_sell        | float | Y        | 龙虎榜卖出额     |
| l_buy         | float | Y        | 龙虎榜买入额     |
| l_amount      | float | Y        | 龙虎榜成交额     |
| net_amount    | float | Y        | 龙虎榜净买入额   |
| net_rate      | float | Y        | 龙虎榜净买额占比 |
| amount_rate   | float | Y        | 龙虎榜成交额占比 |
| float_values  | float | Y        | 当日流通市值     |
| reason        | str   | Y        | 上榜理由         |

#### 调用示例

```python
import tushare as ts

### 设置token
### pro = ts.pro_api(\'YOUR_TOKEN\')
pro = ts.pro_api()

### 获取2018年9月28日的龙虎榜明细
df = pro.top_list(trade_date=\'20180928\')
print(df.head())

### 获取特定股票在2018年9月28日的龙虎榜明细
df_stock = pro.query(\'top_list\', trade_date=\'20180928\', ts_code=\'002219.SZ\')
print(df_stock)
```

---


# 2. ETF专题

## ETF专题

### ETF份额规模 (etf_share_size)

#### 接口描述

获取沪深ETF每日份额和规模数据，能体现规模份额的变化，掌握ETF资金动向，同时提供每日净值和收盘价。数据指标是分批入库，建议在每日19点后提取；另外，涉及海外的ETF数据更新会晚一些属于正常情况。

- **接口标识：** `etf_share_size`
- **限量：** 单次最大5000条，可根据代码或日期循环提取
- **积分要求：** 8000积分

#### 输入参数

| 参数名称   | 参数类型 | 是否必填 | 描述                                 |
| ---------- | -------- | -------- | ------------------------------------ |
| ts_code    | str      | N        | 基金代码 (可从ETF基础信息接口提取)   |
| trade_date | str      | N        | 交易日期 (YYYYMMDD格式)              |
| start_date | str      | N        | 开始日期 (YYYYMMDD格式)              |
| end_date   | str      | N        | 结束日期 (YYYYMMDD格式)              |
| exchange   | str      | N        | 交易所 (SSE: 上交所, SZSE: 深交所) |

#### 输出参数

| 字段名称    | 字段类型 | 描述                                         |
| ----------- | -------- | -------------------------------------------- |
| trade_date  | str      | 交易日期                                     |
| ts_code     | str      | ETF代码                                      |
| etf_name    | str      | 基金名称                                     |
| total_share | float    | 总份额 (万份)                                |
| total_size  | float    | 总规模 (万元)                                |
| nav         | float    | 基金份额净值 (元)                            |
| close       | float    | 收盘价 (元)                                  |
| exchange    | str      | 交易所 (SSE: 上交所, SZSE: 深交所, BSE: 北交所) |

#### 调用示例

```python
### 示例1: 获取”沪深300ETF华夏”ETF2025年以来每个交易日的份额和规模情况
df = pro.etf_share_size(ts_code='510330.SH', start_date='20250101', end_date='20251224')

### 示例2: 获取2025年12月24日上交所的所有ETF份额和规模情况
df = pro.etf_share_size(trade_date='20251224', exchange='SSE')
```

---

### ETF历史分钟行情 (stk_mins)

#### 接口说明

获取ETF分钟数据，支持1min/5min/15min/30min/60min行情，提供Python SDK和 http Restful API两种方式。

- **限量**：单次最大8000行数据，可以通过股票代码和时间循环获取，本接口可以提供超过10年ETF历史分钟数据。
- **权限**：正式权限请参阅 [权限说明](https://tushare.pro/document/1?doc_id=108)。

#### 调用方法

推荐使用Python SDK调用，需要先安装Tushare库：

```bash
pip install tushare
```

然后按如下方式调用：

```python
import tushare as ts

### 设置你的Tushare Pro token
pro = ts.pro_api('YOUR_TOKEN')

### 调用接口
df = pro.stk_mins(ts_code='510330.SH', freq='1min', start_date='2025-06-20 09:00:00', end_date='2025-06-20 19:00:00')

print(df)
```

#### 输入参数

| 参数名称   | 类型     | 是否必填 | 说明                                       |
| ---------- | -------- | -------- | ------------------------------------------ |
| ts_code    | str      | Y        | ETF代码，e.g. 159001.SZ                    |
| freq       | str      | Y        | 分钟频度（1min/5min/15min/30min/60min）      |
| start_date | datetime | N        | 开始日期 格式：YYYY-MM-DD HH:mm:ss         |
| end_date   | datetime | N        | 结束时间 格式：YYYY-MM-DD HH:mm:ss         |

##### freq参数说明

| freq  | 说明   |
| ----- | ------ |
| 1min  | 1分钟  |
| 5min  | 5分钟  |
| 15min | 15分钟 |
| 30min | 30分钟 |
| 60min | 60分钟 |

#### 输出参数

| 字段名称   | 类型  | 说明         |
| ---------- | ----- | ------------ |
| ts_code    | str   | ETF代码      |
| trade_time | str   | 交易时间     |
| open       | float | 开盘价       |
| close      | float | 收盘价       |
| high       | float | 最高价       |
| low        | float | 最低价       |
| vol        | int   | 成交量（股） |
| amount     | float | 成交金额（元） |

#### 调用示例

获取沪深300ETF华夏(510330.SH)在2025年6月20日的1分钟历史数据：

```python
pro = ts.pro_api()
df = pro.stk_mins(ts_code='510330.SH', freq='1min', start_date='2025-06-20 09:00:00', end_date='2025-06-20 19:00:00')
```

##### 数据样例

```
       ts_code           trade_time  close   open   high    low        vol      amount
0    510330.SH  2025-06-20 15:00:00  3.991  3.991  3.992  3.990   800600.0   3194805.0
1    510330.SH  2025-06-20 14:59:00  3.991  3.990  3.991  3.989   182500.0    728177.0
2    510330.SH  2025-06-20 14:58:00  3.990  3.992  3.992  3.990   113700.0    453763.0
3    510330.SH  2025-06-20 14:57:00  3.992  3.992  3.992  3.991    17400.0     69460.0
4    510330.SH  2025-06-20 14:56:00  3.992  3.992  3.992  3.991   447500.0   1786373.0
..         ...                  ...    ...    ...    ...    ...        ...         ...
236  510330.SH  2025-06-20 09:34:00  3.994  3.994  3.995  3.994  2528100.0  10097818.0
237  510330.SH  2025-06-20 09:33:00  3.994  3.991  3.994  3.991   143300.0    572084.0
238  510330.SH  2025-06-20 09:32:00  3.992  3.990  3.993  3.990  1118500.0   4463264.0
239  510330.SH  2025-06-20 09:31:00  3.988  3.984  3.992  3.984  1176100.0   4691600.0
240  510330.SH  2025-06-20 09:30:00  3.983  3.983  3.983  3.983    20700.0     82448.0
```

---

### ETF基准指数 (etf_index)

#### 接口描述

获取ETF基准指数列表信息。

#### 接口信息

- **接口标识**: `etf_index`
- **接口名称**: ETF基准指数
- **限量**: 单次请求最大返回5000行数据（当前未超过2000个）
- **权限**: 用户积累8000积分可调取

#### 输入参数

| 参数名称   | 参数类型 | 是否必选 | 参数描述             |
| ---------- | -------- | -------- | -------------------- |
| ts_code    | str      | N        | 指数代码             |
| pub_date   | str      | N        | 发布日期（格式：YYYYMMDD） |
| base_date  | str      | N        | 指数基期（格式：YYYYMMDD） |

#### 输出参数

| 字段名称       | 字段类型 | 描述                 |
| -------------- | -------- | -------------------- |
| ts_code        | str      | 指数代码             |
| indx_name      | str      | 指数全称             |
| indx_csname    | str      | 指数简称             |
| pub_party_name | str      | 指数发布机构         |
| pub_date       | str      | 指数发布日期         |
| base_date      | str      | 指数基日             |
| bp             | float    | 指数基点(点)         |
| adj_circle     | str      | 指数成份证券调整周期 |

#### 调用示例

```python
#获取当前ETF跟踪的基准指数列表
df = pro.etf_index(fields='ts_code,indx_name,pub_date,bp')
```

---

### ETF基础信息 (etf_basic)

#### 接口描述

获取国内ETF基础信息，包括了QDII。数据来源与沪深交易所公开披露信息。

**限量**：单次请求最大返回5000条数据（当前ETF总数未超过2000）

**权限**：用户积8000积分可调取

#### 接口标识

etf_basic

#### 调用方法

```python
pro.etf_basic(list_status='L', fields='ts_code,extname,index_code,index_name,exchange,mgr_name')
```

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | ETF代码（带.SZ/.SH后缀的6位数字，如：159526.SZ） |
| index_code | str | N | 跟踪指数代码 |
| list_date | str | N | 上市日期（格式：YYYYMMDD） |
| list_status | str | N | 上市状态（L上市 D退市 P待上市） |
| exchange | str | N | 交易所（SH上交所 SZ深交所） |
| mgr | str | N | 管理人（简称，e.g.华夏基金） |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 基金交易代码 |
| csname | str | Y | ETF中文简称 |
| extname | str | Y | ETF扩位简称(对应交易所简称) |
| cname | str | Y | 基金中文全称 |
| index_code | str | Y | ETF基准指数代码 |
| index_name | str | Y | ETF基准指数中文全称 |
| setup_date | str | Y | 设立日期（格式：YYYYMMDD） |
| list_date | str | Y | 上市日期（格式：YYYYMMDD） |
| list_status | str | Y | 存续状态（L上市 D退市 P待上市） |
| exchange | str | Y | 交易所（上交所SH 深交所SZ） |
| mgr_name | str | Y | 基金管理人简称 |
| custod_name | str | Y | 基金托管人名称 |
| mgt_fee | float | Y | 基金管理人收取的费用 |
| etf_type | str | Y | 基金投资通道类型（境内、QDII） |

#### 调用示例

```python
### 获取当前所有上市的ETF列表
df = pro.etf_basic(list_status='L', fields='ts_code,extname,index_code,index_name,exchange,mgr_name')

### 获取"嘉实基金"所有上市的ETF列表
df = pro.etf_basic(mgr='嘉实基金', list_status='L', fields='ts_code,extname,index_code,index_name,exchange,etf_type')

### 获取以沪深300指数为跟踪指数的所有上市的ETF列表
df = pro.etf_basic(index_code='000300.SH', fields='ts_code,extname,index_code,index_name,exchange,mgr_name')
```

---

### ETF实时分钟 (rt_min)

#### 接口描述

获取ETF实时分钟数据，包括1~60min。单次最大1000行数据，可以通过ETF代码提取数据，支持逗号分隔的多个代码同时提取。

#### 调用方法

使用Tushare Pro的Python SDK进行调用。

```python
import tushare as ts

### 初始化pro接口
pro = ts.pro_api('YOUR_TOKEN')
```

#### 权限要求

正式权限请参阅Tushare Pro的权限说明。需要一定的积分才能调用该接口。支持股票当日开盘以来的所有ETF历史分钟数据提取的接口为 `rt_min_daily`，可以单独开通权限。

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 参数描述 |
|---|---|---|---|
| freq | str | Y | 1MIN, 5MIN, 15MIN, 30MIN, 60MIN （大写） |
| ts_code | str | Y | 支持单个和多个：`589960.SH` 或者 `589960.SH,159100.SZ` |

##### freq参数说明

| freq | 说明 |
|---|---|
| 1MIN | 1分钟 |
| 5MIN | 5分钟 |
| 15MIN | 15分钟 |
| 30MIN | 30分钟 |
| 60MIN | 60分钟 |

#### 输出参数

| 字段名称 | 字段类型 | 描述 |
|---|---|---|
| ts_code | str | 股票代码 |
| time | str | 交易时间 |
| open | float | 开盘价 |
| close | float | 收盘价 |
| high | float | 最高价 |
| low | float | 最低价 |
| vol | float | 成交量(股） |
| amount | float | 成交额（元） |

#### 调用示例

```python
### 获取科创新能源ETF易方达589960.SH的实时分钟数据
df = pro.rt_min(ts_code='589960.SH', freq='1MIN')

print(df)
```

---

### ETF实时日线 (rt_etf_k)

#### 接口说明

获取ETF实时日k线行情，支持按ETF代码或代码通配符一次性提取全部ETF实时日k线行情。

#### 调用方法

使用`pro.rt_etf_k()`方法调用。

#### 权限要求

本接口是单独开权限的数据，单独申请权限请参考权限列表。

#### 输入参数

| 名称    | 类型 | 是否必填 | 说明                                                                 |
| :------ | :--- | :------- | :------------------------------------------------------------------- |
| ts_code | str  | Y        | 支持通配符方式，e.g. 5*.SH、15*.SZ、159101.SZ                         |
| topic   | str  | Y        | 分类参数，取上海ETF时，需要输入'HQ_FND_TICK'，参考下面例子         |

#### 输出参数

| 名称        | 类型  | 说明             |
| :---------- | :---- | :--------------- |
| ts_code     | str   | ETF代码          |
| name        | None  | ETF名称          |
| pre_close   | float | 昨收价           |
| high        | float | 最高价           |
| open        | float | 开盘价           |
| low         | float | 最低价           |
| close       | float | 收盘价（最新价） |
| vol         | int   | 成交量（股）     |
| amount      | int   | 成交金额（元）   |
| num         | int   | 开盘以来成交笔数 |
| ask_volume1 | int   | 委托卖盘（股）   |
| bid_volume1 | int   | 委托买盘（股）   |
| trade_time  | str   | 交易时间         |

#### 调用示例

```python
#获取今日所有深市ETF实时日线和成交笔数
df = pro.rt_etf_k(ts_code='1*.SZ')

#获取今日沪市所有ETF实时日线和成交笔数
df = pro.rt_etf_k(ts_code='5*.SH', topic='HQ_FND_TICK')
```

---

### ETF日线行情

**接口标识**：fund_daily

**接口说明**：获取ETF行情每日收盘后成交数据，历史超过10年。

**调用方法**：pro.fund_daily()

**权限要求**：需要至少5000积分才可以调取，5000积分频次更高，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)

#### 输入参数

| 名称       | 类型 | 必选 | 描述                           |
| ---------- | ---- | ---- | ------------------------------ |
| ts_code    | str  | N    | 基金代码                       |
| trade_date | str  | N    | 交易日期(YYYYMMDD格式，下同) |
| start_date | str  | N    | 开始日期                       |
| end_date   | str  | N    | 结束日期                       |

#### 输出参数

| 名称      | 类型  | 默认显示 | 描述       |
| --------- | ----- | -------- | ---------- |
| ts_code   | str   | Y        | TS代码     |
| trade_date| str   | Y        | 交易日期   |
| open      | float | Y        | 开盘价(元) |
| high      | float | Y        | 最高价(元) |
| low       | float | Y        | 最低价(元) |
| close     | float | Y        | 收盘价(元) |
| pre_close | float | Y        | 昨收盘价(元) |
| change    | float | Y        | 涨跌额(元) |
| pct_chg   | float | Y        | 涨跌幅(%)  |
| vol       | float | Y        | 成交量(手) |
| amount    | float | Y        | 成交额(千元) |

#### 调用示例

```python
pro = ts.pro_api()

#获取”沪深300ETF华夏”ETF2025年以来的行情，并通过fields参数指定输出了部分字段
df = pro.fund_daily(ts_code='510330.SH', start_date='20250101', end_date='20250618', fields='trade_date,open,high,low,close,vol,amount')
```

---

### 基金复权因子 (fund_adj)

#### 接口描述

获取基金复权因子，用于计算基金复权行情。

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api()
df = pro.fund_adj(ts_code='513100.SH', start_date='20190101', end_date='20190926')
```

#### 权限要求

用户积600积分可调取，超过5000积分以上频次相对较高。

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 描述 |
|---|---|---|---|
| ts_code | str | N | TS基金代码（支持多只基金输入） |
| trade_date | str | N | 交易日期（格式：yyyymmdd，下同） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |
| offset | str | N | 开始行数 |
| limit | str | N | 最大行数 |

#### 输出参数

| 字段 | 类型 | 默认显示 | 描述 |
|---|---|---|---|
| ts_code | str | Y | ts基金代码 |
| trade_date | str | Y | 交易日期 |
| adj_factor | float | Y | 复权因子 |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.fund_adj(ts_code='513100.SH', start_date='20190101', end_date='20190926')
```

---


# 3. 指数专题

## 指数专题

### 中信行业成分 (ci_index_member)

#### 接口说明

按三级分类提取中信行业成分，可提供某个分类的所有成分，也可按股票代码提取所属分类，参数灵活。

- **接口标识：** `ci_index_member`
- **调用方法：** `pro.ci_index_member()`
- **权限要求：** 用户需5000积分可调取
- **限量：** 单次最大5000行，总量不限制

#### 输入参数

| 参数名称 | 类型 | 是否必填 | 描述 |
|---|---|---|---|
| l1_code | str | N | 一级行业代码 |
| l2_code | str | N | 二级行业代码 |
| l3_code | str | N | 三级行业代码 |
| ts_code | str | N | 股票代码 |
| is_new | str | N | 是否最新（默认为“Y是”） |

#### 输出参数

| 字段名称 | 类型 | 默认输出 | 描述 |
|---|---|---|---|
| l1_code | str | Y | 一级行业代码 |
| l1_name | str | Y | 一级行业名称 |
| l2_code | str | Y | 二级行业代码 |
| l2_name | str | Y | 二级行业名称 |
| l3_code | str | Y | 三级行业代码 |
| l3_name | str | Y | 三级行业名称 |
| ts_code | str | Y | 成分股票代码 |
| name | str | Y | 成分股票名称 |
| in_date | str | Y | 纳入日期 |
| out_date | str | Y | 剔除日期 |
| is_new | str | Y | 是否最新Y是N否 |

#### 调用示例

```python
#获取二级分类元器件的成份股
df = pro.ci_index_member(l2_code='CI005835.CI', fields='l2_code,l1_name,ts_code,name')

#获取000001.SZ所属行业
df = pro.ci_index_member(ts_code='000001.SZ')
```

---

### 中信行业指数行情 (ci_daily)

#### 接口说明

获取中信行业指数日线行情

- **接口**: `ci_daily`
- **描述**: 获取中信行业指数日线行情
- **限量**: 单次最大4000条，可循环提取
- **权限**: 5000积分可调取，可通过指数代码和日期参数循环获取所有数据

#### 调用方法

```python
pro = ts.pro_api('your token')
df = pro.ci_daily(**params)
```

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 行业代码 |
| trade_date | str | N | 交易日期（YYYYMMDD格式，下同） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 指数代码 |
| trade_date | str | Y | 交易日期 |
| open | float | Y | 开盘点位 |
| low | float | Y | 最低点位 |
| high | float | Y | 最高点位 |
| close | float | Y | 收盘点位 |
| pre_close | float | Y | 昨日收盘点位 |
| change | float | Y | 涨跌点位 |
| pct_change | float | Y | 涨跌幅 |
| vol | float | Y | 成交量（万股） |
| amount | float | Y | 成交额（万元） |

#### 调用示例

```python
pro = ts.pro_api('your token')
df = pro.ci_daily(trade_date='20230705', fields='ts_code,trade_date,open,low,high,close')
```

---

### 国际指数 (index_global)

#### 接口描述

获取国际主要指数日线行情。

**接口名称**：`index_global`
**调用方法**：`pro.index_global()`
**权限要求**：用户积6000积分可调取，积分越高频次越高。
**限量**：单次最大提取4000行情数据，可循环获取，总量不限制。

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | TS指数代码，见下表 |
| trade_date | str | N | 交易日期，YYYYMMDD格式，下同 |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

##### TS指数代码

| TS指数代码 | 指数名称 |
| --- | --- |
| XIN9 | 富时中国A50指数 (富时A50) |
| HSI | 恒生指数 |
| HKTECH | 恒生科技指数 |
| HKAH | 恒生AH股H指数 |
| DJI | 道琼斯工业指数 |
| SPX | 标普500指数 |
| IXIC | 纳斯达克指数 |
| FTSE | 富时100指数 |
| FCHI | 法国CAC40指数 |
| GDAXI | 德国DAX指数 |
| N225 | 日经225指数 |
| KS11 | 韩国综合指数 |
| AS51 | 澳大利亚标普200指数 |
| SENSEX | 印度孟买SENSEX指数 |
| IBOVESPA | 巴西IBOVESPA指数 |
| RTS | 俄罗斯RTS指数 |
| TWII | 台湾加权指数 |
| CKLSE | 马来西亚指数 |
| SPTSX | 加拿大S&P/TSX指数 |
| CSX5P | STOXX欧洲50指数 |
| RUT | 罗素2000指数 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | TS指数代码 |
| trade_date | str | Y | 交易日 |
| open | float | Y | 开盘点位 |
| close | float | Y | 收盘点位 |
| high | float | Y | 最高点位 |
| low | float | Y | 最低点位 |
| pre_close | float | Y | 昨日收盘点 |
| change | float | Y | 涨跌点位 |
| pct_chg | float | Y | 涨跌幅 |
| swing | float | Y | 振幅 |
| vol | float | Y | 成交量 （大部分无此项数据） |
| amount | float | N | 成交额 （大部分无此项数据） |

#### 调用示例

```python
pro = ts.pro_api()

#获取富时中国50指数
df = pro.index_global(ts_code='XIN9', start_date='20200201', end_date='20200220')
```

---

### 基金份额 (fund_share)

#### 接口说明

获取公募基金数据，包括基金基础信息、净值、份额、分红、持仓等，覆盖国内所有公募基金。

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api("YOUR_TOKEN")

df = pro.fund_share(ts_code=\'159928.SZ\')
```

#### 权限要求

用户需要至少400积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)。

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 描述 |
|---|---|---|---|
| ts_code | str | N | 基金代码，支持多只基金同时提取，用,分隔 |
| trade_date | str | N | 交易日期（YYYYMMDD） |
| start_date | str | N | 开始日期（YYYYMMDD） |
| end_date | str | N | 结束日期（YYYYMMDD） |

#### 输出参数

| 字段名称 | 字段类型 | 描述 |
|---|---|---|
| ts_code | str | 基金代码 |
| trade_date | str | 交易日期 |
| fd_share | float | 基金份额（万份） |

#### 调用示例

```python
### 获取单只基金的份额
df = pro.fund_share(ts_code=\'159928.SZ\', start_date=\'20180101\', end_date=\'20181018\')

### 获取多只基金的份额
df = pro.fund_share(ts_code=\'159928.SZ,159929.SZ\', start_date=\'20180101\', end_date=\'20181018\')
```

---

### 指数历史分钟 (idx_mins)

#### 接口描述

获取交易所指数分钟数据，支持1min/5min/15min/30min/60min行情，提供Python SDK和 http Restful API两种方式。

**限量**：单次最大8000行数据，可以通过指数代码和时间循环获取，本接口可以提供超过10年历史分钟数据。

**权限**：需单独开权限，正式权限请参阅 [权限说明](https://tushare.pro/document/1?doc_id=108)，可以[在线开通](https://tushare.pro/user/min_subscribe)分钟权限。

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api()

### 获取上证综指000001.SH的历史分钟数据
df = pro.idx_mins(ts_code='000001.SH', freq='1min', start_date='2023-08-25 09:00:00', end_date='2023-08-25 19:00:00')
```

#### 输入参数

| 名称      | 类型     | 是否必选 | 描述                                       |
| :-------- | :------- | :------- | :----------------------------------------- |
| ts_code   | str      | Y        | 指数代码，e.g. 000001.SH                   |
| freq      | str      | Y        | 分钟频度（1min/5min/15min/30min/60min）      |
| start_date| datetime | N        | 开始日期 格式：2023-08-25 09:00:00         |
| end_date  | datetime | N        | 结束时间 格式：2023-08-25 19:00:00         |

**freq参数说明**

| freq  | 说明   |
| :---- | :----- |
| 1min  | 1分钟  |
| 5min  | 5分钟  |
| 15min | 15分钟 |
| 30min | 30分钟 |
| 60min | 60分钟 |

#### 输出参数

| 名称        | 类型  | 描述         |
| :---------- | :---- | :----------- |
| ts_code     | str   | 指数代码     |
| trade_time  | str   | 交易时间     |
| open        | float | 开盘价       |
| close       | float | 收盘价       |
| high        | float | 最高价       |
| low         | float | 最低价       |
| vol         | int   | 成交量(股)   |
| amount      | float | 成交金额（元） |

---

### 指数周线行情 (index_weekly)

#### 接口描述

获取指数周线行情，周线数据从2010年开始。

#### 调用方法

```python
pro.index_weekly(ts_code=\'399300.SZ\', start_date=\'20180101\', end_date=\'20181010\')
```

#### 权限要求

用户需要至少2000积分才可以调取，5000积分以上频次相对较高，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)。

#### 输入参数

| 名称 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | TS代码 |
| trade_date | str | N | 交易日期 (YYYYMMDD) |
| start_date | str | N | 开始日期 (YYYYMMDD) |
| end_date | str | N | 结束日期 (YYYYMMDD) |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | TS代码 |
| trade_date | str | Y | 交易日期 |
| close | float | Y | 收盘点位 |
| open | float | Y | 开盘点位 |
| high | float | Y | 最高点位 |
| low | float | Y | 最低点位 |
| pre_close | float | Y | 昨日收盘点 |
| change | float | Y | 涨跌点 |
| pct_chg | float | Y | 涨跌幅 (%) |
| vol | float | Y | 成交量 (手) |
| amount | float | Y | 成交额 (千元) |

#### 调用示例

```python
import tushare as ts

pro = ts.pro_api()

df = pro.index_weekly(ts_code='399300.SZ', start_date='20180101', end_date='20181010')
```

---

### 指数周线行情 (index_weekly)

#### 接口描述

获取指数周线行情。

#### 调用方法

通过Tushare Pro SDK调用，方法名为`index_weekly`。

#### 权限要求

用户需要至少600积分才可以调取，积分越多频次越高。

#### 输入参数

| 参数名称   | 类型 | 是否必选 | 描述     |
| ---------- | ---- | -------- | -------- |
| ts_code    | str  | N        | TS代码   |
| trade_date | str  | N        | 交易日期 |
| start_date | str  | N        | 开始日期 |
| end_date   | str  | N        | 结束日期 |

#### 输出参数

| 字段名称  | 类型  | 描述         |
| --------- | ----- | ------------ |
| ts_code   | str   | TS指数代码   |
| trade_date| str   | 交易日       |
| close     | float | 收盘点位     |
| open      | float | 开盘点位     |
| high      | float | 最高点位     |
| low       | float | 最低点位     |
| pre_close | float | 昨日收盘点   |
| change    | float | 涨跌点位     |
| pct_chg   | float | 涨跌幅       |
| vol       | float | 成交量（手） |
| amount    | float | 成交额（千元）|

#### 调用示例

```python
import tushare as ts

pro = ts.pro_api('YOUR_TOKEN')

### 获取上证指数周线行情
df = pro.index_weekly(ts_code='000001.SH', start_date='20180101', end_date='20190329', fields='ts_code,trade_date,open,high,low,close,vol,amount')

### 指定交易日期获取数据
df = pro.index_weekly(trade_date='20190329', fields='ts_code,trade_date,open,high,low,close,vol,amount')
```

---

### 指数实时分钟

#### 接口信息

- **接口名称**：指数实时分钟
- **接口标识**：rt_idx_min
- **接口说明**：获取交易所指数实时分钟数据，包括1~60min。单次最大1000行数据，可以通过股票代码提取数据，支持逗号分隔的多个代码同时提取。
- **调用方法**：`pro.rt_idx_min(ts_code='000001.SH', freq='1MIN')`
- **权限要求**：正式权限请参阅Tushare Pro权限说明，可以[在线开通](https://tushare.pro/user/info)权限。

#### 输入参数

| 名称 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| freq | str | Y | 1MIN,5MIN,15MIN,30MIN,60MIN （大写） |
| ts_code | str | Y | 支持单个和多个：000001.SH 或者 000001.SH,399300.SZ |

##### freq参数说明

| freq | 说明 |
| --- | --- |
| 1MIN | 1分钟 |
| 5MIN | 5分钟 |
| 15MIN | 15分钟 |
| 30MIN | 30分钟 |
| 60MIN | 60分钟 |

#### 输出参数

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| ts_code | str | 股票代码 |
| time | None | 交易时间 |
| open | float | 开盘价 |
| close | float | 收盘价 |
| high | float | 最高价 |
| low | float | 最低价 |
| vol | float | 成交量(股） |
| amount | float | 成交额（元） |

#### 调用示例

```python
pro = ts.pro_api()

#获取上证综指000001.SH的实时分钟数据
df = pro.rt_idx_min(ts_code='000001.SH', freq='1MIN')
```

---

### 交易所指数实时日线

#### 接口标识

rt_idx_k

#### 接口说明

获取交易所指数实时日线行情，支持按代码或代码通配符一次性提取全部交易所指数实时日k线行情。

#### 调用方法

通过Tushare Pro SDK调用，例如： `pro.rt_idx_k(...)`

#### 权限要求

本接口是单独开权限的数据，需要单独申请权限。

#### 输入参数

| 参数名称 | 类型 | 是否必填 | 说明 |
|---|---|---|---|
| ts_code | str | Y | 指数代码，支持通配符方式，e.g. 0*.SH、3*.SZ、000001.SH |

#### 输出参数

| 字段名称 | 类型 | 说明 |
|---|---|---|
| ts_code | str | 指数代码 |
| name | str | 指数名称 |
| trade_time | str | 交易时间 |
| close | float | 现价 |
| pre_close | float | 昨收 |
| high | float | 最高价 |
| open | float | 开盘价 |
| low | float | 最低价 |
| vol | float | 成交量 |
| amount | float | 成交金额（元） |

#### 调用示例

```python
#获取单个指数实时行情
df = pro.rt_idx_k(ts_code='000001.SH')

#获取多个指数实时行情,以上证综指和深证A指为例
df = pro.rt_idx_k(ts_code='000001.SH,399107.SZ')

#获取上交所所有指数实时行情，同时指定输出字段
df = pro.rt_idx_k(ts_code='0*.SH', fields='ts_code,name,close,vol')
```

---

### 指数成分和权重 (index_weight)

#### 接口说明

获取各类指数成分和权重，**月度数据** ，建议输入参数里开始日期和结束日分别输入当月第一天和最后一天的日期。

- **接口标识**：`index_weight`
- **调用方法**：`pro.index_weight()`
- **权限要求**：用户需要至少2000积分才可以调取。

#### 输入参数

| 参数名称 | 类型 | 是否必填 | 描述 |
|---|---|---|---|
| index_code | str | Y | 指数代码，来源指数基础信息接口 |
| trade_date | str | N | 交易日期（格式YYYYMMDD，下同） |
| start_date | str | N | 开始日期 |
| end_date | None | N | 结束日期 |

#### 输出参数

| 字段名称 | 类型 | 描述 |
|---|---|---|
| index_code | str | 指数代码 |
| con_code | str | 成分代码 |
| trade_date | str | 交易日期 |
| weight | float | 权重 |

#### 调用示例

```python
pro = ts.pro_api()

#提取沪深300指数2018年9月成分和权重
df = pro.index_weight(index_code='399300.SZ', start_date='20180901', end_date='20180930')
```

---

### 指数技术因子(专业版)

#### 接口信息

- **接口名称**: 指数技术因子(专业版)
- **接口标识**: idx_factor_pro
- **接口说明**: 获取指数每日技术面因子数据，用于跟踪指数当前走势情况，数据由Tushare社区自产，覆盖全历史；输出参数_bfq表示不复权描述中说明了因子的默认传参，如需要特殊参数或者更多因子可以联系管理员评估，指数包括大盘指数 申万行业指数 中信指数
- **调用方法**: `pro.idx_factor_pro()`
- **权限要求**: 5000积分每分钟可以请求30次，8000积分以上每分钟500次

#### 输入参数

| 名称       | 类型 | 是否必填 | 说明                                   |
| ---------- | ---- | -------- | -------------------------------------- |
| ts_code    | str  | N        | 指数代码(大盘指数 申万指数 中信指数) |
| start_date | str  | N        | 开始日期                               |
| end_date   | str  | N        | 结束日期                               |
| trade_date | str  | N        | 交易日期                               |

#### 输出参数

| 名称             | 类型  | 默认显示 | 描述                                                                 |
| ---------------- | ----- | -------- | -------------------------------------------------------------------- |
| ts_code          | str   | Y        | 指数代码                                                             |
| trade_date       | str   | Y        | 交易日期                                                             |
| open             | float | Y        | 开盘价                                                               |
| high             | float | Y        | 最高价                                                               |
| low              | float | Y        | 最低价                                                               |
| close            | float | Y        | 收盘价                                                               |
| pre_close        | float | Y        | 昨收价                                                               |
| change           | float | Y        | 涨跌额                                                               |
| pct_change       | float | Y        | 涨跌幅 （未复权，如果是复权请用 通用行情接口 ）                      |
| vol              | float | Y        | 成交量 （手）                                                        |
| amount           | float | Y        | 成交额 （千元）                                                      |
| asi_bfq          | float | Y        | 振动升降指标-OPEN, CLOSE, HIGH, LOW, M1=26, M2=10                      |
| asit_bfq         | float | Y        | 振动升降指标-OPEN, CLOSE, HIGH, LOW, M1=26, M2=10                      |
| atr_bfq          | float | Y        | 真实波动N日平均值-CLOSE, HIGH, LOW, N=20                               |
| bbi_bfq          | float | Y        | BBI多空指标-CLOSE, M1=3, M2=6, M3=12, M4=20                            |
| bias1_bfq        | float | Y        | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24                                   |
| bias2_bfq        | float | Y        | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24                                   |
| bias3_bfq        | float | Y        | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24                                   |
| boll_lower_bfq   | float | Y        | BOLL指标，布林带-CLOSE, N=20, P=2                                      |
| boll_mid_bfq     | float | Y        | BOLL指标，布林带-CLOSE, N=20, P=2                                      |
| boll_upper_bfq   | float | Y        | BOLL指标，布林带-CLOSE, N=20, P=2                                      |
| brar_ar_bfq      | float | Y        | BRAR情绪指标-OPEN, CLOSE, HIGH, LOW, M1=26                             |
| brar_br_bfq      | float | Y        | BRAR情绪指标-OPEN, CLOSE, HIGH, LOW, M1=26                             |
| cci_bfq          | float | Y        | 顺势指标又叫CCI指标-CLOSE, HIGH, LOW, N=14                             |
| cr_bfq           | float | Y        | CR价格动量指标-CLOSE, HIGH, LOW, N=20                                  |
| dfma_dif_bfq     | float | Y        | 平行线差指标-CLOSE, N1=10, N2=50, M=10                                 |
| dfma_difma_bfq   | float | Y        | 平行线差指标-CLOSE, N1=10, N2=50, M=10                                 |
| dmi_adx_bfq      | float | Y        | 动向指标-CLOSE, HIGH, LOW, M1=14, M2=6                                 |
| dmi_adxr_bfq     | float | Y        | 动向指标-CLOSE, HIGH, LOW, M1=14, M2=6                                 |
| dmi_mdi_bfq      | float | Y        | 动向指标-CLOSE, HIGH, LOW, M1=14, M2=6                                 |
| dmi_pdi_bfq      | float | Y        | 动向指标-CLOSE, HIGH, LOW, M1=14, M2=6                                 |
| downdays         | float | Y        | 连跌天数                                                             |
| updays           | float | Y        | 连涨天数                                                             |
| dpo_bfq          | float | Y        | 区间震荡线-CLOSE, M1=20, M2=10, M3=6                                   |
| madpo_bfq        | float | Y        | 区间震荡线-CLOSE, M1=20, M2=10, M3=6                                   |
| ema_bfq_10       | float | Y        | 指数移动平均-N=10                                                    |
| ema_bfq_20       | float | Y        | 指数移动平均-N=20                                                    |
| ema_bfq_250      | float | Y        | 指数移动平均-N=250                                                   |
| ema_bfq_30       | float | Y        | 指数移动平均-N=30                                                    |
| ema_bfq_5        | float | Y        | 指数移动平均-N=5                                                     |
| ema_bfq_60       | float | Y        | 指数移动平均-N=60                                                    |
| ema_bfq_90       | float | Y        | 指数移动平均-N=90                                                    |
| emv_bfq          | float | Y        | 简易波动指标-HIGH, LOW, VOL, N=14, M=9                                 |
| maemv_bfq        | float | Y        | 简易波动指标-HIGH, LOW, VOL, N=14, M=9                                 |
| expma_12_bfq     | float | Y        | EMA指数平均数指标-CLOSE, N1=12, N2=50                                  |
| expma_50_bfq     | float | Y        | EMA指数平均数指标-CLOSE, N1=12, N2=50                                  |
| kdj_bfq          | float | Y        | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3                              |
| kdj_d_bfq        | float | Y        | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3                              |
| kdj_k_bfq        | float | Y        | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3                              |
| ktn_down_bfq     | float | Y        | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10        |
| ktn_mid_bfq      | float | Y        | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10        |
| ktn_upper_bfq    | float | Y        | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10        |
| lowdays          | float | Y        | LOWRANGE(LOW)表示当前最低价是近多少周期内最低价的最小值              |
| topdays          | float | Y        | TOPRANGE(HIGH)表示当前最高价是近多少周期内最高价的最大值             |
| ma_bfq_10        | float | Y        | 简单移动平均-N=10                                                    |
| ma_bfq_20        | float | Y        | 简单移动平均-N=20                                                    |
| ma_bfq_250       | float | Y        | 简单移动平均-N=250                                                   |
| ma_bfq_30        | float | Y        | 简单移动平均-N=30                                                    |
| ma_bfq_5         | float | Y        | 简单移动平均-N=5                                                     |
| ma_bfq_60        | float | Y        | 简单移动平均-N=60                                                    |
| ma_bfq_90        | float | Y        | 简单移动平均-N=90                                                    |
| macd_bfq         | float | Y        | MACD指标-CLOSE, SHORT=12, LONG=26, M=9                                 |
| macd_dea_bfq     | float | Y        | MACD指标-CLOSE, SHORT=12, LONG=26, M=9                                 |
| macd_dif_bfq     | float | Y        | MACD指标-CLOSE, SHORT=12, LONG=26, M=9                                 |
| mass_bfq         | float | Y        | 梅斯线-HIGH, LOW, N1=9, N2=25, M=6                                     |
| ma_mass_bfq      | float | Y        | 梅斯线-HIGH, LOW, N1=9, N2=25, M=6                                     |
| mfi_bfq          | float | Y        | MFI指标是成交量的RSI指标-CLOSE, HIGH, LOW, VOL, N=14                   |
| mtm_bfq          | float | Y        | 动量指标-CLOSE, N=12, M=6                                              |
| mtmma_bfq        | float | Y        | 动量指标-CLOSE, N=12, M=6                                              |
| obv_bfq          | float | Y        | 能量潮指标-CLOSE, VOL                                                  |
| psy_bfq          | float | Y        | 投资者对股市涨跌产生心理波动的情绪指标-CLOSE, N=12, M=6                |
| psyma_bfq        | float | Y        | 投资者对股市涨跌产生心理波动的情绪指标-CLOSE, N=12, M=6                |
| roc_bfq          | float | Y        | 变动率指标-CLOSE, N=12, M=6                                            |
| maroc_bfq        | float | Y        | 变动率指标-CLOSE, N=12, M=6                                            |
| rsi_bfq_12       | float | Y        | RSI指标-CLOSE, N=12                                                  |
| rsi_bfq_24       | float | Y        | RSI指标-CLOSE, N=24                                                  |
| rsi_bfq_6        | float | Y        | RSI指标-CLOSE, N=6                                                   |
| taq_down_bfq     | float | Y        | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20                                 |
| taq_mid_bfq      | float | Y        | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20                                 |
| taq_up_bfq       | float | Y        | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20                                 |
| trix_bfq         | float | Y        | 三重指数平滑平均线-CLOSE, M1=12, M2=20                                 |
| trma_bfq         | float | Y        | 三重指数平滑平均线-CLOSE, M1=12, M2=20                                 |
| vr_bfq           | float | Y        | VR容量比率-CLOSE, VOL, M1=26                                           |
| wr_bfq           | float | Y        | W&R 威廉指标-CLOSE, HIGH, LOW, N=10, N1=6                              |
| wr1_bfq          | float | Y        | W&R 威廉指标-CLOSE, HIGH, LOW, N=10, N1=6                              |
| xsii_td1_bfq     | float | Y        | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7                                |
| xsii_td2_bfq     | float | Y        | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7                                |
| xsii_td3_bfq     | float | Y        | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7                                |
| xsii_td4_bfq     | float | Y        | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7                                |

#### 调用示例

(页面未提供)

---

### 指数日线行情

#### 接口信息

- **接口名称**: 指数日线行情
- **接口标识**: index_daily
- **接口说明**: 获取指数每日行情，还可以通过bar接口获取。由于服务器压力，目前规则是单次调取最多取8000行记录，可以设置start和end日期补全。指数行情也可以通过通用行情接口获取数据。
- **调用方法**: `pro.index_daily()`
- **权限要求**: 用户累积2000积分可调取，5000积分以上频次相对较高。本接口不包括申万行情数据，申万等行业指数行情需5000积分以上，具体请参阅积分获取办法。

#### 输入参数

| 名称      | 类型 | 是否必填 | 描述                               |
| --------- | ---- | -------- | ---------------------------------- |
| ts_code   | str  | Y        | 指数代码，来源指数基础信息接口     |
| trade_date| str  | N        | 交易日期 （日期格式：YYYYMMDD）    |
| start_date| str  | N        | 开始日期                           |
| end_date  | str  | N        | 结束日期                           |

#### 输出参数

| 名称      | 类型  | 描述         |
| --------- | ----- | ------------ |
| ts_code   | str   | TS指数代码   |
| trade_date| str   | 交易日       |
| close     | float | 收盘点位     |
| open      | float | 开盘点位     |
| high      | float | 最高点位     |
| low       | float | 最低点位     |
| pre_close | float | 昨日收盘点   |
| change    | float | 涨跌点       |
| pct_chg   | float | 涨跌幅（%）  |
| vol       | float | 成交量（手） |
| amount    | float | 成交额（千元）|

#### 调用示例

```python
pro = ts.pro_api()

### 获取指数日线行情
df = pro.index_daily(ts_code='399300.SZ')

### 或者按日期取
df = pro.index_daily(ts_code='399300.SZ', start_date='20180101', end_date='20181010')
```

---

### 指数月线行情

#### 接口标识

index_monthly

#### 接口说明

获取指数月线行情,每月更新一次。

#### 调用方法

```python
pro = ts.pro_api()
df = pro.index_monthly(ts_code='000001.SH', start_date='20180101', end_date='20190330', fields='ts_code,trade_date,open,high,low,close,vol,amount')
```

#### 权限要求

用户需要至少600积分才可以调取，积分越多频次越高。

#### 输入参数

| 名称 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| ts_code | str | N | TS代码 |
| trade_date | str | N | 交易日期 |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| ts_code | str | TS指数代码 |
| trade_date | str | 交易日 |
| close | float | 收盘点位 |
| open | float | 开盘点位 |
| high | float | 最高点位 |
| low | float | 最低点位 |
| pre_close | float | 昨日收盘点 |
| change | float | 涨跌点位 |
| pct_chg | float | 涨跌幅 |
| vol | float | 成交量（手） |
| amount | float | 成交额（千元） |

#### 调用示例

```python
pro = ts.pro_api()

#示例1
df = pro.index_monthly(ts_code='000001.SH', start_date='20180101', end_date='20190330', fields='ts_code,trade_date,open,high,low,close,vol,amount')

#示例2
df = pro.index_monthly(trade_date='20190329', fields='ts_code,trade_date,open,high,low,close,vol,amount')
```

---

### 沪深市场每日交易统计 (daily_info)

#### 接口描述

获取交易所股票交易统计，包括各板块明细。

**接口名称**：`daily_info`
**调用方法**：`pro.daily_info()`
**权限要求**：用户积600积分可调取， 频次有限制，积分越高每分钟调取频次越高，5000积分以上频次相对较高。

#### 输入参数

| 参数名称 | 类型 | 是否必选 | 描述 |
| --- | --- | --- | --- |
| trade_date | str | N | 交易日期（YYYYMMDD格式，下同） |
| ts_code | str | N | 板块代码（请参阅下方列表） |
| exchange | str | N | 股票市场（SH上交所 SZ深交所） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |
| fields | str | N | 指定提取字段 |

##### 板块代码

| 板块代码（TS_CODE） | 板块名称（TS_NAME） | 数据开始日期 |
| --- | --- | --- |
| SZ_MARKET | 深圳市场 | 20041231 |
| SZ_MAIN | 深圳主板 | 20081231 |
| SZ_A | 深圳A股 | 20080103 |
| SZ_B | 深圳B股 | 20080103 |
| SZ_GEM | 创业板 | 20091030 |
| SZ_SME | 中小企业板 | 20040602 |
| SZ_FUND | 深圳基金市场 | 20080103 |
| SZ_FUND_ETF | 深圳基金ETF | 20080103 |
| SZ_FUND_LOF | 深圳基金LOF | 20080103 |
| SZ_FUND_CEF | 深圳封闭基金 | 20080103 |
| SZ_FUND_SF | 深圳分级基金 | 20080103 |
| SZ_BOND | 深圳债券 | 20080103 |
| SZ_BOND_CN | 深圳债券现券 | 20080103 |
| SZ_BOND_REP | 深圳债券回购 | 20080103 |
| SZ_BOND_ABS | 深圳债券ABS | 20080103 |
| SZ_BOND_GOV | 深圳国债 | 20080103 |
| SZ_BOND_ENT | 深圳企业债 | 20080103 |
| SZ_BOND_COR | 深圳公司债 | 20080103 |
| SZ_BOND_CB | 深圳可转债 | 20080103 |
| SZ_WR | 深圳权证 | 20080103 |
| ---- | ---- | --- |
| SH_MARKET | 上海市场 | 20190102 |
| SH_A | 上海A股 | 19910102 |
| SH_B | 上海B股 | 19920221 |
| SH_STAR | 科创板 | 20190722 |
| SH_REP | 股票回购 | 20190102 |
| SH_FUND | 上海基金市场 | 19901219 |
| SH_FUND_ETF | 上海基金ETF | 19901219 |
| SH_FUND_LOF | 上海基金LOF | 19901219 |
| SH_FUND_REP | 上海基金回购 | 19901219 |
| SH_FUND_CEF | 上海封闭式基金 | 19901219 |
| SH_FUND_METF | 上海交易型货币基金 | 19901219 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| trade_date | str | Y | 交易日期 |
| ts_code | str | Y | 市场代码 |
| ts_name | str | Y | 市场名称 |
| com_count | int | Y | 挂牌数 |
| total_share | float | Y | 总股本（亿股） |
| float_share | float | Y | 流通股本（亿股） |
| total_mv | float | Y | 总市值（亿元） |
| float_mv | float | Y | 流通市值（亿元） |
| amount | float | Y | 交易金额（亿元） |
| vol | float | Y | 成交量（亿股） |
| trans_count | int | Y | 成交笔数（万笔） |
| pe | float | Y | 平均市盈率 |
| tr | float | Y | 换手率（％），注：深交所暂无此列 |
| exchange | str | Y | 交易所（SH上交所 SZ深交所） |

#### 调用示例

```python
#获取深圳市场20200320各板块交易数据
df = pro.daily_info(trade_date='20200320', exchange='SZ')

#获取深圳和上海市场20200320各板块交易指定字段的数据
df = pro.daily_info(trade_date='20200320', exchange='SZ,SH', fields='trade_date,ts_name,pe')
```

---

### 深圳市场每日交易概况 (sz_daily_info)

#### 接口说明

- **接口标识**：sz_daily_info
- **接口名称**：深圳市场每日交易概况
- **功能描述**：获取深圳市场每日交易概况
- **调用方法**：`pro.sz_daily_info()`
- **限量**：单次最大2000，可循环获取，总量不限制
- **权限要求**：用户积2000积分可调取， 频次有限制，积分越高每分钟调取频次越高，5000积分以上频次相对较高。

#### 输入参数

| 参数名称 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| trade_date | str | N | 交易日期（YYYYMMDD格式） |
| ts_code | str | N | 板块代码 |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

##### ts_code主要包括：

| 板块代码（TS_CODE） | 板块说明 | 数据开始日期 |
| --- | --- | --- |
| 股票 | 深圳市场股票总和 | 20080102 |
| 主板A股 | 深圳主板A股情况 | 20080102 |
| 主板B股 | 深圳主板B股情况 | 20080102 |
| 创业板A股 | 深圳创业板情况 | 20080102 |
| 基金 | 深圳市场基金总和 | 20080102 |
| ETF | 深圳ETF交易情况 | 20080102 |
| LOF | 深圳LOF交易情况 | 20080102 |
| 封闭式基金 | 深圳封闭式基金交易情况 | 20080102 |
| 基础设施基金 | 深圳RETIS基金交易情况 | 20210621 |
| 债券 | 深圳债券市场总和 | 20080102 |
| 债券现券 | 深圳现券交易情况 | 20080102 |
| 债券回购 | 深圳债券回购交易情况 | 20080102 |
| ABS | 深圳ABS交易情况 | 20080102 |
| 期权 | 深圳期权总和 | 20080102 |

#### 输出参数

| 字段名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| trade_date | str | Y | 交易日期 |
| ts_code | str | Y | 市场类型 |
| count | int | Y | 股票个数 |
| amount | float | Y | 成交金额 |
| vol | None | Y | 成交量 |
| total_share | float | Y | 总股本 |
| total_mv | float | Y | 总市值 |
| float_share | float | Y | 流通股票 |
| float_mv | float | Y | 流通市值 |

#### 调用示例

```python
### 获取深圳市场20200320交易数据
df = pro.sz_daily_info(trade_date='20200320')

### 获取深圳市场交易情况
df = pro.sz_daily_info(trade_date='20200320', ts_code='股票')
```

---

### 申万实时行情

#### 接口信息

- **接口名称**：申万实时行情
- **接口标识**：`rt_sw_k`
- **接口说明**：获取申万行业指数的最新截面数据
- **调用方法**：`pro.rt_sw_k()`
- **权限要求**：本接口是单独开权限的数据，单独申请权限请参考权限列表

#### 输入参数

| 名称    | 类型 | 是否必填 | 说明                                                                   |
| :------ | :--- | :------- | :--------------------------------------------------------------------- |
| ts_code | str  | N        | 指数代码，如: 801005.SI；可以是逗号隔开的多个，如: 801005.SI,801001.SI |

#### 输出参数

| 名称       | 类型  | 默认显示 | 说明         |
| :--------- | :---- | :------- | :----------- |
| ts_code    | str   | Y        | 指数代码     |
| name       | str   | Y        | 指数名称     |
| trade_time | str   | Y        | 交易时间     |
| close      | float | Y        | 现价         |
| pre_close  | float | Y        | 昨收         |
| high       | float | Y        | 最高价       |
| open       | float | Y        | 开盘价       |
| low        | float | Y        | 最低价       |
| vol        | float | Y        | 成交量（股） |
| amount     | float | Y        | 成交金额（元） |
| pct_change | float | Y        | 增长率       |

#### 调用示例

```python
pro = ts.pro_api()

### 一次性提取全部申万指数实时数据
df = pro.rt_sw_k()

### 按ts_code提取行情数据，例如提取801053.SI(贵金属) 实时行情
df = pro.rt_sw_k(ts_code='801053.SI')
```

---

### 申万行业分类 (index_classify)

#### 接口描述

获取申万行业分类，可以获取申万2014年版本（28个一级分类，104个二级分类，227个三级分类）和2021年本版（31个一级分类，134个二级分类，346个三级分类）列表信息。

#### 调用方法

```python
### 获取申万一级行业列表
df = pro.index_classify(level='L1', src='SW2021')

### 获取申万二级行业列表
df = pro.index_classify(level='L2', src='SW2021')

### 获取申万三级级行业列表
df = pro.index_classify(level='L3', src='SW2021')
```

#### 权限要求

用户需2000积分可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)。

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| index_code | str | N | 指数代码 |
| level | str | N | 行业分级（L1/L2/L3） |
| parent_code | str | N | 父级代码（一级为0） |
| src | str | N | 指数来源（SW2014：申万2014年版本，SW2021：申万2021年版本） |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| index_code | str | Y | 指数代码 |
| industry_name | str | Y | 行业名称 |
| parent_code | str | Y | 父级代码 |
| level | str | Y | 行业层级 |
| industry_code | str | Y | 行业代码 |
| is_pub | str | Y | 是否发布了指数 |
| src | str | N | 行业分类（SW申万） |

#### 申万行业指数分类标准2021版

注：指数成分股小于5条该指数行情不发布

| 行业代码 | 指数代码 | 一级行业 | 二级行业 | 三级行业 | 指数类别 | 是否发布 | 变动原因 | 成分股数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 110000 | 801010 | 农林牧渔 | | | 一级行业 | 1 | 2021保留 | 100 |
| 110100 | 801016 | 农林牧渔 | 种植业 | | 二级行业 | 1 | 2021保留 | 20 |
| 110101 | 850111 | 农林牧渔 | 种植业 | 种子 | 三级行业 | 1 | 2021改名 | 8 |
| 110102 | 850112 | 农林牧渔 | 种植业 | 粮食种植 | 三级行业 | 0 | 2021保留 | 2 |
| 110103 | 850113 | 农林牧渔 | 种植业 | 其他种植业 | 三级行业 | 1 | 2021保留 | 6 |
| 110104 | 850114 | 农林牧渔 | 种植业 | 食用菌 | 三级行业 | 0 | 2021新增 | 4 |
| 110200 | 801015 | 农林牧渔 | 渔业 | | 二级行业 | 1 | 2021保留 | 11 |
| 110201 | 850121 | 农林牧渔 | 渔业 | 海洋捕捞 | 三级行业 | 0 | 2021保留 | 2 |
| 110202 | 850122 | 农林牧渔 | 渔业 | 水产养殖 | 三级行业 | 1 | 2021保留 | 9 |

... (由于内容过长，此处省略，完整内容已写入文件)

---

### 申万行业成分构成(分级) (index_member_all)

#### 接口说明

按三级分类提取申万行业成分，可提供某个分类的所有成分，也可按股票代码提取所属分类，参数灵活。

- **接口标识：** `index_member_all`
- **调用方法：** `pro.index_member_all()`
- **权限要求：** 用户需2000积分可调取
- **限量：** 单次最大2000行，总量不限制

#### 输入参数

| 名称      | 类型 | 必选 | 描述             |
| --------- | ---- | ---- | ---------------- |
| l1_code   | str  | N    | 一级行业代码     |
| l2_code   | str  | N    | 二级行业代码     |
| l3_code   | str  | N    | 三级行业代码     |
| ts_code   | str  | N    | 股票代码         |
| is_new    | str  | N    | 是否最新（默认为“Y是”） |

#### 输出参数

| 名称      | 类型 | 默认显示 | 描述         |
| --------- | ---- | -------- | ------------ |
| l1_code   | str  | Y        | 一级行业代码 |
| l1_name   | str  | Y        | 一级行业名称 |
| l2_code   | str  | Y        | 二级行业代码 |
| l2_name   | str  | Y        | 二级行业名称 |
| l3_code   | str  | Y        | 三级行业代码 |
| l3_name   | str  | Y        | 三级行业名称 |
| ts_code   | str  | Y        | 成分股票代码 |
| name      | str  | Y        | 成分股票名称 |
| in_date   | str  | Y        | 纳入日期     |
| out_date  | str  | Y        | 剔除日期     |
| is_new    | str  | Y        | 是否最新Y是N否 |

#### 调用示例

```python
### 获取黄金分类的成份股
df = pro.index_member_all(l3_code='850531.SI')

### 获取000001.SZ所属行业
df = pro.index_member_all(ts_code='000001.SZ')
```

---

### 申万行业日线行情 (sw_daily)

#### 接口说明

获取申万行业日线行情（默认是申万2021版行情）

#### 调用方法

```python
pro.sw_daily(ts_code, trade_date, start_date, end_date)
```

#### 权限要求

5000积分可调取，单次最大4000行数据，可通过指数代码和日期参数循环提取。

#### 输入参数

| 参数名称   | 参数类型 | 是否必填 | 描述     |
| ---------- | -------- | -------- | -------- |
| ts_code    | str      | N        | 行业代码 |
| trade_date | str      | N        | 交易日期 |
| start_date | str      | N        | 开始日期 |
| end_date   | str      | N        | 结束日期 |

#### 输出参数

| 字段名称   | 字段类型 | 描述           |
| ---------- | -------- | -------------- |
| ts_code    | str      | 指数代码       |
| trade_date | str      | 交易日期       |
| name       | str      | 指数名称       |
| open       | float    | 开盘点位       |
| low        | float    | 最低点位       |
| high       | float    | 最高点位       |
| close      | float    | 收盘点位       |
| change     | float    | 涨跌点位       |
| pct_change | float    | 涨跌幅         |
| vol        | float    | 成交量（万股） |
| amount     | float    | 成交额（万元） |
| pe         | float    | 市盈率         |
| pb         | float    | 市净率         |
| float_mv   | float    | 流通市值（万元）|
| total_mv   | float    | 总市值（万元） |

#### 调用示例

```python
pro = ts.pro_api('your token')

#获取20230705当日所有申万行业指数的ts_code,name,open,close,vol,pe,pb数据
df = pro.sw_daily(trade_date='20230705', fields='ts_code,name,open,close,vol,pe,pb')
```

---


# 4. 债券专题

## 债券专题

### 债券回购日行情

#### 接口信息

- **接口名称**: 债券回购日行情
- **接口标识**: repo_daily
- **接口说明**: 获取债券回购日行情数据，包括成交价格、成交金额等。
- **调用方法**: `pro.repo_daily()`
- **权限要求**: 用户需要累积2000积分才可以调取。

#### 输入参数

| 参数名称   | 类型 | 是否必填 | 描述                               |
| ---------- | ---- | -------- | ---------------------------------- |
| ts_code    | str  | N        | TS代码                             |
| trade_date | str  | N        | 交易日期 (YYYYMMDD格式，下同)      |
| start_date | str  | N        | 开始日期                           |
| end_date   | str  | N        | 结束日期                           |

#### 输出参数

| 字段名称      | 类型  | 默认显示 | 描述             |
| ------------- | ----- | -------- | ---------------- |
| ts_code       | str   | Y        | TS代码           |
| trade_date    | str   | Y        | 交易日期         |
| repo_maturity | str   | Y        | 期限品种         |
| pre_close     | float | Y        | 前收盘(%)        |
| open          | float | Y        | 开盘价(%)        |
| high          | float | Y        | 最高价(%)        |
| low           | float | Y        | 最低价(%)        |
| close         | float | Y        | 收盘价(%)        |
| weight        | float | Y        | 加权价(%)        |
| weight_r      | float | Y        | 加权价(利率债)(%) |
| amount        | float | Y        | 成交金额(万元)   |
| num           | int   | Y        | 成交笔数(笔)     |

#### 调用示例

```python
import tushare as ts

### 初始化pro接口
pro = ts.pro_api('YOUR_TOKEN')

### 获取2020年8月4日债券回购日行情
df = pro.repo_daily(trade_date='20200804')

print(df)
```

---

### 债券大宗交易 (bond_blk)

#### 接口说明

获取沪深交易所债券大宗交易数据。

#### 调用方法

```python
pro.bond_blk(**kwargs)
```

#### 权限要求

用户满5000积分有数据权限，单次最大1000条，可根据日期循环提取，总量不限制。

#### 输入参数

| 名称       | 类型 | 是否必填 | 描述                               |
| ---------- | ---- | -------- | ---------------------------------- |
| ts_code    | str  | N        | 债券代码                           |
| trade_date | str  | N        | 交易日期（YYYYMMDD格式，下同）     |
| start_date | str  | N        | 开始日期                           |
| end_date   | str  | N        | 结束日期                           |

#### 输出参数

| 名称       | 类型  | 默认显示 | 描述                                   |
| ---------- | ----- | -------- | -------------------------------------- |
| trade_date | str   | Y        | 交易日期                               |
| ts_code    | str   | Y        | 债券代码                               |
| name       | str   | Y        | 债券名称                               |
| price      | float | Y        | 成交价（元）                           |
| vol        | float | Y        | 累计成交数量（万股/万份/万张/万手）    |
| amount     | float | Y        | 累计成交金额（万元）                   |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.bond_blk(start_date='20210701', end_date='20210930')
```

---

### 可转债发行 (cb_issue)

#### 接口描述

获取可转债发行数据。

**调用方法**

```python
pro.cb_issue(**kwargs)
```

**权限要求**

用户需要至少2000积分才可以调取，5000积分以上频次相对较高，积分越多权限越大。

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | TS代码 |
| ann_date | str | N | 发行公告日 |
| start_date | str | N | 公告开始日期 |
| end_date | str | N | 公告结束日期 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 转债代码 |
| ann_date | str | Y | 发行公告日 |
| res_ann_date | str | Y | 发行结果公告日 |
| plan_issue_size | float | Y | 计划发行总额（元） |
| issue_size | float | Y | 发行总额（元） |
| issue_price | float | Y | 发行价格 |
| issue_type | str | Y | 发行方式 |
| issue_cost | float | N | 发行费用（元） |
| onl_code | str | Y | 网上申购代码 |
| onl_name | str | Y | 网上申购简称 |
| onl_date | str | Y | 网上发行日期 |
| onl_size | float | Y | 网上发行总额（张） |
| onl_pch_vol | float | Y | 网上发行有效申购数量（张） |
| onl_pch_num | int | Y | 网上发行有效申购户数 |
| onl_pch_excess | float | Y | 网上发行超额认购倍数 |
| onl_winning_rate | float | N | 网上发行中签率（%） |
| shd_ration_code | str | Y | 老股东配售代码 |
| shd_ration_name | str | Y | 老股东配售简称 |
| shd_ration_date | str | Y | 老股东配售日 |
| shd_ration_record_date | str | Y | 老股东配售股权登记日 |
| shd_ration_pay_date | str | Y | 老股东配售缴款日 |
| shd_ration_price | float | Y | 老股东配售价格 |
| shd_ration_ratio | float | Y | 老股东配售比例 |
| shd_ration_size | float | Y | 老股东配售数量（张） |
| shd_ration_vol | float | N | 老股东配售有效申购数量（张） |
| shd_ration_num | int | N | 老股东配售有效申购户数 |
| shd_ration_excess | float | N | 老股东配售超额认购倍数 |
| offl_size | float | Y | 网下发行总额（张） |
| offl_deposit | float | N | 网下发行定金比例（%） |
| offl_pch_vol | float | N | 网下发行有效申购数量（张） |
| offl_pch_num | int | N | 网下发行有效申购户数 |
| offl_pch_excess | float | N | 网下发行超额认购倍数 |
| offl_winning_rate | float | N | 网下发行中签率 |
| lead_underwriter | str | N | 主承销商 |
| lead_underwriter_vol | float | N | 主承销商包销数量（张） |

#### 调用示例

```python
import tushare as ts

pro = ts.pro_api('YOUR_TOKEN')

### 获取可转债发行数据
df = pro.cb_issue(ann_date='20190612')

### 获取可转债发行数据，自定义字段
df = pro.cb_issue(fields='ts_code,ann_date,issue_size')
```

---

### 可转债基本信息 (cb_basic)

#### 接口描述

获取可转债基本信息。

**接口名称**：`cb_basic`
**限量**：单次最大2000，总量不限制
**权限**：用户需要至少2000积分才可以调取，但有流量控制，5000积分以上频次相对较高，积分越多权限越大。

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api('your token')

### 获取单只可转债基础信息
df = pro.cb_basic(ts_code='125002.SZ')

### 获取多只可转债基础信息
df = pro.cb_basic(ts_code='125002.SZ,125009.SZ')

### 获取某个上市日期的可转债基础信息
df = pro.cb_basic(list_date='20020628')
```

#### 输入参数

| 参数名称 | 类型 | 是否必选 | 描述 |
| :--- | :--- | :--- | :--- |
| ts_code | str | N | 转债代码 |
| list_date | str | N | 上市日期 |
| exchange | str | N | 上市交易所 |

#### 输出参数

| 字段名称 | 类型 | 默认显示 | 描述 |
| :--- | :--- | :--- | :--- |
| ts_code | str | Y | 转债代码 |
| bond_full_name | str | Y | 转债名称 |
| bond_short_name | str | Y | 转债简称 |
| cb_code | str | Y | 转股申报代码 |
| stk_code | str | Y | 正股代码 |
| stk_short_name | str | Y | 正股简称 |
| maturity | float | Y | 发行期限（年） |
| par | float | Y | 面值 |
| issue_price | float | Y | 发行价格 |
| issue_size | float | Y | 发行总额（元） |
| remain_size | float | Y | 债券余额（元） |
| value_date | str | Y | 起息日期 |
| maturity_date | str | Y | 到期日期 |
| rate_type | str | Y | 利率类型 |
| coupon_rate | float | Y | 票面利率（%） |
| add_rate | float | Y | 补偿利率（%） |
| pay_per_year | int | Y | 年付息次数 |
| list_date | str | Y | 上市日期 |
| delist_date | str | Y | 摘牌日 |
| exchange | str | Y | 上市交易所 |
| conv_start_date | str | Y | 转股起始日 |
| conv_end_date | str | Y | 转股截止日 |
| conv_stop_date | str | Y | 停止转股日(提前到期) |
| first_conv_price | float | Y | 初始转股价 |
| conv_price | float | Y | 最新转股价 |
| rate_clause | str | Y | 利率说明 |
| put_clause | str | N | 赎回条款 |
| maturity_put_price | str | N | 到期赎回价格(含税) |
| call_clause | str | N | 回售条款 |
| reset_clause | str | N | 特别向下修正条款 |
| conv_clause | str | N | 转股条款 |
| guarantor | str | N | 担保人 |
| guarantee_type | str | N | 担保方式 |
| issue_rating | str | N | 发行信用等级 |
| newest_rating | str | N | 最新信用等级 |
| rating_comp | str | N | 最新评级机构 |

#### 调用示例

```python
pro = ts.pro_api(your token)
#获取可转债基础信息列表
df = pro.cb_basic(fields="ts_code,bond_short_name,stk_code,stk_short_name,list_date,delist_date")
```

##### 数据示例

```
    ts_code bond_short_name   stk_code stk_short_name   list_date delist_date
0    125002.SZ            万科转债  000002.SZ            万科Ａ  2002-06-28  2004-04-30
1    125009.SZ            宝安转券  000009.SZ           中国宝安  1993-02-10  1996-01-01
2    125069.SZ            侨城转债  000069.SZ           华侨城Ａ  2004-01-16  2005-04-29
3    125301.SZ            丝绸转债  000301.SZ           东方盛虹  1998-09-15  2003-08-28
4    126301.SZ            丝绸转2  000301.SZ           东方盛虹  2002-09-24  2006-09-18
```

---

### 可转债技术因子(专业版) (cb_factor_pro)

#### 接口说明

获取可转债每日技术面因子数据，用于跟踪可转债当前走势情况，数据由Tushare社区自产，覆盖全历史；输出参数_bfq表示不复权，_qfq表示前复权 _hfq表示后复权，描述中说明了因子的默认传参，如需要特殊参数或者更多因子可以联系管理员评估。

#### 调用方法

```python
pro.cb_factor_pro(ts_code='113632.SH')
```

#### 权限要求

5000积分每分钟可以请求30次，8000积分以上每分钟500次。

#### 输入参数

| 名称       | 类型 | 是否必填 | 说明     |
| ---------- | ---- | -------- | -------- |
| ts_code    | str  | N        | 可转债代码 |
| start_date | str  | N        | 开始日期   |
| end_date   | str  | N        | 结束日期   |
| trade_date | str  | N        | 交易日期   |

#### 输出参数

| 名称             | 类型  | 默认显示 | 说明                                                                 |
| ---------------- | ----- | -------- | -------------------------------------------------------------------- |
| ts_code          | str   | Y        | 转债代码                                                             |
| trade_date       | str   | Y        | 交易日期                                                             |
| open             | float | Y        | 开盘价                                                               |
| high             | float | Y        | 最高价                                                               |
| low              | float | Y        | 最低价                                                               |
| close            | float | Y        | 收盘价                                                               |
| pre_close        | float | Y        | 昨收价                                                               |
| change           | float | Y        | 涨跌额                                                               |
| pct_change       | float | Y        | 涨跌幅 （未复权，如果是复权请用 通用行情接口 ）                     |
| vol              | float | Y        | 成交量 （手）                                                        |
| amount           | float | Y        | 成交金额(万元)                                                       |
| asi_bfq          | float | Y        | 振动升降指标-OPEN, CLOSE, HIGH, LOW, M1=26, M2=10                      |
| asit_bfq         | float | Y        | 振动升降指标-OPEN, CLOSE, HIGH, LOW, M1=26, M2=10                      |
| atr_bfq          | float | Y        | 真实波动N日平均值-CLOSE, HIGH, LOW, N=20                               |
| bbi_bfq          | float | Y        | BBI多空指标-CLOSE, M1=3, M2=6, M3=12, M4=20                            |
| bias1_bfq        | float | Y        | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24                                   |
| bias2_bfq        | float | Y        | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24                                   |
| bias3_bfq        | float | Y        | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24                                   |
| boll_lower_bfq   | float | Y        | BOLL指标，布林带-CLOSE, N=20, P=2                                      |
| boll_mid_bfq     | float | Y        | BOLL指标，布林带-CLOSE, N=20, P=2                                      |
| boll_upper_bfq   | float | Y        | BOLL指标，布林带-CLOSE, N=20, P=2                                      |
| brar_ar_bfq      | float | Y        | BRAR情绪指标-OPEN, CLOSE, HIGH, LOW, M1=26                             |
| brar_br_bfq      | float | Y        | BRAR情绪指标-OPEN, CLOSE, HIGH, LOW, M1=26                             |
| cci_bfq          | float | Y        | 顺势指标又叫CCI指标-CLOSE, HIGH, LOW, N=14                             |
| cr_bfq           | float | Y        | CR价格动量指标-CLOSE, HIGH, LOW, N=20                                  |
| dfma_dif_bfq     | float | Y        | 平行线差指标-CLOSE, N1=10, N2=50, M=10                                 |
| dfma_difma_bfq   | float | Y        | 平行线差指标-CLOSE, N1=10, N2=50, M=10                                 |
| dmi_adx_bfq      | float | Y        | 动向指标-CLOSE, HIGH, LOW, M1=14, M2=6                                 |
| dmi_adxr_bfq     | float | Y        | 动向指标-CLOSE, HIGH, LOW, M1=14, M2=6                                 |
| dmi_mdi_bfq      | float | Y        | 动向指标-CLOSE, HIGH, LOW, M1=14, M2=6                                 |
| dmi_pdi_bfq      | float | Y        | 动向指标-CLOSE, HIGH, LOW, M1=14, M2=6                                 |
| downdays         | float | Y        | 连跌天数                                                             |
| updays           | float | Y        | 连涨天数                                                             |
| dpo_bfq          | float | Y        | 区间震荡线-CLOSE, M1=20, M2=10, M3=6                                   |
| madpo_bfq        | float | Y        | 区间震荡线-CLOSE, M1=20, M2=10, M3=6                                   |
| ema_bfq_10       | float | Y        | 指数移动平均-N=10                                                    |
| ema_bfq_20       | float | Y        | 指数移动平均-N=20                                                    |
| ema_bfq_250      | float | Y        | 指数移动平均-N=250                                                   |
| ema_bfq_30       | float | Y        | 指数移动平均-N=30                                                    |
| ema_bfq_5        | float | Y        | 指数移动平均-N=5                                                     |
| ema_bfq_60       | float | Y        | 指数移动平均-N=60                                                    |
| ema_bfq_90       | float | Y        | 指数移动平均-N=90                                                    |
| emv_bfq          | float | Y        | 简易波动指标-HIGH, LOW, VOL, N=14, M=9                                 |
| maemv_bfq        | float | Y        | 简易波动指标-HIGH, LOW, VOL, N=14, M=9                                 |
| expma_12_bfq     | float | Y        | EMA指数平均数指标-CLOSE, N1=12, N2=50                                  |
| expma_50_bfq     | float | Y        | EMA指数平均数指标-CLOSE, N1=12, N2=50                                  |
| kdj_bfq          | float | Y        | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3                              |
| kdj_d_bfq        | float | Y        | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3                              |
| kdj_k_bfq        | float | Y        | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3                              |
| ktn_down_bfq     | float | Y        | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10        |
| ktn_mid_bfq      | float | Y        | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10        |
| ktn_upper_bfq    | float | Y        | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10        |
| lowdays          | float | Y        | LOWRANGE(LOW)表示当前最低价是近多少周期内最低价的最小值              |
| topdays          | float | Y        | TOPRANGE(HIGH)表示当前最高价是近多少周期内最高价的最大值             |
| ma_bfq_10        | float | Y        | 简单移动平均-N=10                                                    |
| ma_bfq_20        | float | Y        | 简单移动平均-N=20                                                    |
| ma_bfq_250       | float | Y        | 简单移动平均-N=250                                                   |
| ma_bfq_30        | float | Y        | 简单移动平均-N=30                                                    |
| ma_bfq_5         | float | Y        | 简单移动平均-N=5                                                     |
| ma_bfq_60        | float | Y        | 简单移动平均-N=60                                                    |
| ma_bfq_90        | float | Y        | 简单移动平均-N=90                                                    |
| macd_bfq         | float | Y        | MACD指标-CLOSE, SHORT=12, LONG=26, M=9                                 |
| macd_dea_bfq     | float | Y        | MACD指标-CLOSE, SHORT=12, LONG=26, M=9                                 |
| macd_dif_bfq     | float | Y        | MACD指标-CLOSE, SHORT=12, LONG=26, M=9                                 |
| mass_bfq         | float | Y        | 梅斯线-HIGH, LOW, N1=9, N2=25, M=6                                     |
| ma_mass_bfq      | float | Y        | 梅斯线-HIGH, LOW, N1=9, N2=25, M=6                                     |
| mfi_bfq          | float | Y        | MFI指标是成交量的RSI指标-CLOSE, HIGH, LOW, VOL, N=14                   |
| mtm_bfq          | float | Y        | 动量指标-CLOSE, N=12, M=6                                              |
| mtmma_bfq        | float | Y        | 动量指标-CLOSE, N=12, M=6                                              |
| obv_bfq          | float | Y        | 能量潮指标-CLOSE, VOL                                                  |
| psy_bfq          | float | Y        | 投资者对股市涨跌产生心理波动的情绪指标-CLOSE, N=12, M=6                |
| psyma_bfq        | float | Y        | 投资者对股市涨跌产生心理波动的情绪指标-CLOSE, N=12, M=6                |
| roc_bfq          | float | Y        | 变动率指标-CLOSE, N=12, M=6                                            |
| maroc_bfq        | float | Y        | 变动率指标-CLOSE, N=12, M=6                                            |
| rsi_bfq_12       | float | Y        | RSI指标-CLOSE, N=12                                                  |
| rsi_bfq_24       | float | Y        | RSI指标-CLOSE, N=24                                                  |
| rsi_bfq_6        | float | Y        | RSI指标-CLOSE, N=6                                                   |
| taq_down_bfq     | float | Y        | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20                                 |
| taq_mid_bfq      | float | Y        | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20                                 |
| taq_up_bfq       | float | Y        | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20                                 |
| trix_bfq         | float | Y        | 三重指数平滑平均线-CLOSE, M1=12, M2=20                                 |
| trma_bfq         | float | Y        | 三重指数平滑平均线-CLOSE, M1=12, M2=20                                 |
| vr_bfq           | float | Y        | VR容量比率-CLOSE, VOL, M1=26                                           |
| wr_bfq           | float | Y        | W&R 威廉指标-CLOSE, HIGH, LOW, N=10, N1=6                              |
| wr1_bfq          | float | Y        | W&R 威廉指标-CLOSE, HIGH, LOW, N=10, N1=6                              |
| xsii_td1_bfq     | float | Y        | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7                                |
| xsii_td2_bfq     | float | Y        | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7                                |
| xsii_td3_bfq     | float | Y        | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7                                |
| xsii_td4_bfq     | float | Y        | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7                                |

#### 调用示例

```python
pro = ts.pro_api()

#获取鹤21转债113632.SH所以有历史因子数据
df = pro.cb_factor_pro(ts_code='113632.SH')

#获取交易日期为20250724当天所有可转债的因子数据
df = pro.hk_income(trade_date='20250724')
```

---

### 可转债票面利率 (cb_rate)

#### 接口说明

获取可转债票面利率

#### 调用方法

```python
pro.cb_rate(ts_code='...', fields='...')
```

#### 权限要求

用户需要至少5000积分才可以调取。

#### 输入参数

| 名称      | 类型 | 必选 | 描述             |
| --------- | ---- | ---- | ---------------- |
| ts_code   | str  | Y    | 转债代码，支持多值输入 |

#### 输出参数

| 名称            | 类型  | 默认显示 | 描述          |
| --------------- | ----- | -------- | ------------- |
| ts_code         | str   | Y        | 转债代码      |
| rate_freq       | int   | N        | 付息频率(次/年) |
| rate_start_date | str   | N        | 付息开始日期  |
| rate_end_date   | str   | N        | 付息结束日期  |
| coupon_rate     | float | N        | 票面利率(%)   |

#### 调用示例

```python
pro = ts.pro_api(your token)
#获取可转债基础信息列表
df = pro.cb_rate(ts_code='123046.SZ,127064.SZ',fields="ts_code,rate_freq,rate_start_date,rate_end_date,coupon_rate")
```

---

### 可转债行情 (cb_daily)

#### 接口说明

- **接口标识**：cb_daily
- **接口名称**：可转债行情
- **功能描述**：获取可转债行情
- **调用方法**：pro.cb_daily()
- **权限要求**：用户需要至少2000积分才可以调取，5000积分以上频次相对较高，积分越多权限越大。

#### 输入参数

| 参数名称   | 参数类型 | 是否必填 | 参数描述                         |
| ---------- | -------- | -------- | -------------------------------- |
| ts_code    | str      | N        | TS代码                           |
| trade_date | str      | N        | 交易日期(YYYYMMDD格式，下同)     |
| start_date | str      | N        | 开始日期                         |
| end_date   | str      | N        | 结束日期                         |

#### 输出参数

| 字段名称       | 字段类型 | 默认显示 | 字段描述         |
| -------------- | -------- | -------- | ---------------- |
| ts_code        | str      | Y        | 转债代码         |
| trade_date     | str      | Y        | 交易日期         |
| pre_close      | float    | Y        | 昨收盘价(元)     |
| open           | float    | Y        | 开盘价(元)       |
| high           | float    | Y        | 最高价(元)       |
| low            | float    | Y        | 最低价(元)       |
| close          | float    | Y        | 收盘价(元)       |
| change         | float    | Y        | 涨跌(元)         |
| pct_chg        | float    | Y        | 涨跌幅(%)        |
| vol            | float    | Y        | 成交量(手)       |
| amount         | float    | Y        | 成交金额(万元)   |
| bond_value     | float    | N        | 纯债价值         |
| bond_over_rate | float    | N        | 纯债溢价率(%)    |
| cb_value       | float    | N        | 转股价值         |
| cb_over_rate   | float    | N        | 转股溢价率(%)    |

#### 调用示例

```python
pro = ts.pro_api()

#获取可转债行情
df = pro.cb_daily(trade_date='20190719', fields='ts_code,trade_date, pre_close,open,high,low,close')
```

---

### 可转债赎回信息 (cb_call)

#### 接口说明

获取可转债到期赎回、强制赎回等信息。数据来源于公开披露渠道，供个人和机构研究使用，请不要用于数据商业目的。

#### 调用方法

```python
pro.cb_call()
```

#### 权限要求

本接口需5000积分。

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 转债代码，支持多值输入 |
| ann_date | str | N | 公告日期(YYYYMMDD格式，下同) |
| start_date | str | N | 公告开始日期 |
| end_date | str | N | 公告结束日期 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 转债代码 |
| call_type | str | Y | 赎回类型：到赎、强赎 |
| is_call | str | Y | 是否赎回：已满足强赎条件、公告提示强赎、公告实施强赎、公告到期赎回、公告不强赎 |
| ann_date | str | Y | 公告/提示日期 |
| call_date | str | Y | 赎回日期 |
| call_price | float | Y | 赎回价格(含税，元/张) |
| call_price_tax | float | Y | 赎回价格(扣税，元/张) |
| call_vol | float | Y | 赎回债券数量(张) |
| call_amount | float | Y | 赎回金额(万元) |
| payment_date | str | Y | 行权后款项到账日 |
| call_reg_date | str | Y | 赎回登记日 |

#### 调用示例

```python
pro = ts.pro_api('your token')

#获取可转债行情
df = pro.cb_call(fields='ts_code,call_type,is_call,ann_date,call_date,call_price')
```

---

### 可转债转股价变动

#### 接口信息

- **接口名称**: 可转债转股价变动
- **接口标识**: cb_price_chg
- **接口说明**: 获取可转债转股价变动
- **调用方法**: `pro.cb_price_chg()`
- **权限要求**: 本接口需单独开权限（跟积分没关系），具体请参阅积分获取办法

#### 输入参数

| 名称    | 类型 | 是否必填 | 说明               |
| :------ | :--- | :------- | :----------------- |
| ts_code | str  | Y        | 转债代码，支持多值输入 |

#### 输出参数

| 名称                  | 类型  | 默认显示 | 说明         |
| :-------------------- | :---- | :------- | :----------- |
| ts_code               | str   | Y        | 转债代码     |
| bond_short_name       | str   | Y        | 转债简称     |
| publish_date          | str   | Y        | 公告日期     |
| change_date           | str   | Y        | 变动日期     |
| convert_price_initial | float | Y        | 初始转股价格 |
| convertprice_bef      | float | Y        | 修正前转股价格 |
| convertprice_aft      | float | Y        | 修正后转股价格 |

#### 调用示例

```python
pro = ts.pro_api(your token)
#获取可转债转股价变动
df = pro.cb_price_chg(ts_code="113556.SH,128114.SZ,128110.SZ",fields="ts_code,bond_short_name,change_date,convert_price_initial,convertprice_bef,convertprice_aft")
```

---

### 可转债转股结果

#### 接口信息

- **接口名称**：可转债转股结果
- **接口标识**：cb_share
- **接口说明**：获取可转债转股结果
- **调用方法**：`pro.cb_share()`
- **权限要求**：用户需要至少2000积分才可以调取，但有流量控制，5000积分以上频次相对较高，积分越多权限越大。

#### 输入参数

| 名称      | 类型 | 是否必填 | 说明                           |
| --------- | ---- | -------- | ------------------------------ |
| ts_code   | str  | Y        | 转债代码，支持多值输入         |
| ann_date  | str  | Y        | 公告日期（YYYYMMDD格式，下同） |
| start_date| str  | N        | 公告开始日期                   |
| end_date  | str  | N        | 公告结束日期                   |

#### 输出参数

| 名称                  | 类型  | 默认显示 | 描述             |
| --------------------- | ----- | -------- | ---------------- |
| ts_code               | str   | Y        | 债券代码         |
| bond_short_name       | str   | Y        | 债券简称         |
| publish_date          | str   | Y        | 公告日期         |
| end_date              | str   | Y        | 统计截止日期     |
| issue_size            | float | Y        | 可转债发行总额   |
| convert_price_initial | float | Y        | 初始转换价格     |
| convert_price         | float | Y        | 本次转换价格     |
| convert_val           | float | Y        | 本次转股金额     |
| convert_vol           | float | Y        | 本次转股数量     |
| convert_ratio         | float | Y        | 本次转股比例     |
| acc_convert_val       | float | Y        | 累计转股金额     |
| acc_convert_vol       | float | Y        | 累计转股数量     |
| acc_convert_ratio     | float | Y        | 累计转股比例     |
| remain_size           | float | Y        | 可转债剩余金额   |
| total_shares          | float | Y        | 转股后总股本     |

#### 调用示例

```python
pro = ts.pro_api(your token)
#获取可转债转股结果
df = pro.cb_share(ts_code="113001.SH,110027.SH",fields="ts_code,end_date,convert_price,convert_val,convert_ratio,acc_convert_ratio")
```

---

### 国债收益率曲线 (yc_cb)

#### 接口说明

获取中债收益率曲线，目前可获取中债国债收益率曲线即期和到期收益率曲线数据。

- **接口标识**：yc_cb
- **调用方法**：pro.yc_cb()
- **限量**：单次最大2000，总量不限制，可循环提取
- **权限**：属于单独的权限接口，请在群里联系群主或管理员

#### 输入参数

| 参数名称   | 类型  | 是否必填 | 描述                                   |
| ---------- | ----- | -------- | -------------------------------------- |
| ts_code    | str   | N        | 收益率曲线编码：1001.CB-国债收益率曲线 |
| curve_type | str   | N        | 曲线类型：0-到期，1-即期               |
| trade_date | str   | N        | 交易日期                               |
| start_date | str   | N        | 查询起始日期                           |
| end_date   | str   | N        | 查询结束日期                           |
| curve_term | float | N        | 期限                                   |

#### 输出参数

| 字段名称    | 类型  | 默认显示 | 描述                           |
| ----------- | ----- | -------- | ------------------------------ |
| trade_date  | str   | Y        | 交易日期                       |
| ts_code     | str   | Y        | 曲线编码                       |
| curve_name  | str   | Y        | 曲线名称                       |
| curve_type  | str   | Y        | 曲线类型：0-到期，1-即期       |
| curve_term  | float | Y        | 期限(年)                       |
| yield       | float | Y        | 收益率(%)                      |

#### 调用示例

```python
pro = ts.pro_api(your_token)
#获取中债收益率曲线
df = pro.yc_cb(ts_code='1001.CB', curve_type='0', trade_date='20200203')
```

---

### 大宗交易明细 (bond_blk_detail)

#### 接口说明

获取沪深交易所债券大宗交易数据。本接口目前只有深交所的大宗交易明细，上交所明细已经包含在大宗交易接口里，未单独罗列。

#### 调用方法

```python
pro.bond_blk_detail(**kwargs)
```

#### 权限要求

用户满5000积分有数据权限，单次最大1000条，可根据日期循环提取，总量不限制。

#### 输入参数

| 参数名称   | 参数类型 | 是否必填 | 参数描述                           |
| ---------- | -------- | -------- | ---------------------------------- |
| ts_code    | str      | N        | 债券代码                           |
| trade_date | str      | N        | 交易日期（YYYYMMDD格式，下同）     |
| start_date | str      | N        | 开始日期                           |
| end_date   | str      | N        | 结束日期                           |

#### 输出参数

| 字段名称    | 字段类型 | 默认显示 | 字段描述                           |
| ----------- | -------- | -------- | ---------------------------------- |
| trade_date  | str      | Y        | 交易日期                           |
| ts_code     | str      | Y        | 债券代码                           |
| name        | str      | Y        | 债券名称                           |
| price       | float    | Y        | 成交价（元）                       |
| vol         | float    | Y        | 成交数量（万股/万份/万张/万手）    |
| amount      | float    | Y        | 成交金额（万元）                   |
| buy_dp      | str      | Y        | 买方营业部                         |
| sell_dp     | str      | Y        | 卖方营业部                         |

#### 调用示例

```python
import tushare as ts

### 初始化pro接口
pro = ts.pro_api('YOUR_TOKEN')

### 拉取数据
df = pro.bond_blk_detail(start_date='20210701', end_date='20210930')

print(df)
```

---

### 柜台流通式债券报价 (bc_otcqt)

#### 接口说明

- **接口标识：** bc_otcqt
- **接口名称：** 柜台流通式债券报价
- **功能描述：** 获取柜台流通式债券报价数据。
- **调用方法：** `pro.bc_otcqt()`
- **权限要求：** 用户需要至少500积分可以试用调取，2000积分以上频次相对较高，积分越多权限越大。

#### 输入参数

| 参数名称 | 类型 | 是否必填 | 描述 |
|---|---|---|---|
| trade_date | str | N | 交易日期(YYYYMMDD格式，下同) |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |
| ts_code | str | N | TS代码 |
| bank | str | N | 报价机构 |

#### 输出参数

| 字段名称 | 类型 | 描述 |
|---|---|---|
| trade_date | str | 报价日期 |
| qt_time | str | 报价时间 |
| bank | str | 报价机构 |
| ts_code | str | 债券编码 |
| name | str | 债券简称 |
| maturity | str | 期限 |
| remain_maturity | str | 剩余期限 |
| bond_type | str | 债券类型 |
| coupon_rate | float | 票面利率（%） |
| buy_price | float | 投资者买入全价 |
| sell_price | float | 投资者卖出全价 |
| buy_yield | float | 投资者买入到期收益率（%） |
| sell_yield | float | 投资者卖出到期收益率（%） |

#### 调用示例

```python
pro = ts.pro_api(your_token)
#柜台流通式债券报价
df = pro.bc_otcqt(start_date='20240325',end_date='20240329',ts_code='200013.BC',fields='trade_date,qt_time,bank,ts_code,name,remain_maturity,buy_yield,sell_yield')
```

---

### 柜台流通式债券最优报价

**接口标识**：`bc_bestotcqt`

**接口说明**：提供柜台流通式债券的最优报价数据，方便投资者了解市场情况。

**调用方法**：
```python
pro.bc_bestotcqt()
```

**权限要求**：用户需要至少500积分可以试用调取，2000积分以上频次相对较高，积分越多权限越大。

**输入参数**：

| 名称 | 类型 | 是否必填 | 说明 |
|---|---|---|---|
| trade_date | str | N | 报价日期(YYYYMMDD格式) |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |
| ts_code | str | N | TS代码 |

**输出参数**：

| 字段 | 类型 | 说明 |
|---|---|---|
| trade_date | str | 报价日期 |
| ts_code | str | 债券编码 |
| name | str | 债券简称 |
| remain_maturity | str | 剩余期限 |
| bond_type | str | 债券类型 |
| best_buy_bank | str | 最优报买价方 |
| best_buy_yield | float | 投资者最优买入价到期收益率（%） |
| best_buy_price | float | 投资者最优买入全价 |
| best_sell_bank | str | 最优卖报价方 |
| best_sell_yield | float | 投资者最优卖出价到期收益率（%） |
| best_sell_price | float | 投资者最优卖出全价 |

**调用示例**：

```python
pro = ts.pro_api('your_token')
df = pro.bc_bestotcqt(ts_code='200013.BC', start_date='20240325', end_date='20240329', fields='trade_date,ts_code,name,remain_maturity,best_buy_bank,best_buy_yield,best_sell_bank,best_sell_yield')
print(df)
```

---

### 财经日历 (eco_cal)

#### 接口说明

获取全球财经日历、包括经济事件数据更新。

#### 调用方法

```python
pro = ts.pro_api()
df = pro.eco_cal(**kwargs)
```

#### 权限要求

2000积分可调取，单次最大获取100行数据。

#### 输入参数

| 参数名称 | 类型 | 是否必填 | 描述 |
|---|---|---|---|
| date | str | N | 日期（YYYYMMDD格式） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |
| currency | str | N | 货币代码 |
| country | str | N | 国家（比如：中国、美国） |
| event | str | N | 事件 （支持模糊匹配： *非农*） |

#### 输出参数

| 字段名称 | 类型 | 默认显示 | 描述 |
|---|---|---|---|
| date | str | Y | 日期 |
| time | str | Y | 时间 |
| currency | str | Y | 货币代码 |
| country | str | Y | 国家 |
| event | str | Y | 经济事件 |
| value | str | Y | 今值 |
| pre_value | str | Y | 前值 |
| fore_value | str | Y | 预测值 |

#### 调用示例

```python
pro = ts.pro_api()

#获取指定日期全球经济日历
df = pro.eco_cal(date='20200403')

#获取中国经济事件
df = pro.eco_cal(country='中国')

#获取美国非农数据
df = pro.eco_cal(event='美国季调后非农*', fields='date,time,country,event,value,pre_value,fore_value')
```

---


# 5. 外汇数据

## 外汇数据

### 外汇基础信息（海外） (fx_obasic)

#### 接口说明

- **接口标识**：fx_obasic
- **接口名称**：外汇基础信息（海外）
- **功能描述**：获取海外外汇基础信息，目前只有FXCM交易商的数据。
- **调用方法**：`pro.fx_obasic()`

#### 权限要求

用户需要至少2000积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=131)。

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | --- | --- |
| exchange | str | N | 交易商 |
| classify | str | N | 分类 |
| ts_code | str | N | TS代码 |

##### classify分类说明

| 序号 | 分类代码 | 分类名称 | 样例 |
| --- | --- | --- | --- |
| 1 | FX | 外汇货币对 | USDCNH（美元人民币对） |
| 2 | INDEX | 指数 | US30（美国道琼斯工业平均指数） |
| 3 | COMMODITY | 大宗商品 | SOYF（大豆） |
| 4 | METAL | 金属 | XAUUSD （黄金） |
| 5 | BUND | 国库债券 | Bund（长期欧元债券） |
| 6 | CRYPTO | 加密数字货币 | BTCUSD (比特币) |
| 7 | FX_BASKET | 外汇篮子 | USDOLLAR （美元指数） |

#### 输出参数

| 字段名称 | 字段类型 | 默认显示 | 字段描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 外汇代码 |
| name | str | Y | 名称 |
| classify | str | Y | 分类 |
| exchange | str | Y | 交易商 |
| min_unit | float | Y | 最小交易单位 |
| max_unit | float | Y | 最大交易单位 |
| pip | float | Y | 点 |
| pip_cost | float | Y | 点值 |
| traget_spread | float | Y | 目标差价 |
| min_stop_distance | float | Y | 最小止损距离（点子） |
| trading_hours | str | Y | 交易时间 |
| break_time | str | Y | 休市时间 |

#### 调用示例

```python
import tushare as ts

### 初始化pro接口
pro = ts.pro_api("YOUR_TOKEN")

### 获取差价合约(CFD)中指数产品的基础信息
df = pro.fx_obasic(exchange=
'FXCM
', classify=
'INDEX
', fields=
'ts_code,name,min_unit,max_unit,pip,pip_cost
')
print(df)
```

#### 数据示例

```
        ts_code                  name     min_unit  max_unit  pip  pip_cost
0    AUS200.FXCM  澳大利亚标准普尔200指数       1.0    2000.0  1.0       0.1
1     CHN50.FXCM      富时中国A50指数       1.0     100.0  1.0       0.1
2     ESP35.FXCM    西班牙IBEX35指数       1.0    5000.0  1.0       0.1
3   EUSTX50.FXCM      欧洲斯托克50指数       1.0    5000.0  1.0       0.1
4     FRA40.FXCM      法国CAC40指数       1.0    5000.0  1.0       0.1
5     GER30.FXCM        德国DAX指数       1.0    1000.0  1.0       0.1
6     HKG33.FXCM         香港恒生指数       1.0     300.0  1.0       1.0
7    JPN225.FXCM        日经225指数      10.0    1000.0  1.0      10.0
8    NAS100.FXCM    美国纳斯达克100指数       1.0    5000.0  1.0       0.1
9    SPX500.FXCM      美国标普500指数       1.0    5000.0  0.1       0.1
10    UK100.FXCM      英国富时100指数       1.0    4000.0  1.0       0.1
11     US30.FXCM      道琼斯工业平均指数       1.0    4000.0  1.0       0.1
12   US2000.FXCM     美国罗素2000指数       1.0    5000.0  0.1       0.1
```

---

### 外汇日线行情 (fx_daily)

#### 接口说明

获取外汇日线行情

#### 调用方法

```python
pro.fx_daily()
```

#### 权限要求

用户需要至少2000积分才可以调取，但有流量控制，5000积分以上频次相对较高，积分越多权限越大。

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | TS代码 |
| trade_date | str | N | 交易日期（GMT，日期是格林尼治时间，比北京时间晚一天） |
| start_date | str | N | 开始日期（GMT） |
| end_date | str | N | 结束日期（GMT） |
| exchange | str | N | 交易商，目前只有FXCM |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 外汇代码 |
| trade_date | str | Y | 交易日期 |
| bid_open | float | Y | 买入开盘价 |
| bid_close | float | Y | 买入收盘价 |
| bid_high | float | Y | 买入最高价 |
| bid_low | float | Y | 买入最低价 |
| ask_open | float | Y | 卖出开盘价 |
| ask_close | float | Y | 卖出收盘价 |
| ask_high | float | Y | 卖出最高价 |
| ask_low | float | Y | 卖出最低价 |
| tick_qty | int | Y | 报价笔数 |
| exchange | str | N | 交易商 |

#### 调用示例

```python
pro = ts.pro_api()

#获取美元人民币交易对的日线行情
df = pro.fx_daily(ts_code='USDCNH.FXCM', start_date='20190101', end_date='20190524')
```

---


# 6. 美股数据

## 美股数据

### 美股交易日历

**接口名称**: 美股交易日历

**接口标识**: us_tradecal

**接口说明**: 获取美股交易日历信息

**调用方法**:

```python
pro = ts.pro_api()
df = pro.us_tradecal(start_date='20200101', end_date='20200701')
```

**权限要求**: 单次最大6000，可根据日期阶段获取

**输入参数**:

| 名称 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |
| is_open | str | N | 是否交易 0：休市 、1：交易 |

**输出参数**:

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| cal_date | str | 日历日期 (默认输出) |
| is_open | int | 是否交易 '0'休市 '1'交易 (默认输出) |
| pretrade_date | str | 上一个交易日 (默认输出) |

**调用示例**:

```python
pro = ts.pro_api()
df = pro.us_tradecal(start_date='20200101', end_date='20200701')
```

---

### 美股利润表

#### 接口信息

- **接口名称**: 美股利润表
- **接口标识**: us_income
- **接口说明**: 获取美股上市公司财务利润表数据（目前只覆盖主要美股和中概股）。
- **调用方法**: `pro.us_income()`
- **权限要求**: 需单独开权限或有15000积分，具体权限信息请参考[权限列表](https://tushare.pro/document/1?doc_id=108)。

#### 输入参数

| 参数名称    | 类型 | 是否必填 | 描述                                                                  |
| :---------- | :--- | :------- | :-------------------------------------------------------------------- |
| ts_code     | str  | Y        | 股票代码                                                              |
| period      | str  | N        | 报告期（格式：YYYYMMDD，每个季度最后一天的日期，如20241231)           |
| ind_name    | str  | N        | 指标名(如：新增借款）                                                 |
| report_type | str  | N        | 报告期类型(Q1一季报Q2半年报Q3三季报Q4年报)                            |
| start_date  | str  | N        | 报告期开始时间（格式：YYYYMMDD）                                      |
| end_date    | str  | N        | 报告结束始时间（格式：YYYYMMDD）                                      |

#### 输出参数

| 字段名称    | 类型  | 默认显示 | 描述                                         |
| :---------- | :---- | :------- | :------------------------------------------- |
| ts_code     | str   | Y        | 股票代码                                     |
| end_date    | str   | Y        | 报告期                                       |
| ind_type    | str   | Y        | 报告期类型(Q1一季报Q2半年报Q3三季报Q4年报)   |
| name        | str   | Y        | 股票名称                                     |
| ind_name    | str   | Y        | 财务科目名称                                 |
| ind_value   | float | Y        | 财务科目值                                   |
| report_type | str   | Y        | 报告类型                                     |

#### 调用示例

```python
pro = ts.pro_api()

### 获取美股英伟达NVDA股票的2024年度利润表数据
df = pro.us_income(ts_code='NVDA', period='20241231')

### 获取美股英伟达NVDA股票利润表历年营业额数据
df = pro.us_income(ts_code='NVDA', ind_name='营业额')
```

---

### 美股基础信息 (us_basic)

#### 接口描述

获取美股列表信息，单次最大6000，可分页提取。

#### 调用方法

```python
pro = ts.pro_api()
df = pro.us_basic(**kwargs)
```

#### 权限要求

120积分可以试用，5000积分有正式权限

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 股票代码 |
| classify | str | N | 股票分类 |
| offset | str | N | 开始行数 |
| limit | str | N | 每页最大行数 |

#### 输出参数

| 字段名称 | 字段类型 | 描述 |
| --- | --- | --- |
| ts_code | str | 美股代码 |
| name | str | 中文名称 |
| enname | str | 英文名称 |
| classify | str | 分类ADR/GDR/EQ |
| list_date | str | 上市日期 |
| delist_date | str | 退市日期 |

#### 调用示例

```python
pro = ts.pro_api()

#获取默认美国股票基础信息，单次6000行
df = pro.us_basic()
```

---

### 美股复权因子 (us_adjfactor)

#### 接口说明

获取美股每日复权因子数据，在每天美股收盘后滚动刷新。

#### 调用方法

```python
pro.us_adjfactor(ts_code="", trade_date="", start_date="", end_date="")
```

#### 权限要求

本接口是在开通美股日线权限后自动获取权限，具体请参考[Tushare权限说明](https://tushare.pro/document/1?doc_id=108)。

#### 输入参数

| 参数名称   | 参数类型 | 是否必填 | 参数描述                                 |
| ---------- | -------- | -------- | ---------------------------------------- |
| ts_code    | str      | N        | 股票代码                                 |
| trade_date | str      | N        | 交易日期（格式：YYYYMMDD，下同）         |
| start_date | str      | N        | 开始日期                                 |
| end_date   | str      | N        | 结束日期                                 |

#### 输出参数

| 字段名称      | 字段类型 | 默认显示 | 字段描述     |
| ------------- | -------- | -------- | ------------ |
| ts_code       | str      | Y        | 股票代码     |
| trade_date    | str      | Y        | 交易日期     |
| exchange      | str      | Y        | 交易所       |
| cum_adjfactor | float    | Y        | 累计复权因子 |
| close_price   | float    | Y        | 收盘价       |

#### 调用示例

```python
import tushare as ts

### 初始化pro接口
pro = ts.pro_api('YOUR_TOKEN')

### 获取美股单一股票复权因子
df = pro.us_adjfactor(ts_code='AAPL', start_date='20240101', end_date='20251022')
print(df)

### 获取美股某一日全部股票的复权因子
df = pro.us_adjfactor(trade_date='20251031')
print(df)
```

---

### 美股复权行情 (us_daily_adj)

#### 接口说明

获取美股复权行情，支持美股全市场股票，提供股本、市值、复权因子和成交信息等多个数据指标。

- **接口**: `us_daily_adj`
- **调用方法**: `pro.us_daily_adj()`
- **限量**: 单次最大可以提取8000条数据，可循环获取全部，支持分页提取。
- **权限要求**: 120积分可以试用查看数据。

**注**：美股复权逻辑是：价格 * 复权因子 = 复权价格，比如close * adj_factor = 前复权收盘价。复权因子历史数据可能除权等被刷新，请注意动态更新。

#### 输入参数

| 名称 | 类型 | 是否必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 股票代码（e.g. AAPL） |
| trade_date | str | N | 交易日期（YYYYMMDD） |
| start_date | str | N | 开始日期（YYYYMMDD） |
| end_date | str | N | 结束日期（YYYYMMDD） |
| exchange | str | N | 交易所（NAS/NYS/OTC) |
| offset | int | N | 开始行数 |
| limit | int | N | 每页行数 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 股票代码 |
| trade_date | str | Y | 交易日期 |
| close | float | Y | 收盘价 |
| open | float | Y | 开盘价 |
| high | float | Y | 最高价 |
| low | float | Y | 最低价 |
| pre_close | float | Y | 昨收价 |
| change | float | Y | 涨跌额 |
| pct_change | float | Y | 涨跌幅 |
| vol | int | Y | 成交量 |
| amount | float | Y | 成交额 |
| vwap | float | Y | 平均价 |
| adj_factor | float | Y | 复权因子 |
| turnover_ratio | float | Y | 换手率 |
| free_share | int | Y | 流通股本 |
| total_share | int | Y | 总股本 |
| free_mv | float | Y | 流通市值 |
| total_mv | float | Y | 总市值 |
| exchange | str | Y | 交易所代码 |

#### 调用示例

```python
import tushare as ts

### 初始化pro接口
pro = ts.pro_api()

### 获取单一股票行情
df = pro.us_daily_adj(ts_code='AAPL', start_date='20240101', end_date='20240722')
print(df)

### 获取某一日某个交易所的全部股票
df = pro.us_daily_adj(trade_date='20240722', exchange='NAS')
print(df)
```

---

### 美股日线行情 (us_daily)

#### 接口描述

获取美股行情（未复权），包括全部股票全历史行情，以及重要的市场和估值指标。

#### 调用方法

```python
pro.us_daily()
```

#### 权限要求

120积分可以试用查看数据，开通正式权限请参考权限说明文档。

#### 输入参数

| 参数名称   | 参数类型 | 是否必填 | 参数描述             |
| ---------- | -------- | -------- | -------------------- |
| ts_code    | str      | N        | 股票代码（e.g. AAPL） |
| trade_date | str      | N        | 交易日期（YYYYMMDD）   |
| start_date | str      | N        | 开始日期（YYYYMMDD）   |
| end_date   | str      | N        | 结束日期（YYYYMMDD）   |

#### 输出参数

| 字段名称       | 字段类型 | 默认显示 | 字段描述 |
| -------------- | -------- | -------- | -------- |
| ts_code        | str      | Y        | 股票代码 |
| trade_date     | str      | Y        | 交易日期 |
| close          | float    | Y        | 收盘价   |
| open           | float    | Y        | 开盘价   |
| high           | float    | Y        | 最高价   |
| low            | float    | Y        | 最低价   |
| pre_close      | float    | Y        | 昨收价   |
| change         | float    | N        | 涨跌额   |
| pct_change     | float    | Y        | 涨跌幅   |
| vol            | float    | Y        | 成交量   |
| amount         | float    | Y        | 成交额   |
| vwap           | float    | Y        | 平均价   |
| turnover_ratio | float    | N        | 换手率   |
| total_mv       | float    | N        | 总市值   |
| pe             | float    | N        | PE       |
| pb             | float    | N        | PB       |

#### 调用示例

```python
pro = ts.pro_api()

#获取单一股票行情
df = pro.us_daily(ts_code='AAPL', start_date='20190101', end_date='20190904')

#获取某一日所有股票
df = pro.us_daily(trade_date='20190904')
```

---

### 美股现金流量表 (us_cashflow)

#### 接口描述

获取美股上市公司现金流量表数据（目前只覆盖主要美股和中概股）。

#### 调用方法

```python
pro.us_cashflow(ts_code='NVDA', period='20241231')
```

#### 权限要求

需单独开权限或有15000积分，具体权限信息请参考[权限列表](https.tushare.pro/document/1?doc_id=108)。

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 股票代码 |
| period | str | N | 报告期（格式：YYYYMMDD，每个季度最后一天的日期，如20241231) |
| ind_name | str | N | 指标名(如：新增借款） |
| report_type | str | N | 报告期类型(Q1一季报Q2半年报Q3三季报Q4年报) |
| start_date | str | N | 报告期开始时间（格式：YYYYMMDD） |
| end_date | str | N | 报告结束始时间（格式：YYYYMMDD） |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 股票代码 |
| end_date | str | Y | 报告期 |
| ind_type | str | Y | 报告期类型(Q1一季报Q2半年报Q3三季报Q4年报) |
| name | str | Y | 股票名称 |
| ind_name | str | Y | 财务科目名称 |
| ind_value | float | Y | 财务科目值 |
| report_type | str | Y | 报告类型 |

#### 调用示例

```python
pro = ts.pro_api()

#获取美股英伟达NVDA股票的2024年度现金流量表数据
df = pro.us_cashflow(ts_code='NVDA', period='20241231')

#获取美股英伟达NVDA股票现金流量表历年新增借款数据
df = pro.us_cashflow(ts_code='NVDA', ind_name='新增借款')
```

---

### 美股财务指标数据 (us_fina_indicator)

#### 接口说明

获取美股上市公司财务指标数据，目前只覆盖主要美股和中概股。为避免服务器压力，现阶段每次请求最多返回200条记录，可通过设置日期多次请求获取更多数据。

#### 调用方法

```python
pro = ts.pro_api()
df = pro.us_fina_indicator(ts_code='NVDA', period='20241231')
```

#### 权限要求

需单独开权限或有15000积分，具体权限信息请参考[权限列表](https://tushare.pro/document/1?doc_id=108)

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| :--- | :--- | :--- | :--- |
| ts_code | str | Y | 股票代码 |
| period | str | N | 报告期（格式：YYYYMMDD，每个季度最后一天的日期，如20241231) |
| report_type | str | N | 报告期类型(Q1一季报Q2半年报Q3三季报Q4年报) |
| start_date | str | N | 报告期开始时间（格式：YYYYMMDD） |
| end_date | str | N | 报告结束始时间（格式：YYYYMMDD） |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| :--- | :--- | :--- | :--- |
| ts_code | str | Y | 股票代码 |
| end_date | str | Y | 报告期 |
| ind_type | str | Y | 报告类型,Q1一季报,Q2中报,Q3三季报,Q4年报 |
| security_name_abbr | str | Y | 股票名称 |
| accounting_standards | str | Y | 会计准则 |
| notice_date | str | Y | 公告日期 |
| start_date | str | Y | 报告期开始时间 |
| std_report_date | str | Y | 标准报告期 |
| financial_date | str | Y | 年结日 |
| currency | str | Y | 币种 |
| date_type | str | Y | 报告期类型 |
| report_type | str | Y | 报告类型 |
| operate_income | float | Y | 收入 |
| operate_income_yoy | float | Y | 收入增长 |
| gross_profit | float | Y | 毛利 |
| gross_profit_yoy | float | Y | 毛利增长 |
| parent_holder_netprofit | float | Y | 归母净利润 |
| parent_holder_netprofit_yoy | float | Y | 归母净利润增长 |
| basic_eps | float | Y | 基本每股收益 |
| diluted_eps | float | Y | 稀释每股收益 |
| gross_profit_ratio | float | Y | 销售毛利率 |
| net_profit_ratio | float | Y | 销售净利率 |
| accounts_rece_tr | float | Y | 应收账款周转率(次) |
| inventory_tr | float | Y | 存货周转率(次) |
| total_assets_tr | float | Y | 总资产周转率(次) |
| accounts_rece_tdays | float | Y | 应收账款周转天数 |
| inventory_tdays | float | Y | 存货周转天数 |
| total_assets_tdays | float | Y | 总资产周转天数 |
| roe_avg | float | Y | 净资产收益率 |
| roa | float | Y | 总资产净利率 |
| current_ratio | float | Y | 流动比率(倍) |
| speed_ratio | float | Y | 速动比率(倍) |
| ocf_liqdebt | float | Y | 经营业务现金净额/流动负债 |
| debt_asset_ratio | float | Y | 资产负债率 |
| equity_ratio | float | Y | 产权比率 |
| basic_eps_yoy | float | Y | 基本每股收益同比增长 |
| gross_profit_ratio_yoy | float | Y | 毛利率同比增长(%) |
| net_profit_ratio_yoy | float | Y | 净利率同比增长(%) |
| roe_avg_yoy | float | Y | 平均净资产收益率同比增长(%) |
| roa_yoy | float | Y | 净资产收益率同比增长(%) |
| debt_asset_ratio_yoy | float | Y | 资产负债率同比增长(%) |
| current_ratio_yoy | float | Y | 流动比率同比增长(%) |
| speed_ratio_yoy | float | Y | 速动比率同比增长(%) |
| currency_abbr | str | Y | 币种 |
| total_income | float | Y | 收入总额 |
| total_income_yoy | float | Y | 收入总额同比增长 |
| premium_income | float | Y | 保费收入 |
| premium_income_yoy | float | Y | 保费收入同比 |
| basic_eps_cs | float | Y | 基本每股收益 |
| basic_eps_cs_yoy | float | Y | 基本每股收益同比增长 |
| diluted_eps_cs | float | Y | 稀释每股收益 |
| payout_ratio | float | Y | 保费收入/赔付支出 |
| capitial_ratio | float | Y | 总资产周转率 |
| roe | float | Y | 净资产收益率 |
| roe_yoy | float | Y | 净资产收益率同比增长 |
| debt_ratio | float | Y | 资产负债率 |
| debt_ratio_yoy | float | Y | 资产负债率同比增长 |
| net_interest_income | float | Y | 净利息收入 |
| net_interest_income_yoy | float | Y | 净利息收入增长 |
| diluted_eps_cs_yoy | float | Y | 稀释每股收益增长 |
| loan_loss_provision | float | Y | 贷款损失准备 |
| loan_loss_provision_yoy | float | Y | 贷款损失准备增长 |
| loan_deposit | float | Y | 贷款/存款 |
| loan_equity | float | Y | 贷款/股东权益(倍) |
| loan_assets | float | Y | 贷款/总资产 |
| deposit_equity | float | Y | 存款/股东权益(倍) |
| deposit_assets | float | Y | 存款/总资产 |
| rol | float | Y | 贷款回报率 |
| rod | float | Y | 存款回报率 |

**注：** 输出指标太多可在接口fields参数设定你需要的指标，例如：`fields='ts_coe,bps,basic_eps'`

#### 调用示例

```python
#获取美股英伟达NVDA股票2024年度的财务指标数据
df = pro.us_fina_indicator(ts_code='NVDA', period='20241231')

#获取美股英伟达NVDA股票历年年报财务指标数据
df = pro.us_fina_indicator(ts_code='NVDA', report_type='Q4')
```

---

### 美股资产负债表 (us_balancesheet)

#### 接口说明

- **接口标识**：us_balancesheet
- **接口名称**：美股资产负债表
- **功能描述**：获取美股上市公司资产负债表（目前只覆盖主要美股和中概股）
- **调用方法**：`pro.us_balancesheet()`
- **权限要求**：需单独开权限或有15000积分，具体权限信息请参考权限列表

#### 输入参数

| 参数名称    | 类型 | 是否必填 | 描述                                                                 |
| :---------- | :--- | :------- | :------------------------------------------------------------------- |
| ts_code     | str  | Y        | 股票代码                                                             |
| period      | str  | N        | 报告期（格式：YYYYMMDD，每个季度最后一天的日期，如20241231)         |
| ind_name    | str  | N        | 指标名(如：新增借款）                                                |
| report_type | str  | N        | 报告期类型(Q1一季报Q2半年报Q3三季报Q4年报)                           |
| start_date  | str  | N        | 报告期开始时间（格式：YYYYMMDD）                                     |
| end_date    | str  | N        | 报告结束始时间（格式：YYYYMMDD）                                     |

#### 输出参数

| 字段名称    | 类型  | 描述                                         |
| :---------- | :---- | :------------------------------------------- |
| ts_code     | str   | 股票代码                                     |
| end_date    | str   | 报告期                                       |
| ind_type    | str   | 报告期类型(Q1一季报Q2半年报Q3三季报Q4年报)   |
| name        | str   | 股票名称                                     |
| ind_name    | str   | 财务科目名称                                 |
| ind_value   | float | 财务科目值                                   |
| report_type | str   | 报告类型                                     |

#### 调用示例

```python
pro = ts.pro_api()

### 获取美股英伟达NVDA股票Q4的资产负债表数据
df = pro.us_balancesheet(ts_code='NVDA', report_type='Q4')

### 获取美股英伟达NVDA股票历年应收帐款指标数据
df = pro.us_balancesheet(ts_code='NVDA', ind_name='应收帐款')
```

---


# 7. 行业经济

## TMT行业

### 全国电影剧本备案数据 (film_record)

#### 接口说明

获取全国电影剧本备案的公示数据。

#### 调用方法

```python
pro.film_record(start_date='20181014', end_date='20181214')
```

#### 权限要求

用户需要至少120积分才可以调取，积分越多调取频次越高。

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ann_date | str | N | 公布日期 （至少输入一个参数，格式：YYYYMMDD，日期不连续，定期公布） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| rec_no | str | Y | 备案号 |
| film_name | str | Y | 影片名称 |
| rec_org | str | Y | 备案单位 |
| script_writer | str | Y | 编剧 |
| rec_result | str | Y | 备案结果 |
| rec_area | str | Y | 备案地（备案时间） |
| classified | str | Y | 影片分类 |
| date_range | str | Y | 备案日期区间 |
| ann_date | str | Y | 备案结果发布时间 |

#### 调用示例

```python
pro = ts.pro_api()
#或者
#pro = ts.pro_api('your token')

df = pro.film_record(start_date='20181014', end_date='20181214')
```

---

### 全国电视剧备案公示数据 (teleplay_record)

#### 接口描述

获取2009年以来全国拍摄制作电视剧备案公示数据。

**数据权限**：用户需要至少积分600才可以调取，积分越多调取频次越高。

#### 调用方法

```python
pro.teleplay_record(**kwargs)
```

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| report_date | str | N | 备案月份（YYYYMM） |
| start_date | str | N | 备案开始月份（YYYYMM） |
| end_date | str | N | 备案结束月份（YYYYMM） |
| org | str | N | 备案机构 |
| name | str | N | 电视剧名称 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| name | str | Y | 电视剧名称 |
| classify | str | Y | 题材 |
| types | str | Y | 体裁 |
| org | str | Y | 报备机构 |
| report_date | str | Y | 报备时间 |
| license_key | str | Y | 许可证号 |
| episodes | str | Y | 集数 |
| shooting_date | str | Y | 拍摄时间 |
| prod_cycle | str | Y | 制作周期 |
| content | str | Y | 内容提要 |
| pro_opi | str | Y | 省级管理部门备案意见 |
| dept_opi | str | Y | 相关部门意见 |
| remarks | str | Y | 备注 |

#### 调用示例

```python
import tushare as ts

pro = ts.pro_api()

### 按备案月份查询
df = pro.teleplay_record(report_date='201905')

### 按备案机构查询
df = pro.teleplay_record(org='上海新文化传媒集团股份有限公司')

### 按电视剧名称查询
df = pro.teleplay_record(name='三体')
```

---

### 台湾电子产业月营收 (tmt_twincome)

#### 接口说明

获取台湾TMT电子产业领域各类产品月度营收数据。

#### 调用方法

```python
pro.tmt_twincome(item='...', start_date='...', end_date='...')
```

#### 权限要求

文档未明确说明积分要求，但提及“由于服务器压力，单次最多获取30个月数据，后续再逐步全部开放”。

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 参数描述 |
|---|---|---|---|
| date | str | N | 报告期 |
| item | str | Y | 产品代码 |
| start_date | str | N | 报告期开始日期 |
| end_date | str | N | 报告期结束日期 |

#### 输出参数

| 字段名称 | 字段类型 | 字段描述 |
|---|---|---|
| date | str | 报告期 |
| item | str | 产品代码 |
| op_income | str | 月度收入 |

#### 调用示例

```python
import tushare as ts

### 初始化pro接口
pro = ts.pro_api('YOUR_TOKEN')

### 获取PCB月度营收
df = pro.tmt_twincome(item='8')
print(df)

### 获取PCB月度营收（20120101-20181010）
df = pro.tmt_twincome(item='8', start_date='20120101', end_date='20181010')
print(df)
```

#### 产品代码列表

| TS代码 | 类别名称 |
|---|---|
| 1 | PC |
| 2 | NB |
| 3 | 主机板 |
| 4 | 印刷电路板 |
| 5 | IC载板 |
| 6 | PCB组装 |
| 7 | 软板 |
| 8 | PCB |
| 9 | PCB原料 |
| 10 | 铜箔基板 |
| 11 | 玻纤纱布 |
| 12 | FCCL |
| 13 | 显示卡 |
| 14 | 绘图卡 |
| 15 | 电视卡 |
| 16 | 泛工业电脑 |
| 17 | POS |
| 18 | 工业电脑 |
| 19 | 光电IO |
| 20 | 监视器 |
| 21 | 扫描器 |
| 22 | PC周边 |
| 23 | 储存媒体 |
| 24 | 光碟 |
| 25 | 硬盘磁盘 |
| 26 | 发光二极体 |
| 27 | 太阳能 |
| 28 | LCD面板 |
| 29 | 背光模组 |
| 30 | LCD原料 |
| 31 | LCD其它 |
| 32 | 触控面板 |
| 33 | 监控系统 |
| 34 | 其它光电 |
| 35 | 电子零组件 |
| 36 | 二极体整流 |
| 37 | 连接器 |
| 38 | 电源供应器 |
| 39 | 机壳 |
| 40 | 被动元件 |
| 41 | 石英元件 |
| 42 | 3C二次电源 |
| 43 | 网路设备 |
| 44 | 数据机 |
| 45 | 网路卡 |
| 46 | 半导体 |
| 47 | 晶圆制造 |
| 48 | IC封测 |
| 49 | 特用IC |
| 50 | 记忆体模组 |
| 51 | 晶圆材料 |
| 52 | IC设计 |
| 53 | IC光罩 |
| 54 | 电子设备 |
| 55 | 手机 |
| 56 | 通讯设备 |
| 57 | 电信业 |
| 58 | 网路服务 |
| 59 | 卫星通讯 |
| 60 | 光纤通讯 |
| 61 | 3C通路 |
| 62 | 消费性电子 |
| 63 | 照相机 |
| 64 | 软件服务 |
| 65 | 系统整合 |

---

### 台湾电子产业月营收明细 (tmt_twincomedetail)

#### 接口说明

获取台湾TMT行业上市公司各类产品月度营收情况。

#### 接口信息

- **接口名称**：台湾电子产业月营收明细
- **接口标识**：tmt_twincomedetail
- **调用方法**：`pro.tmt_twincomedetail()`
- **权限要求**：无特别说明，需调用pro_api()接口权限。

#### 输入参数

| 名称       | 类型 | 必选 | 描述           |
| ---------- | ---- | ---- | -------------- |
| date       | str  | N    | 报告期         |
| item       | str  | N    | 产品代码       |
| symbol     | str  | N    | 公司代码       |
| start_date | str  | N    | 报告期开始日期 |
| end_date   | str  | N    | 报告期结束日期 |
| source     | str  | N    | None           |

#### 输出参数

| 名称           | 类型 | 描述                     |
| -------------- | ---- | ------------------------ |
| date           | str  | 报告期                   |
| item           | str  | 产品代码                 |
| symbol         | str  | 公司代码                 |
| op_income      | str  | 月度营收                 |
| consop_income  | str  | 合并月度营收（默认不展示） |

#### 调用示例

```python
pro = ts.pro_api()

#获取台湾松上电子PCB的月度营收数据
df = pro.tmt_twincomedetail(item='8', symbol='6156')
```

---

### 影院日度票房 (bo_cinema)

#### 接口描述

获取每日各影院的票房数据。数据从2018年9月开始，更多历史数据正在补充。

#### 权限要求

用户需要至少500积分才可以调取。

#### 调用方法

```python
pro.bo_cinema(date='YYYYMMDD')
```

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 描述 |
|---|---|---|---|
| date | str | Y | 日期(格式:YYYYMMDD) |

#### 输出参数

| 字段名称 | 字段类型 | 描述 |
|---|---|---|
| date | str | 日期 |
| c_name | str | 影院名称 |
| aud_count | int | 观众人数 |
| att_ratio | float | 上座率 |
| day_amount | float | 当日票房 |
| day_showcount | float | 当日场次 |
| avg_price | float | 场均票价（元） |
| p_pc | float | 场均人次 |
| rank | int | 排名 |

#### 调用示例

```python
import tushare as ts

### 初始化pro接口
pro = ts.pro_api('YOUR_TOKEN')

### 调用接口
df = pro.bo_cinema(date='20181014')

### 查看数据
print(df)
```

---

### 电影周度票房 (bo_weekly)

#### 接口说明

获取周度票房数据。本周更新上一周数据，数据从2008年第一周开始，拥有超过10年的历史数据。

#### 调用方法

```python
pro = ts.pro_api()
df = pro.bo_weekly(date='20181008')
```

#### 权限要求

用户需要至少500积分才可以调取。

#### 输入参数

| 名称   | 类型 | 必选 | 描述                             |
| ------ | ---- | ---- | -------------------------------- |
| date   | str  | Y    | 日期（每周一日期，格式YYYYMMDD） |

#### 输出参数

| 名称        | 类型  | 默认显示 | 描述         |
| ----------- | ----- | -------- | ------------ |
| date        | str   | Y        | 日期         |
| name        | str   | Y        | 影片名称     |
| avg_price   | float | Y        | 平均票价     |
| week_amount | float | Y        | 当周票房（万） |
| total       | float | Y        | 累计票房（万） |
| list_day    | int   | Y        | 上映天数     |
| p_pc        | int   | Y        | 场均人次     |
| wom_index   | float | Y        | 口碑指数     |
| up_ratio    | float | Y        | 环比变化 （%） |
| rank        | int   | Y        | 排名         |

#### 调用示例

```python
pro = ts.pro_api()
#或者
#pro = ts.pro_api('your token')

df = pro.bo_weekly(date='20181008')
print(df)
```

##### 数据示例

```
        date      name  avg_price  week_amount    total  list_day  p_pc  \
    0  20181008  无双       36.0      25640.0  93705.0        15    12   
    1  20181008  影       36.0      10277.0  55406.0        15     8   
    2  20181008  找到你       32.0       9318.0  15234.0        10    11   
    3  20181008  李茶的姑妈       35.0       5823.0  57263.0        15     6   
    4  20181008  胖子行动队       34.0       3875.0  23683.0        15     7   
    5  20181008  嗝嗝老师       30.0       2917.0   2941.0         3    10   
    6  20181008  悲伤逆流成河       34.0       2475.0  33532.0        24     7   
    7  20181008  超能泰坦       30.0       1202.0   1202.0         3     4   
    8  20181008  阿凡提之奇缘历险       34.0        675.0   7251.0        14     5
```

---

### 电影日度票房 (bo_daily)

#### 接口说明

获取电影日度票房。数据更新：当日更新上一日数据。数据历史： 数据从2018年9月开始，更多历史数据正在补充。

#### 调用方法

```python
pro = ts.pro_api()
df = pro.bo_daily(date='20181014')
```

#### 权限要求

用户需要至少500积分才可以调取。

#### 输入参数

| 名称   | 类型 | 必选 | 描述               |
| ------ | ---- | ---- | ------------------ |
| date   | str  | Y    | 日期 （格式YYYYMMDD） |

#### 输出参数

| 名称       | 类型  | 默认显示 | 描述           |
| ---------- | ----- | -------- | -------------- |
| date       | str   | Y        | 日期           |
| name       | str   | Y        | 影片名称       |
| avg_price  | float | Y        | 平均票价       |
| day_amount | float | Y        | 当日票房（万） |
| total      | float | Y        | 累计票房（万） |
| list_day   | int   | Y        | 上映天数       |
| p_pc       | int   | Y        | 场均人次       |
| wom_index  | float | Y        | 口碑指数       |
| up_ratio   | float | Y        | 环比变化 （%） |
| rank       | int   | Y        | 排名           |

#### 调用示例

```python
pro = ts.pro_api()
#或者
#pro = ts.pro_api('your token')

df = pro.bo_daily(date='20181014')
```

---

### 电影月度票房 (bo_monthly)

#### 接口说明

- **接口标识**：bo_monthly
- **接口说明**：获取电影月度票房数据
- **数据更新**：本月更新上一月数据
- **数据历史**：数据从2008年1月1日开始，超过10年历史数据。
- **权限要求**：用户需要至少500积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)

#### 调用方法

```python
pro = ts.pro_api()
#或者
#pro = ts.pro_api("your token")
df = pro.bo_monthly(date="20180901")
```

#### 输入参数

| 名称   | 类型 | 必选 | 描述                         |
| ------ | ---- | ---- | ---------------------------- |
| date   | str  | Y    | 日期（每月1号，格式YYYYMMDD） |

#### 输出参数

| 名称         | 类型  | 默认显示 | 描述         |
| ------------ | ----- | -------- | ------------ |
| date         | str   | Y        | 日期         |
| name         | str   | Y        | 影片名称     |
| list_date    | str   | Y        | 上映日期     |
| avg_price    | float | Y        | 平均票价     |
| month_amount | float | Y        | 当月票房（万） |
| list_day     | int   | Y        | 月内天数     |
| p_pc         | int   | Y        | 场均人次     |
| wom_index    | float | Y        | 口碑指数     |
| m_ratio      | float | Y        | 月度占比（%）  |
| rank         | int   | Y        | 排名         |

#### 调用示例

```python
pro = ts.pro_api()
#或者
#pro = ts.pro_api("your token")
df = pro.bo_monthly(date="20180901")
```

##### 示例数据

```
                    date       name   list_date  avg_price  month_amount  list_day  p_pc  \
    0   20180901  碟中谍6：全面瓦解  2018-08-31       37.0      104316.0        30    14   
    1   20180901  反贪风暴3          2018-09-14       36.0       40473.0        17    11   
    2   20180901  黄金兄弟           2018-09-21       35.0       23242.0        10    14   
    3   20180901  蚁人2：黄蜂女现身  2018-08-24       35.0       14641.0        30     8   
    4   20180901  悲伤逆流成河       2018-09-21       34.0       14054.0        10    14   
    5   20180901  阿尔法：狼伴归途   2018-09-07       34.0       11298.0        24     7   
    6   20180901  江湖儿女           2018-09-21       34.0        5373.0        10     8   
    7   20180901  快把我哥带走       2018-08-17       32.0        5365.0        30     7   
    8   20180901  镰仓物语           2018-09-14       32.0        4509.0        17     6   
    9   20180901  大闹西游           2018-09-22       34.0        3419.0         9    10
```

---


# 8. 宏观经济

## 价格指数

### 居民消费价格指数 (cn_cpi)

#### 接口说明

获取CPI居民消费价格数据，包括全国、城市和农村的数据。

#### 调用方法

```python
pro.cn_cpi(**kwargs)
```

#### 权限要求

用户积累600积分可以使用。

#### 输入参数

| 名称      | 类型 | 必选 | 描述                                                 |
| --------- | ---- | ---- | ---------------------------------------------------- |
| m         | str  | N    | 月份（YYYYMM，下同），支持多个月份同时输入，逗号分隔 |
| start_m   | str  | N    | 开始月份                                             |
| end_m     | str  | N    | 结束月份                                             |

#### 输出参数

| 名称       | 类型  | 默认显示 | 描述         |
| ---------- | ----- | -------- | ------------ |
| month      | str   | Y        | 月份YYYYMM   |
| nt_val     | float | Y        | 全国当月值   |
| nt_yoy     | float | Y        | 全国同比（%） |
| nt_mom     | float | Y        | 全国环比（%） |
| nt_accu    | float | Y        | 全国累计值   |
| town_val   | float | Y        | 城市当月值   |
| town_yoy   | float | Y        | 城市同比（%） |
| town_mom   | float | Y        | 城市环比（%） |
| town_accu  | float | Y        | 城市累计值   |
| cnt_val    | float | Y        | 农村当月值   |
| cnt_yoy    | float | Y        | 农村同比（%） |
| cnt_mom    | float | Y        | 农村环比（%） |
| cnt_accu   | float | Y        | 农村累计值   |

#### 调用示例

```python
import tushare as ts

pro = ts.pro_api()

### 获取2018年1月至2019年3月的CPI数据
df = pro.cn_cpi(start_m='201801', end_m='201903')

### 获取指定字段
df = pro.cn_cpi(start_m='201801', end_m='201903', fields='month,nt_val,nt_yoy')

print(df)
```

---

### 工业生产者出厂价格指数 (cn_ppi)

#### 接口说明

获取PPI工业生产者出厂价格指数数据。

#### 调用方法

```python
pro.cn_ppi(**kwargs)
```

#### 权限要求

用户600积分可以使用。

#### 输入参数

| 名称      | 类型 | 是否必选 | 描述                                       |
| --------- | ---- | -------- | ------------------------------------------ |
| m         | str  | N        | 月份（YYYYMM），支持多个月份同时输入，逗号分隔 |
| start_m   | str  | N        | 开始月份                                   |
| end_m     | str  | N        | 结束月份                                   |

#### 输出参数

| 名称               | 类型  | 描述                                  |
| ------------------ | ----- | ------------------------------------- |
| month              | str   | 月份YYYYMM                            |
| ppi_yoy            | float | PPI：全部工业品：当月同比             |
| ppi_mp_yoy         | float | PPI：生产资料：当月同比               |
| ppi_mp_qm_yoy      | float | PPI：生产资料：采掘业：当月同比       |
| ppi_mp_rm_yoy      | float | PPI：生产资料：原料业：当月同比       |
| ppi_mp_p_yoy       | float | PPI：生产资料：加工业：当月同比       |
| ppi_cg_yoy         | float | PPI：生活资料：当月同比               |
| ppi_cg_f_yoy       | float | PPI：生活资料：食品类：当月同比       |
| ppi_cg_c_yoy       | float | PPI：生活资料：衣着类：当月同比       |
| ppi_cg_adu_yoy     | float | PPI：生活资料：一般日用品类：当月同比 |
| ppi_cg_dcg_yoy     | float | PPI：生活资料：耐用消费品类：当月同比 |
| ppi_mom            | float | PPI：全部工业品：环比                 |
| ppi_mp_mom         | float | PPI：生产资料：环比                   |
| ppi_mp_qm_mom      | float | PPI：生产资料：采掘业：环比           |
| ppi_mp_rm_mom      | float | PPI：生产资料：原料业：环比           |
| ppi_mp_p_mom       | float | PPI：生产资料：加工业：环比           |
| ppi_cg_mom         | float | PPI：生活资料：环比                   |
| ppi_cg_f_mom       | float | PPI：生活资料：食品类：环比           |
| ppi_cg_c_mom       | float | PPI：生活资料：衣着类：环比           |
| ppi_cg_adu_mom     | float | PPI：生活资料：一般日用品类：环比     |
| ppi_cg_dcg_mom     | float | PPI：生活资料：耐用消费品类：环比     |
| ppi_accu           | float | PPI：全部工业品：累计同比             |
| ppi_mp_accu        | float | PPI：生产资料：累计同比               |
| ppi_mp_qm_accu     | float | PPI：生产资料：采掘业：累计同比       |
| ppi_mp_rm_accu     | float | PPI：生产资料：原料业：累计同比       |
| ppi_mp_p_accu      | float | PPI：生产资料：加工业：累计同比       |
| ppi_cg_accu        | float | PPI：生活资料：累计同比               |
| ppi_cg_f_accu      | float | PPI：生活资料：食品类：累计同比       |
| ppi_cg_c_accu      | float | PPI：生活资料：衣着类：累计同比       |
| ppi_cg_adu_accu    | float | PPI：生活资料：一般日用品类：累计同比 |
| ppi_cg_dcg_accu    | float | PPI：生活资料：耐用消费品类：累计同比 |

#### 调用示例

```python
import tushare as ts

pro = ts.pro_api()

### 获取2019年5月至2020年5月的PPI数据
df = pro.cn_ppi(start_m='201905', end_m='202005')

### 获取指定字段
df = pro.cn_ppi(start_m='201905', end_m='202005', fields='month,ppi_yoy,ppi_mom,ppi_accu')
```

---

## 利率数据

### Hibor利率 (hibor)

#### 接口说明

Hibor利率。HIBOR (Hongkong InterBank Offered Rate)，是香港银行同行业拆借利率。指香港货币市场上，银行与银行之间的一年期以下的短期资金借贷利率，从伦敦同业拆借利率（LIBOR）变化出来的。

#### 调用方法

```python
pro.hibor(start_date='20180101', end_date='20181130')
```

#### 权限要求

用户积累120积分可以调取。

#### 输入参数

| 名称       | 类型 | 是否必填 | 描述                                 |
| ---------- | ---- | -------- | ------------------------------------ |
| date       | str  | N        | 日期 (日期输入格式：YYYYMMDD，下同) |
| start_date | str  | N        | 开始日期                             |
| end_date   | str  | N        | 结束日期                             |

#### 输出参数

| 名称 | 类型  | 默认显示 | 描述   |
| ---- | ----- | -------- | ------ |
| date | str   | Y        | 日期   |
| on   | float | Y        | 隔夜   |
| 1w   | float | Y        | 1周    |
| 2w   | float | Y        | 2周    |
| 1m   | float | Y        | 1个月  |
| 2m   | float | Y        | 2个月  |
| 3m   | float | Y        | 3个月  |
| 6m   | float | Y        | 6个月  |
| 12m  | float | Y        | 12个月 |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.hibor(start_date='20180101', end_date='20181130')
```

---

### LPR贷款基础利率 (shibor_lpr)

#### 接口说明

LPR贷款基础利率

#### 调用方法

```python
pro = ts.pro_api()
df = pro.shibor_lpr(start_date='20180101', end_date='20181130', fields='date,1y')
```

#### 权限要求

用户积累120积分可以调取

#### 输入参数

| 名称       | 类型 | 必选 | 描述                               |
| ---------- | ---- | ---- | ---------------------------------- |
| date       | str  | N    | 日期 (日期输入格式：YYYYMMDD，下同) |
| start_date | str  | N    | 开始日期                           |
| end_date   | str  | N    | 结束日期                           |

#### 输出参数

| 名称 | 类型  | 默认显示 | 描述       |
| ---- | ----- | -------- | ---------- |
| date | str   | Y        | 日期       |
| 1y   | float | Y        | 1年贷款利率 |
| 5y   | float | Y        | 5年贷款利率 |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.shibor_lpr(start_date='20180101', end_date='20181130', fields='date,1y')
```

---

### Libor拆借利率 (libor)

#### 接口说明

Libor（London Interbank Offered Rate ），即伦敦同业拆借利率，是指伦敦的第一流银行之间短期资金借贷的利率，是国际金融市场中大多数浮动利率的基础利率。作为银行从市场上筹集资金进行转贷的融资成本，贷款协议中议定的LIBOR通常是由几家指定的参考银行，在规定的时间（一般是伦敦时间上午11：00）报价的平均利率。

#### 调用方法

```python
pro = ts.pro_api()
df = pro.libor(curr_type='USD', start_date='20180101', end_date='20181130')
```

#### 权限要求

用户积累120积分可以调取

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| date | str | N | 日期 (日期输入格式：YYYYMMDD，下同) |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |
| curr_type | str | N | 货币代码 (USD美元 EUR欧元 JPY日元 GBP英镑 CHF瑞郎，默认是USD) |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| date | str | Y | 日期 |
| curr_type | str | Y | 货币 |
| on | float | Y | 隔夜 |
| 1w | float | Y | 1周 |
| 1m | float | Y | 1个月 |
| 2m | float | Y | 2个月 |
| 3m | float | Y | 3个月 |
| 6m | float | Y | 6个月 |
| 12m | float | Y | 12个月 |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.libor(curr_type='USD', start_date='20180101', end_date='20181130')
print(df)
```

---

### Shibor利率数据 (shibor)

#### 接口说明

shibor利率

#### 调用方法

```python
pro = ts.pro_api()
df = pro.shibor(start_date='20180101', end_date='20181101')
```

#### 权限要求

用户积累120积分可以调取

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| date | str | N | 日期 (日期输入格式：YYYYMMDD，下同) |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| date | str | Y | 日期 |
| on | float | Y | 隔夜 |
| 1w | float | Y | 1周 |
| 2w | float | Y | 2周 |
| 1m | float | Y | 1个月 |
| 3m | float | Y | 3个月 |
| 6m | float | Y | 6个月 |
| 9m | float | Y | 9个月 |
| 1y | float | Y | 1年 |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.shibor(start_date='20180101', end_date='20181101')
```

---

### Shibor报价数据

#### 接口信息

- **接口名称**：Shibor报价数据
- **接口标识**：shibor_quote
- **接口说明**：获取Shibor（上海银行间同业拆放利率）的报价数据。
- **调用方法**：`pro.shibor_quote()`
- **权限要求**：用户积累120积分可以调取。

#### 输入参数

| 名称 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| date | str | N | 日期 (日期输入格式：YYYYMMDD) |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |
| bank | str | N | 银行名称 （中文名称，例如 农业银行） |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| date | str | Y | 日期 |
| bank | str | Y | 报价银行 |
| on_b | float | Y | 隔夜_Bid |
| on_a | float | Y | 隔夜_Ask |
| 1w_b | float | Y | 1周_Bid |
| 1w_a | float | Y | 1周_Ask |
| 2w_b | float | Y | 2周_Bid |
| 2w_a | float | Y | 2周_Ask |
| 1m_b | float | Y | 1月_Bid |
| 1m_a | float | Y | 1月_Ask |
| 3m_b | float | Y | 3月_Bid |
| 3m_a | float | Y | 3月_Ask |
| 6m_b | float | Y | 6月_Bid |
| 6m_a | float | Y | 6月_Ask |
| 9m_b | float | Y | 9月_Bid |
| 9m_a | float | Y | 9月_Ask |
| 1y_b | float | Y | 1年_Bid |
| 1y_a | float | Y | 1年_Ask |

#### 调用示例

```python
import tushare as ts

pro = ts.pro_api()

df = pro.shibor_quote(start_date='20180101', end_date='20181101')
```

---

### 广州民间借贷利率 (gz_index)

#### 接口说明

- **接口标识**：gz_index
- **接口名称**：广州民间借贷利率
- **功能描述**：获取广州民间借贷利率数据。
- **权限要求**：用户需要积攒2000积分可调取。

#### 调用方法

```python
pro.gz_index(**kwargs)
```

#### 输入参数

| 参数名称   | 参数类型 | 是否必填 | 参数描述 |
| ---------- | -------- | -------- | -------- |
| date       | str      | N        | 日期     |
| start_date | str      | N        | 开始日期 |
| end_date   | str      | N        | 结束日期 |

#### 输出参数

| 字段名称  | 字段类型 | 默认显示 | 字段描述                                 |
| --------- | -------- | -------- | ---------------------------------------- |
| date      | str      | Y        | 日期                                     |
| d10_rate  | float    | Y        | 小额贷市场平均利率（十天） （单位：%，下同） |
| m1_rate   | float    | Y        | 小额贷市场平均利率（一月期）             |
| m3_rate   | float    | Y        | 小额贷市场平均利率（三月期）             |
| m6_rate   | float    | Y        | 小额贷市场平均利率（六月期）             |
| m12_rate  | float    | Y        | 小额贷市场平均利率（一年期）             |
| long_rate | float    | Y        | 小额贷市场平均利率（长期）               |

#### 调用示例

```python
import tushare as ts

### 设置token
### pro = ts.pro_api('YOUR_TOKEN')

### 初始化pro接口
pro = ts.pro_api()

### 调用接口
df = pro.gz_index(start_date='20180101', end_date='20190401')

### 打印数据
print(df)
```

---

### 温州民间借贷利率 (wz_index)

#### 接口说明

温州民间借贷利率，即温州指数。

#### 调用方法

```python
pro.wz_index(start_date='20180101', end_date='20190401')
```

#### 权限要求

用户需要积攒2000积分可调取。

#### 输入参数

| 名称 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| date | str | N | 日期 |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| date | str | Y | 日期 |
| comp_rate | float | Y | 温州民间融资综合利率指数 (%，下同) |
| center_rate | float | Y | 民间借贷服务中心利率 |
| micro_rate | float | Y | 小额贷款公司放款利率 |
| cm_rate | float | Y | 民间资本管理公司融资价格 |
| sdb_rate | float | Y | 社会直接借贷利率 |
| om_rate | float | Y | 其他市场主体利率 |
| aa_rate | float | Y | 农村互助会互助金费率 |
| m1_rate | float | Y | 温州地区民间借贷分期限利率（一月期） |
| m3_rate | float | Y | 温州地区民间借贷分期限利率（三月期） |
| m6_rate | float | Y | 温州地区民间借贷分期限利率（六月期） |
| m12_rate | float | Y | 温州地区民间借贷分期限利率（一年期） |
| long_rate | float | Y | 温州地区民间借贷分期限利率（长期） |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.wz_index(start_date='20180101', end_date='20190401')
```

---

## 国民经济

### GDP数据 (cn_gdp)

#### 接口说明

获取国民经济之GDP数据。

- **接口标识：** `cn_gdp`
- **调用方法：** `pro.cn_gdp()`
- **权限要求：** 用户积累600积分可以使用
- **限量：** 单次最大10000，一次可以提取全部数据

#### 输入参数

| 参数名称  | 参数类型 | 是否必填 | 参数描述                                  |
| :-------- | :------- | :------- | :---------------------------------------- |
| q         | str      | N        | 季度（例如：2019Q1表示2019年第一季度）    |
| start_q   | str      | N        | 开始季度                                  |
| end_q     | str      | N        | 结束季度                                  |
| fields    | str      | N        | 指定输出字段 (e.g. fields='quarter,gdp,gdp_yoy') |

#### 输出参数

| 字段名称 | 字段类型 | 默认显示 | 字段描述             |
| :------- | :------- | :------- | :------------------- |
| quarter  | str      | Y        | 季度                 |
| gdp      | float    | Y        | GDP累计值（亿元）    |
| gdp_yoy  | float    | Y        | 当季同比增速（%）    |
| pi       | float    | Y        | 第一产业累计值（亿元） |
| pi_yoy   | float    | Y        | 第一产业同比增速（%）  |
| si       | float    | Y        | 第二产业累计值（亿元） |
| si_yoy   | float    | Y        | 第二产业同比增速（%）  |
| ti       | float    | Y        | 第三产业累计值（亿元） |
| ti_yoy   | float    | Y        | 第三产业同比增速（%）  |

#### 调用示例

```python
import tushare as ts

### 初始化pro接口
pro = ts.pro_api('YOUR_TOKEN')

### 调用接口
df = pro.cn_gdp(start_q='2018Q1', end_q='2019Q3')

### 查看数据
print(df)

### 获取指定字段
df = pro.cn_gdp(start_q='2018Q1', end_q='2019Q3', fields='quarter,gdp,gdp_yoy')

### 查看数据
print(df)
```

---

## 景气度

### 采购经理人指数 (cn_pmi)

#### 接口说明

- **接口标识**：`cn_pmi`
- **接口名称**：采购经理人指数
- **功能描述**：获取采购经理人指数数据。
- **调用方法**：`pro.cn_pmi()`
- **权限要求**：用户积累2000积分可以使用
- **限量**：单次最大2000，一次可以提取全部数据

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| m | str | N | 月度（202401表示，2024年1月） |
| start_m | str | N | 开始月度 |
| end_m | str | N | 结束月度 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| month | str | N | 月份YYYYMM |
| pmi010000 | float | N | 制造业PMI |
| pmi010100 | float | N | 制造业PMI:企业规模/大型企业 |
| pmi010200 | float | N | 制造业PMI:企业规模/中型企业 |
| pmi010300 | float | N | 制造业PMI:企业规模/小型企业 |
| pmi010400 | float | N | 制造业PMI:构成指数/生产指数 |
| pmi010401 | float | N | 制造业PMI:构成指数/生产指数:企业规模/大型企业 |
| pmi010402 | float | N | 制造业PMI:构成指数/生产指数:企业规模/中型企业 |
| pmi010403 | float | N | 制造业PMI:构成指数/生产指数:企业规模/小型企业 |
| pmi010500 | float | N | 制造业PMI:构成指数/新订单指数 |
| pmi010501 | float | N | 制造业PMI:构成指数/新订单指数:企业规模/大型企业 |
| pmi010502 | float | N | 制造业PMI:构成指数/新订单指数:企业规模/中型企业 |
| pmi010503 | float | N | 制造业PMI:构成指数/新订单指数:企业规模/小型企业 |
| pmi010600 | float | N | 制造业PMI:构成指数/供应商配送时间指数 |
| pmi010601 | float | N | 制造业PMI:构成指数/供应商配送时间指数:企业规模/大型企业 |
| pmi010602 | float | N | 制造业PMI:构成指数/供应商配送时间指数:企业规模/中型企业 |
| pmi010603 | float | N | 制造业PMI:构成指数/供应商配送时间指数:企业规模/小型企业 |
| pmi010700 | float | N | 制造业PMI:构成指数/原材料库存指数 |
| pmi010701 | float | N | 制造业PMI:构成指数/原材料库存指数:企业规模/大型企业 |
| pmi010702 | float | N | 制造业PMI:构成指数/原材料库存指数:企业规模/中型企业 |
| pmi010703 | float | N | 制造业PMI:构成指数/原材料库存指数:企业规模/小型企业 |
| pmi010800 | float | N | 制造业PMI:构成指数/从业人员指数 |
| pmi010801 | float | N | 制造业PMI:构成指数/从业人员指数:企业规模/大型企业 |
| pmi010802 | float | N | 制造业PMI:构成指数/从业人员指数:企业规模/中型企业 |
| pmi010803 | float | N | 制造业PMI:构成指数/从业人员指数:企业规模/小型企业 |
| pmi010900 | float | N | 制造业PMI:其他/新出口订单 |
| pmi011000 | float | N | 制造业PMI:其他/进口 |
| pmi011100 | float | N | 制造业PMI:其他/采购量 |
| pmi011200 | float | N | 制造业PMI:其他/主要原材料购进价格 |
| pmi011300 | float | N | 制造业PMI:其他/出厂价格 |
| pmi011400 | float | N | 制造业PMI:其他/产成品库存 |
| pmi011500 | float | N | 制造业PMI:其他/在手订单 |
| pmi011600 | float | N | 制造业PMI:其他/生产经营活动预期 |
| pmi011700 | float | N | 制造业PMI:分行业/装备制造业 |
| pmi011800 | float | N | 制造业PMI:分行业/高技术制造业 |
| pmi011900 | float | N | 制造业PMI:分行业/基础原材料制造业 |
| pmi012000 | float | N | 制造业PMI:分行业/消费品制造业 |
| pmi020100 | float | N | 非制造业PMI:商务活动 |
| pmi020101 | float | N | 非制造业PMI:商务活动:分行业/建筑业 |
| pmi020102 | float | N | 非制造业PMI:商务活动:分行业/服务业业 |
| pmi020200 | float | N | 非制造业PMI:新订单指数 |
| pmi020201 | float | N | 非制造业PMI:新订单指数:分行业/建筑业 |
| pmi020202 | float | N | 非制造业PMI:新订单指数:分行业/服务业 |
| pmi020300 | float | N | 非制造业PMI:投入品价格指数 |
| pmi020301 | float | N | 非制造业PMI:投入品价格指数:分行业/建筑业 |
| pmi020302 | float | N | 非制造业PMI:投入品价格指数:分行业/服务业 |
| pmi020400 | float | N | 非制造业PMI:销售价格指数 |
| pmi020401 | float | N | 非制造业PMI:销售价格指数:分行业/建筑业 |
| pmi020402 | float | N | 非制造业PMI:销售价格指数:分行业/服务业 |
| pmi020500 | float | N | 非制造业PMI:从业人员指数 |
| pmi020501 | float | N | 非制造业PMI:从业人员指数:分行业/建筑业 |
| pmi020502 | float | N | 非制造业PMI:从业人员指数:分行业/服务业 |
| pmi020600 | float | N | 非制造业PMI:业务活动预期指数 |
| pmi020601 | float | N | 非制造业PMI:业务活动预期指数:分行业/建筑业 |
| pmi020602 | float | N | 非制造业PMI:业务活动预期指数:分行业/服务业 |
| pmi020700 | float | N | 非制造业PMI:新出口订单 |
| pmi020800 | float | N | 非制造业PMI:在手订单 |
| pmi020900 | float | N | 非制造业PMI:存货 |
| pmi021000 | float | N | 非制造业PMI:供应商配送时间 |
| pmi030000 | float | N | 中国综合PMI:产出指数 |

#### 调用示例

```python
pro = ts.pro_api()

#获取指定字段
df = pro.cn_pmi(start_m='201901', end_m='202003', fields='month,pmi010000,pmi010400')
```

---

## 社会融资

### 社融数据（月度） (sf_month)

#### 接口说明

- **接口标识**：sf_month
- **接口名称**：社融数据（月度）
- **功能描述**：获取月度社会融资数据
- **调用方法**：`pro.sf_month()`
- **权限要求**：需2000积分
- **限量**：单次最大2000条数据，可循环提取

#### 输入参数

| 名称      | 类型 | 是否必填 | 说明                                                 |
| :-------- | :--- | :------- | :--------------------------------------------------- |
| m         | str  | N        | 月份（YYYYMM，下同），支持多个月份同时输入，逗号分隔 |
| start_m   | str  | N        | 开始月份                                             |
| end_m     | str  | N        | 结束月份                                             |

#### 输出参数

| 名称       | 类型  | 默认显示 | 描述                     |
| :--------- | :---- | :------- | :----------------------- |
| month      | str   | Y        | 月度                     |
| inc_month  | float | Y        | 社融增量当月值（亿元）   |
| inc_cumval | float | Y        | 社融增量累计值（亿元）   |
| stk_endval | float | Y        | 社融存量期末值（万亿元） |

#### 调用示例

```python
pro = ts.pro_api()

df = pro.sf_month(start_m='201901', end_m='202307')
```

---

## 美国利率

### 国债实际收益率曲线利率 (us_trycr)

#### 接口说明

- **接口名称**：国债实际收益率曲线利率
- **接口标识**：us_trycr
- **功能描述**：获取国债实际收益率曲线利率
- **调用方法**：pro.us_trycr()
- **权限要求**：用户积累120积分可以使用，积分越高频次越高。

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 描述 |
|---|---|---|---|
| date | str | N | 日期 （YYYYMMDD格式，下同） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |
| fields | str | N | 指定输出字段 |

#### 输出参数

| 字段名称 | 字段类型 | 默认显示 | 描述 |
|---|---|---|---|
| date | str | Y | 日期 |
| y5 | float | Y | 5年期 |
| y7 | float | Y | 7年期 |
| y10 | float | Y | 10年期 |
| y20 | float | Y | 20年期 |
| y30 | float | Y | 30年期 |

#### 调用示例

```python
pro = ts.pro_api()

### 获取全部数据
df = pro.us_trycr(start_date='20180101', end_date='20200327')

### 获取5年期和20年期数据
df = pro.us_trycr(start_date='20180101', end_date='20200327', fields='y5,y20')
```

---

### 国债收益率曲线利率 (us_tycr)

#### 接口说明

获取美国每日国债收益率曲线利率。

- **接口标识：** `us_tycr`
- **调用方法：** `pro.us_tycr()`
- **权限要求：** 用户积累120积分可以使用，积分越高频次越高。

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 描述 |
|---|---|---|---|
| date | str | N | 日期 （YYYYMMDD格式，下同） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |
| fields | str | N | 指定输出字段（e.g. fields='m1,y1'） |

#### 输出参数

| 字段名称 | 字段类型 | 默认显示 | 描述 |
|---|---|---|---|
| date | str | Y | 日期 |
| m1 | float | Y | 1月期 |
| m2 | float | Y | 2月期 |
| m3 | float | Y | 3月期 |
| m4 | float | Y | 4月期（数据从20221019开始） |
| m6 | float | Y | 6月期 |
| y1 | float | Y | 1年期 |
| y2 | float | Y | 2年期 |
| y3 | float | Y | 3年期 |
| y5 | float | Y | 5年期 |
| y7 | float | Y | 7年期 |
| y10 | float | Y | 10年期 |
| y20 | float | Y | 20年期 |
| y30 | float | Y | 30年期 |

#### 调用示例

```python
pro = ts.pro_api()

### 获取全部数据
df = pro.us_tycr(start_date='20180101', end_date='20200327')

### 获取1月期和1年期数据
df = pro.us_tycr(start_date='20180101', end_date='20200327', fields='m1,y1')
```

---

### 国债长期利率 (us_tltr)

#### 接口说明

- **接口标识：** `us_tltr`
- **接口名称：** 国债长期利率
- **功能描述：** 获取国债长期利率数据。
- **限量：** 单次最大可获取2000行数据，可循环获取。
- **权限：** 用户积累120积分可以使用，积分越高频次越高。

#### 调用方法

```python
import tushare as ts

pro = ts.pro_api('YOUR_TOKEN')
df = pro.us_tltr(start_date='20180101', end_date='20200327')
```

#### 输入参数

| 参数名称   | 类型 | 是否必填 | 描述     |
| ---------- | ---- | -------- | -------- |
| date       | str  | N        | 日期     |
| start_date | str  | N        | 开始日期 |
| end_date   | str  | N        | 结束日期 |
| fields     | str  | N        | 指定字段 |

#### 输出参数

| 字段名称 | 类型  | 默认显示 | 描述                               |
| -------- | ----- | -------- | ---------------------------------- |
| date     | str   | Y        | 日期                               |
| ltc      | float | Y        | 收益率 LT COMPOSITE (>10 Yrs)      |
| cmt      | float | Y        | 20年期CMT利率(TREASURY 20-Yr CMT) |
| e_factor | float | Y        | 外推因子EXTRAPOLATION FACTOR       |

#### 调用示例

##### 获取全部数据

```python
import tushare as ts

pro = ts.pro_api('YOUR_TOKEN')

df = pro.us_tltr(start_date='20180101', end_date='20200327')
print(df)
```

##### 获取指定字段数据

```python
import tushare as ts

pro = ts.pro_api('YOUR_TOKEN')

#获取5年期和20年期数据
df = pro.us_tltr(start_date='20180101', end_date='20200327', fields='ltc,cmt')
print(df)
```

---

### 国债实际长期利率平均值

#### 接口信息

- **接口名称**：国债实际长期利率平均值
- **接口标识**：us_trltr
- **接口说明**：获取国债实际长期利率平均值
- **调用方法**：`pro.us_trltr()`
- **权限要求**：用户积累120积分可以使用，积分越高频次越高。

#### 输入参数

| 参数名称 | 类型 | 是否必填 | 描述 |
|---|---|---|---|
| date | str | N | 日期 |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |
| fields | str | N | 指定字段 |

#### 输出参数

| 字段名称 | 类型 | 默认显示 | 描述 |
|---|---|---|---|
| date | str | Y | 日期 |
| ltr_avg | float | Y | 实际平均利率LT Real Average (10> Yrs) |

#### 调用示例

```python
pro = ts.pro_api()

### 获取20180101到20200327之间的数据
df = pro.us_trltr(start_date='20180101', end_date='20200327')

### 获取指定字段
df = pro.us_trltr(start_date='20180101', end_date='20200327', fields='ltr_avg')
```

---

### 短期国债利率 (us_tbr)

#### 接口说明
获取美国短期国债利率数据

#### 调用方法
```python
pro.us_tbr()
```

#### 权限要求
用户积累120积分可以使用，积分越高频次越高。

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| date | str | N | 日期 |
| start_date | str | N | 开始日期(YYYYMMDD格式) |
| end_date | str | N | 结束日期 |
| fields | str | N | 指定输出字段(e.g. fields='w4_bd,w52_ce') |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| date | str | Y | 日期 |
| w4_bd | float | Y | 4周银行折现收益率 |
| w4_ce | float | Y | 4周票面利率 |
| w8_bd | float | Y | 8周银行折现收益率 |
| w8_ce | float | Y | 8周票面利率 |
| w13_bd | float | Y | 13周银行折现收益率 |
| w13_ce | float | Y | 13周票面利率 |
| w17_bd | float | Y | 17周银行折现收益率（数据从20221019开始） |
| w17_ce | float | Y | 17周票面利率（数据从20221019开始） |
| w26_bd | float | Y | 26周银行折现收益率 |
| w26_ce | float | Y | 26周票面利率 |
| w52_bd | float | Y | 52周银行折现收益率 |
| w52_ce | float | Y | 52周票面利率 |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.us_tbr(start_date='20180101', end_date='20200327')

#获取指定字段数据
df = pro.us_tbr(start_date='20180101', end_date='20200327', fields='w4_bd,w52_ce')
```

---

## 货币供应量

### 货币供应量（月） (cn_m)

#### 接口说明

获取货币供应量之月度数据。

#### 调用方法

```python
pro = ts.pro_api()
df = pro.cn_m(start_m='201901', end_m='202003')
```

#### 权限要求

用户积累600积分可以使用。

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| m | str | N | 月度（202001表示，2020年1月） |
| start_m | str | N | 开始月度 |
| end_m | str | N | 结束月度 |
| fields | str | N | 指定输出字段（e.g. fields='month,m0,m1,m2'） |

#### 输出参数

| 字段名称 | 字段类型 | 描述 |
| --- | --- | --- |
| month | str | 月份YYYYMM |
| m0 | float | M0（亿元） |
| m0_yoy | float | M0同比（%） |
| m0_mom | float | M0环比（%） |
| m1 | float | M1（亿元） |
| m1_yoy | float | M1同比（%） |
| m1_mom | float | M1环比（%） |
| m2 | float | M2（亿元） |
| m2_yoy | float | M2同比（%） |
| m2_mom | float | M2环比（%） |

#### 调用示例

```python
pro = ts.pro_api()
#获取2019年1月到2020年3月的货币供应量数据
df = pro.cn_m(start_m='201901', end_m='202003')

#获取指定字段
df = pro.cn_m(start_m='201901', end_m='202003', fields='month,m0,m1,m2')
```

---


# 9. 大模型语料专题数据

## 大模型语料专题数据

### 上市公司全量公告 (anns_d)

#### 接口描述

获取全量公告数据，提供pdf下载URL。

**限量**：单次最大2000条数，可以跟进日期循环获取全量。

**权限**：本接口为单独权限，请参考[权限说明](https://tushare.pro/document/1?doc_id=108)。

#### 调用方法

```python
pro.anns_d(ann_date='20230621')
```

#### 输入参数

| 名称      | 类型 | 必选 | 描述                               |
| --------- | ---- | ---- | ---------------------------------- |
| ts_code   | str  | N    | 股票代码                           |
| ann_date  | str  | N    | 公告日期（yyyymmdd格式，下同）     |
| start_date| str  | N    | 公告开始日期                       |
| end_date  | str  | N    | 公告结束日期                       |

#### 输出参数

| 名称      | 类型     | 默认显示 | 描述             |
| --------- | -------- | -------- | ---------------- |
| ann_date  | str      | Y        | 公告日期         |
| ts_code   | str      | Y        | 股票代码         |
| name      | str      | Y        | 股票名称         |
| title     | str      | Y        | 标题             |
| url       | str      | Y        | URL，原文下载链接 |
| rec_time  | datetime | N        | 发布时间         |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.anns_d(ann_date='20230621')
```

---

### 上证E互动 (irm_qa_sh)

#### 接口说明

获取上交所e互动董秘问答文本数据。上证e互动是由上海证券交易所建立、上海证券市场所有参与主体无偿使用的沟通平台,旨在引导和促进上市公司、投资者等各市场参与主体之间的信息沟通,构建集中、便捷的互动渠道。本接口数据记录了以上沟通问答的文本数据。

**接口**：irm_qa_sh，历史数据开始于2023年6月。
**限量**：单次请求最大返回3000行数据，可根据股票代码，日期等参数循环提取全部数据
**权限**：用户后120积分可以试用，正式权限为10000积分，或申请单独开权限

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 股票代码 |
| trade_date | str | N | 交易日期（格式YYYYMMDD，下同） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |
| pub_date | str | N | 发布开始日期(格式：2025-06-03 16:43:03) |
| pub_date | str | N | 发布结束日期(格式：2025-06-03 18:43:23) |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 股票代码 |
| name | str | Y | 公司名称 |
| trade_date | str | Y | 日期 |
| q | str | Y | 问题 |
| a | str | Y | 回复 |
| pub_time | datetime | Y | 回复时间 |

#### 接口调用

```python
pro = ts.pro_api()

#获取2025年2月12日上证e互动的问答文本
df = pro.irm_qa_sh(ann_date='20250212')
```

#### 数据样例

```
           ts_code  name                                                  q                                                  a
    0   601121.SH  宝地矿业  股价利多因素主要看基本面，关键是业绩，利空因素就是减持和低价增发，目前宝地的业绩难以抵消股东...  尊敬的投资者，您好！衷心感谢您对宝地矿业的关注与鞭策。公司将加快推进重点项目建设，做好生产经...
    1   600615.SH  丰华股份  您好！我是一名城市居民，长期关注空气污染问题。想请问贵公司在日常经营过程中，是否采取了有效的...  尊敬的投资者您好！公司不属于重点排污单位。公司高度重视环境保护工作，采取有效措施不断提高环境...
    2   600615.SH  丰华股份       公司镁合金等材料在机器人行业应用前景远大。公司是不是可以考虑加大在机器人方面的战略布局？  尊敬的投资者您好！镁合金材料在轻量化方面应用领域宽泛，目前公司的镁合金产品主要应用于交通工具...
    3   601121.SH  宝地矿业  如果宝地矿业董事会看好自己公司的投资价值，为什么宁可委托申万宏源证券投资理财，也不用自有资金...  尊敬的投资者，您好。感谢您对宝地矿业的关注与建议。公司始终秉持稳健的财务管理和资金使用原则，...
    4   600615.SH  丰华股份  尊敬的董秘您好，据报道人形机器人所使用除peek材料之外，最多的就是镁合金相关材质，请问公司...                   尊敬的投资者您好！目前公司没有人形机器人项目储备，感谢您的关注！
```

---

### 券商研究报告 (research_report)

#### 接口描述

获取券商研究报告-个股、行业等，历史数据从20170101开始提供，增量每天两次更新。

#### 接口限量

单次最大1000条，可根据日期或券商名称代码循环提取，每天总量不限制。

#### 权限要求

本接口需单独开权限（跟积分没关系），具体请参阅[权限说明](https://tushare.pro/document/1?doc_id=108)。

#### 调用方法

```python
pro.research_report(trade_date='20260121', fields='trade_date,file_name,author,inst_csname')
```

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 参数描述 |
|---|---|---|---|
| trade_date | str | N | 研报日期（格式：YYYYMMDD） |
| start_date | str | N | 研报开始日期 |
| end_date | str | N | 研报结束日期 |
| report_type | str | N | 研报类别：个股研报/行业研报 |
| ts_code | str | N | 股票代码 |
| inst_csname | str | N | 券商名称 |
| ind_name | str | N | 行业名称 |

#### 输出参数

| 字段名称 | 字段类型 | 描述 |
|---|---|---|
| trade_date | str | 研报发布时间 |
| abstr | str | 研报摘要 |
| title | str | 研报标题 |
| report_type | str | 研报类别 |
| author | str | 作者 |
| name | str | 股票名称 |
| ts_code | str | 股票代码 |
| inst_csname | str | 机构简称 |
| ind_name | str | 行业名称 |
| url | str | 下载链接 |

#### 调用示例

```python
import tushare as ts

### 初始化pro接口
pro = ts.pro_api('YOUR_TOKEN')

### 获取2026年1月21日券商研报数据
df = pro.research_report(trade_date='20260121', fields='trade_date,file_name,author,inst_csname')

print(df)
```

---

### 国家政策法规库

#### 接口信息

- **接口名称**: 国家政策法规库
- **接口标识**: npr
- **接口说明**: 获取国家行政机关公开披露的各类法规、条例政策、批复、通知等文本数据。
- **调用方法**: `pro.npr()`
- **权限要求**: 本接口需单独开权限（跟积分没关系），具体请参阅权限说明

#### 输入参数

| 名称 | 类型 | 是否必填 | 描述 | 可选内容 |
| --- | --- | --- | --- | --- |
| org | str | N | 发布机构 | 国务院办公厅/国务院办公厅/国务院、中央军委/国务院应急管理办公室 |
| start_date | datetime | N | 发布开始时间 | 格式样例：2024-11-21 00:00:00 |
| end_date | datetime | N | 发布结束时间 | 格式样例：2024-11-28 00:00:00 |
| ptype | str | N | 类型 | 对外经贸合作/农业、畜牧业、渔业/海关/城市规划/土地/科技/教育/卫生/民航 等110类 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| pubtime | datetime | Y | 发布时间 |
| title | str | Y | 标题 |
| url | str | N | 政策文件url |
| content_html | str | N | 正文内容 |
| pcode | str | Y | 发文字号 |
| puborg | str | Y | 发文机关 |
| ptype | str | Y | 主题分类 |

#### 调用示例

```python
pro = ts.pro_api()

#获取由国务院发布的相关政策文件
df = pro.npr(org='国务院')

#获取由“国务院”发布的“科技”相关政策和批复文件
df = pro.npr(org='国务院', 
            ptype='科技', 
            end_date='2025-08-26 17:00:00', 
            fields='pubtime,title,pcode')
```

---

### 新闻快讯 (news)

#### 接口说明

获取主流新闻网站的快讯新闻数据,提供超过6年以上历史新闻。

#### 调用方法

```python
pro = ts.pro_api()
df = pro.news(src='sina', start_date='2018-11-21 09:00:00', end_date='2018-11-22 10:10:00')
```

#### 权限要求

本接口需单独开权限（跟积分没关系），具体请参阅权限说明。

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| start_date | datetime | Y | 开始日期(格式：2018-11-20 09:00:00） |
| end_date | datetime | Y | 结束日期 |
| src | str | Y | 新闻来源 见下表 |

##### 数据源

| 来源名称 | src标识 | 描述 |
| --- | --- | --- |
| 新浪财经 | sina | 获取新浪财经实时资讯 |
| 华尔街见闻 | wallstreetcn | 华尔街见闻快讯 |
| 同花顺 | 10jqka | 同花顺财经新闻 |
| 东方财富 | eastmoney | 东方财富财经新闻 |
| 云财经 | yuncaijing | 云财经新闻 |
| 凤凰新闻 | fenghuang | 凤凰新闻 |
| 金融界 | jinrongjie | 金融界新闻 |
| 财联社 | cls | 财联社快讯 |
| 第一财经 | yicai | 第一财经快讯 |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| datetime | str | Y | 新闻时间 |
| content | str | Y | 内容 |
| title | str | Y | 标题 |
| channels | str | N | 分类 |

#### 调用示例

```python
pro = ts.pro_api()
df = pro.news(src='sina', start_date='2018-11-21 09:00:00', end_date='2018-11-22 10:10:00')
```

---

### 新闻联播文字稿 (cctv_news)

#### 接口说明

获取新闻联播文字稿数据，数据开始于2017年。

#### 调用方法

```python
pro.cctv_news(date='YYYYMMDD')
```

#### 权限要求

本接口需单独开权限（跟积分没关系），具体请参阅权限说明。

#### 输入参数

| 名称 | 类型 | 是否必填 | 说明 |
|---|---|---|---|
| date | str | Y | 日期（输入格式：YYYYMMDD 比如：20181211） |

#### 输出参数

| 字段 | 类型 | 说明 |
|---|---|---|
| date | str | 日期 |
| title | str | 标题 |
| content | str | 内容 |

#### 调用示例

```python
import tushare as ts

### 初始化pro接口
pro = ts.pro_api('YOUR_TOKEN')

### 获取2018年12月11日新闻联播文字稿内容
df = pro.cctv_news(date='20181211')

print(df)
```
df)
```

---

### 新闻通讯 (major_news)

#### 接口说明

- **接口标识**：major_news
- **接口名称**：新闻通讯
- **功能描述**：获取长篇通讯信息，覆盖主要新闻资讯网站，提供超过8年历史新闻。
- **调用方法**：pro.major_news()
- **权限要求**：本接口需单独开权限（跟积分没关系），具体请参阅[权限说明](https://tushare.pro/document/1?doc_id=108)

#### 输入参数

| 参数名称 | 参数类型 | 是否必填 | 参数描述 |
|---|---|---|---|
| src | str | N | 新闻来源（新华网、凤凰财经、同花顺、新浪财经、华尔街见闻、中证网、财新网、第一财经、财联社） |
| start_date | str | N | 新闻发布开始时间，e.g. 2018-11-21 00:00:00 |
| end_date | str | N | 新闻发布结束时间，e.g. 2018-11-22 00:00:00 |

#### 输出参数

| 字段名称 | 字段类型 | 是否默认输出 | 字段描述 |
|---|---|---|---|
| title | str | Y | 标题 |
| content | str | N | 内容 (默认不显示，需要在fields里指定) |
| pub_time | str | Y | 发布时间 |
| src | str | Y | 来源网站 |

#### 调用示例

```python
pro = ts.pro_api()

### 提取新闻
df = pro.major_news(src='新浪财经', start_date='2018-11-21 00:00:00', end_date='2018-11-22 00:00:00')

### 提取新闻内容
df = pro.major_news(src='新浪财经', start_date='2018-11-21 00:00:00', end_date='2018-11-22 00:00:00', fields='title,content')
```

---

### 深证互动易 (irm_qa_sz)

#### 接口说明

互动易是由深交所官方推出,供投资者与上市公司直接沟通的平台,一站式公司资讯汇集,提供第一手的互动问答、投资者关系信息、公司声音等内容。

#### 接口信息

- **接口标识**：irm_qa_sz
- **历史数据**：始于2010年10月
- **调用方法**：pro.irm_qa_sz()
- **权限要求**：用户后120积分可以试用，正式权限为10000积分，或申请单独开权限。

#### 输入参数

| 名称 | 类型 | 必选 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | N | 股票代码 |
| trade_date | str | N | 交易日期（格式YYYYMMDD，下同） |
| start_date | str | N | 开始日期 |
| end_date | str | N | 结束日期 |
| pub_date | str | N | 发布开始日期(格式：2025-06-03 16:43:03) |
| pub_date | str | N | 发布结束日期(格式：2025-06-03 18:43:23) |

#### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
| --- | --- | --- | --- |
| ts_code | str | Y | 股票代码 |
| name | str | Y | 公司名称 |
| trade_date | str | Y | 发布时间 |
| q | str | Y | 问题 |
| a | str | Y | 回复 |
| pub_time | str | Y | 答复时间 |
| industry | str | Y | 涉及行业 |

#### 调用示例

```python
pro = ts.pro_api()

#获取2025年2月12日深证互动易的问答文本
df = pro.irm_qa_sz(ann_date='20250212')
```

---


---

*本文档由自动化工具从 [Tushare Pro 官网](https://tushare.pro/document/2) 采集生成，生成日期：2026年2月24日。如有更新，请以官网最新文档为准。*
