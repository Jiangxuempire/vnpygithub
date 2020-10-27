import talib
from vnpy.app.cta_strategy.base import StopOrderStatus

from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    Direction,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)
from vnpy.strategy.class_strategy.new_strategy import NewBarGenerator
from vnpy.trader.constant import Interval, Offset


class TextV1(CtaTemplate):
    """"""
    author = "yuya"
    open_window = 15
    kk_length = 80
    kk_dev = 2.0
    rsi_length = 58
    atr_length = 16
    fixed_size = 1
    # max_size = 10000

    rsi_up = 0
    rsi_down = 0
    kk_up = 0
    kk_mid = 0
    kk_down = 0
    kk_mid_new = 0
    rsi_mid = 0
    rsi_current = 0
    rsi_last = 0
    atr_value = 0

    exit_long = 0
    exit_short = 0

    # 画图专用
    time_list = []
    open_list = []
    high_list = []
    low_list = []
    close_list = []
    volume_list = []

    entry_up_list = []
    entry_down_list = []
    mid_list = []
    rsi_list = []
    exit_up_list = []
    exit_down_list = []
    kk_up_list = []
    kk_down_list = []

    singnal_plot = []
    singnal_list = None
    singnal = None

    plot_echarts = {}

    parameters = []
    variables = []

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = NewBarGenerator(
            on_bar=self.on_bar,
            window=self.open_window,
            on_window_bar=self.on_minute_bar
        )
        self.am_hour = ArrayManager(int(self.rsi_length) * 3 + 2)

        self.exit_long_nex = 0
        self.exit_long_last = 0
        self.exit_short_nex = 0
        self.exit_short_last = 0

        self.kk_length_new = 0

        self.buy_price = 0
        self.sell_price = 0
        self.short_price = 0
        self.cover_price = 0

        self.buy_orderids = []
        self.sell_orderids = []
        self.short_orderids = []
        self.cover_orderids = []

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

    def on_minute_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        self.am_hour.update_bar(bar)
        if not self.am_hour.inited:
            return

        rsi_array = talib.RSI(self.am_hour.close[:-1], self.rsi_length)
        rsi_ma = talib.SMA(rsi_array, self.rsi_length)
        rsi_std = talib.STDDEV(rsi_array, self.rsi_length)

        rsi_dev_array = abs(rsi_array - rsi_ma) / rsi_std
        dev_max = talib.MAX(rsi_dev_array, self.rsi_length)

        up = rsi_ma + rsi_std * dev_max
        down = rsi_ma - rsi_std * dev_max

        rsi_value = self.am_hour.rsi(self.rsi_length)

        # # 画图专用
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

        self.kk_up_list.append(up[-1])
        self.kk_down_list.append(down[-1])
        self.entry_up_list.append(rsi_value)
        self.entry_down_list.append(rsi_ma[-1])


        self.singnal_plot.append(plot)

        self.plot_echarts = {
            "datetime": self.time_list,
            "open": self.open_list,
            "high": self.high_list,
            "low": self.low_list,
            "close": self.close_list,
            "volume": self.low_list,

            "up": self.kk_up_list,
            "down": self.kk_down_list,
            "rsi": self.entry_up_list,
            "rsi_ma": self.entry_down_list,
            "signal": self.singnal_plot

        }
        self.singnal_list = self.singnal

        self.sync_data()
        self.put_event()

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        # if trade.direction == Direction.LONG:
        #     self.long_entry = trade.price  # 成交最高价
        #     self.long_stop = self.long_entry - 2 * self.atr_value
        # else:
        #     self.short_entry = trade.price
        #     self.short_stop = self.short_entry + 2 * self.atr_value

        # 画图专用
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

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    # def on_stop_order(self, stop_order: StopOrder):
    #     """
    #     Callback of stop order update.
    #     """
    #     # 只处理结束的停止单 如果订单是等待中就返回
    #     if stop_order.status == StopOrderStatus.WAITING:
    #         return
    #
    #     # 买入停止单
    #     if stop_order.stop_orderid in self.buy_orderids:
    #         # 移除委托号 已完成和已撤销的订单号
    #         self.buy_orderids.remove(stop_order.stop_orderid)
    #
    #         # 如果没任何委托，清空
    #         if not self.buy_orderids:
    #             self.buy_price = 0
    #
    #         # 若是  已撤单，且目前无仓位，则立即重发
    #         if stop_order.status == StopOrderStatus.CANCELLED and not self.pos:
    #             self.buy_price = self.entry_up
    #             self.buy_orderids = self.buy(self.entry_up, self.trading_size, True)
    #
    #     elif stop_order.stop_orderid in self.short_orderids:
    #         self.short_orderids.remove(stop_order.stop_orderid)
    #
    #         if not self.short_orderids:
    #             self.short_price = 0
    #
    #         if stop_order.status == StopOrderStatus.CANCELLED and not self.pos:
    #             self.short_price = self.entry_down
    #             self.short_orderids = self.short(self.entry_down, self.trading_size, True)
    #
    #     elif stop_order.stop_orderid in self.sell_orderids:
    #         self.sell_orderids.remove(stop_order.stop_orderid)
    #
    #         if not self.sell_orderids:
    #             self.sell_price = 0
    #
    #         if stop_order.status == StopOrderStatus.CANCELLED and self.pos > 0:
    #             exit_down = max(self.long_stop, self.exit_down)
    #             self.sell_price = exit_down
    #             self.sell_orderids = self.sell(exit_down, abs(self.pos), True)
    #
    #     elif stop_order.stop_orderid in self.cover_orderids:
    #         self.cover_orderids.remove(stop_order.stop_orderid)
    #
    #         if not self.cover_orderids:
    #             self.cover_price = 0
    #
    #         if stop_order.status == StopOrderStatus.CANCELLED and self.pos < 0:
    #             exit_up = min(self.short_stop, self.exit_up)
    #             self.cover_price = exit_up
    #             self.cover_orderids = self.cover(exit_up, abs(self.pos), True)
    #
    #     self.sync_data()
    #
    # def cancel_orders(self, vt_orderids: list):
    #     """"""
    #     for vt_orderid in vt_orderids:
    #         self.cancel_order(vt_orderid)
