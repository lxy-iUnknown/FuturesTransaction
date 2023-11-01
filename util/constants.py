import dataclasses


@dataclasses.dataclass(eq=False, frozen=True)
class TransactionParameters:
    T: int    # 突破周期
    M: int    # ATR计算天数
    R: int    # 最大持仓数量
    N: float  # 加仓触发ATR数量
    K: float  # 止损回撤率
    P: float  # 止盈利润倍数
    Q: float  # 止盈回撤比例


DATE = '日期'
OPEN = '开盘价(元)'
CLOSE = '最高价(元)'
LOW = '最低价(元)'
HIGH = '收盘价(元)'
TR = '真实波动幅度'

TRANSACTION_PARAMETERS = TransactionParameters(20, 7, 4, 0.5, 2.0, 3.0, 0.6)
