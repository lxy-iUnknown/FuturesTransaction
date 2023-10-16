from dataclasses import dataclass


@dataclass(eq=False, frozen=True)
class AnalyzerParameters:
    T: int    # 突破周期
    M: int    # ATR计算天数
    R: int    # 最大持仓数量
    N: float  # 加仓触发ATR数量
    K: float  # 止损回撤率
    P: float  # 止盈利润倍数
    Q: float  # 止盈回撤比例

    @staticmethod
    def __ensure_positive(value, value_name: str) -> None:
        """
        确保参数大于0
        :param value: 参数
        :param value_name: 参数名
        :return: 如果检验成功，则返回原本的参数
        :raise ValueError: 参数检验失败
        """
        if value <= 0:
            raise ValueError(f"Argument '{value_name}' must be positive, not {value}")

    @staticmethod
    def __ensure_ratio(value, value_name: str) -> None:
        """
        确保参数在[0, 1]之间
        :param value: 参数
        :param value_name: 参数名
        :return: 如果检验成功，则返回原本的参数
        :raise ValueError: 参数检验失败
        """
        if value < 0 or value > 1:
            raise ValueError(f"Argument '{value_name}' must be in [0, 1], not {value}")

    def __post_init__(self):
        self.__ensure_positive(self.T, 'T')
        self.__ensure_positive(self.M, 'M')
        self.__ensure_positive(self.R, 'R')
        self.__ensure_positive(self.N, 'N')
        self.__ensure_positive(self.K, 'K')
        self.__ensure_positive(self.P, 'P')
        self.__ensure_ratio(self.Q, 'Q')


@dataclass(eq=False, frozen=True)
class ColumnNames:
    DATE: str    # 日期
    OPEN: str    # 开盘价
    CLOSE: str   # 收盘价
    LOW: str     # 最低价
    HIGH: str    # 最高价
    TR: str      # TR


COLUMN_NAMES = ColumnNames('日期', '开盘价(元)', '最高价(元)', '最低价(元)', '收盘价(元)', '真实波动幅度')
PARAMS = AnalyzerParameters(20, 7, 4, 0.5, 2.0, 3.0, 0.6)
