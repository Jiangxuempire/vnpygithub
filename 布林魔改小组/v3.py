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
    fast_length = 5
    slow_length = 5
    fixed_size = 1

    condition_long = False
    condition_short = False
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
        self.am = ArrayManager(int(self.fast_length) * 5 + 5)

        self.mtm_size: int = self.fast_length * 2

        self.mtm_count: int = 0
        self.mtm_atr_inited: bool = False
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

        self.indicator_boll_array()

        if not self.indicator_boll_inited:
            return



        # 计算 大布林
        sma_array = am.sma(self.slow_length, True)
        std_array = am.std(self.slow_length, True)
        dev = abs(self.am.close[:-1] - sma_array[:-1]) / std_array[:-1]

        dev_max = dev[-self.slow_length:].mean()
        boll_up_max_array = sma_array + std_array * dev_max
        boll_down_max_array = sma_array - std_array * dev_max

        boll_up_max = boll_up_max_array[-1]
        boll_down_max = boll_down_max_array[-1]

        # 大于大周期布林上轨，不做空，小于布林下轨，不做多
        if bar.close_price > boll_up_max:
            self.condition_long = True
        # else:
        #     self.condition_long = False

        if bar.close_price < boll_down_max:
            self.condition_short = True
        # else:
        #     self.condition_short = False

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

            if condition1 and condition2:
                # 在大网下轨，不做多
                if self.condition_short:
                    self.buy(bar.close_price + 10, self.fixed_size)

            elif condition3 and condition4:
                # 在大网上轨，不做空
                if self.condition_long:
                    self.short(bar.close_price - 10, self.fixed_size)

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

    def atr_wd(self):
        """
        计算 atr 相对 close 的波动因子
        """
        if not self.inited:
            return

        atr = atr_array(self.am.high, self.am.low, self.am.close, self.fast_length)
        avg_close = np.mean(self.am.close[-self.fast_length:])
        wd_atr = atr / avg_close
        return wd_atr

    def mtm_atr(self):
        """
        1、计算 mtm值（用去掉量纲方式计算）
        2、用 atr 的方式计算得到 mtm_atr
        """
        if not self.inited:
            return

        if not self.mtm_atr_inited:
            self.mtm_count += 1
            if self.mtm_count >= self.mtm_size:
                self.mtm_atr_inited = True

        self.mtm_close_mean_array[:-1] = self.mtm_close_mean_array[1:]
        self.mtm_high_mean_array[:-1] = self.mtm_high_mean_array[1:]
        self.mtm_low_mean_array[:-1] = self.mtm_low_mean_array[1:]

        mtm_low = self.am.low[-self.fast_length:] / self.am.low[-self.fast_length - 1: -1] - 1
        mtm_high = self.am.high[-self.fast_length:] / self.am.high[-self.fast_length - 1: -1] - 1
        mtm_close = self.am.close[-self.fast_length:] / self.am.close[-self.fast_length - 1: -1] - 1

        mtm_atr = atr_array(high=mtm_high, low=mtm_low, close=mtm_close, n=self.fast_length)

        # 计算 mean
        mtm_low_mean = np.mean(mtm_low)
        mtm_high_mean = np.mean(mtm_high)
        mtm_close_mean = np.mean(mtm_close)

        self.mtm_close_mean_array[-1] = mtm_close_mean
        self.mtm_high_mean_array[-1] = mtm_high_mean
        self.mtm_low_array[-1] = mtm_low_mean

        return mtm_atr

    def mtm_atr_mean(self):
        """
        1、计算 mtm值（用去掉量纲方式计算），后求均值，再计算 mtm_atr_mean
        """
        if not self.inited:
            return

        if not self.mtm_atr_inited:
            return

        mtm_atr_mean = atr_array(high=self.mtm_high_mean_array,
                                 low=self.mtm_low_mean_array,
                                 close=self.mtm_close_mean_array,
                                 n=self.fast_length)
        return mtm_atr_mean

    def indicator_dev_array(self):
        """
        :return:
        """
        if not self.mtm_atr_inited:
            return

        if not self.indicator_dev_inited:
            self.indicator_dev_count += 1
            if self.indicator_dev_count >= self.mtm_size:
                self.indicator_dev_inited = True

        atr_wd = self.atr_wd()
        mtm_atr = self.mtm_atr()
        mtm_atr_mean = self.mtm_atr_mean()

        indicator = self.am.close[-self.fast_length:] / self.am.close[-self.fast_length - 1: -1] - 1

        indicator = indicator * atr_wd
        indicator = indicator * mtm_atr
        indicator = indicator * mtm_atr_mean

        mean = indicator[-self.fast_length:].mean()
        std = indicator[-self.fast_length:].std(ddof=0)
        dev = abs(indicator[-1] - mean) / std

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
        dev = self.indicator_dev[-self.fast_length:].max()

        up = indicator + std * dev
        down = indicator - std * dev

        self.boll_up_array[-1] = up
        self.boll_down_array[-1] = down
        self.boll_mid_array[-1] = indicator
