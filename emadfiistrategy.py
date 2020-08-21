# _*_coding : UTF-8 _*_
# 开发团队 ：yunya
# 开发人员 ：Administrator
# 开发时间 : 2020/6/29 10:57
# 文件名称 ：aberrationstrategy.py
# 开发工具 ： PyCharm
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
from vnpy.app.cta_strategy.base import EngineType
from vnpy.trader.object import Direction
from vnpy.app.cta_strategy.new_strategy import NewBarGenerator

class EmaDifferenceStrategy(CtaTemplate):
    """
    策略逻辑：
        1、计算两条不同周期均线的差离值，差离值二次求均值。
        2、当差离值大于零做多，小于零做空。
        3、成交价格回撤 2% 固定止损，当利润达到 5% 时，止损位移动到成本价。
    """
    author = "yunya"

    open_window = 15
    express_length = 30 # 特快
    fast_length = 60  # 快
    slow_length = 150  # 慢
    diff_ema_length = 30  # 差离ema
    atr_length = 6
    atr_multiple = 2.0      # 成交价 2倍ATR为固定止损位
    entry_mulitple = 5.0    # 当前价格超过成交价的5%时，止损价为成交价
    pay_up = 5
    fixed_size = 1

    current_express_fast_diff = 0
    last_express_fast_diff = 0
    current_fast_slow_diff = 0
    last_fast_slow_diff = 0
    current_express_fast_ema = 0
    last_express_fast_ema = 0
    current_fast_slow_ema = 0
    last_fast_slow_ema = 0
    express_fast_inited = 0
    fast_slow_inited = 0
    price_tick = 0
    atr_value = 0
    long_entry = 0
    long_stop = 0
    short_entry = 0
    short_stop = 0
    exit_long = 0
    exit_short = 0


    parameters = [
            "open_window",
            "express_length",
            "fast_length",
            "slow_length",
            "diff_ema_length",
            "atr_length",
            "atr_multiple",
            "entry_mulitple",
            "pay_up",
            "fixed_size",
    ]

    variables = [
            "current_express_fast_diff",
            "last_express_fast_diff",
            "current_fast_slow_diff",
            "last_fast_slow_diff",
            "current_express_fast_ema",
            "last_express_fast_ema",
            "current_fast_slow_ema",
            "last_fast_slow_ema",
            "express_fast_inited",
            "fast_slow_inited",
            "price_tick",
            "atr_value",
            "long_entry",
            "long_stop",
            "short_entry",
            "short_stop",
            "exit_long",
            "exit_short",

    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = NewBarGenerator(self.on_bar, self.open_window, self.on_xmin_bar)
        self.am = ArrayManager(int(self.slow_length) * 100)

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

        # 计算ema
        express_value = am.ema(self.express_length, True)
        fast_value = am.ema(self.fast_length, True)
        slow_value = am.ema(self.slow_length, True)

        # 计算差离值
        express_fast_diff = express_value - fast_value
        fast_slow_diff = fast_value - slow_value

        # 计算差离均值
        express_fast_ema = talib.EMA(express_fast_diff, self.diff_ema_length)
        fast_slow_ema = talib.EMA(fast_slow_diff, self.diff_ema_length)
        # print(f"express_fast_ema: {express_fast_ema[-10:]}" + "\n")
        # print(f"fast_slow_ema: {fast_slow_ema[-10:]}" + "\n")

        # 判断差离线交叉情况（上穿,下穿）
        self.current_express_fast_diff = express_fast_diff[-1]
        self.last_express_fast_diff = express_fast_diff[-2]
        self.current_fast_slow_diff = fast_slow_diff[-1]
        self.last_fast_slow_diff = fast_slow_diff[-2]

        self.current_express_fast_ema = express_fast_ema[-1]
        self.last_express_fast_ema = express_fast_ema[-2]
        self.current_fast_slow_ema = fast_slow_ema[-1]
        self.last_fast_slow_ema = fast_slow_ema[-2]

        # 计算上穿，下穿零轴
        if self.current_express_fast_ema > 0 and self.last_express_fast_ema <= 0:
            self.express_fast_inited = 1

        elif self.current_express_fast_ema < 0 and self.last_express_fast_ema >= 0:
            self.express_fast_inited = -1
        else:
            self.express_fast_inited = 0
        print(f"特慢：{self.express_fast_inited}" + "\n")
        if self.current_fast_slow_ema > 0 and self.last_fast_slow_ema <= 0:
            self.fast_slow_inited = 1

        elif self.current_fast_slow_ema < 0 and self.last_fast_slow_ema >= 0:
            self.fast_slow_inited = -1
        else:
            self.fast_slow_inited = 0

        # 如果没有仓位，两条布林window一样
        if self.pos == 0:
            # 判断是回测，还是实盘
            engine_type = self.get_engine_type()
            if engine_type == EngineType.BACKTESTING:
                long_price = bar.close_price - 10
                short_price = bar.close_price + 10
            else:
                self.price_tick = self.get_pricetick()
                long_price = bar.close_price - self.price_tick * self.pay_up
                short_price = bar.close_price + self.price_tick * self.pay_up

            self.atr_value = self.am.atr(self.atr_length)

            if self.fast_slow_inited > 0:
                self.buy(long_price, self.fixed_size)

            elif self.fast_slow_inited < 0:
                self.short(short_price, self.fixed_size)

        elif self.pos > 0:
            long_stop_entry = bar.close_price * (1 - self.entry_mulitple / 100)
            self.exit_long = max(self.long_stop, long_stop_entry)

            if self.express_fast_inited < 0:
                # self.exit_long = bar.close_price - self.price_tick * self.pay_up
                self.exit_long = bar.close_price - 10

            self.sell(self.exit_long, abs(self.pos), True)

        elif self.pos < 0:
            short_stop_entry = bar.close_price * (1 + self.entry_mulitple / 100)
            self.exit_short = min(self.short_stop, short_stop_entry)

            if self.express_fast_inited > 0:
                # self.exit_short = bar.close_price + self.price_tick * self.pay_up
                self.exit_short = bar.close_price + 10
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
            self.long_entry = trade.price  # 成交最高价
            self.long_stop = self.long_entry - self.atr_multiple * self.atr_value
        else:
            self.short_entry = trade.price
            self.short_stop = self.short_entry + self.atr_multiple * self.atr_value

        self.sync_data()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        self.put_event()
        pass
