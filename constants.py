from typing import NamedTuple, TypeVar
from dataclasses import dataclass


@dataclass(eq=False)
class AnalyzerParameters:
    _T = TypeVar('_T')

    T: int    # 突破周期
    M: int    # ATR计算天数
    R: int    # 最大持仓数量
    N: float  # 加仓触发ATR数量
    K: float  # 止损回撤率
    P: float  # 止盈利润倍数
    Q: float  # 止盈回撤比例

    @staticmethod
    def _ensure_positive(value: _T, value_name: str) -> _T:
        """
        确保参数大于0
        :param value: 参数
        :param value_name: 参数名
        :return: 如果检验成功，则返回原本的参数
        :raise ValueError: 参数检验失败
        """
        if value <= 0:
            raise ValueError(f"Argument '{value_name}' must be positive, not {value}")
        return value

    @staticmethod
    def _ensure_ratio(value: _T, value_name: str) -> _T:
        """
        确保参数在[0, 1]之间
        :param value: 参数
        :param value_name: 参数名
        :return: 如果检验成功，则返回原本的参数
        :raise ValueError: 参数检验失败
        """
        if value < 0 or value > 1:
            raise ValueError(f"Argument '{value_name}' must be in [0, 1], not {value}")
        return value

    # noinspection PyPep8Naming
    def __init__(self, T: int, M: int, R: int, N: float, K: float, P: float, Q: float):
        self.T = self._ensure_positive(T, 'T')
        self.M = self._ensure_positive(M, 'M')
        self.R = self._ensure_positive(R, 'R')
        self.N = self._ensure_positive(N, 'N')
        self.K = self._ensure_positive(K, 'K')
        self.P = self._ensure_positive(P, 'P')
        self.Q = self._ensure_ratio(Q, 'Q')


class ColumnNames(NamedTuple):
    DATE: str    # 日期
    OPEN: str    # 开盘价
    CLOSE: str   # 收盘价
    LOW: str     # 最低价
    HIGH: str    # 最高价
    TR: str      # TR


COLUMN_NAMES = ColumnNames('日期', '开盘价(元)', '最高价(元)', '最低价(元)', '收盘价(元)', '真实波动幅度')
PARAMS = AnalyzerParameters(20, 7, 4, 0.5, 2.0, 3.0, 0.6)
