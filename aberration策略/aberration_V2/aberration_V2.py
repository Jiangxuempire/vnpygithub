# _*_coding : UTF-8 _*_
# 开发团队 ：yunya
# 开发人员 ：Administrator
# 开发时间 : 2020/6/29 10:57
# 文件名称 ：aberrationstrategy.py
# 开发工具 ： PyCharm

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

class Aberration_V2_Strategy(CtaTemplate):
    """
    1、v1基础版上，调整了开仓进场条件为布林带收口。
    2、去掉cci
    """
    author = "yunya"

    open_window = 15
    boll_length = 440
    boll_dev = 1.8
    fixed_size = 1

    boll_up = 0
    boll_up_last = 0
    boll_down = 0
    boll_down_last = 0
    boll_mid = 0
    boll_mid_new = 0
    boll_mid_array = 0
    boll_length_new = 0
    exit_long_nex = 0
    exit_long_last = 0
    exit_short_nex = 0
    exit_short_last = 0
    bbw_min = 0
    bbw_ma = 0
    bbw = 0

    amplitude = 0
    stop_time = 8
    time_stop = 0
    amplitude_inited = False

    # # 画图专用
    # time_list = []
    # open_list = []
    # high_list = []
    # low_list = []
    # close_list = []
    # volume_list = []
    # up_list = []
    # down_list = []
    # mid_list = []
    # mid_new_list = []
    # bias_value_list = []
    # bias_list = []
    # singnal_plot = []
    # singnal_list = None
    # singnal = None
    #
    # plot_echarts = {}

    parameters = [
            "open_window",
            "boll_length",
            "boll_dev",
            "fixed_size",
    ]
    variables = [
        "boll_up",
        "boll_down",
        "boll_mid",
        "bias_value",
        "cci_value",
        "exit_long",
        "exit_short",
        "boll_length_new",
        "exit_long_nex",
        "exit_long_last",
        "exit_short_nex",
        "exit_short_last",
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar, self.open_window, self.on_xmin_bar)
        self.am = ArrayManager(int(self.boll_length) * 2)

        self.boll_length_new = self.boll_length

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(15)

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
        boll_up_array, boll_down_array = self.am.boll(self.boll_length, self.boll_dev, True)
        boll_mid_array = am.sma(self.boll_length, True)

        self.boll_up = boll_up_array[-1]
        self.boll_up_last = boll_up_array[-2]
        self.boll_down = boll_down_array[-1]
        self.boll_down_last = boll_down_array[-2]
        self.boll_mid = boll_mid_array[-1]

        #   计算布林宽度
        bbw_array = (boll_up_array - boll_down_array) / boll_mid_array
        bbw_length = int(self.boll_length / 2)
        self.bbw_min = bbw_array[-bbw_length - 1: -1].min()
        self.bbw_ma = bbw_array[-bbw_length - 1: -1].mean()
        self.bbw = bbw_array[-1]

        #   计算新中轨
        close_short = am.close[-1] < am.close[-2]
        close_long = am.close[-1] > am.close[-2]
        if close_short or close_long:
            self.boll_length_new -= 1
            self.boll_length_new = max(self.boll_length_new, 10)
        self.boll_mid_new = am.sma(self.boll_length_new, True)

        # 如果没有仓位，两条布林window一样
        if self.pos == 0:
            self.exit_long_nex = 0
            self.exit_long_last = 0
            self.exit_short_nex = 0
            self.exit_short_last = 0
            self.boll_length_new = self.boll_length

            if self.bbw > self.bbw_min and self.bbw_min < self.bbw_ma:
                if self.am.close[-1] > self.boll_up and self.am.close[-2] <= self.boll_up_last:
                    self.buy(bar.close_price, self.fixed_size)

                elif self.am.close[-1] < self.boll_up and self.am.close[-2] >= self.boll_up_last:
                    self.short(bar.close_price, self.fixed_size)

        elif self.pos > 0:

            # 仓位是long 时，如果价格上穿新布林中轨
            con1 = am.close[-1] < self.boll_mid_new[-1]
            con2 = am.close[-2] >= self.boll_mid_new[-2]

            if con1 and con2:
                self.exit_long_nex = am.close[-1]  # 保存当前收盘价
                if self.exit_long_nex > self.exit_long_last or self.exit_long_last == 0:
                    self.exit_long_last = self.exit_long_nex
                    self.boll_length_new = self.boll_length - 10
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
                # print(f"我是多单，收盘价在新中轨上方，以原中轨挂止损单:{self.exit_long}")

            self.sell(self.exit_long, abs(self.pos), True)

        elif self.pos < 0:
            # 仓位是short 时，如果价格上穿新布林中轨
            con3 = am.close[-1] > self.boll_mid_new[-1]
            con4 = am.close[-2] <= self.boll_mid_new[-2]

            if con3 and con4:
                self.exit_short_nex = am.close[-1]
                if self.exit_short_nex < self.exit_short_last or self.exit_short_last == 0:
                    self.exit_short_last = self.exit_short_nex
                    self.boll_length_new = self.boll_length - 10

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

            self.cover(self.exit_short, abs(self.pos), True)

        # # 画图专用
        # if self.singnal != self.singnal_list:
        #     plot = self.singnal
        # else:
        #     plot = None
        #
        # self.time_list.append(bar.datetime)
        # self.open_list.append(bar.open_price)
        # self.high_list.append(bar.high_price)
        # self.low_list.append(bar.low_price)
        # self.close_list.append(bar.close_price)
        # self.volume_list.append(bar.volume)
        # self.up_list.append(self.boll_up)
        # self.down_list.append(self.boll_down)
        # self.mid_list.append(self.boll_mid)
        # self.mid_new_list.append(self.boll_mid_new[-1])
        # self.singnal_plot.append(plot)
        #
        # self.plot_echarts = {
        #     "datetime": self.time_list,
        #     "open": self.open_list,
        #     "high": self.high_list,
        #     "low": self.low_list,
        #     "close": self.close_list,
        #     "volume": self.low_list,
        #     "boll_up": self.up_list,
        #     "boll_down": self.down_list,
        #     "boll_mid": self.mid_list,
        #     "boll_mid_new": self.mid_new_list,
        #     "bias": self.bias_value_list,
        #     "bias_value": self.bias_list,
        #     "signal": self.singnal_plot
        #
        # }
        # self.singnal_list = self.singnal

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
        pass

        # #   画图专用
        # if trade.direction.value == Direction.LONG.value:
        #     if trade.offset.value == Offset.OPEN.value:
        #         self.singnal = 1
        #
        #     elif trade.offset.value == Offset.CLOSE.value:
        #         self.singnal = 0
        #
        #     else:
        #         self.singnal = None
        #
        # elif trade.direction.value == Direction.SHORT.value:
        #     if trade.offset.value == Offset.OPEN.value:
        #         self.singnal = -1
        #
        #     elif trade.offset.value == Offset.CLOSE.value:
        #         self.singnal = 0
        #
        #     else:
        #         self.singnal = None

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        self.put_event()
        pass
