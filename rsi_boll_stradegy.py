# _*_coding : UTF-8 _*_
# 开发团队 ：yunya
# 开发人员 ：Administrator
# 开发时间 : 2020/9/3 20:30
# 文件名称 ：rsi_boll_stradegy.py
# 开发工具 ： PyCharm

from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    ArrayManager,
)
from vnpy.trader.object import Direction
from  vnpy.app.cta_strategy.new_strategy import NewBarGenerator

class RisBollStrategy(CtaTemplate):
    """
    目前使用中轨加速，可以考虑使用另外一根均线来加速，这样可以避免在开仓时被平。
    """
    author = "yunya"

    open_window = 15
    boll_length = 80
    boll_dev = 2.0
    rsi_window = 12
    rsi_entry = 19
    atr_window = 16
    long_trailing = 4.0
    short_trailing = 4.0
    fixed_size = 1

    rsi_long = 0
    rsi_short = 0
    rsi_value = 0
    atr_value = 0
    boll_up = 0
    boll_down = 0
    boll_mid = 0
    boll_mid_new = 0
    exit_long = 0
    exit_short = 0
    boll_length_new = 0
    exit_long_nex = 0
    exit_long_last = 0
    exit_short_nex = 0
    exit_short_last = 0
    long_stop_trade = 0
    short_stop_trade = 0
    trade_price_long = 0
    trade_price_short = 0

    parameters = [
                "open_window",
                "boll_length",
                "boll_dev",
                "rsi_window",
                "rsi_entry",
                "atr_window",
                "long_trailing",
                "short_trailing",
                "fixed_size",
                ]

    variables = [
            "rsi_long",
            "rsi_short",
            "rsi_value",
            "atr_value",
            "boll_up",
            "boll_down",
            "boll_mid",
            "boll_mid_new",
            "exit_long",
            "exit_short",
            "boll_length_new",
            "exit_long_nex",
            "exit_long_last",
            "exit_short_nex",
            "exit_short_last",
            "long_stop_trade",
            "short_stop_trade",
            "trade_price_long",
            "trade_price_short",
                ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = NewBarGenerator(self.on_bar, self.open_window, self.on_xmin_bar)
        self.am = ArrayManager(int(self.boll_length) + 100)

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

    def on_xmin_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        # 计算原布林带
        self.boll_up, self.boll_down = self.am.boll(self.boll_length, self.boll_dev)
        self.boll_mid = am.sma(self.boll_length)
        self.rsi_value = am.rsi(self.rsi_window)

        # 如果没有仓位，两条布林window一样
        if self.pos == 0:
            self.atr_value = am.atr(self.atr_window)
            self.exit_long_nex = 0
            self.exit_long_last = 0
            self.exit_short_nex = 0
            self.exit_short_last = 0
            self.boll_length_new = self.boll_length

            if self.rsi_value > self.rsi_long:
                self.buy(self.boll_up, self.fixed_size, True)

            if self.rsi_value < self.rsi_short:
                self.short(self.boll_down, self.fixed_size, True)

        elif self.pos > 0:
            # 上涨或下跌时，布林中轨均值减1
            close_long = am.close[-1] > am.close[-2] > am.close[-3] > am.close[-4]

            if close_long:
                self.boll_length_new -= 1
                self.boll_length_new = max(self.boll_length_new, 10)

            # 计算新的布林带
            self.boll_mid_new = am.sma(self.boll_length_new, True)

            # 仓位是long 时，如果价格上穿新布林中轨
            con1 = am.close[-1] < self.boll_mid_new[-1]
            con2 = am.close[-2] >= self.boll_mid_new[-2]

            if con1 and con2:
                self.exit_long_nex = am.close[-1]  # 保存当前收盘价
                if self.exit_long_nex > self.exit_long_last or self.exit_long_last == 0:
                    self.exit_long_last = self.exit_long_nex
                    self.boll_length_new = self.boll_length
                    # 下穿新均线，以原布林均线挂出停止单，避免快速下跌而无法止损
                    self.exit_long = self.boll_mid

                else:
                    # 收盘价在两条均线平均价上方，以当前收盘价挂出限价单
                    if self.am.close[-1] > ((self.boll_mid + self.boll_mid_new[-1]) / 2):
                        self.exit_long = bar.close_price

                    elif bar.close_price < self.boll_mid:
                        self.exit_long = bar.close_price
                    else:
                        self.exit_long = self.boll_mid

            else:
                self.exit_long = self.boll_mid

            if bar.close_price < self.trade_price_long * (1 - self.long_trailing / 100):
                exit_long_price = self.trade_price_long * (1 - (self.long_trailing + 1) / 100)
                self.exit_long = max(exit_long_price, self.exit_long)

            self.exit_long = max(self.exit_long, self.long_stop_trade)
            self.sell(self.exit_long, abs(self.pos), True)

        elif self.pos < 0:
            close_short = am.close[-1] < am.close[-2] < am.close[-3] < am.close[-4]

            if close_short:
                self.boll_length_new -= 1
                self.boll_length_new = max(self.boll_length_new, 10)

            # 计算新的布林带
            self.boll_mid_new = am.sma(self.boll_length_new, True)

            # 仓位是short 时，如果价格上穿新布林中轨
            con3 = am.close[-1] > self.boll_mid_new[-1]
            con4 = am.close[-2] <= self.boll_mid_new[-2]

            if con3 and con4:
                self.exit_short_nex = am.close[-1]
                if self.exit_short_nex < self.exit_short_last or self.exit_short_last == 0:
                    self.exit_short_last = self.exit_short_nex
                    self.boll_length_new = self.boll_length

                    self.exit_short = self.boll_mid
                else:
                    if self.am.close[-1] < (self.boll_mid + self.boll_mid_new[-1] / 2):
                        self.exit_short = bar.close_price

                    elif bar.close_price > self.boll_mid:
                        self.exit_short = bar.close_price
                    else:
                        self.exit_short = self.boll_mid
            else:
                self.exit_short = self.boll_mid

            # 如果 有3%以上的收益，止损价为买入成交价
            if bar.close_price > self.trade_price_short * (1 + self.short_trailing / 100):
                exit_short_price = self.trade_price_short * (1 + (self.short_trailing + 1) / 100)
                self.exit_short = min(exit_short_price, self.exit_short)

            self.exit_short = min(self.exit_short, self.short_stop_trade)
            self.cover(self.exit_short, abs(self.pos), True)

        self.put_event()
        self.sync_data()

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
            self.long_stop_trade = self.trade_price_long - 2 * self.atr_value
        else:
            self.trade_price_short = trade.price
            self.short_stop_trade = self.trade_price_short + 2 * self.atr_value

        self.sync_data()
        self.put_event()