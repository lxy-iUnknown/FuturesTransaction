# 依赖库

pandas、openpyxl、tqdm、nevergrad

# 交易策略

- 突破周期定义为T，当前ATR计算天数定义为M（不包括当前日的前M日）
- 入市规则
    - 每次当日价格突破此前T日（不包括当前日）最高价格时，以当日前T日最高价格建立1个单位多仓头寸
    - 每次当日价格突破此前T日（不包括当前日）最低价格时，以当日前T日最高价格建立1个单位空仓头寸
- 加仓规则：价格在建仓后，价格每再突破N个当前ATR加仓1个头寸，最多持仓量为R个头寸
- 止损规则：当前价格与最后一次加仓时候的价格回撤K个入市ATR（建仓日ATR）
- 止盈规则：当持仓利润超过P个当日ATR时，利润回撤到本次入市的最高利润的比例Q时止盈
- 当数据到达最后一行，如果有持仓，并当天没有止损和止盈条件触发时，以当日收盘价计算离市利润，离市类型为“到期离市”，当止盈和止损同时发生时，按照止损获取的利润和价格计算

从第T+1日开始，每天计算当天的最高价、最低价、开盘价、收盘价、ATR、入市时间、入市类型（开多或开空），入市ATR，入市时间、入市价格、多头持仓数量、空头持仓数量、前T日最高价、前T日最高价、本次入市以来最高利润、当前利润、离市类型（止损多平、止损空平、止盈多平、止盈空平、到期离市）离市利润（本行发生离市时记录，否则为None）

# 算法流程

从第T+1日开始，每天执行以下操作：

- 从表格中读取并记录最高价、最低价、开盘价、收盘价、真实波动幅度(TR)，使用TR计算ATR（计算天数为M）
- 计算前T日最高价和最低价
- 入市（建仓）
    - 条件
        - 多仓：当日**最高价**高于此前T日最高价格
        - 空仓：当日**最低价**低于此前T日最低价格
    - 操作
        1. 记录入市时间、入市价格（当日**前T日**最高价格）、入市ATR，入市类型记为“开多”/“开空”
        2. 向多头/空头开仓价列表中添加本次开仓价（入市价：当日**前T日**最高价格），更新上一次开仓价
- 加仓（多头/空头）
    - 条件
        1. 价格条件
            - 多仓：当日**最高价**高于上一次开仓价加上N个当日ATR
            - 空仓：当日**最低价**低于上一次开仓价减去N个当日ATR
        2. 持仓数量小于等于R
    - 操作：向多头/空头开仓价列表中添加本次开仓价（上一次开仓价加/减N个当日ATR）
- 更新当前利润以及入市以来最高利润：使用收盘价作为当前利润计算价格
- 止损（**代码写在前面**）
    - 条件
        - 多仓：当日**最低价**低于上一次开仓价**减去**K个入市ATR
        - 空仓：当日**最高价**高于上一次开仓价**加上**K个入市ATR
    - 规则：离市类型设为“止损多平”/“止损空平”，离市价设为K倍入市ATR和上一次开仓价之和/差
- 止盈（**代码写在后面**）
    - 条件：当前利润超过P个当日ATR时准备止盈，当前利润小于入市以来最高利润的比例Q时正式止盈
    - 规则：离市类型设为“止盈多平”/“止盈空平”，离市利润设为入市以来最高利润的比例Q（不必通过离市价格计算离市利润）
- 到期离市（**代码写在更后面**）：离市类型设为“到期离市”，离市价设为收盘价

输出当日最高价、最低价、开盘价、收盘价、ATR、入市时间、入市类型，入市ATR，入市时间、入市价格、多头持仓数量、空头持仓数量、前T日最高价、前T日最高价、本次入市以来最高利润、当前利润、离市类型、离市利润。如果当日发生离市，则清除所有与入市和离市相关的数据