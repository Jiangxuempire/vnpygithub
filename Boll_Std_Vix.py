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
from vnpy.trader.constant import Direction


class BollStdvix(CtaTemplate):
    """"""
    author = "yunya"

    win_open = 15
    boll_window = 80
    atr_window = 30
    rsi_window = 16
    rsi_entry = 19
    atr_multiple = 2.1
    fixed_size = 1

    rsi_value = 0
    rsi_long = 0
    rsi_short = 0

    entry_rsi = 0
    entry_crossover = 0
    atr_value = 0
    intra_trade_high = 0
    intra_trade_low = 0
    long_entry = 0
    short_entry = 0
    long_stop = 0
    short_stop = 0
    current_sma = 0
    sma_array = 0
    boll_up_array = 0
    boll_down_array = 0
    trade_price_long = 0
    long_stop_trade = 0
    trade_price_short = 0
    short_stop_trade = 0

    parameters = [
            "win_open",
            "boll_window",
            "atr_window",
            "rsi_window",
            "rsi_entry",
            "atr_multiple",
            "fixed_size",
    ]

    variables = [
            "entry_crossover",
            "entry_rsi",
            "atr_value",
            "long_entry",
            "short_entry",
            "long_stop",
            "short_stop"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = NewBarGenerator(self.on_bar, self.win_open, self.on_xmin_bar)
        self.am = ArrayManager(self.boll_window + 100)

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.rsi_long = 50 + self.rsi_entry
        self.rsi_short = 50 - self.rsi_entry
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
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)

    def on_xmin_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        # Calculate array  计算数组
        self.rsi_value = am.rsi(self.rsi_window, True)
        self.sma_array = am.sma(self.boll_window, True)
        std_array = am.std(self.boll_window, True)
        dev = abs(self.am.close[:-1] - self.sma_array[:-1]) / std_array[:-1]
        dev_max = dev[-self.boll_window:].max()
        self.boll_up_array = self.sma_array + std_array * dev_max
        self.boll_down_array = self.sma_array - std_array * dev_max

        # Get current and last index
        last_rsi_value = self.rsi_value[-2]
        current_rsi_value = self.rsi_value[-1]

        self.current_sma = self.sma_array[-1]
        last_close = self.am.close[-2]
        self.current_boll_up = self.boll_up_array[-1]
        last_boll_up = self.boll_up_array[-2]
        self.current_boll_down = self.boll_down_array[-1]
        last_boll_down = self.boll_down_array[-2]

        # Get crossover
        if current_rsi_value > self.rsi_short > last_rsi_value:
            self.entry_rsi = 1
        elif current_rsi_value < self.rsi_long < last_rsi_value:
            self.entry_rsi = -1
        else:
            self.entry_rsi = 0

        if bar.close_price > self.current_boll_up and last_close <= last_boll_up:
            self.entry_crossover = 1

        elif bar.close_price < self.current_boll_down and last_close >= last_boll_down:
            self.entry_crossover = -1
        else:
            self.entry_crossover = 0

        if not self.pos:
            self.atr_value = am.atr(self.atr_window)
            # 进出场逻辑，可以优化
            if self.entry_crossover > 0:
                self.long_entry = max(self.current_boll_up,bar.close_price)
                self.buy(self.long_entry, self.fixed_size)

            elif self.entry_crossover < 0:
                self.short_entry = min(self.current_boll_down,bar.close_price)
                self.short(self.short_entry, self.fixed_size)

        elif self.pos > 0:

            self.long_stop = max(self.long_stop_trade, self.current_sma)
            self.sell(self.long_stop, abs(self.pos), True)

        elif self.pos < 0:
            self.short_stop = min(self.short_stop_trade, self.current_sma)
            self.cover(self.short_stop, abs(self.pos), True)

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
        if trade.direction == Direction.LONG:
            self.trade_price_long = trade.price  # 成交最高价
            self.long_stop_trade = self.trade_price_long - self.atr_multiple * self.atr_value

        else:
            self.trade_price_short = trade.price
            self.short_stop_trade = self.trade_price_short + self.atr_multiple * self.atr_value

        self.sync_data()
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        self.put_event()
        pass
