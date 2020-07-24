from typing import Any
import numpy as np
import talib

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
from vnpy.app.cta_strategy.new_strategy import NewBarGenerator
from vnpy.trader.constant import Interval


class MacdRsibollDcStrategy(CtaTemplate):
    """

    """
    author = "yunya"

    hour_window = 1
    minute_window = 50
    open_window = 5
    fast_macd = 12
    slow_macd = 26
    signal_macd = 9
    macd_trend_level = 1.0
    rsi_length = 15
    boll_length = 20
    boll_dev = 2.0
    dc_length = 20
    atr_window = 30
    trailing_tax = 2.0
    risk_level = 5000

    exit_down = 0
    exit_up = 0
    macd = 0
    macd_entry = 0
    rsi_entry = 0
    intra_trade_high = 0
    intra_trade_low = 0
    long_stop = 0
    short_stop = 0
    atr_value = 0

    parameters = [
                "hour_window",
                "minute_window",
                "open_window",
                "fast_macd",
                "slow_macd",
                "signal_macd",
                "macd_trend_level",
                "boll_length",
                "boll_dev",
                "rsi_length",
                "dc_length",
                "atr_window",
                "trailing_tax",
                "risk_level",
    ]

    variables = [
                "exit_down",
                "exit_up",
                "macd",
                "macd_entry",
                "rsi_entry",
                "intra_trade_high",
                "intra_trade_low",
                "long_stop",
                "short_stop",
                "atr_value",
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
        self.atr_stop_array = np.zeros(10)

        self.bg_xhour = NewBarGenerator(
            on_bar=self.on_bar,
            window=self.hour_window,
            on_window_bar=self.on_xhour_bar,
            interval=Interval.HOUR
        )
        self.am_hour = ArrayManager(200)

        self.bg_xminute = NewBarGenerator(
            on_bar=self.on_bar,
            window=self.minute_window,
            on_window_bar=self.on_xminute_bar
        )
        self.am_xminute = ArrayManager(200)

        self.bg_open = NewBarGenerator(
            on_bar=self.on_bar,
            window=self.open_window,
            on_window_bar=self.on_5min_bar
        )
        self.am_open = ArrayManager(self.dc_length * int(self.minute_window / self.open_window) + 30)

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化。。")
        self.load_bar(30)

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
        self.bg_open.update_tick(tick)
        self.ask = tick.ask_price_1  # 卖一价
        self.bid = tick.bid_price_1  # 买一价

        self.put_event()

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg_xhour.update_bar(bar)
        self.bg_xminute.update_bar(bar)
        self.bg_open.update_bar(bar)


    def on_5min_bar(self, bar: BarData):

        self.cancel_all()
        self.am_open.update_bar(bar)

        if not self.am_open.inited or not self.am_xminute.inited or not self.am_hour.inited:
            return

        #
        self.exit_up, self.exit_down = self.am_open.donchian(self.dc_length * int(self.minute_window / self.open_window))

        if not self.pos:
            
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            if self.macd_entry > 0 and self.rsi_entry > 0:
                self.buy(self.boll_up, self.trading_size, True)
                # print(bar.datetime, self.boll_up, self.trading_size)
                # print(bar.datetime, self.entry_up, self.trading_size, bar)

            if self.macd_entry < 0 and self.rsi_entry < 0:
                self.short(self.boll_down, self.trading_size, True)

        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            long_high = self.intra_trade_high * \
                            (1 - self.trailing_tax / 100)
            self.long_stop = max(self.exit_down, long_high)
            self.sell(self.long_stop, abs(self.pos), True)

        elif self.pos < 0:
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
            short_low = self.intra_trade_low * \
                             (1 + self.trailing_tax / 100)
            self.short_stop = min(self.exit_up,short_low)
            self.cover(short_low, abs(self.pos), True)

        self.put_event()

    def on_xminute_bar(self, bar: BarData):
        """
        :param bar:
        :return:
        """
        self.am_xminute.update_bar(bar)
        if not self.am_hour.inited or not self.am_xminute.inited:
            return

        rsi_array = talib.RSI(self.am_xminute.close[:-1], self.rsi_length)
        ema_array = talib.EMA(self.am_xminute.close, self.rsi_length)

        dev_array = abs(self.am_xminute.close[:-1] - ema_array[:-1]) / rsi_array

        rsi_up_array = rsi_array + rsi_array * dev_array
        rsi_dow_array = rsi_array - rsi_array * dev_array

        self.rsi_value = self.am_xminute.rsi(self.rsi_length, True)
        self.rsi_up = rsi_up_array[-1]
        self.rsi_dow = rsi_dow_array[-1]

        current_rsi_up = rsi_up_array[-1]
        current_rsi_down = rsi_dow_array[-1]
        current_rsi_value = self.rsi_value[-1]

        if current_rsi_value > current_rsi_up:
            self.rsi_entry = 1
        elif current_rsi_value < current_rsi_down:
            self.rsi_entry = -1
        else:
            self.rsi_entry = 0

        self.boll_up,self.boll_down = self.am_xminute.boll(self.boll_length,self.boll_dev)

    def on_xhour_bar(self, bar: BarData):
        """"""
        am_hour = self.am_hour
        am_hour.update_bar(bar)

        if not am_hour.inited:
            return
        macd_signal, signal, hist = self.am_hour.macd(
                                                    self.fast_macd,
                                                    self.slow_macd,
                                                    self.signal_macd
                                                    )
        self.macd = signal - hist

        if self.macd > self.macd_trend_level:
            self.macd_entry = 1

        elif self.macd < (-self.macd_trend_level):
            self.macd_entry = -1
        else:
            self.macd_entry = 0

        # 动态调整仓位
        if not self.pos:
            self.atr_value = self.am_hour.atr(self.atr_window)

            if self.atr_value == 0: #保证仓位值是有效的
                return
            #正向合约
            atr_risk = self.am_hour.atr(self.atr_window)
            self.trading_size = max(int(self.risk_level / atr_risk), 1)

        self.put_event()

    def on_trade(self, trade: TradeData):
        """
        有成交时
        Callback of new trade data update.
        """
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

