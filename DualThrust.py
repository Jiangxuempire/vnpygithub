#_*_coding : utf_8 _*_


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
from vnpy.trader.constant import Interval, Direction
from time import time


class DudlThrust_NewStrategy(CtaTemplate):
    """"""
    author = "yunyu"

    window_min = 15
    rolling_period = 70
    upper_open = 0.5
    lower_open = 0.6
    stop_multiplier = 2.0
    dc_length = 30
    cci_length = 10
    cci_stop = 20
    trailing_tax = 1.8
    fixed_size = 1


    up = 0
    down = 0
    exit_shour = 0
    exit_long = 0
    intra_trade_high = 0
    intra_trade_low = 0
    long_stop = 0
    short_stop = 0
    long_entry = 0
    short_entry = 0
    long_out = 0
    short_out = 0
    cci_value = 0
    ask = 0
    bid = 0

    parameters = [
                "window_min",
                "rolling_period",
                "upper_open",
                "lower_open",
                "stop_multiplier",
                "dc_length",
                "cci_length",
                "cci_stop",
                "trailing_tax",
                "fixed_size",
                ]

    variables = [
                "up",
                "down",
                "exit_shour",
                "exit_long",
                "intra_trade_high",
                "intra_trade_low",
                "long_stop",
                "short_stop",
                "long_entry",
                "short_entry",
                "long_out",
                "short_out",
                "cci_value"
                ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(on_bar=self.on_bar)
        self.am = ArrayManager((max(self.dc_length,self.rolling_period) + 10) * 60)

        self.bg_xmin = BarGenerator(on_bar=self.on_bar,window=self.window_min,on_window_bar=self.on_xmin_bar)
        self.am_xmin = ArrayManager(max(self.dc_length,self.rolling_period) + 10)


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

        self.put_event()

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg_xmin.update_bar(bar)
        self.cancel_all()

        self.exit_shour,self.exit_long = self.am.donchian(self.dc_length * 60)

        if self.pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            if self.cci_value > self.cci_stop:
                self.buy(self.up, self.fixed_size,True)

            elif self.cci_value < -self.cci_stop:
                self.short(self.down, self.fixed_size,True)

        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high,bar.high_price)
            self.intra_trade_low = bar.low_price

            self.long_out = self.intra_trade_high * (
                1 - self.trailing_tax / 100
            )

            self.long_stop = max(self.long_entry,self.long_out,self.exit_long)
            self.sell(self.long_stop, abs(self.pos), True)

        elif self.pos < 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = min(self.intra_trade_low,bar.low_price)

            self.short_out = self.intra_trade_low * (
                1 + self.trailing_tax / 100
            )

            self.short_stop = min(self.short_entry,self.short_out,self.exit_shour)
            self.cover(self.short_stop, abs(self.pos), True)

        self.put_event()


    def on_xmin_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.am_xmin.update_bar(bar)

        if not self.am_xmin.inited:
            return

        self.up, self.down = self.dualthrust(
                                            self.am_xmin.high,
                                            self.am_xmin.low,
                                            self.am_xmin.close,
                                            self.am_xmin.open,
                                            self.rolling_period,
                                            self.upper_open,
                                            self.lower_open
                                            )
        self.cci_value = self.am_xmin.cci(self.cci_length)

        self.atr_value = self.am.atr(16)
        self.put_event()

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
            long_price = trade.price
            self.long_entry = long_price - self.stop_multiplier * self.atr_value
        else:
            short_price = trade.price
            self.short_entry = short_price + self.stop_multiplier * self.atr_value

        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
        # self.put_event()

    def market_order(self):
        """"""
        pass
        # self.buy(self.last_tick.limit_up, 1)
        # self.write_log("执行市价单测试")

    def limit_order(self):
        """"""
        pass
        # self.buy(self.last_tick.limit_down, 1)
        # self.write_log("执行限价单测试")

    def stop_order(self):
        """"""
        pass
        # self.buy(self.last_tick.ask_price_1, 1, True)
        # self.write_log("执行停止单测试")



    def dualthrust(self,high,low,close,open,n,k1,k2):
        """
        :param high:
        :param low:
        :param close:
        :return:
        """
        #计算N日最高价的最高价，收盘价的最高价、最低价，最低价的最低价
        hh = high[-n:-1].max()
        lc = close[-n:-1].min()
        hc = close[-n:-1].max()
        ll = low[-n:-1].max()

        #计算range,上下轨的距离前一根K线开盘价的距离
        range = max(hh - lc,hc - ll)

        up = open[-2] + k1 * range
        down = open[-2] - k2 * range

        return  up,down










