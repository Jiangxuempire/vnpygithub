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
from vnpy.app.cta_strategy.base import EngineType
from vnpy.trader.constant import Interval


class RsiMomentumMinuteStrategy(CtaTemplate):
    """
    EOS 遗产回测参数为：
                open_window = 50
                rsi_window = 3
                rsi_entry = 3
                atr_window = 30
                atr_ma_window = 15
                exit_window = 33
    """
    author = "yunya"

    open_window = 15
    rsi_window = 4
    rsi_entry = 19
    atr_window = 16
    atr_ma_window = 10
    exit_window = 20
    pay_up = 10
    trading_size = 1
    # risk_level = 5000


    # trading_size = 0
    atr_value = 0
    atr_ma = 0
    rsi_value = 0
    rsi_long = 0
    rsi_short = 0
    exit_up = 0
    exit_down = 0
    tick_price = 0
    engine_type = 0

    parameters = [
            "open_window",
            "rsi_window",
            "rsi_entry",
            "atr_window",
            "atr_ma_window",
            "exit_window",
            "pay_up",
            "trading_size",
    ]
    variables = ["atr_value", "atr_ma", "rsi_value", "rsi_long", "rsi_short", "exit_up", "exit_down"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(
            self.on_bar, self.open_window, self.on_hour_bar, interval=Interval.MINUTE)
        self.am = ArrayManager()

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")

        self.rsi_long = 50 + self.rsi_entry
        self.rsi_short = 50 - self.rsi_entry
        self.engine_type = self.get_engine_type()  # 测试还是实盘

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

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)

    def on_hour_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        atr_array = am.atr(self.atr_window, array=True)
        self.atr_value = atr_array[-1]
        self.atr_ma = atr_array[-self.atr_ma_window:].mean()
        self.rsi_value = am.rsi(self.rsi_window)
        self.exit_up, self.exit_down = self.am.donchian(self.exit_window)

        if self.pos == 0:
            # self.trading_size = max(int(self.risk_level / self.atr_value), 1)

            if self.engine_type != EngineType.LIVE:
                self.tick_price = self.get_pricetick() * self.pay_up
            else:
                self.tick_price = bar.close_price * 5 / 1000

            if self.atr_value > self.atr_ma:
                if self.rsi_value > self.rsi_long:
                    self.buy(bar.close_price + self.tick_price * self.pay_up, self.trading_size)
                elif self.rsi_value < self.rsi_short:
                    self.short(bar.close_price - self.tick_price * self.pay_up, self.trading_size)

        elif self.pos > 0:
            self.sell(self.exit_down, abs(self.pos), stop=True)

        elif self.pos < 0:
            self.cover(self.exit_up, abs(self.pos), stop=True)

        self.put_event()
        self.sync_data()  # 保存到硬盘

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

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
