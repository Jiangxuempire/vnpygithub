import talib
import numpy as np
from vnpy.app.cta_strategy import (
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
    CtaSignal,
    TargetPosTemplate
)

class RsiSignal(CtaSignal):
    """"""

    def __init__(self, rsi_window: int, rsi_level: float):
        """Constructor"""
        super().__init__()

        self.rsi_window = rsi_window
        self.rsi_level = rsi_level
        self.rsi_long = 50 + self.rsi_level
        self.rsi_short = 50 - self.rsi_level

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.am.update_bar(bar)
        if not self.am.inited:
            self.set_signal_pos(0)

        rsi_value = self.am.rsi(self.rsi_window)

        if rsi_value >= self.rsi_long:
            self.set_signal_pos(1)
        elif rsi_value <= self.rsi_short:
            self.set_signal_pos(-1)
        else:
            self.set_signal_pos(0)


class CciSignal(CtaSignal):
    """
    """
    cci_up_array = 0
    cci_dow_array = 0
    cci_value = 0
    cci_up = 0
    cci_down = 0
    cci_ma = 0
    last_cci_value = 0
    current_cci_value = 0
    last_cci_up = 0
    current_cci_up = 0
    last_cci_down = 0
    current_cci_down = 0
    last_cci_ma = 0
    current_cci_ma = 0

    def __init__(self, open_window: int, cci_window: int, cci_level: float):
        """"""
        super().__init__()
        self.open_window = open_window
        self.cci_window = cci_window
        self.cci_level = cci_level
        self.cci_long = self.cci_level
        self.cci_short = -self.cci_level

        self.bg = BarGenerator(self.on_bar, self.open_window, self.on_x_bar)
        self.am = ArrayManager()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)
        
    def on_bar(self, bar: BarData):
        """
        :param bar: 
        :return: 
        """
        self.bg.update_bar(bar)
        
    def on_x_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.am.update_bar(bar)
        if not self.am.inited:
            self.set_signal_pos(0)

        # 计算 前一根K线的 cci
        cci_array = talib.CCI(self.am.high[:-1], self.am.low[:-1], self.am.close[:-1], self.cci_window)
        cci_ema = talib.EMA(cci_array,self.cci_window)

        dev_array = abs(cci_array[-self.cci_window:] - cci_ema[-self.cci_window:]) / cci_ema[-self.cci_window:]
        dev = np.max(dev_array[-self.cci_window:])

        self.cci_up_array = cci_ema[-self.cci_window:] + cci_array[-self.cci_window:] * dev
        self.cci_dow_array = cci_ema[-self.cci_window:] - cci_array[-self.cci_window:] * dev

        self.cci_value = self.am.cci(self.cci_window,True)

        self.last_cci_value = self.cci_value[-2]
        self.current_cci_value = self.cci_value[-1]
        self.last_cci_up = self.cci_up_array[-2]
        self.current_cci_up = self.cci_up_array[-1]
        self.last_cci_down = self.cci_dow_array[-2]
        self.current_cci_down = self.cci_dow_array[-1]
        self.last_cci_ma = cci_ema[-2]
        self.current_cci_ma = cci_ema[-1]

        if self.last_cci_value <= self.last_cci_up and self.current_cci_value > self.current_cci_up:
            self.set_signal_pos(1)

        elif self.last_cci_value >= self.last_cci_up and self.current_cci_value < self.current_cci_up:
            self.set_signal_pos(-1)

        cci_sell = self.last_cci_value >= self.last_cci_ma and self.current_cci_value < self.current_cci_ma
        cci_court = self.last_cci_value <= self.last_cci_ma and self.current_cci_value > self.current_cci_ma
        if cci_sell and cci_court:
            self.set_signal_pos(0)


class BollVixSignal(CtaSignal):
    """
    布林 vix
    """
    sma_array = 0
    boll_up_array = 0
    boll_down_array = 0
    entry_crossover = 0
    atr_value = 0
    intra_trade_high = 0
    intra_trade_low = 0
    long_stop = 0
    short_stop = 0
    
    def __init__(self, open_window, boll_window: int):
        """"""
        super().__init__()
        self.open_window = open_window
        self.boll_window = boll_window

        self.bg = BarGenerator(self.on_bar, self.open_window, self.on_xmin_bar)
        self.am = ArrayManager()

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

    def on_xmin_bar(self, bar: BarData):
        """"""
        self.am.update_bar(bar)
        if not self.am.inited:
            self.set_signal_pos(0)

        # Calculate array  计算数组
        self.sma_array = self.am.sma(self.boll_window, True)
        std_array = self.am.sma(self.boll_window, True)
        dev = abs(self.am.close[:-1] - self.sma_array[:-1]) / std_array[:-1]
        dev_max = dev[-self.boll_window:].max()
        self.boll_up_array = self.sma_array[:-1] + std_array[:-1] * dev_max
        self.boll_down_array = self.sma_array[:-1] - std_array[:-1] * dev_max
        
        # Get current and last index
        last_sma = self.sma_array[-2]
        current_sma = self.sma_array[-1]
        last_close = self.am.close[-2]
        current_boll_up = self.boll_up_array[-1]
        last_boll_up = self.boll_up_array[-2]
        current_boll_down = self.boll_down_array[-1]
        last_boll_down = self.boll_down_array[-2]

        # Get crossover
        if last_close <= last_boll_up and current_boll_up < bar.close_price:
            self.set_signal_pos(1)
            
        elif last_close >= last_boll_down and current_boll_down > bar.close_price:
            self.set_signal_pos(-1)

        exit_long = last_close >= last_sma and current_sma > bar.close_price
        exit_short = last_close <= last_sma and current_sma < bar.close_price

        if exit_long and exit_short:
            self.set_signal_pos(0)

class MultiSignalStrategy(TargetPosTemplate):
    """"""

    author = "用Python的交易员"

    open_window = 36
    boll_window = 24
    cci_window = 150
    atr_length = 30

    signal_pos = {}

    parameters = ["rsi_window", "rsi_level", "cci_window",
                  "cci_level", "fast_window", "slow_window"]
    variables = ["signal_pos", "target_pos"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        # self.rsi_signal = RsiSignal(self.rsi_window, self.rsi_level)
        # self.cci_signal = CciSignal(self.cci_window, self.cci_level)
        self.bollvix_signal = BollVixSignal(self.open_window, self.boll_window)

        self.signal_pos = {
            "rsi": 0,
            "cci": 0,
            "bollvix": 0
        }

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
        super(MultiSignalStrategy, self).on_tick(tick)

        self.rsi_signal.on_tick(tick)
        self.cci_signal.on_tick(tick)
        self.bollvix_signal.on_tick(tick)

        self.calculate_target_pos()

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        super(MultiSignalStrategy, self).on_bar(bar)

        # self.rsi_signal.on_bar(bar)
        # self.cci_signal.on_bar(bar)
        self.bollvix_signal.on_bar(bar)

        self.calculate_target_pos()

    def calculate_target_pos(self):
        # """"""
        # self.signal_pos["rsi"] = self.rsi_signal.get_signal_pos()
        # self.signal_pos["cci"] = self.cci_signal.get_signal_pos()
        self.signal_pos["bollvix"] = self.bollvix_signal.get_signal_pos()

        target_pos = 0
        for v in self.signal_pos.values():
            target_pos += v

        self.set_target_pos(target_pos)

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        super(MultiSignalStrategy, self).on_order(order)

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
