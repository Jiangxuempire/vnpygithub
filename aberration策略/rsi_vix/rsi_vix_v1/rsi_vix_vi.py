import talib

from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    ArrayManager,
)
from vnpy.app.cta_strategy.base import EngineType
from vnpy.app.cta_strategy.new_strategy import NewBarGenerator
from vnpy.trader.constant import Interval, Direction, Offset
import numpy as np


class RSIVixV1(CtaTemplate):
    """"""
    author = "yunya"

    open_window = 15
    rsi_length = 600
    # exit_length = 30
    atr_length = 16
    fixed_size = 1

    rsi_current = 0
    rsi_last = 0
    rsi_mid_current = 0
    rsi_mid_last = 0
    rsi_up_current = 0
    rsi_up_last = 0
    rsi_down_current = 0
    rsi_down_last = 0
    exit_long = 0
    exit_short = 0
    dc_up = 0
    dc_down = 0
    atr_value = 0

    target_pos = 0
    pos_inited = 0
    ema_mid = 0




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
    rsi_list = []
    exit_long_list = []
    exit_short_list = []
    singnal_plot = []
    singnal_list = None
    singnal = None

    plot_echarts = {}

    param_xeters = [
        "max_window",
        "rsi_length",
        "fixed_size",
    ]

    variables = [
        "rsi_mid_current",
        "rsi_mid_last",
        "rsi_up_current",
        "rsi_up_last",
        "rsi_down_current",
        "rsi_down_last",
        "pos_inited",
        "target_pos"
    ]

    def __init__(self, cta_engine, strategy_nam_xe, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_nam_xe, vt_symbol, setting)

        self.bg_x = NewBarGenerator(self.on_bar, self.open_window, self.on_x_bar, interval=Interval.MINUTE)
        self.am_x = ArrayManager(int(self.rsi_length * 3))

        self.long_stop = 0
        self.short_stop = 0
        self.exit_long = 0
        self.exit_short = 0

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(12)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")
        self.put_event()

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")
        self.put_event()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg_x.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg_x.update_bar(bar)

    def on_x_bar(self, bar: BarData):
        """"""
        am_x = self.am_x
        am_x.update_bar(bar)
        if not am_x.inited:
            return

        rsi_value = self.am_x.rsi(self.rsi_length, True)

        rsi_array = talib.RSI(self.am_x.close[:-1], self.rsi_length)
        rsi_ma = talib.SMA(rsi_array, self.rsi_length)

        rsi_std = talib.STDDEV(rsi_array, self.rsi_length)

        rsi_dev_array = abs(rsi_array - rsi_ma) / rsi_std
        dev_max = talib.MAX(rsi_dev_array, self.rsi_length)

        up = rsi_ma + rsi_std * dev_max
        down = rsi_ma - rsi_std * dev_max

        self.rsi_current = rsi_value[-1]
        self.rsi_last = rsi_value[-2]

        self.rsi_mid_current = rsi_ma[-1]
        self.rsi_mid_last = rsi_ma[-2]

        self.rsi_up_current = up[-1]
        self.rsi_up_last = up[-2]

        self.rsi_down_current = down[-1]
        self.rsi_down_last = down[-1]

        # self.dc_up, self.dc_down = self.am.donchian(self.exit_length)
        # self.atr_value = self.am.atr(self.atr_length)

        if not self.pos:
            if self.rsi_current > self.rsi_up_current:
                self.buy(bar.close_price, self.fixed_size)

            elif self.rsi_current < self.rsi_down_current:
                self.short(bar.close_price, self.fixed_size)

        elif self.pos > 0:
            if self.rsi_current < self.rsi_mid_current and self.rsi_last >= self.rsi_mid_last:
                self.exit_long = bar.close_price
                self.sell(self.exit_long, abs(self.pos))
            # else:
            #     #   挂出保护止损
            #     self.exit_long = max(self.dc_down, self.long_stop)
            #     self.sell(self.exit_long, abs(self.pos), True)

        elif self.pos < 0:
            if self.rsi_current > self.rsi_mid_current and self.rsi_last <= self.rsi_mid_last:
                self.exit_short = bar.close_price
                self.cover(self.exit_short, abs(self.pos))
            # else:
            #     self.exit_short = min(self.dc_up, self.short_stop)
            #     self.cover(self.exit_short, abs(self.pos), stop=True)

        # 画图专用
        if self.singnal != self.singnal_list:
            plot = self.singnal
        else:
            plot = None

        self.time_list.append(bar.datetime)
        self.open_list.append(bar.open_price)
        self.high_list.append(bar.high_price)
        self.low_list.append(bar.low_price)
        self.close_list.append(bar.close_price)
        self.volume_list.append(bar.volume)

        self.up_list.append(up[-1])
        self.down_list.append(down[-1])
        self.rsi_list.append(rsi_value[-1])
        self.mid_list.append(rsi_ma[-1])
        # self.exit_long_list.append(self.exit_long)
        # self.exit_short_list.append(self.exit_short)
        self.singnal_plot.append(plot)

        self.plot_echarts = {
            "datetime": self.time_list,
            "open": self.open_list,
            "high": self.high_list,
            "low": self.low_list,
            "close": self.close_list,
            "volume": self.low_list,

            "rsi_up": self.up_list,
            "rsi_down": self.down_list,
            "rsi": self.rsi_list,
            "rsi_mid": self.mid_list,
            "exit_long": self.exit_long_list,
            "exit_short": self.exit_short_list,
            "signal": self.singnal_plot

        }
        self.singnal_list = self.singnal

        self.put_event()
        self.sync_data()  # 保存到硬盘

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
        # if trade.direction == Direction.LONG:
        #     long_entry = trade.price  # 成交最高价
        #     self.long_stop = long_entry - 2 * self.atr_value
        # else:
        #     short_entry = trade.price
        #     self.short_stop = short_entry + 2 * self.atr_value
        #
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

        self.sync_data()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
