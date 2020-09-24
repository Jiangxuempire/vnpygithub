# _*_coding : UTF-8 _*_
# 开发团队 ：yunya
# 开发人员 ：Administrator
# 开发时间 : 2020/6/29 10:57
# 文件名称 ：aberrationstrategy.py
# 开发工具 ： PyCharm
import talib

from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)

# from vnpy.app.cta_strategy.new_strategy import NewBarGenerator
import numpy as np


class IndicatorStrategy(CtaTemplate):
    """
    目前使用中轨加速，可以考虑使用另外一根均线来加速，这样可以避免在开仓时被平。
    """
    author = "yunya"

    open_window = 15
    fast_length = 50
    slow_length = 100
    fixed_size = 1

    condition_long = 0
    condition_short = 0
    indicator_current = 0
    indicator_last = 0
    boll_up_current = 0
    boll_up_last = 0
    boll_down_current = 0
    boll_down_last = 0
    boll_mid_current = 0
    boll_mid_last = 0

    parameters = [
            "open_window",
            "fast_length",
            "slow_length",
            "fixed_size",
    ]

    variables = [
            "condition_long",
            "condition_short",
            "indicator_current",
            "indicator_last",
            "boll_up_current",
            "boll_up_last",
            "boll_down_current",
            "boll_down_last",
            "boll_mid_current",
            "boll_mid_last",

    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar, self.open_window, self.on_xmin_bar)
        self.am = ArrayManager(self.slow_length + 100)

        self.mtm_size: int = self.slow_length

        self.mtm_count: int = 0
        self.mtm_inited: bool = False
        self.mtm_close_array: np.ndarray = np.zeros(self.mtm_size)
        self.mtm_high_array: np.ndarray = np.zeros(self.mtm_size)
        self.mtm_low_array: np.ndarray = np.zeros(self.mtm_size)

        self.mtm_mean_count: int = 0
        self.mtm_mean_inited: bool = False
        self.mtm_close_mean_array: np.ndarray = np.zeros(self.mtm_size)
        self.mtm_high_mean_array: np.ndarray = np.zeros(self.mtm_size)
        self.mtm_low_mean_array: np.ndarray = np.zeros(self.mtm_size)

        self.indicator_count: int = 0
        self.indicator_inited: bool = False
        self.indicator: np.ndarray = np.zeros(self.mtm_size)

        self.indicator_dev_count: int = 0
        self.indicator_dev_inited: bool = False
        self.indicator_dev: np.ndarray = np.zeros(self.mtm_size)

        self.indicator_boll_count: int = 0
        self.indicator_boll_inited: bool = False
        self.boll_up_array: np.ndarray = np.zeros(4)
        self.boll_down_array: np.ndarray = np.zeros(4)
        self.boll_mid_array: np.ndarray = np.zeros(4)

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(20)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)

    def on_xmin_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        am = self.am
        am.update_bar(bar)

        if not am.inited:
            return

        # 获取 mtm 三因子合成数组均值
        self.indicator_boll_array()

        if not self.indicator_boll_inited:
            return

        # 计算 大布林
        sma_array = am.sma(self.slow_length, True)
        std_array = am.std(self.slow_length, True)
        dev = abs(am.close - sma_array) / std_array

        dev_max = dev[-self.slow_length:].mean()
        boll_up_max_array = sma_array[-1] + std_array[-1] * dev_max
        boll_down_max_array = sma_array[-1] - std_array[-1] * dev_max

        # 大于大周期布林上轨，不做空，小于布林下轨，不做多
        self.condition_long = bar.close_price > boll_up_max_array
        self.condition_short = bar.close_price < boll_down_max_array

        self.indicator_current = self.indicator[-1]
        self.indicator_last = self.indicator[-2]
        self.boll_up_current = self.boll_up_array[-1]
        self.boll_up_last = self.boll_up_array[-2]
        self.boll_down_current = self.boll_down_array[-1]
        self.boll_down_last = self.boll_down_array[-2]
        self.boll_mid_current = self.boll_mid_array[-1]
        self.boll_mid_last = self.boll_mid_array[-2]

        # 如果没有仓位，两条布林window一样
        if self.pos == 0:
            condition1 = self.indicator_current > self.boll_up_current
            condition2 = self.indicator_last <= self.boll_up_last

            condition3 = self.indicator_current < self.boll_up_current
            condition4 = self.indicator_last >= self.boll_down_last

            if condition1 and condition2 and self.condition_short:
                self.buy(bar.close_price, self.fixed_size)

            elif condition3 and condition4 and self.condition_long:
                self.short(bar.close_price, self.fixed_size)

        elif self.pos > 0:
            condition1 = self.indicator_current < self.boll_mid_current
            condition2 = self.indicator_last >= self.boll_mid_last
            if condition1 and condition2:
                self.sell(bar.close_price - 10, abs(self.pos))

        elif self.pos < 0:
            condition1 = self.indicator_current > self.boll_mid_current
            condition2 = self.indicator_last <= self.boll_mid_last
            if condition1 and condition2:
                self.cover(bar.close_price + 10, abs(self.pos))

        self.put_event()
        self.sync_data()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        self.put_event()
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        pass
        # if trade.direction == Direction.LONG:
        #     self.trade_price_long = trade.price  # 成交最高价
        #     self.long_stop_trade = self.trade_price_long - self.atr_multiple * self.atr_value
        # else:
        #     self.trade_price_short = trade.price
        #     self.short_stop_trade = self.trade_price_short + self.atr_multiple * self.atr_value
        #
        # self.sync_data()
        # self.put_event()

    def mtm_array(self):
        """
        close,high,low mtm数组

        df['mtm'] = df['close'] / df['close'].shift(n1) - 1
        :return:
        """
        if not self.inited:
            return

        if not self.mtm_inited:
            self.mtm_count += 1
            if self.mtm_count >= self.mtm_size:
                self.mtm_inited = True

        self.mtm_close_array[:-1] = self.mtm_close_array[1:]
        self.mtm_high_array[:-1] = self.mtm_high_array[1:]
        self.mtm_low_array[:-1] = self.mtm_low_array[1:]

        mtm_close = self.am.close[-1] / self.am.close[-self.fast_length] - 1
        mtm_high = self.am.high[-1] / self.am.high[-self.fast_length] - 1
        mtm_low = self.am.low[-1] / self.am.low[-self.fast_length] - 1

        self.mtm_close_array[-1] = mtm_close
        self.mtm_high_array[-1] = mtm_high
        self.mtm_low_array[-1] = mtm_low

    def mtm_mean_array(self):
        """
        计算 close,high,low mtm数组的平均值数组

         df['mtm_mean'] = df['mtm'].rolling(window=n1, min_periods=1).mean()
        :return:
        """
        # 计算 close,high,low mtm数组
        self.mtm_array()
        if not self.mtm_inited:
            return

        if not self.mtm_mean_inited:
            self.mtm_mean_count += 1
            if self.mtm_mean_count >= self.mtm_size:
                self.mtm_mean_inited = True

        self.mtm_close_mean_array[:-1] = self.mtm_close_mean_array[1:]
        self.mtm_high_mean_array[:-1] = self.mtm_high_mean_array[1:]
        self.mtm_low_mean_array[:-1] = self.mtm_low_mean_array[1:]

        mtm_close_mean = self.mtm_close_array[-self.fast_length:].mean()
        mtm_high_mean = self.mtm_high_array[-self.fast_length:].mean()
        mtm_low_mean = self.mtm_low_array[-self.fast_length:].mean()

        self.mtm_close_mean_array[-1] = mtm_close_mean
        self.mtm_high_mean_array[-1] = mtm_high_mean
        self.mtm_low_array[-1] = mtm_low_mean

    def indicator_array(self):

        # 计算 mtm high,low,close 均值数组
        self.mtm_mean_array()

        if not self.mtm_mean_inited:
            return

        if not self.indicator_inited:
            self.indicator_count += 1
            if self.indicator_count >= self.mtm_size:
                self.indicator_inited = True

        self.indicator[:-1] = self.indicator[1:]

        # 计算 atr 相对 close 波动率因子wd_atr
        atr_value = self.am.atr(self.fast_length, True)
        close_ma = self.am.sma(self.fast_length, True)
        wd_atr = atr_value / close_ma

        # 参考ATR，对MTM指标，计算波动率因子
        mtm_atr = talib.ATR(self.mtm_high_array, self.mtm_low_array, self.mtm_close_array, self.fast_length)

        # 参考ATR，对MTM mean指标，计算波动率因子
        mtm_atr_mean = talib.ATR(self.mtm_high_mean_array,
                                 self.mtm_low_mean_array,
                                 self.mtm_close_mean_array,
                                 self.fast_length)

        # 求 均值
        indicator = self.mtm_close_array[-self.fast_length:].mean()

        # mtm_mean指标分别乘以三个波动率因子
        indicator = indicator * mtm_atr[-1]
        indicator = indicator * mtm_atr_mean[-1]
        indicator = indicator * wd_atr[-1]

        self.indicator[-1] = indicator

    def indicator_dev_array(self):
        """
        求 dev 值
        up = ema + dev * std 
        :return:
        """
        # 计算 mtm_mean指标分别乘以三个波动率因子的数组
        self.indicator_array()

        if not self.indicator_inited:
            return

        if not self.indicator_dev_inited:
            self.indicator_dev_count += 1
            if self.indicator_dev_count >= self.mtm_size:
                self.indicator_dev_inited = True

        self.indicator_dev[:-1] = self.indicator_dev[1:]

        # 求 均值
        indicator = self.indicator[-self.fast_length:].mean()
        std = self.indicator[-self.fast_length:].std(ddof=0)
        close_mean = self.am.close[-self.fast_length:].mean()
        dev = abs(indicator - close_mean) / std

        self.indicator_dev[-1] = dev

    def indicator_boll_array(self):
        """
        上下轨
        :return:
        """
        # 计算 mtm_mean指标分别乘以三个波动率因子的数组
        self.indicator_dev_array()

        if not self.indicator_dev_inited:
            return

        if not self.indicator_boll_inited:
            self.indicator_boll_count += 1
            if self.indicator_boll_count >= self.mtm_size:
                self.indicator_boll_inited = True

        self.boll_up_array[:-1] = self.boll_up_array[1:]
        self.boll_down_array[:-1] = self.boll_down_array[1:]
        self.boll_mid_array[:-1] = self.boll_mid_array[1:]

        # 求 均值
        indicator = self.indicator[-self.fast_length:].mean()
        std = self.indicator[-self.fast_length:].std(ddof=0)
        dev = self.indicator_dev[-self.fast_length:].min()

        up = indicator + std * dev
        down = indicator - std * dev

        self.boll_up_array[-1] = up
        self.boll_down_array[-1] = down
        self.boll_mid_array[-1] = indicator
