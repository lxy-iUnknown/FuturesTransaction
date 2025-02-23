import enum
import math

import numpy as np
import pandas as pd

from data.data_io import load_data
from util.constants import HIGH, LOW, HIGH_MAX, LOW_MIN, TR, ATR
from util.transaction_params import TransactionParams


class EnterType(enum.IntEnum):
    LongPosition = 0
    ShortPosition = 1
    Undefined = -1


class TransactionProfit:
    def __init__(self, params: TransactionParams | None = None):
        input_data = load_data()
        self._input = input_data
        self._last_index = len(input_data) - 1

        self._high_window = input_data[HIGH].rolling(window=0, closed='left')
        self._low_window = input_data[LOW].rolling(window=0, closed='left')
        self._tr_series: pd.Series = input_data[TR]  # 输入数据TR

        self._positions: list[float] = []  # 每一次开仓价格

        self._clear_all()

        if params:
            self._set_params(params)

    def _clear_all(self):
        self._positions.clear()

        self._current_profit = math.nan  # 当前利润

        # 状态：
        # 1. 未入市 (enter_type == Undefined, exiting == False)
        # 2. 已入市但未离市 (enter_type != Undefined, exiting == True)
        # 3. 已入市且正在离市 (enter_type != Undefined, exiting == False)
        self._enter_type = EnterType.Undefined
        self._enter_price = math.nan  # 入市价格
        self._enter_atr = math.nan  # 入市ATR

        self._exiting = False  # 是否正在离市

        self._max_profit = -math.inf  # 入市以来最高利润（由于利润有可能是负数，因此初始化为-∞）

        self._stop_profit_prepared = False  # 是否已准备止盈

    @property
    def _last_open_price(self):
        """
        获取上一次开仓价格
        :return: 上一次开仓价格
        """
        assert self._position_count != 0, '未开仓'
        return self._positions[-1]

    @property
    def _position_count(self):
        """
        获取持仓数目
        :return: 持仓数目
        """
        return len(self._positions)

    @property
    def _entered(self):
        """
        判断是否已入市
        :return: 是否已入市
        """
        return self._enter_type != EnterType.Undefined

    def _enter_common(self, enter_type: EnterType, enter_price: float, atr: float):
        """
        记录入市时间、入市类型、入市价格（此前T日最高价格）、入市ATR
        :param enter_price: 入市价格
        :param enter_type: 入市类型
        :param atr: 当日ATR
        :return:
        """
        self._positions.append(enter_price)
        self._enter_price = enter_price
        self._enter_type = enter_type
        self._enter_atr = atr

    def _enter(self, high: float, low: float, high_max: float, low_min: float, atr: float):
        """
        入市操作
        :param high: 当日最高价
        :param low: 当日最低价
        :param high_max: 前T日最高价
        :param low_min: 前T日最低价
        :param atr: 当日ATR
        :return:
        """
        if self._entered:
            return
        if high > high_max:
            # 当日最高价高于此前T日最高价格
            self._enter_common(EnterType.LongPosition, high_max, atr)
        elif low < low_min:
            # 当日最低价低于此前T日最低价格
            self._enter_common(EnterType.ShortPosition, high_max, atr)

    def _add_common(self, add_price: float):
        """
        加仓操作
        :param add_price: 加仓价格
        :return:
        """
        self._positions.append(add_price)

    def _add_position(self, high: float, low: float, atr: float):
        """
        加仓操作
        :param high: 当日最高价
        :param low: 当日最低价
        :param atr: 当日ATR
        :return:
        """
        if not self._entered or self._position_count >= self._params.R:
            return
        price_break = self._params.N * atr
        if self._enter_type == EnterType.LongPosition:
            # 当日最高价高于上一次开仓价加上N个当日ATR
            open_price = self._last_open_price + price_break
            if high > open_price:
                self._add_common(open_price)
        elif self._enter_type == EnterType.ShortPosition:
            # 当日最低价低于上一次开仓价加上N个当日ATR
            open_price = self._last_open_price - price_break
            if low < open_price:
                self._add_common(open_price)

    def _update_profit(self, profit: float):
        """
        更新当日持仓利润和最大利润
        :param profit: 当日持仓利润
        :return:
        """
        max_profit = self._max_profit
        self._current_profit = profit
        # 两个数最大值的特化(specialization)版本，因为max函数支持任意多个参数
        self._max_profit = max_profit if max_profit > profit else profit

    def _calculate_profit(self, price: float):
        """
        计算并更新当日持仓利润和最大利润
        :param price: 利润计算价格
        :return:
        """
        if not self._entered:
            return
        profit = price * self._position_count - sum(self._positions)
        if self._enter_type == EnterType.ShortPosition:
            profit = -profit
        self._update_profit(profit)

    def _exiting_with_price(self, exit_price: float):
        """
        准备离市（使用离市价格计算离市利润）
        :param exit_price 离市价格
        :return:
        """
        self._calculate_profit(exit_price)
        self._exiting = True

    def _exiting_with_profit(self, exit_profit: float):
        """
        准备离市（直接使用离市利润）
        :param exit_profit 离市利润
        :return:
        """
        self._update_profit(exit_profit)
        self._exiting = True

    def _stop_loss(self, high: float, low: float):
        """
        止损操作
        :param high: 当日最高价
        :param low: 当日最低价
        :return:
        """
        if not self._entered:
            return
        if self._enter_type == EnterType.LongPosition:
            # 当日最低价小于K倍入市ATR和上一次开仓价之差
            exit_price = self._last_open_price - self._params.K * self._enter_atr
            if low < exit_price:
                self._exiting_with_price(exit_price)
        elif self._enter_type == EnterType.ShortPosition:
            # 当日最高价大于K倍入市ATR和上一次开仓价之和
            exit_price = self._last_open_price + self._params.K * self._enter_atr
            if high > exit_price:
                self._exiting_with_price(exit_price)

    def _stop_profit(self, atr: float):
        """
        止盈操作
        :param atr: 当日ATR
        :return:
        """
        if self._stop_profit_prepared:
            # 当前利润小于入市以来最高利润的比例Q时正式止盈
            exit_profit = self._params.Q * self._max_profit
            if self._current_profit < exit_profit:
                self._exiting_with_profit(exit_profit)
                self._stop_profit_prepared = False
        elif self._entered and self._current_profit > self._params.P * atr:
            # 当前利润超过P个当日ATR时准备止盈
            self._stop_profit_prepared = True

    def _expire(self, index: int, close_price: float):
        """
        :param close_price: 收盘价
        :return:
        """
        # 日期到达最后一天
        if self._entered and index == self._last_index:
            self._exiting_with_price(close_price)

    # noinspection PyPep8Naming
    def _calculate_min_max(self, T: int):
        # 设置滑动窗口大小
        self._high_window.window = T
        self._low_window.window = T
        # 计算前T日最高价和最低价
        return self._high_window.max(), self._low_window.min()

    # noinspection PyPep8Naming
    def _calculate_atr(self, T: int, M: int):
        atr_start_date = T + M
        # 计算前T日ATR
        series = pd.concat([
            # 前T + M日用NaN填充不会影响最终的计算结果
            pd.Series(np.full(atr_start_date, np.nan)),
            pd.Series(self._tr_series[T + 1: atr_start_date + 1].mean()),
            self._tr_series[atr_start_date + 1:],
        ], ignore_index=True)
        return series.ewm(alpha=1.0 / M, adjust=False, ignore_na=False).mean().fillna(0)

    def _set_params(self, params: TransactionParams):
        self._params = params
        # 计算前T日最高价和最低价
        high_max, low_min = self._calculate_min_max(params.T)
        # 计算前T日ATR
        atr = self._calculate_atr(params.T, params.M)
        # 插入数据
        input_data = self._input
        input_data[HIGH_MAX] = high_max
        input_data[LOW_MIN] = low_min
        input_data[ATR] = atr

    def with_params(self, params: TransactionParams):
        self._set_params(params)
        return self

    def transact(self):
        assert self._params is not None, 'No parameters'
        last_profit = 0.0
        for index, _, open_price, close_price, \
                high, low, tr, high_max, low_min, atr in (
                self._input[self._params.T:].itertuples(name=None)):
            self._enter(high, low, high_max, low_min, atr)
            self._add_position(high, low, atr)
            self._calculate_profit(close_price)
            self._stop_loss(high, low)
            self._stop_profit(atr)
            self._expire(index, close_price)
            if self._exiting:
                last_profit = self._current_profit
                self._clear_all()
        return last_profit
