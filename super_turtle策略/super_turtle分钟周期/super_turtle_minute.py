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
from vnpy.trader.constant import Interval, Offset


class SuperTurtleMinuteV1(CtaTemplate):
    """"""
    author = "yuya"

    open_window = 15
    entry_window = 620
    exit_window = 120
    atr_window = 16
    max_size = 1000

    trading_size = 0
    entry_up = 0
    entry_down = 0
    exit_up = 0
    exit_down = 0
    atr_value = 0

    long_entry = 0
    short_entry = 0
    long_stop = 0
    short_stop = 0
    max_atr = 0

    # 画图专用
    time_list = []
    open_list = []
    high_list = []
    low_list = []
    close_list = []
    volume_list = []
    entry_up_list = []
    entry_down_list = []

    exit_up_list = []
    exit_down_list = []

    singnal_plot = []
    singnal_list = None
    singnal = None

    plot_echarts = {}

    parameters = ["entry_window", "exit_window", "atr_window", "risk_level"]
    variables = [
        "entry_up", "entry_down", "exit_up",
        "exit_down", "trading_size", "atr_value"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(
            self.on_bar, self.open_window, self.on_hour_bar, interval=Interval.MINUTE)
        self.am = ArrayManager(self.entry_window * 3)

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

    def on_hour_bar(self, bar: BarData):
        """"""

        self.am.update_bar(bar)
        if not self.am.inited:
            return

        self.entry_up, self.entry_down = self.am.donchian(self.entry_window)
        self.exit_up, self.exit_down = self.am.donchian(self.exit_window)

        if not self.pos:
            self.atr_value = self.am.atr(self.atr_window)

            if self.atr_value == 0:
                return
            # 反向合约的计算方法，
            atr_risk = talib.ATR(
                1 / self.am.high,
                1 / self.am.low,
                1 / self.am.close,
                self.atr_window
            )[-1]

            self.max_atr = max(int(0.1 / atr_risk), self.max_atr)
            self.trading_size = int(int(0.1 / atr_risk) / self.max_atr * self.max_size)
            self.trading_size = max(self.trading_size, 1)

            #   先使用固定仓位回测
            self.trading_size = 1

            self.long_entry = 0
            self.short_entry = 0
            self.long_stop = 0
            self.short_stop = 0

            if not self.buy_orderids:
                self.buy_price = self.entry_up
                self.buy_orderids = self.buy(self.entry_up, self.trading_size, True)

            elif self.buy_price != self.entry_up:
                self.cancel_orders(self.buy_orderids)

            if not self.short_orderids:
                self.short_price = self.entry_down
                self.short_orderids = self.short(self.entry_down, self.trading_size, True)

            elif self.short_price != self.entry_down:
                self.cancel_orders(self.short_orderids)

        elif self.pos > 0:
            exit_down = max(self.long_stop, self.exit_down)

            if not self.sell_orderids:
                self.sell_price = exit_down
                self.sell_orderids = self.sell(exit_down, abs(self.pos), True)

            elif self.sell_price != exit_down:
                self.cancel_orders(self.sell_orderids)

        elif self.pos < 0:
            exit_up = min(self.short_stop, self.exit_up)

            if not self.cover_orderids:
                self.cover_price = exit_up
                self.cover_orderids = self.cover(exit_up, abs(self.pos), True)

            elif self.cover_price != exit_up:
                self.cancel_orders(self.cover_orderids)

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
        self.entry_up_list.append(self.entry_up)
        self.entry_down_list.append(self.entry_down)
        self.exit_up_list.append(self.exit_up)
        self.exit_down_list.append(self.exit_down)

        self.singnal_plot.append(plot)

        self.plot_echarts = {
            "datetime": self.time_list,
            "open": self.open_list,
            "high": self.high_list,
            "low": self.low_list,
            "close": self.close_list,
            "volume": self.low_list,
            "long_up": self.entry_up_list,
            "short_down": self.entry_down_list,
            "exit_up": self.exit_up_list,
            "exit_down": self.exit_down_list,

            "signal": self.singnal_plot

        }
        self.singnal_list = self.singnal

        self.put_event()

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        if trade.direction == Direction.LONG:
            self.long_entry = trade.price  # 成交最高价
            self.long_stop = self.long_entry - 2 * self.atr_value
        else:
            self.short_entry = trade.price
            self.short_stop = self.short_entry + 2 * self.atr_value

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

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        # 只处理结束的停止单 如果订单是等待中就返回
        if stop_order.status == StopOrderStatus.WAITING:
            return

        # 买入停止单
        if stop_order.stop_orderid in self.buy_orderids:
            # 移除委托号 已完成和已撤销的订单号
            self.buy_orderids.remove(stop_order.stop_orderid)

            # 如果没任何委托，清空
            if not self.buy_orderids:
                self.buy_price = 0

            # 若是  已撤单，且目前无仓位，则立即重发
            if stop_order.status == StopOrderStatus.CANCELLED and not self.pos:
                self.buy_price = self.entry_up
                self.buy_orderids = self.buy(self.entry_up, self.trading_size, True)

        elif stop_order.stop_orderid in self.short_orderids:
            self.short_orderids.remove(stop_order.stop_orderid)

            if not self.short_orderids:
                self.short_price = 0

            if stop_order.status == StopOrderStatus.CANCELLED and not self.pos:
                self.short_price = self.entry_down
                self.short_orderids = self.short(self.entry_down, self.trading_size, True)

        elif stop_order.stop_orderid in self.sell_orderids:
            self.sell_orderids.remove(stop_order.stop_orderid)

            if not self.sell_orderids:
                self.sell_price = 0

            if stop_order.status == StopOrderStatus.CANCELLED and self.pos > 0:
                exit_down = max(self.long_stop, self.exit_down)
                self.sell_price = exit_down
                self.sell_orderids = self.sell(exit_down, abs(self.pos), True)

        elif stop_order.stop_orderid in self.cover_orderids:
            self.cover_orderids.remove(stop_order.stop_orderid)

            if not self.cover_orderids:
                self.cover_price = 0

            if stop_order.status == StopOrderStatus.CANCELLED and self.pos < 0:
                exit_up = min(self.short_stop, self.exit_up)
                self.cover_price = exit_up
                self.cover_orderids = self.cover(exit_up, abs(self.pos), True)

    def cancel_orders(self, vt_orderids: list):
        """"""
        for vt_orderid in vt_orderids:
            self.cancel_order(vt_orderid)
