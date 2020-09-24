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

    """

    author = "yunya"

    open_window = 45
    rsi_window = 100
    exit_window = 65
    ema_window = 65
    atr_window = 16
    atr_window_ma = 10
    atr_multiplier = 10.0
    pos_trailing = 3.0
    fixed_size = 1

    exit_up = 0
    exit_down = 0
    atr_value = 0
    atr_value_ma = 0
    long_entry = 0
    short_entry = 0
    long_stop = 0
    short_stop = 0
    long_trade_stop = 0
    short_trade_stop = 0
    intra_trade_high = 0
    intra_trade_low = 0
    rsi_value_current = 0
    rsi_value_last = 0
    rsi_up_current = 0
    rsi_up_last = 0
    rsi_down_current = 0
    rsi_down_last = 0
    exit_long_nex = 0
    exit_long_last = 0
    exit_long = 0
    exit_short_nex = 0
    exit_short_last = 0
    exit_short = 0
    boll_mid = 0
    boll_mid_new = 0
    ema_window_new = 0

    parameters = [
            "open_window",
            "rsi_window",
            "exit_window",
            "ema_window",
            "atr_window",
            "atr_multiplier",
            "pos_trailing",
            "fixed_size",
    ]
    variables = [
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
            "rsi_value_current",
            "rsi_value_last",
            "rsi_up_current",
            "rsi_up_last",
            "rsi_down_current",
            "rsi_down_last",
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg = NewBarGenerator(self.on_bar, self.open_window, self.on_15min_bar)
        self.am = ArrayManager(self.rsi_window * 2)

        self.count: int = 0
        self.size: int = 4
        self.rsi_inited: bool = False
        self.rsi_up_array: np.ndarray = np.zeros(self.size)
        self.rsi_down_array: np.ndarray = np.zeros(self.size)

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
        rsi_array = talib.RSI(self.am.close, self.rsi_window)

        if not self.rsi_inited:
            self.count += 1
            if self.count >= self.size:
                self.rsi_inited = True

        # rsi 上下轨容器
        self.rsi_up_array[:-1] = self.rsi_up_array[1:]
        self.rsi_down_array[:-1] = self.rsi_down_array[1:]

        rsi_up = rsi_array[-self.rsi_window:].max()
        rsi_down = rsi_array[-self.rsi_window:].min()

        self.rsi_up_array[-1] = rsi_up
        self.rsi_down_array[-1] = rsi_down

        if not self.rsi_inited:
            return

        rsi_value_array = am.rsi(self.rsi_window, True)

        self.rsi_value_current = rsi_value_array[-1]
        self.rsi_value_last = rsi_value_array[-2]

        # 取前一个值
        self.rsi_up_current = self.rsi_up_array[-2]
        self.rsi_up_last = self.rsi_up_array[-3]
        self.rsi_down_current = self.rsi_down_array[-2]
        self.rsi_down_last = self.rsi_down_array[-3]

        self.exit_up, self.exit_down = self.am.donchian(self.exit_window)
        atr_value_array = am.atr(self.atr_window, True)
        self.atr_value = atr_value_array[-1]
        self.atr_value_ma = atr_value_array[-self.atr_window_ma:].mean()

        self.boll_mid = am.sma(self.ema_window)

        # 没有仓
        if not self.pos:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price
            rsi_inited_up = self.rsi_value_current > self.rsi_up_current and self.rsi_value_last <= self.rsi_up_last
            rsi_inited_down = self.rsi_value_current < self.rsi_down_current and self.rsi_value_last >= self.rsi_down_last
            atr_inited = self.atr_value > self.atr_window_ma

            self.ema_window_new = self.ema_window

            if rsi_inited_up and atr_inited and self.rsi_value_current > 50:
                self.buy(bar.close_price + 5, self.fixed_size)

            elif rsi_inited_down and atr_inited and self.rsi_value_current < 50:
                self.short(bar.close_price - 5, self.fixed_size)

        # 有多仓
        elif self.pos > 0:

            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price
            self.long_stop = self.intra_trade_high - self.atr_value * self.atr_multiplier

            self.long_stop = max(self.long_stop, self.exit_down)
            self.long_stop = max(self.long_stop, self.long_trade_stop)

            # 上涨或下跌时，布林中轨均值减1
            close_long = am.close[-1] > am.close[-2] > am.close[-3]

            if close_long:
                self.ema_window_new -= 1
                self.ema_window_new = max(self.ema_window_new, 10)

            # 计算新的布林带
            self.boll_mid_new = am.sma(self.ema_window_new, True)

            # 仓位是long 时，如果价格上穿新布林中轨
            con1 = am.close[-1] < self.boll_mid_new[-1]
            con2 = am.close[-2] >= self.boll_mid_new[-2]

            if con1 and con2:
                self.exit_long_nex = am.close[-1]  # 保存当前收盘价
                if self.exit_long_nex > self.exit_long_last or self.exit_long_last == 0:
                    self.exit_long_last = self.exit_long_nex
                    self.ema_window_new = self.ema_window
                    # 下穿新均线，以原布林均线挂出停止单，避免快速下跌而无法止损
                    self.exit_long = self.boll_mid
                    # print(f"我是多单，exitlast:{self.exit_short_last},重置布林中轨参数，止损挂{self.exit_long}：")
                else:
                    # 收盘价在两条均线平均价上方，以当前收盘价挂出限价单
                    if self.am.close[-1] > ((self.boll_mid + self.boll_mid_new[-1]) / 2):
                        self.exit_long = bar.close_price
                        # print(f"我是多单，收盘价在两个中轨均值上方，以收盘价挂止损单:{self.exit_long}")
                    elif bar.close_price < self.boll_mid:
                        self.exit_long = bar.close_price
                    else:
                        self.exit_long = self.boll_mid
                        # print(f"我是多单，收盘价在两个中轨均值下方，以原中轨挂止损单:{self.exit_long},")
            else:
                self.exit_long = self.boll_mid

            self.long_stop = max(self.long_stop, self.exit_long)

            self.sell(self.long_stop, abs(self.pos), True)

        # 有空仓
        elif self.pos < 0:

            self.intra_trade_high = bar.high_price
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
            self.short_stop = self.intra_trade_low + self.atr_value * self.atr_multiplier

            self.short_stop = min(self.short_stop, self.exit_up)
            self.short_stop = min(self.short_stop, self.short_trade_stop)

            close_short = am.close[-1] < am.close[-2] < am.close[-3]
            if close_short:
                self.ema_window_new -= 1
                self.ema_window_new = max(self.ema_window_new, 10)

            # 计算新的布林带
            self.boll_mid_new = am.sma(self.ema_window_new, True)

            # 仓位是short 时，如果价格上穿新布林中轨
            con3 = am.close[-1] > self.boll_mid_new[-1]
            con4 = am.close[-2] <= self.boll_mid_new[-2]

            if con3 and con4:
                self.exit_short_nex = am.close[-1]
                if self.exit_short_nex < self.exit_short_last or self.exit_short_last == 0:
                    self.exit_short_last = self.exit_short_nex
                    self.ema_window_new = self.ema_window

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

            self.short_stop = min(self.short_stop, self.exit_short)

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
