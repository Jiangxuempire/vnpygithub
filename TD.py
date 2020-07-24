# _*_coding : UTF-8 _*_
#开发团队 ：yunya
#开发人员 ：Administrator
#开发时间 : 2020/6/24 20:28
#文件名称 ：TD.py
#开发工具 ： PyCharm

# _*_coding : UTF-8 _*_
#开发团队 ：yunya
#开发人员 ：Administrator
#开发时间 : 2020/6/12 14:34
#文件名称 ：mike_boll_strategy.py
#开发工具 ： PyCharm


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
import numpy as np
from vnpy.trader.constant import Direction ,Interval


class Mike_Boll_Strategy(CtaTemplate):
    """"""

    author = "yunya"
    td_long = 0
    td_short = 0


    parameters = [

                    ]

    variables = [

                    ]

    def __init__(self, cta_engine, strategy_nam_xhoure, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_nam_xhoure, vt_symbol, setting)


        self.bg = BarGenerator(
                                on_bar=self.on_bar,
                                window=1,
                                on_window_bar=self.on_hour_bar,
                                interval=Interval.HOUR
                            )
        self.am = ArrayManager()
        self.td_long = np.zeros(30)
        self.td_short = np.zeros(30)

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


    def on_hour_bar(self, bar: BarData):
        """
        """

        self.am.update_bar(bar)
        if not self.am.inited:
            return

        self.td_long[1:] = self.td_long[:-1]
        self.td_short[1:] = self.td_short[:-1]

        self.td_long,self.td_short = self.td(self.td_long,self.td_short,self.am.close)

        print(f"")







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

    def td_(self,td_long,td_short,close):

        if close[-1] > close[-4]:
            td_long[-1] = td_long[-2] + 1
        else:
            td_long[-1] = 0

        if close[-1] < close[-4]:
            td_short[-1] = td_short + 1
        else:
            td_short[-1] = 0

        if td_long[-1] == 9:
            long_td9 = 9
        else:
            long_td9 = 0

        if td_long[-1] == 13:
            long_td13 = 13
        else:
            long_td13 = 0

        if td_short[-1] == 9:
            short_td9 = 9
        else:
            short_td9 = 0

        if td_short[-1] == 13:
            short_td13 = 13
        else:
            short_td13 = 0

        return long_td9,long_td13,short_td9,short_td13
