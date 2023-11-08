import datetime
import enum
import math
import warnings

import numpy as np
import pandas as pd

from util.constants import TRANSACTION_PARAMS, HIGH, LOW, HIGH_MAX, LOW_MIN, TR, ATR

ATR_START_DATE = TRANSACTION_PARAMS.T + TRANSACTION_PARAMS.M


class EnterType(enum.StrEnum):
    LongPosition = '开多'
    ShortPosition = '开空'
    Undefined = ''


class ExitType(enum.StrEnum):
    LongProfit = '止盈多平'
    LongLoss = '止损空平'
    ShortProfit = '止盈空平'
    ShortLoss = '止损空平'
    Expired = '到期离市'
    Undefined = ''


class Transaction:
    def __init__(self, input_data: pd.DataFrame, output_data: pd.DataFrame):
        tr_series = input_data[TR]
        # 计算前T日ATR
        series = pd.concat([
            pd.Series(np.full(ATR_START_DATE, np.nan)),
            pd.Series(tr_series[TRANSACTION_PARAMS.T + 1: ATR_START_DATE + 1].mean(skipna=False)),
            tr_series[ATR_START_DATE + 1:],
        ], ignore_index=True)
        # 计算前T日最高价和最低价
        input_data[HIGH_MAX] = input_data[HIGH].rolling(window=TRANSACTION_PARAMS.T, closed='left').max()
        input_data[LOW_MIN] = input_data[LOW].rolling(window=TRANSACTION_PARAMS.T, closed='left').min()
        # 计算前T日ATR
        input_data[ATR] = series.ewm(alpha=1.0 / TRANSACTION_PARAMS.M, adjust=False).mean().fillna(0)

        self._input = input_data
        self._output = output_data
        self._last_index = len(input_data) - 1

        self._tr_series: pd.Series = input_data[TR]  # 输入数据TR

        self._positions: list[float] = []  # 每一次开仓价格

        self._clear_all()

    # noinspection PyTypeChecker
    def _clear_all(self):
        self._positions.clear()

        self._current_profit = math.nan  # 当前利润

        self._enter_type = EnterType.Undefined
        self._enter_time: datetime.datetime = pd.NaT  # 入市时间
        self._enter_price = math.nan  # 入市价格
        self._enter_atr = math.nan  # 入市ATR

        self._exit_type = ExitType.Undefined  # 离市类型
        self._exit_time: datetime.datetime = pd.NaT  # 离市时间
        self._exit_profit = math.nan  # 离市利润

        self._max_profit = -math.inf  # 入市以来最高利润（由于利润有可能是负数，因此初始化为-∞）

        self._stop_profit_prepared = False  # 是否已准备止盈

    @property
    def _last_open_price(self):
        """
        获取上一次开仓价格
        :return: 上一次开仓价格
        """
        return math.nan if self._position_count == 0 else self._positions[-1]

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

    @property
    def _exiting(self):
        """
        判断是否正在离市
        :return: 是否正在离市
        """
        return self._exit_type != ExitType.Undefined

    def _enter_common(self, time_today: datetime.datetime,
                      enter_type: EnterType, enter_price: float, atr: float):
        """
        记录入市时间、入市类型、入市价格（此前T日最高价格）、入市ATR
        :param enter_price: 入市价格
        :param time_today: 当日日期
        :param enter_type: 入市类型
        :param atr: 当日ATR
        :return:
        """
        self._positions.append(enter_price)
        self._enter_time = time_today
        self._enter_price = enter_price
        self._enter_type = enter_type
        self._enter_atr = atr

    def _enter(self, time_today: datetime.datetime, high: float, low: float,
               high_max: float, low_min: float, atr: float):
        """
        入市操作
        :param time_today: 当日日期
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
            self._enter_common(time_today, EnterType.LongPosition, high_max, atr)
        elif low < low_min:
            # 当日最低价低于此前T日最低价格
            self._enter_common(time_today, EnterType.ShortPosition, high_max, atr)

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
        if not self._entered or self._position_count >= TRANSACTION_PARAMS.R:
            return
        price_break = TRANSACTION_PARAMS.N * atr
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
        self._current_profit = profit
        self._max_profit = max(self._max_profit, profit)

    def _calculate_profit(self, price: float):
        """
        计算并更新当日持仓利润和最大利润
        :param price: 利润计算价格
        :return:
        """
        if self._entered:
            profit = price * self._position_count - sum(self._positions)
            if self._enter_type == EnterType.ShortPosition:
                profit = -profit
            self._update_profit(profit)

    def _exiting_common(self, time_today: datetime.datetime, exit_type: ExitType):
        """
        准备离市
        :param time_today: 当日日期
        :param exit_type: 离市类型
        :return:
        """
        self._exit_type = exit_type
        self._exit_time = time_today
        self._exit_profit = self._current_profit

    def _exiting_with_price(self, time_today: datetime.datetime,
                            exit_price: float, exit_type: ExitType):
        """
        准备离市（使用离市价格计算离市利润）
        :param time_today: 当日日期
        :param exit_price 离市价格
        :param exit_type: 离市类型
        :return:
        """
        self._calculate_profit(exit_price)
        self._exiting_common(time_today, exit_type)

    def _exiting_with_profit(self, time_today: datetime.datetime,
                             exit_profit: float, exit_type: ExitType):
        """
        准备离市（直接使用离市利润）
        :param time_today: 当日日期
        :param exit_profit 离市利润
        :param exit_type: 离市类型
        :return:
        """
        self._update_profit(exit_profit)
        self._exiting_common(time_today, exit_type)

    def _stop_loss(self, time_today: datetime.datetime, high: float, low: float):
        """
        止损操作
        :param time_today: 当日日期
        :param high: 当日最高价
        :param low: 当日最低价
        :return:
        """
        if not self._entered:
            return
        if self._enter_type == EnterType.LongPosition:
            # 当日最低价小于K倍入市ATR和上一次开仓价之差
            exit_price = self._last_open_price - TRANSACTION_PARAMS.K * self._enter_atr
            if low < exit_price:
                self._exiting_with_price(time_today, exit_price, ExitType.LongLoss)
        elif self._enter_type == EnterType.ShortPosition:
            # 当日最高价大于K倍入市ATR和上一次开仓价之和
            exit_price = self._last_open_price + TRANSACTION_PARAMS.K * self._enter_atr
            if high > exit_price:
                self._exiting_with_price(time_today, exit_price, ExitType.ShortLoss)

    def _stop_profit(self, time_today: datetime.datetime, atr: float):
        """
        止盈操作
        :param time_today: 当日日期
        :param atr: 当日ATR
        :return:
        """
        if self._stop_profit_prepared:
            # 当前利润小于入市以来最高利润的比例Q时正式止盈
            exit_profit = TRANSACTION_PARAMS.Q * self._max_profit
            if self._current_profit < exit_profit:
                if self._enter_type == EnterType.LongPosition:
                    self._exiting_with_profit(time_today, exit_profit, ExitType.LongProfit)
                elif self._enter_type == EnterType.ShortPosition:
                    self._exiting_with_profit(time_today, exit_profit, ExitType.ShortProfit)
                self._stop_profit_prepared = False
        elif self._entered and self._current_profit > TRANSACTION_PARAMS.P * atr:
            # 当前利润超过P个当日ATR时准备止盈
            self._stop_profit_prepared = True

    def _expire(self, index: int, time_today: datetime.datetime, close_price: float):
        """
        :param time_today: 当日日期
        :param close_price: 收盘价
        :return:
        """
        # 日期到达最后一天
        if self._entered and index == self._last_index:
            self._exiting_with_price(time_today, close_price, ExitType.Expired)

    def _write_info(self, index: int, time_today: int, high: float,
                    low: float, open_price: float, close_price: float,
                    high_max: float, low_min: float, atr: float):
        """
        输出当日信息
        :param index: 日期下标
        :param time_today: 当日日期
        :param high: 当日最高价
        :param low: 当日最低价
        :param open_price: 当日开盘价
        :param close_price: 当日收盘价
        :param atr: 当日ATR
        :return:
        """
        if self._entered:
            enter_time = self._enter_time
            enter_type = self._enter_type
            enter_atr = self._enter_atr
            enter_price = self._enter_price

            position_count = self._position_count
            if enter_type == EnterType.LongPosition:
                long_position_count = position_count
                short_position_count = 0
            else:
                short_position_count = position_count
                long_position_count = 0

            max_profit = self._max_profit
            current_profit = self._current_profit
            exit_type = self._exit_type
            exit_time = self._exit_time
            exit_profit = self._exit_profit
        else:
            enter_time = pd.NaT
            enter_type = EnterType.Undefined
            enter_atr = math.nan
            enter_price = math.nan

            long_position_count = 0
            short_position_count = 0

            max_profit = math.nan
            current_profit = math.nan
            exit_type = ExitType.Undefined
            exit_time = pd.NaT
            exit_profit = math.nan

        if index < ATR_START_DATE:
            atr = math.nan

        # https://github.com/pandas-dev/pandas/issues/39122
        # https://github.com/pandas-dev/pandas/pull/52532
        with warnings.catch_warnings(action='ignore', category=FutureWarning):
            self._output.loc[index - TRANSACTION_PARAMS.T] = (
                time_today, atr, high, low, open_price, close_price, enter_time, str(enter_type),
                enter_atr, enter_price, long_position_count, short_position_count, high_max,
                low_min, max_profit, current_profit, str(exit_type), exit_time, exit_profit
            )
        if self._exiting:
            # 清空所有数据
            self._clear_all()

    def transact(self):
        for index, time_today, open_price, close_price, \
                high, low, tr, high_max, low_min, atr \
                in self._input[TRANSACTION_PARAMS.T:].itertuples(name=None):
            self._enter(time_today, high, low, high_max, low_min, atr)
            self._add_position(high, low, atr)
            self._calculate_profit(close_price)
            self._stop_loss(time_today, high, low)
            self._stop_profit(time_today, atr)
            self._expire(index, time_today, close_price)
            self._write_info(index, time_today, high, low,
                             open_price, close_price, high_max, low_min, atr)
