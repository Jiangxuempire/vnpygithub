# _*_coding : utf_8 _*_


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
import talib
import numpy as np
from vnpy.trader.constant import Interval, Direction, Offset


class DudlThrustV1(CtaTemplate):
    """"""
    author = "yunyu"

    hour_window = 4
    open_window = 15
    rolling_period = 10
    upper_lower = 0.1
    dc_length = 20
    atr_length = 16
    fixed_size = 1

    bar_time = 0
    up = 0
    down = 0
    exit_short = 0
    exit_long = 0
    atr_value = 0
    intra_trade_high = 0
    intra_trade_low = 0
    long_stop = 0
    short_stop = 0
    long_entry = 0
    short_entry = 0
    ask = 0
    bid = 0

    # 画图专用
    time_list = []
    open_list = []
    high_list = []
    low_list = []
    close_list = []
    volume_list = []
    up_list = []
    down_list = []
    mid_list = []
    mid_new_list = []
    exit_long_list = []
    exit_short_list = []
    bias_value_list = []
    bias_list = []
    singnal_plot = []
    singnal_list = None
    singnal = None

    plot_echarts = {}

    parameters = [
        "window_min",
        "rolling_period",
        "upper_open",
        "lower_open",
        "stop_multiplier",
        "fixed_size",
    ]

    variables = [
        "up",
        "down",
        "intra_trade_high",
        "intra_trade_low",
        "long_stop",
        "short_stop",
        "long_entry",
        "short_entry",
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(on_bar=self.on_bar,
                               window=self.open_window,
                               on_window_bar=self.on_min_bar,
                               interval=Interval.MINUTE)

        self.am = ArrayManager()

        self.bg_m = BarGenerator(on_bar=self.on_bar,
                                 window=self.open_window,
                                 on_window_bar=self.on_hour_bar,
                                 interval=Interval.HOUR)

        self.am_m = ArrayManager()

        self.bar_open = 0

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
        self.ask = tick.ask_price_1  # 卖一价
        self.bid = tick.bid_price_1  # 买一价

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg_m.update_bar(bar)
        self.bg.update_bar(bar)

    def on_min_bar(self, bar: BarData):
        """
        1、大周期计算出轨道，每个周期只做一次多单，空单  通过bar.time 来判断是不是新的一个周期。
        2、小周期开平逻辑，止赢止损逻辑
        """
        self.cancel_all()

        self.am.update_bar(bar)

        if not self.am.inited and not self.am_m.inited:
            return

        if self.up <= 0 or self.down <= 0:
            return

        self.exit_short, self.exit_long = self.am.donchian(self.dc_length)

        if not self.pos:
            self.atr_value = self.am.atr(self.atr_length)

            if bar.close_price > self.bar_open:
                self.buy(self.up, self.fixed_size, True)

            elif bar.close_price < self.bar_open:
                self.short(self.down, self.fixed_size, True)

        elif self.pos > 0:
            self.sell(self.exit_long, abs(self.pos), True)

        elif self.pos < 0:
            self.cover(self.exit_short, abs(self.pos), True)

        # # 画图专用
        # if self.singnal != self.singnal_list:
        #     plot = self.singnal
        # else:
        #     plot = None
        #
        # self.time_list.append(bar.datetime)
        # self.open_list.append(bar.open_price)
        # self.high_list.append(bar.high_price)
        # self.low_list.append(bar.low_price)
        # self.close_list.append(bar.close_price)
        # self.volume_list.append(bar.volume)
        # self.up_list.append(self.up)
        # self.down_list.append(self.down)
        #
        # # self.mid_list.append(self.boll_mid)
        # # self.mid_new_list.append(self.boll_mid_new[-1])
        # # self.exit_long_list.append(self.exit_long)
        # # self.exit_short_list.append(self.exit_short)
        # self.singnal_plot.append(plot)
        #
        # self.plot_echarts = {
        #     "datetime": self.time_list,
        #     "open": self.open_list,
        #     "high": self.high_list,
        #     "low": self.low_list,
        #     "close": self.close_list,
        #     "volume": self.low_list,
        #     "up": self.up_list,
        #     "down": self.down_list,
        #     # "boll_mid": self.mid_list,
        #     # "boll_mid_new": self.mid_new_list,
        #     # "bias": self.bias_value_list,
        #     # "bias_value": self.bias_list,
        #     # "exit_long": self.exit_long_list,
        #     # "exit_short": self.exit_short_list,
        #     "signal": self.singnal_plot
        #
        # }
        # self.singnal_list = self.singnal

        self.put_event()
        self.sync_data()

    def on_hour_bar(self, bar: BarData):
        """
        计算轨道
        """
        self.am_m.update_bar(bar)

        if not self.am_m.inited:
            return

        hh = talib.MAX(self.am_m.high, timeperiod=self.rolling_period)
        lc = talib.MIN(self.am_m.close, self.rolling_period)
        hc = talib.MAX(self.am_m.close, self.rolling_period)
        ll = talib.MAX(self.am_m.low, self.rolling_period)
        max_np = [hh - lc, hc - ll]
        max_array = np.max(max_np, axis=0)
        up = self.am_m.open[-self.rolling_period:] + self.upper_lower * max_array[-self.rolling_period:]
        down = self.am_m.open[-self.rolling_period:] - self.upper_lower * max_array[-self.rolling_period:]

        self.bar_open = bar.close_price
        self.up = up[-2]
        self.down = down[-2]

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        if trade.direction == Direction.LONG:
            long_entry = trade.price
            self.long_stop = long_entry - 2 * self.atr_value
        else:
            short_entry = trade.price
            self.short_stop = short_entry + 2 * self.atr_value

        #   画图专用
        if trade.direction.value == Direction.LONG.value:
            if trade.offset.value == Offset.OPEN.value:
                self.singnal = 1

            elif trade.offset.value == Offset.CLOSE.value:
                self.singnal = 0

            else:
                self.singnal = None

        elif trade.direction.value == Direction.SHORT.value:
            if trade.offset.value == Offset.OPEN.value:
                self.singnal = -1

            elif trade.offset.value == Offset.CLOSE.value:
                self.singnal = 0

            else:
                self.singnal = None

        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
        # self.put_event()

