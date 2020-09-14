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
from vnpy.app.cta_strategy.new_strategy import NewBarGenerator
import numpy as np
import talib

from vnpy.trader.constant import Direction


class RsiDcVixStrategy(CtaTemplate):
    """
    Rsi 原版逻辑

      Rsi 值 上破临界值 80 时平空做多，下破临界值 20 时平多做空。

    Rsi 策略优化思路：
    一、指标计算方式
        1、计算 N 周期 rsi
        2、计算 N 周期 RSI 的最大值为上轨，最小值为下轨
        3、rsi 上穿上轨，并且 rsi 大于 50 ，做多
        3、rsi 下穿下轨，并且 rsi 小于 50 ，做空

    二、 开平仓位逻辑
        1、如果没有仓位
        2、
        3、移动止损 挂停止单 


    """

    author = "yunya"

    open_window = 15
    rsi_window = 50
    exit_window = 50
    atr_window = 16
    atr_multiplier = 15.0
    pos_trailing = 5.0
    fixed_size = 1

    rsi_up = 0
    rsi_down = 0
    rsi_value = 0
    exit_up = 0
    exit_down = 0
    atr_value = 0
    long_entry = 0
    short_entry = 0
    long_stop = 0
    short_stop = 0
    long_trade_stop = 0
    short_trade_stop = 0
    intra_trade_high = 0
    intra_trade_low = 0

    parameters = [
            "open_window",
            "rsi_window",
            "exit_window",
            "atr_window",
            "atr_multiplier",
            "pos_trailing",
            "fixed_size",
    ]
    variables = [
            "rsi_up",
            "rsi_down",
            "rsi_value",
            "exit_up",
            "exit_down",
            "atr_value",
            "long_entry",
            "short_entry",
            "long_stop",
            "short_stop",
            "long_trade_stop",
            "short_trade_stop",
            "intra_trade_high",
            "intra_trade_low",
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg = NewBarGenerator(self.on_bar, self.open_window, self.on_15min_bar)
        self.am = ArrayManager(self.rsi_window * 3)

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
        Callback of new tick data update.
        """
        self.bg.update_bar(bar)

    def on_15min_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.cancel_all()

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        # 计算 dev_max
        rsi_array = talib.RSI(self.am.close[:-1], self.rsi_window)

        self.rsi_up = rsi_array[-self.rsi_window:].max()
        self.rsi_down = rsi_array[-self.rsi_window:].min()

        self.rsi_value = am.rsi(self.rsi_window)
        self.exit_up, self.exit_down = self.am.donchian(self.exit_window)
        self.atr_value = am.atr(self.atr_window)

        # 没有仓
        if not self.pos:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            if self.rsi_value > self.rsi_up:
                self.buy(bar.close_price + 5, self.fixed_size)

            elif self.rsi_value < self.rsi_down:
                self.short(bar.close_price - 5, self.fixed_size)

        # 有多仓
        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price
            self.long_stop = self.intra_trade_high - self.atr_value * self.atr_multiplier

            self.long_stop = max(self.long_stop, self.exit_down)
            self.long_stop = max(self.long_stop, self.long_trade_stop)

            self.sell(self.long_stop, abs(self.pos), True)

        # 有空仓
        elif self.pos < 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
            self.short_stop = self.intra_trade_low + self.atr_value * self.atr_multiplier

            self.short_stop = min(self.short_stop, self.exit_up)
            self.short_stop = min(self.short_stop, self.short_trade_stop)

            self.cover(self.short_stop, abs(self.pos), True)

        self.put_event()
        self.sync_data()

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
            self.long_entry = trade.price  # 成交最高价
            self.long_trade_stop = self.long_entry * (1 - self.pos_trailing / 100)
        else:
            self.short_entry = trade.price
            self.short_trade_stop = self.short_entry * (1 + self.pos_trailing / 100)
        self.put_event()
        self.sync_data()
