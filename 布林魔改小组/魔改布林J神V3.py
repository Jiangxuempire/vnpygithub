# _*_coding : UTF-8 _*_
# 开发团队 ：yunya
# 开发人员 ：Administrator
# 开发时间 : 2020/6/29 10:57
# 文件名称 ：aberrationstrategy.py
# 开发工具 ： PyCharm

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
from scipy.ndimage.interpolation import shift
import talib as ta


class IndicatorStrategy(CtaTemplate):
    """
    目前使用中轨加速，可以考虑使用另外一根均线来加速，这样可以避免在开仓时被平。
    """
    author = "yunya"

    open_window = 15
    boll_window = 150
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

        self.size = 5
        self.bg = BarGenerator(self.on_bar, self.open_window, self.on_xmin_bar)
        self.am = ArrayManager(self.boll_window * self.size + 5)

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

        #   计算 MTM
        mtm = self.am.close / shift(self.am.close, self.boll_window) - 1
        mtm_mean = ta.SMA(mtm[-self.boll_window * (self.size - 1):], self.boll_window)

        # 计算wd_atr
        close_shift = shift(am.close, 1)
        high_shift = shift(am.high, 1)
        low_shift = shift(am.low, 1)

        close_shift[0] = close_shift[1]
        high_shift[0] = high_shift[1]
        low_shift[0] = low_shift[1]

        c1 = am.high - am.low
        c2 = abs(am.high - close_shift)
        c3 = abs(am.low - close_shift)
        tr = np.max([c1, c2, c3], axis=0)
        atr = ta.SMA(tr, self.boll_window)
        ma = ta.SMA(self.am.close, self.boll_window)
        wd_atr = atr / ma

        # 计算MTM
        mtm_low = am.low / low_shift - 1
        mtm_high = am.high / high_shift - 1
        mtm_close = am.close / close_shift - 1

        mtm_close_shift = shift(mtm_close, 1)
        mtm_close_shift[0] = mtm_close_shift[1]

        mtm_c1 = mtm_high - mtm_low
        mtm_c2 = abs(mtm_high - mtm_close_shift)
        mtm_c3 = abs(mtm_low - mtm_close_shift)
        mtm_tr = np.max([mtm_c1, mtm_c2, mtm_c3], axis=0)

        mtm_atr = ta.SMA(mtm_tr, self.boll_window)

        # 计算MTM均值
        mtm_low_mean = ta.SMA(mtm_low, self.boll_window)
        mtm_high_mean = ta.SMA(mtm_high, self.boll_window)
        mtm_close_mean = ta.SMA(mtm_close, self.boll_window)

        mtm_close_mean_shift = shift(mtm_close_mean[-self.boll_window * (self.size - 2):], 1)
        mtm_close_mean_shift[0] = mtm_close_mean_shift[1]

        mtm_c4 = mtm_high_mean[-self.boll_window * (self.size - 2):] - mtm_low_mean[
                                                                       -self.boll_window * (self.size - 2):]
        mtm_c5 = abs(mtm_high_mean[-self.boll_window * (self.size - 2):] - mtm_close_mean_shift)
        mtm_c6 = abs(mtm_low_mean[-self.boll_window * (self.size - 2):] - mtm_close_mean_shift)

        mtm_tr_2 = np.max([mtm_c4, mtm_c5, mtm_c6], axis=0)
        mtm_atr_mean = ta.SMA(mtm_tr_2, self.boll_window)

        indicator = mtm_mean[-self.boll_window * (self.size - 3):]

        # mtm_mean指标分别乘以三个波动率因子
        indicator = indicator * mtm_atr[-self.boll_window * (self.size - 3):]
        indicator = indicator * mtm_atr_mean[-self.boll_window * (self.size - 3):]
        indicator = indicator * wd_atr[-self.boll_window * (self.size - 3):]

        median = ta.SMA(indicator, self.boll_window)
        self.indicator = indicator
        self.mid = median

        std = ta.STDDEV(indicator * 100000000000000, self.boll_window)
        std = std / 100000000000000
        z = abs(indicator - median) / std
        m = ta.SMA(z, self.boll_window)

        self.up = median[-self.boll_window:] + std[-self.boll_window:] * m[-self.boll_window:]
        self.down = median[-self.boll_window:] - std[-self.boll_window:] * m[-self.boll_window:]

        if not self.pos:
            if self.indicator[-1] > self.up[-1] and self.indicator[-2] <= self.up[-2]:
                self.buy(bar.close_price, self.fixed_size)

            elif self.indicator[-1] < self.down[-1] and self.indicator[-2] >= self.down[-2]:
                self.short(bar.close_price, self.fixed_size)

        elif self.pos > 0:
            if self.indicator[-1] < self.mid[-1] and self.indicator[-2] >= self.mid[-2]:
                self.sell(bar.close_price, abs(self.pos))

        elif self.pos < 0:
            if self.indicator[-1] > self.mid[-1] and self.indicator[-2] <= self.mid[-2]:
                self.cover(bar.close_price, abs(self.pos))

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


