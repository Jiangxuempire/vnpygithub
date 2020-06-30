# _*_coding : UTF-8 _*_
#开发团队 ：yunya
#开发人员 ：Administrator
#开发时间 : 2020/6/29 10:57
#文件名称 ：aberrationstrategy.py
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
from vnpy.trader.object import Direction
from  vnpy.app.cta_strategy.new_strategy import NewBarGenerator

class AberrationStrategy(CtaTemplate):
    """"""
    author = "yunya"

    open_window = 15
    boll_length = 80
    boll_dev = 2.0
    cci_length = 6
    cci_exit = 10.0
    fixed_size = 1

    boll_mid = 0
    boll_mid_new = 0
    cci_value = 0
    exit_long = 0
    exit_short = 0
    boll_length_new = 0
    exit_long_nex = 0
    exit_long_last = 0
    exit_short_nex = 0
    exit_short_last = 0


    parameters = [
                "open_window",
                "boll_length",
                "boll_dev",
                "cci_length",
                "cci_exit",
                "fixed_size",
                ]

    variables = [
                "boll_mid",
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

        self.bg = NewBarGenerator(self.on_bar, self.open_window, self.on_xmin_bar)
        self.am = ArrayManager(int(self.boll_length) + 100)

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
        self.boll_up,self.boll_down = self.am.boll(self.boll_length,self.boll_dev)
        self.boll_mid = am.sma(self.boll_length)
        self.cci_value = am.cci(self.cci_length)

        # 如果没有仓位，两条布林window一样
        if self.pos == 0:
            self.exit_long_nex = 0
            self.exit_short_last = 0
            self.exit_short_nex = 0
            self.exit_short_last = 0
            self.boll_length_new = self.boll_length

            if self.cci_value > self.cci_exit:
                self.buy(self.boll_up, self.fixed_size, True)

            if self.cci_value < -self.cci_exit:
                self.short(self.boll_down, self.fixed_size, True)

        elif self.pos > 0:
            # 上涨或下跌时，布林中轨均值减1
            close_long = am.close[-1] > am.close[-2] > am.close[-3]

            if close_long:
                self.boll_length_new -= 1
                self.boll_length_new = max(self.boll_length_new,20)

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
                    # print(f"我是多单，exitlast:{self.exit_short_last},重置布林中轨参数，止损挂{self.exit_long}：")
                else:
                    # 收盘价在两条均线平均价上方，以当前收盘价挂出限价单
                    if self.am.close[-1] > ((self.boll_mid + self.boll_mid_new[-1]) / 2 ):
                        self.exit_long = bar.close_price
                        # print(f"我是多单，收盘价在两个中轨均值上方，以收盘价挂止损单:{self.exit_long}")
                    else:
                        self.exit_long = self.boll_mid
                        # print(f"我是多单，收盘价在两个中轨均值下方，以原中轨挂止损单:{self.exit_long},")
            else:
                self.exit_long = self.boll_mid
                # print(f"我是多单，收盘价在新中轨上方，以原中轨挂止损单:{self.exit_long}")

            self.sell(self.exit_long, abs(self.pos), True)

        elif self.pos < 0:
            close_short = am.close[-1] < am.close[-2] < am.close[-3]

            if close_short:
                self.boll_length_new -= 1
                self.boll_length_new = max(self.boll_length_new,20)

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
                    else:
                        self.exit_short = self.boll_mid

            else:
                self.exit_short = self.boll_mid

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
        self.put_event()
        pass
    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        self.put_event()
        pass

