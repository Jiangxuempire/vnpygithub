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


import talib as ta
import numpy as np
from scipy.ndimage.interpolation import shift


class AdaptBollStrategy(CtaTemplate):
    """"""

    author = "用Python的交易员"

    boll_window = 10
    fixed_size = 1

    boll_up = 0
    boll_down = 0
    cci_value = 0
    atr_value = 0

    intra_trade_high = 0
    intra_trade_low = 0
    long_stop = 0
    short_stop = 0

    parameters = [
        "boll_window",
        "boll_dev",
        "cci_window",
        "atr_window",
        "sl_multiplier",
        "fixed_size"
    ]
    variables = [
        "boll_up",
        "boll_down",
        "cci_value",
        "atr_value",
        "intra_trade_high",
        "intra_trade_low",
        "long_stop",
        "short_stop"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager(self.boll_window * 2)

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(10)

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
        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        # 计算wd_atr
        atr = am.atr(self.boll_window, array=True)
        ma = am.sma(self.boll_window, array=True)
        wd_atr = atr / ma

        # 计算MTM值
        high_shift = shift(am.high, 1)
        low_shift = shift(am.low, 1)
        close_shift = shift(am.close, 1)

        # 补全
        high_shift[0] = high_shift[1]
        low_shift[0] = low_shift[1]
        close_shift[0] = close_shift[1]

        # 计算mtm
        mtm_high = am.high / high_shift - 1
        mtm_low = am.low / low_shift - 1
        mtm_close = am.close / close_shift - 1

        mtm_atr = ta.ATR(mtm_high, mtm_low, mtm_close, self.boll_window)

        # 计算MTM均值
        mtm_high_mean = ta.SMA(mtm_high, self.boll_window)
        mtm_low_mean = ta.SMA(mtm_low, self.boll_window)
        mtm_close_mean = ta.SMA(mtm_close, self.boll_window)
        mtm_mean_atr = ta.ATR(
            mtm_high_mean, mtm_low_mean, mtm_close_mean, self.boll_window
        )

        # 平滑因子
        indicator = mtm_close_mean
        indicator = indicator * wd_atr * mtm_atr * mtm_mean_atr

        print(indicator)

        # 自适应布林带
        median = ta.SMA(indicator, self.boll_window)

        std = ta.STDDEV(indicator, self.boll_window)
        z_score = abs(indicator - median) / std
        m = z_score[-self.boll_window-1:-2].max()
        up = median + std * m
        dn = median - std * m

        print(f"上轨：{up}")

        # 交易逻辑跟其他策略写法类似了，注意上面所有变量，都是numpy.array，最新值访问：dn[-1]
        




    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
