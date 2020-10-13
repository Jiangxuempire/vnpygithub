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
    boll_window = 10
    slow_length = 55
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
        self.am = ArrayManager(self.boll_window * 3 + 50)

        self.count: int = 0
        self.count_boll: int = 0
        self.indicator_inited: bool = False
        self.boll_inited: bool = False
        self.mtm_size: int = self.slow_length

        self.indicator_np_array: np.ndarray = np.zeros(self.boll_window * 3 + 5)

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

        indicator = self.indicator_array(
            self.am.high,
            self.am.low,
            self.am.close,
            self.boll_window,
            self.indicator_np_array)

        if not self.indicator_inited:
            return

        # 自适应布林带
        median = ta.SMA(indicator, self.boll_window)
        std = np.std(indicator, axis=0)
        z_score = abs(indicator - median) / std
        m_z = z_score[-self.boll_window - 1:-2].max()
        up = median + std * m_z
        dn = median - std * m_z

        if indicator[-1] > up[-1] and indicator[-2] <= up[-2]:
            print("开多" + "\n")
        elif indicator[-1] < median[-1] and indicator[-2] >= median[-2]:
            print("平多" + "\n")

        if indicator[-1] < dn[-1] and indicator[-2] >= dn[-2]:
            print("开空" + "\n")
        elif indicator[-1] > median[-1] and indicator[-2] <= median[-2]:
            print("平空" + "\n")

        #
        # exit()
        #
        # # 计算 大布林
        # sma_array = am.sma(self.slow_length, True)
        # std_array = am.std(self.slow_length, True)
        # dev = abs(self.am.close[:-1] - sma_array[:-1]) / std_array[:-1]
        #
        # dev_max = dev[-self.slow_length:].mean()
        # boll_up_max_array = sma_array + std_array * dev_max
        # boll_down_max_array = sma_array - std_array * dev_max
        #
        # boll_up_max = boll_up_max_array[-1]
        # boll_down_max = boll_down_max_array[-1]
        #
        # # 大于大周期布林上轨，不做空，小于布林下轨，不做多
        # if bar.close_price > boll_up_max:
        #     self.condition_long = True
        # else:
        #     self.condition_long = False
        #
        # if bar.close_price < boll_down_max:
        #     self.condition_short = True
        # else:
        #     self.condition_short = False
        #
        # self.indicator_current = self.indicator[-1]
        # self.indicator_last = self.indicator[-2]
        # self.boll_up_current = self.boll_up_array[-1]
        # self.boll_up_last = self.boll_up_array[-2]
        # self.boll_down_current = self.boll_down_array[-1]
        # self.boll_down_last = self.boll_down_array[-2]
        # self.boll_mid_current = self.boll_mid_array[-1]
        # self.boll_mid_last = self.boll_mid_array[-2]
        #
        # # 如果没有仓位，两条布林window一样
        # if self.pos == 0:
        #     condition1 = self.indicator_current > self.boll_up_current
        #     condition2 = self.indicator_last <= self.boll_up_last
        #
        #     condition3 = self.indicator_current < self.boll_up_current
        #     condition4 = self.indicator_last >= self.boll_down_last
        #
        #     if condition1 and condition2:
        #         # 在大网下轨，不做多
        #         if self.condition_short:
        #             self.buy(bar.close_price + 10, self.fixed_size)
        #
        #     elif condition3 and condition4:
        #         # 在大网上轨，不做空
        #         if self.condition_long:
        #             self.short(bar.close_price - 10, self.fixed_size)
        #
        # elif self.pos > 0:
        #     condition1 = self.indicator_current < self.boll_mid_current
        #     condition2 = self.indicator_last >= self.boll_mid_last
        #     if condition1 and condition2:
        #         self.sell(bar.close_price - 10, abs(self.pos))
        #
        # elif self.pos < 0:
        #     condition1 = self.indicator_current > self.boll_mid_current
        #     condition2 = self.indicator_last <= self.boll_mid_last
        #     if condition1 and condition2:
        #         self.cover(bar.close_price + 10, abs(self.pos))
        #
        # self.put_event()
        # self.sync_data()

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

    def atr_wd(self, high, low, close, n):
        """
        计算 atr 相对 close 的波动因子
        """
        atr = ta.ATR(high, low, close, n)
        ma = ta.SMA(close, n)

        wd_atr = atr / ma

        return wd_atr[-1]

    def mtm_atr(self, high, low, close, n):
        """
        1、计算 mtm值（用去掉量纲方式计算）
        2、用 atr 的方式计算得到 mtm_atr
        """
        # 计算MTM值
        high_shift = shift(high, 1)
        low_shift = shift(low, 1)
        close_shift = shift(close, 1)

        # 补全
        high_shift[0] = high_shift[1]
        low_shift[0] = low_shift[1]
        close_shift[0] = close_shift[1]

        # 计算mtm
        mtm_high = high / high_shift - 1
        mtm_low = low / low_shift - 1
        mtm_close = close / close_shift - 1

        mtm_atr = ta.ATR(mtm_high, mtm_low, mtm_close, n)

        return mtm_atr[-1]

    def mem_atr_mean_array(self, high, low, close, n):
        """
        :return:
        """
        # 计算MTM值
        high_shift = shift(high, 1)
        low_shift = shift(low, 1)
        close_shift = shift(close, 1)

        # 补全
        high_shift[0] = high_shift[1]
        low_shift[0] = low_shift[1]
        close_shift[0] = close_shift[1]

        # 计算mtm
        mtm_high = high / high_shift - 1
        mtm_low = low / low_shift - 1
        mtm_close = close / close_shift - 1

        # 计算MTM均值
        mtm_high_mean = ta.SMA(mtm_high, n)
        mtm_low_mean = ta.SMA(mtm_low, n)
        mtm_close_mean = ta.SMA(mtm_close, n)
        mtm_mean_atr = ta.ATR(mtm_high_mean, mtm_low_mean, mtm_close_mean, n)

        return mtm_mean_atr[-1]

    def indicator_array(self, high, low, close, n, indicator_np):
        """
        :return:
        """
        self.count += 1
        if not self.indicator_inited and self.count >= self.mtm_size:
            self.indicator_inited = True

        indicator_np[:-1] = indicator_np[1:]
        close_shift = shift(close, 1)
        close_shift[0] = close_shift[1]
        mtm_close = close / close_shift - 1
        close_mtm = ta.SMA(mtm_close, n)[-1]

        atr_wd = self.atr_wd(high, low, close, n)
        mtm_atr = self.mtm_atr(high, low, close, n)
        mtm_atr_mean = self.mem_atr_mean_array(high, low, close, n)

        indicator = close_mtm * atr_wd * mtm_atr * mtm_atr_mean
        indicator_np[-1] = indicator

        return indicator_np

    # def boll_indicator(self, high, low, close, n, indicator_np):
    #
    #     indicator_np = self.indicator_array(high, low, close, n, indicator_np)
    #
    #     if not self.indicator_inited:
    #         return
    #
    #     self.count_boll += 1
    #     if not self.boll_inited and self.count_boll >= self.mtm_size:
    #         self.boll_inited = True
    #
    #     median = ta.SMA(indicator_np, self.boll_window)
    #     std = np.std(indicator_np, axis=0)
    #     z_score = abs(indicator_np - median) / std
    #     m_z = z_score[-self.boll_window - 1:-2].max()
    #     up = median + std * m_z
    #     dn = median - std * m_z
    #     print(up)
