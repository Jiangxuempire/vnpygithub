# _*_coding : UTF-8 _*_
#开发团队 ：yunya
#开发人员 ：Administrator
#开发时间 : 2020/6/26 14:01
#文件名称 ：macd_boll_dc_straetgy.py
#开发工具 ： PyCharm

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
from  vnpy.app.cta_strategy.new_strategy import NewBarGenerator
from vnpy.trader.constant import Direction, Interval


class MacdBollDcStrategy(CtaTemplate):
    """"""

    author = "云崖"

    open_window = 2
    xminute_window = 15
    xhour_window = 1
    fast_length = 14
    show_length = 28
    boll_length = 20
    boll_dev = 2.0
    dc_length = 30
    trailing_tax = 2.0
    fixed_size = 1

    macd_inited = 0
    boll_up = 0
    boll_down = 0
    dc_up = 0
    dc_down = 0
    exit_long = 0
    exit_short = 0
    long_stop = 0
    short_stop = 0

    intra_trade_high = 0
    intra_trade_low = 0






    parameters = [
                    "open_window",
                    "xminute_window",
                    "xhour_window",
                    "fast_length",
                    "show_length",
                    "boll_length",
                    "boll_dev",
                    "dc_length",
                    "trailing_tax",
                    "fixed_size",
                    ]

    variables = [
                "macd_inited",
                "boll_up",
                "boll_down",
                "dc_up",
                "dc_down",
                "exit_long",
                "exit_short",
                "long_stop",
                "short_stop",
                    ]

    def __init__(self, cta_engine, strategy_nam_xminutee, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_nam_xminutee, vt_symbol, setting)

        self.bg_open = NewBarGenerator(self.on_bar, self.open_window, self.on_open_bar)
        self.am_open = ArrayManager()

        self.bg_xminute = NewBarGenerator(self.on_bar, self.xminute_window, self.on_xminute_bar)
        self.am_xminute = ArrayManager(150)

        self.bg_xhour = NewBarGenerator(self.on_bar,
                                        self.xhour_window,
                                        self.on_xhour_bar,
                                        interval=Interval.HOUR)
        self.am_xhour = ArrayManager()

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
        self.bg_xminute.update_tick(tick)
        self.ask = tick.ask_price_1  # 卖一价
        self.bid = tick.bid_price_1  # 买一价

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg_xhour.update_bar(bar)
        self.bg_xminute.update_bar(bar)
        self.bg_open.update_bar(bar)

    def on_open_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        self.am_open.update_bar(bar)
        if not self.am_xminute.inited or not self.am_open.inited :

            return

        if self.pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            self.long_stop = 0
            self.short_stop = 0

            if self.macd_inited > 0:
                self.buy(self.boll_up,self.fixed_size,True)

            elif self.macd_inited < 0:
                self.short(self.boll_down,self.fixed_size,True)

        elif self.pos > 0:
                self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
                self.intra_trade_low = bar.low_price

                long_high = self.intra_trade_high * (1 - self.trailing_tax / 100)
                self.long_stop = max(self.exit_long,long_high)

                self.sell(self.long_stop, abs(self.pos), True)

        elif self.pos < 0:
                self.intra_trade_high = bar.high_price
                self.intra_trade_low = min(self.intra_trade_low, bar.low_price)

                stop_low = self.intra_trade_low * (1 + self.trailing_tax / 100)
                self.short_stop = min(self.exit_short,stop_low)

                self.cover(self.short_stop, abs(self.pos), True)

        self.put_event()

    def on_xminute_bar(self, bar: BarData):
        """"""
        self.am_xminute.update_bar(bar)
        if not self.am_xminute.inited:
            return

        self.boll_up, self.boll_down = self.am_xminute.boll(self.boll_length, self.boll_dev)
        self.exit_short, self.exit_long = self.am_xminute.donchian(self.dc_length)

    def on_xhour_bar(self,bar:BarData):
        """
        :param bar:
        :type bar:
        :return:
        :rtype:
        """
        self.am_xhour.update_bar(bar)
        if self.am_xhour.inited:
            return
        fast_ema_value = self.am_xhour.ema(self.fast_length, True)
        show_ema_value = self.am_xhour.ema(self.show_length, True)
        diff = fast_ema_value - show_ema_value
        macd_diff = (fast_ema_value - show_ema_value) / show_ema_value * 100

        if diff[-2] > macd_diff[-2]:
            self.macd_inited = 1

        elif diff[-2] < macd_diff[-2]:
            self.macd_inited = -1

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        self.put_event()

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        self.put_event()
