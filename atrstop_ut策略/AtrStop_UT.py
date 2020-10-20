from typing import Any
import numpy as np
from vnpy.trader.constant import Direction, Offset

from vnpy.app.cta_strategy import (
    CtaTemplate,
    BarGenerator,
    ArrayManager,
    TickData,
    OrderData,
    BarData,
    TradeData,
    StopOrder
)
from  vnpy.app.cta_strategy.new_strategy import NewBarGenerator

class AtrStop_Ut(CtaTemplate):
    """"""
    author = "yunya"

    atrstop_window = 46
    open_window = 5
    distance_line = 2.0
    nloss_singnal = 2.7
    sl_multiplier = 10.0
    fixd_size = 1
    atr_window = 30

    atr_entry = 0
    current_atr_stop = 0.0
    last_atr_stop = 0.0
    intra_trade_high = 0
    intra_trade_low = 0
    nloss_array = 0.0
    long_stop = 0
    short_stop = 0
    ask = 0
    bid = 0
    atr_value = 0

    # 画图专用
    time_list = []
    open_list = []
    high_list = []
    low_list = []
    close_list = []
    volume_list = []

    atr_stop_list = []
    ema_list = []

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
            "atrstop_window",
            "open_window",
            "nloss_singnal",
            "sl_multiplier",
            "distance_line",
            "fixd_size",
            "atr_window"
    ]

    variables = [
        "current_atr_stop",
        "last_atr_stop",
        "long_stop",
        "short_stop",
        "atr_entry",
        "atr_value",
        "ask",
        "bid"
    ]

    def __init__(
            self,
            cta_engine: Any,
            strategy_name: str,
            vt_symbol: str,
            setting: dict,
    ):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.atr_stop_array = np.zeros(50)

        self.bg_xmin = BarGenerator(
            self.on_bar,
            window=self.atrstop_window,
            on_window_bar=self.on_xmin_bar
        )
        self.am_xmin = ArrayManager()

        self.bg_5min = BarGenerator(
            self.on_bar,
            window=self.open_window,
            on_window_bar=self.on_5min_bar
        )
        self.am_5min = ArrayManager()

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化。。")
        self.load_bar(10)

        self.put_event()

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动。。")
        self.put_event()

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止。。")
        self.put_event()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg_5min.update_tick(tick)
        self.ask = tick.ask_price_1  # 卖一价
        self.bid = tick.bid_price_1  # 买一价

        self.put_event()

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg_xmin.update_bar(bar)
        self.bg_5min.update_bar(bar)

    def on_5min_bar(self, bar: BarData):

        self.cancel_all()
        self.am_5min.update_bar(bar)

        if not self.am_5min.inited or not self.am_xmin.inited:
            return
        if self.atr_stop_array[-3] == 0:
            return
        self.atr_value = self.am_5min.atr(self.atr_window)

        if not self.pos:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            up_limit = self.current_atr_stop * (1 + self.distance_line / 100)
            down_limit = self.current_atr_stop * (1 - self.distance_line / 100)

            if self.atr_entry > 0 and bar.close_price < up_limit:
                self.buy(self.current_atr_stop, self.fixd_size, True)

            elif self.atr_entry < 0 and bar.close_price > down_limit:
                self.short(self.current_atr_stop, self.fixd_size, True)

        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price

            self.long_stop = self.intra_trade_high - self.atr_value * self.sl_multiplier
            self.sell(self.long_stop, abs(self.pos), True)

        else:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)

            self.short_stop = self.intra_trade_low + self.atr_value * self.sl_multiplier
            self.cover(self.short_stop, abs(self.pos), True)

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
        # self.up_list.append(self.boll_up)
        # self.down_list.append(self.boll_down)
        # self.mid_list.append(self.boll_mid)
        # self.mid_new_list.append(self.boll_mid_new[-1])
        # self.exit_long_list.append(self.exit_long)
        # self.exit_short_list.append(self.exit_short)
        # self.singnal_plot.append(plot)
        #
        # self.plot_echarts = {
        #     "datetime": self.time_list,
        #     "open": self.open_list,
        #     "high": self.high_list,
        #     "low": self.low_list,
        #     "close": self.close_list,
        #     "volume": self.low_list,
        #     "boll_up": self.up_list,
        #     "boll_down": self.down_list,
        #     "boll_mid": self.mid_list,
        #     "boll_mid_new": self.mid_new_list,
        #     "bias": self.bias_value_list,
        #     "bias_value": self.bias_list,
        #     "exit_long": self.exit_long_list,
        #     "exit_short": self.exit_short_list,
        #     "signal": self.singnal_plot
        #
        # }
        # self.singnal_list = self.singnal

        self.put_event()

    def on_xmin_bar(self, bar: BarData):
        """"""
        am_xmin = self.am_xmin
        am_xmin.update_bar(bar)

        self.atr_stop_array[:-1] = self.atr_stop_array[1:]

        if not am_xmin.inited:
            return

        # 计算轨道线 nloss
        self.ema_array = am_xmin.ema(3, array=True)
        self.nloss_array = am_xmin.atr(16, array=True) * self.nloss_singnal

        # 计算轨道线
        self.atr_stop_array = self.atrstop(
            am_xmin.close,
            self.atr_stop_array,
            self.nloss_array
        )

        # 初始化
        if self.atr_stop_array[-3] == 0:
            return

        self.current_atr_stop = self.atr_stop_array[-1]
        self.last_atr_stop = self.atr_stop_array[-2]
        current_ema = self.ema_array[-1]
        last_ema = self.ema_array[-2]

        if last_ema <= self.last_atr_stop and current_ema > self.current_atr_stop:
            self.atr_entry = 1
        elif last_ema >= self.last_atr_stop and current_ema < self.current_atr_stop:
            self.atr_entry = -1

        self.time_list.append(bar.datetime)
        self.open_list.append(bar.open_price)
        self.high_list.append(bar.high_price)
        self.low_list.append(bar.low_price)
        self.close_list.append(bar.close_price)
        self.volume_list.append(bar.volume)
        self.atr_stop_list.append(self.last_atr_stop)
        self.ema_list.append(self.ema_array[-1])

        self.plot_echarts = {
                "datetime": self.time_list,
                "open": self.open_list,
                "high": self.high_list,
                "low": self.low_list,
                "close": self.close_list,
                "volume": self.low_list,
                "atr_stop": self.atr_stop_list,
                "ema": self.ema_list,
                "signal": None

            }
        self.put_event()

    def on_trade(self, trade: TradeData):
        """
        有成交时
        Callback of new trade data update.
        """

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

    def on_order(self, order: OrderData):
        """
        订单更新回调
        Callback of new order data update.
        """

        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        self.put_event()

    def atrstop(self, close, atrstop, nlossatr):

        # 计算轨道线
        if (close[-1] > atrstop[-2]) and (close[-2] > atrstop[-2]):
            atrstop[-1] = max(atrstop[-2], close[-1] - nlossatr[-1])

        elif (close[-1] < atrstop[-2]) and (close[-2] < atrstop[-2]):
            atrstop[-1] = min(atrstop[-2], close[-1] + nlossatr[-1])

        elif close[-1] > atrstop[-2]:
            atrstop[-1] = (close[-1] - nlossatr[-1])

        else:
            atrstop[-1] = (close[-1] + nlossatr[-1])

        return atrstop


