import dataclasses


@dataclasses.dataclass(eq=False, frozen=True)
class TransactParams:
    T: int  # 突破周期
    M: int  # ATR计算天数
    R: int  # 最大持仓数量
    N: float  # 加仓触发ATR数量
    K: float  # 止损回撤率
    P: float  # 止盈利润倍数
    Q: float  # 止盈回撤比例
