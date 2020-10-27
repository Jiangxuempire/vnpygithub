from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    ArrayManager,
)
from vnpy.app.cta_strategy.base import EngineType, StopOrderStatus
from vnpy.app.cta_strategy.new_strategy import NewBarGenerator
from vnpy.trader.constant import Interval, Direction, Offset
import numpy as np


class BollVixV1(CtaTemplate):
    """"""
    author = "yunya"

    open_window = 15
    boll_length = 380
    fixed_size = 1

    boll_mid_current = 0
    boll_mid_last = 0
    boll_up_current = 0
    boll_up_last = 0
    boll_down_current = 0
    boll_down_last = 0
    target_pos = 0
    boll_mid = 0

    # # 画图专用
    # time_list = []
    # open_list = []
    # high_list = []
    # low_list = []
    # close_list = []
    # volume_list = []
    # up_list = []
    # down_list = []
    # mid_list = []
    # mid_new_list = []
    # bias_value_list = []
    # bias_list = []
    # singnal_plot = []
    # singnal_list = None
    # singnal = None
    #
    # plot_echarts = {}

    parameters = [
        "open_window",
        "boll_length",
        "fixed_size",
    ]

    variables = [
        "boll_mid",
        "boll_up_current",
        "boll_up_last",
        "boll_down_current",
        "boll_down_last"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = NewBarGenerator(self.on_bar, self.open_window, self.on_minute_bar, interval=Interval.MINUTE)
        self.am = ArrayManager(self.boll_length * 2)

        self.sell_price = 0
        self.cover_price = 0

        self.sell_orderids = []
        self.cover_orderids = []

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

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        # 计算布林
        sma_array = self.am.sma(self.boll_length, True)
        std_array = self.am.std(self.boll_length, True)
        dev = abs(self.am.close[:-1] - sma_array[:-1]) / std_array[:-1]
        dev_max = dev[-self.boll_length:].max()
        up = sma_array + std_array * dev_max
        down = sma_array - std_array * dev_max

        boll_mid_array = self.am.sma(self.boll_length, True)

        # 计算数组
        self.boll_mid = boll_mid_array[-2]
        self.boll_up_current = up[-1]
        self.boll_up_last = up[-2]
        self.boll_down_current = down[-1]
        self.boll_down_last = down[-2]

        if not self.pos:

            if self.am.close[-1] > self.boll_up_current and self.am.close[-2] <= self.boll_up_last:
                self.buy(bar.close_price, self.fixed_size)

            elif self.am.close[-1] < self.boll_down_current and self.am.close[-2] >= self.boll_down_last:
                self.short(bar.close_price, self.fixed_size)

        elif self.pos > 0:
            if not self.sell_orderids:
                self.sell_price = self.boll_mid
                self.sell_orderids = self.sell(self.boll_mid, abs(self.pos), True)

            elif self.sell_price != self.boll_mid:
                self.cancel_orders(self.sell_orderids)

        elif self.pos < 0:
            if not self.cover_orderids:
                self.cover_price = self.boll_mid
                self.cover_orderids = self.cover(self.boll_mid, abs(self.pos), True)

            elif self.cover_price != self.boll_mid:
                self.cancel_orders(self.cover_orderids)

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
        # self.up_list.append(self.boll_up_current)
        # self.down_list.append(self.boll_down_current)
        # self.mid_list.append(self.boll_mid)
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
        #     "signal": self.singnal_plot
        #
        # }
        # self.singnal_list = self.singnal

        self.put_event()

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
        # if trade.direction.value == Direction.LONG.value:
        #     if trade.offset.value == Offset.OPEN.value:
        #         self.singnal = 1
        #
        #     elif trade.offset.value == Offset.CLOSE.value:
        #         self.singnal = 0
        #
        #     else:
        #         self.singnal = None
        #
        # elif trade.direction.value == Direction.SHORT.value:
        #     if trade.offset.value == Offset.OPEN.value:
        #         self.singnal = -1
        #
        #     elif trade.offset.value == Offset.CLOSE.value:
        #         self.singnal = 0
        #
        #     else:
        #         self.singnal = None

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        # 只处理结束的停止单 如果订单是等待中就返回
        if stop_order.status == StopOrderStatus.WAITING:
            return

        if stop_order.stop_orderid in self.sell_orderids:
            self.sell_orderids.remove(stop_order.stop_orderid)

            if not self.sell_orderids:
                self.sell_price = 0

            if stop_order.status == StopOrderStatus.CANCELLED and self.pos > 0:
                self.sell_price = self.boll_mid
                self.sell_orderids = self.sell(self.boll_mid, abs(self.pos), True)

        elif stop_order.stop_orderid in self.cover_orderids:
            self.cover_orderids.remove(stop_order.stop_orderid)

            if not self.cover_orderids:
                self.cover_price = 0

            if stop_order.status == StopOrderStatus.CANCELLED and self.pos < 0:
                self.cover_price = self.boll_mid
                self.cover_orderids = self.cover(self.boll_mid, abs(self.pos), True)

    def cancel_orders(self, vt_orderids: list):
        """"""
        for vt_orderid in vt_orderids:
            self.cancel_order(vt_orderid)

