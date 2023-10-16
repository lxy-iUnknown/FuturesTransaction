import dataclasses
import typing


@dataclasses.dataclass(eq=False, frozen=True)
class TransactionParameters:
    T: int    # 突破周期
    M: int    # ATR计算天数
    R: int    # 最大持仓数量
    N: float  # 加仓触发ATR数量
    K: float  # 止损回撤率
    P: float  # 止盈利润倍数
    Q: float  # 止盈回撤比例


class ColumnNames(typing.NamedTuple):
    DATE: str    # 日期
    OPEN: str    # 开盘价
    CLOSE: str   # 收盘价
    LOW: str     # 最低价
    HIGH: str    # 最高价
    TR: str      # TR


COLUMN_NAMES = ColumnNames('日期', '开盘价(元)', '最高价(元)', '最低价(元)', '收盘价(元)', '真实波动幅度')
TRANSACTION_PARAMETERS = TransactionParameters(20, 7, 4, 0.5, 2.0, 3.0, 0.6)