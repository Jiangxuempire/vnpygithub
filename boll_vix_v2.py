from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    ArrayManager,
)
from vnpy.app.cta_strategy.base import EngineType
from vnpy.app.cta_strategy.new_strategy import NewBarGenerator
from vnpy.trader.constant import Interval, Direction, Offset
import numpy as np


class BollVixV2(CtaTemplate):
    """"""
    author = "yunya"

    open_window = 30
    boll_length = 610
    dc_length = 80
    fixed_size = 1

    boll_mid_current = 0
    boll_mid_last = 0
    boll_up_current = 0
    boll_up_last = 0
    boll_down_current = 0
    boll_down_last = 0
    target_pos = 0
    pos_inited = 0
    boll_mid = 0
    exit_long = 0
    exit_short = 0
    long_price = 0
    short_price = 0

    # 画图专用
    time_list = []
    open_list = []
    high_list = []
    low_list = []
    close_list = []
    volume_list = []
    up_list = []
    down_list = []
    mid_list = []
    mid_new_list = []
    bias_value_list = []
    bias_list = []
    exit_long_list = []
    exit_short_list = []
    singnal_plot = []
    singnal_list = None
    singnal = None

    plot_echarts = {}

    parameters = [
        "open_window",
        "boll_length",
        "fixed_size",
    ]

    variables = [
        "boll_mid_current",
        "boll_mid_last",
        "boll_up_current",
        "boll_up_last",
        "boll_down_current",
        "boll_down_last",
        "pos_inited",
        "target_pos"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = NewBarGenerator(self.on_bar, self.open_window, self.on_minute_bar, interval=Interval.MINUTE)
        self.am = ArrayManager(self.boll_length * 2)

        self.up_array: np.ndarray = np.zeros(5)
        self.down_array: np.ndarray = np.zeros(5)
        self.boll_inited = False
        self.boll_count = 0

        self.engine_type = self.get_engine_type()
        self.vt_orderids = []
        self.order_price = 0

        self.pos_inited = 0

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(12)

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

        # 只有实盘交易才使用BestLimit算法
        if self.engine_type != EngineType.LIVE:
            return

        #  当前没有仓位
        order_volume_open = self.target_pos - self.pos

        if not order_volume_open:
            return

        if order_volume_open > 0:
            if not self.vt_orderids:
                self.order_price = tick.bid_price_1
                vt_orderids = self.buy(self.order_price, abs(order_volume_open))
                self.vt_orderids.extend(vt_orderids)
            elif self.order_price != tick.bid_price_1:
                for vt_orderid in self.vt_orderids:
                    self.cancel_order(vt_orderid)

        elif order_volume_open < 0:
            if not self.vt_orderids:
                self.order_price = tick.ask_price_1
                vt_orderids = self.short(self.order_price, abs(order_volume_open))
                self.vt_orderids.extend(vt_orderids)
            elif self.order_price != tick.ask_price_1:
                for vt_orderid in self.vt_orderids:
                    self.cancel_order(vt_orderid)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)

    def on_minute_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        # 计算布林
        sma_array = self.am.sma(self.boll_length, True)
        std_array = self.am.std(self.boll_length, True)
        dev = abs(self.am.close[:-1] - sma_array[:-1]) / std_array[:-1]
        # dev_max = dev[-self.boll_length:].max()
        dev_max = dev[-self.boll_length:].mean()
        up = sma_array + std_array * dev_max
        down = sma_array - std_array * dev_max

        boll_mid_array = self.am.sma(self.boll_length, True)

        dc_up, dc_down = self.am.donchian(self.dc_length, True)
        self.exit_short = dc_up[-2]
        self.exit_long = dc_down[-2]

        # 计算数组
        self.boll_mid = boll_mid_array[-2]
        self.boll_up_current = up[-1]
        self.boll_up_last = up[-2]
        self.boll_down_current = down[-1]
        self.boll_down_last = down[-2]

        if not self.pos:
            self.pos_inited = 0

            if self.am.close[-1] > self.boll_up_current and self.am.close[-2] <= self.boll_up_last:

                if self.engine_type == EngineType.BACKTESTING:
                    self.buy(bar.close_price, self.fixed_size)
                else:
                    self.target_pos = self.fixed_size
                    print("没有仓位，我开多")

            elif self.am.close[-1] < self.boll_down_current and self.am.close[-2] >= self.boll_down_last:

                if self.engine_type == EngineType.BACKTESTING:
                    self.short(bar.close_price, self.fixed_size)
                else:
                    self.target_pos = -self.fixed_size
                    print("没有仓位，我开空")

        elif self.pos > 0:

            self.long_price = max(self.exit_long, self.boll_mid)
            self.sell(self.long_price, abs(self.pos), True)

        elif self.pos < 0:
            self.short_price = min(self.exit_short, self.boll_mid)
            self.cover(self.short_price, abs(self.pos), True)
        #
        #   画图专用
        if self.singnal != self.singnal_list:
            plot = self.singnal
        else:
            plot = None

        self.time_list.append(bar.datetime)
        self.open_list.append(bar.open_price)
        self.high_list.append(bar.high_price)
        self.low_list.append(bar.low_price)
        self.close_list.append(bar.close_price)
        self.volume_list.append(bar.volume)
        self.up_list.append(self.boll_up_current)
        self.down_list.append(self.boll_down_current)
        self.mid_list.append(self.boll_mid)
        self.exit_long_list.append(self.long_price)
        self.exit_short_list.append(self.short_price)
        self.singnal_plot.append(plot)

        self.plot_echarts = {
            "datetime": self.time_list,
            "open": self.open_list,
            "high": self.high_list,
            "low": self.low_list,
            "close": self.close_list,
            "volume": self.low_list,
            "boll_up": self.up_list,
            "boll_down": self.down_list,
            "boll_mid": self.mid_list,
            "exit_long": self.exit_long_list,
            "exit_short": self.exit_short_list,
            "signal": self.singnal_plot

        }
        self.singnal_list = self.singnal

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
        if trade.direction.value == Direction.LONG.value:
            if trade.offset.value == Offset.OPEN.value:
                self.singnal = 1

            elif trade.offset.value == Offset.CLOSE.value:
                self.singnal = 0

            else:
                self.singnal = None

        elif trade.direction.value == Direction.SHORT.value:
            if trade.offset.value == Offset.OPEN.value:
                self.singnal = -1

            elif trade.offset.value == Offset.CLOSE.value:
                self.singnal = 0

            else:
                self.singnal = None

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass

    def boll_calculate(self):
        """
        计算布林
        :return:
        """

        if not self.boll_inited:
            self.boll_count += 1
            if self.boll_count >= 6:
                self.boll_inited = True

        self.up_array[:-1] = self.up_array[1:]
        self.down_array[:-1] = self.down_array[1:]

        sma_array = self.am.sma(self.boll_length, True)
        std_array = self.am.std(self.boll_length, True)
        dev = abs(self.am.close[:-1] - sma_array[:-1]) / std_array[:-1]
        dev_max = dev[-self.boll_length:].max()
        up = sma_array[-1] + std_array[-1] * dev_max
        down = sma_array[-1] - std_array[-1] * dev_max

        self.up_array[-1] = up
        self.down_array[-1] = down
