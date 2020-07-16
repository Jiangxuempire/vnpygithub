# _*_coding : UTF-8 _*_
#开发团队 ：yunya
#开发人员 ：Administrator
#开发时间 : 2020/7/14 16:04
#文件名称 ：deviationstrategy.py
#开发工具 ： PyCharm
import talib

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

from vnpy.trader.constant import Interval, Exchange, Direction


class DeviationStrategy(CtaTemplate):
    """"""
    author = "yunya"

    exchange = "BYBIT"
    xminute_window = 15
    short_length = 30
    medium_length = 60
    long_length = 120
    entry_window = 28
    exit_window = 7
    atr_window = 4
    trading_size = 1
    # risk_level = 0.2

    ema_initde = 0
    # trading_size = 0
    entry_up = 0
    entry_down = 0
    exit_up = 0
    exit_down = 0
    atr_value = 0

    long_entry = 0
    short_entry = 0
    long_stop = 0
    short_stop = 0

    parameters = ["entry_window", "exit_window", "atr_window", "risk_level"]
    variables = [
        "ema_initde","entry_up", "entry_down", "exit_up",
        "exit_down", "atr_value"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(
            self.on_bar, self.xminute_window, self.on_xminute_bar, interval=Interval.MINUTE)
        self.am = ArrayManager(self.long_length + 100)

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar_exchange(days=10)

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

    def on_xminute_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        self.am.update_bar(bar)
        if not self.am.inited:
            return

        self.entry_up, self.entry_down = self.am.donchian(self.entry_window)
        self.exit_up, self.exit_down = self.am.donchian(self.exit_window)

        short_ema = self.am.ema(self.short_length,True)
        mdeium_ema = self.am.ema(self.medium_length,True)
        long_ema = self.am.ema(self.long_length,True)

        short_mdeium_array = short_ema - mdeium_ema
        mdeium__long_array = mdeium_ema - long_ema

        current_short_mdeium = short_mdeium_array[-1]
        last_short_mdeium = short_mdeium_array[-2]

        current_mdeium_long = mdeium__long_array[-1]
        last_mdeium_long = mdeium__long_array[-2]

        con1 = current_short_mdeium > current_mdeium_long
        con2 = last_short_mdeium <= last_mdeium_long
        con3 = current_short_mdeium < current_mdeium_long
        con4 = last_short_mdeium >= last_mdeium_long

        if con1 and con2:
            self.ema_initde = 1

        elif con3 and con4:
            self.ema_initde = -1

        if not self.pos:
            self.atr_value = self.am.atr(self.atr_window)

            # if self.atr_value == 0:
            #     return
            # # 反向合约的计算方法，
            # atr_risk = talib.ATR(
            #     1 / self.am.high,
            #     1 / self.am.low,
            #     1 / self.am.close,
            #     self.atr_window
            # )[-1]
            # self.trading_size = max(int(self.risk_level / atr_risk), 1)

            self.long_entry = 0
            self.short_entry = 0
            self.long_stop = 0
            self.short_stop = 0

            if self.ema_initde > 0:
                self.buy(self.entry_up, self.trading_size, True)

            elif self.ema_initde < 0:
                self.short(self.entry_down, self.trading_size, True)

        elif self.pos > 0:
            sell_price = max(self.long_stop, self.exit_down)
            self.sell(sell_price, abs(self.pos), True)

        elif self.pos < 0:
            cover_price = min(self.short_stop, self.exit_up)
            self.cover(cover_price, abs(self.pos), True)

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
        pass

    def load_bar_exchange(self,days:int):
        """"
        判断是属于那个交易所，使用不同的初始化方式
        """
        if self.exchange == Exchange.HUOBI:
            self.load_bar(days=days,use_database=True)
            self.write_log(f"{self.exchange}交易所，从本地获取{days}数据初始化！")

        elif self.exchange == Exchange.OKEX:
            self.load_bar(days=days, use_database=True)
            self.write_log(f"{self.exchange}交易所，从本地获取{days}数据初始化！")
        else:
            self.load_bar(days=days)
            self.write_log(f"{self.exchange}交易所，从交易获取{days}数据初始化！")
