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
    rsi_length = 12
    exit_length = 30
    fixed_size = 1

    rsi_mid_current = 0
    rsi_mid_last = 0
    rsi_up_current = 0
    rsi_up_last = 0
    rsi_down_current = 0
    rsi_down_last = 0
    rsi_current = 0
    rsi_last = 0
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
    mid_new_list = []
    bias_value_list = []
    bias_list = []
    singnal_plot = []
    singnal_list = None
    singnal = None

    plot_echarts = {}

    parameters = [
        "open_window",
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

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = NewBarGenerator(self.on_bar, self.open_window, self.on_minute_bar, interval=Interval.MINUTE)
        self.am = ArrayManager(self.rsi_length * 3)

        self.rsi_up_array: np.ndarray = np.zeros(3)
        self.rsi_down_array: np.ndarray = np.zeros(3)
        self.count = 0
        self.size = 3
        self.rsi_inited = False

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
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)

    def on_minute_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        # 计算 rsi dc 通道
        rsi_array = talib.RSI(self.am.close[:-1], self.rsi_length)
        rsi_ema = talib.SMA(rsi_array, self.rsi_length)

        self.rsi_up = rsi_ema[-self.rsi_length:].max()
        self.rsi_down = rsi_ema[-self.rsi_length:].min()

        self.rsi = self.am.rsi(self.rsi_length)

        atr_array = am.atr(self.rsi_length, array=True)
        self.atr_value = atr_array[-1]
        self.atr_ma = atr_array[-self.rsi_length:].mean()

        self.exit_up, self.exit_down = self.am.donchian(self.exit_length)

        if not self.pos:
            if self.atr_value > self.atr_ma:
                if self.rsi > self.rsi_up:
                    self.buy(bar.close_price, self.fixed_size)

                elif self.rsi < self.rsi_down:
                    self.cover(bar.close_price, self.fixed_size)

        elif self.pos > 0:
            self.exit_long = max(self.exit_down, self.long_stop)
            self.sell(self.exit_long, abs(self.pos), stop=True)

        elif self.pos < 0:
            self.exit_short = min(self.exit_up, self.short_stop)
            self.cover(self.exit_up, abs(self.pos), stop=True)

        # 画图专用
        if self.singnal != self.singnal_list:
            plot = self.singnal
        else:
            plot = None

        # self.time_list.append(bar.datetime)
        # self.open_list.append(bar.open_price)
        # self.high_list.append(bar.high_price)
        # self.low_list.append(bar.low_price)
        # self.close_list.append(bar.close_price)
        # self.volume_list.append(bar.volume)
        # # self.up_list.append(self.rsi_up_current)
        # # self.down_list.append(self.rsi_down_current)
        # # self.mid_list.append(self.rsi_mid)
        # self.mid_list.append(self.rsi_current)
        # self.singnal_plot.append(plot)
        #
        # self.plot_echarts = {
        #     "datetime": self.time_list,
        #     "open": self.open_list,
        #     "high": self.high_list,
        #     "low": self.low_list,
        #     "close": self.close_list,
        #     "volume": self.low_list,
        #     # "rsi_up": self.up_list,
        #     # "rsi_down": self.down_list,
        #     # "rsi_mid": self.mid_list,
        #     "rsi": self.mid_list,
        #     "signal": self.singnal_plot
        #
        # }
        # self.singnal_list = self.singnal

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
        if trade.direction == Direction.LONG:
            long_entry = trade.price  # 成交最高价
            self.long_stop = long_entry - 3 * self.atr_value
        else:
            short_entry = trade.price
            self.short_stop = short_entry + 3 * self.atr_value

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
