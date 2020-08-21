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

class EmaDifferenceStrategy(CtaTemplate):
    """
    策略逻辑：
        1、计算两条不同周期均线的差离值，差离值二次求均值。
        2、当差离值大于零做多，小于零做空。
        3、成交价格回撤 2% 固定止损，当利润达到 5% 时，止损位移动到成本价。



        1、计算四条差离值线，并求30周期ema 如果所有差离线全部在零线附近（-0.1，+0.1），
        2、如果所有线上穿大周期开多，所有线下穿大周期开空。
        3、引入打分系统，各个指标计算，每个值为正向一分，分数达到N值开多，小于-N 开空。 小于N-时减部分仓位。
        4、判断各线之间上穿和下穿来打分，短周期上穿长周期加1分，短周期下穿长周期减1分，长周期是否拐头，拐头向上加一分，向下减一分。
    """
    author = "yunya"

    open_window = 15
    fastest_length = 10     # 最快
    fast_length = 30        # 快
    slow_length = 60        # 慢
    slowest_length = 120    # 最慢
    extremely_slow_length = 180  # 特慢
    diff_ema_length = 30    # 差离ema
    diff_deviate = 0.2      # 零轴的偏离最
    fixed_size = 1

    fast_ema = 0        # 差离均值
    slow_ema = 0
    slowest_ema = 0
    extremely_slow_ema = 0

    fast_diff_deviate = 0       # 差离线与零轴的位置
    slow_diff_deviate = 0
    slowest_diff_deviate = 0
    extremely_slow_diff_deviate = 0

    fast_slow_to = 0         # 判断上穿，下穿，上穿1 下穿-1
    fast_slowest_to = 0
    fast_extremely_slow_to = 0

    slow_slowest_to = 0
    slow_extremely_to = 0
    slowest_extremely_to = 0




    parameters = [

                ]

    variables = [

                ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = NewBarGenerator(self.on_bar, self.open_window, self.on_xmin_bar)
        self.am = ArrayManager(int(self.extremelyslow_length) * 100)

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
        fastest_value = am.ema(self.fastest_length, True)
        fast_value = am.ema(self.fast_length, True)
        slow_value = am.ema(self.slow_length, True)
        slowest_value = am.ema(self.slowest_length, True)
        extremely_slow_value = am.ema(self.extremely_slow_length, True)

        # 计算差离值
        fastest_fast_diff = fastest_value - fast_value
        fast_slow_diff = fast_value - slow_value
        slow_slowest_diff = slow_value - slowest_value
        slowest_extremely_slow_diff = slow_value - extremely_slow_value

        # 计算差离均值
        self.fast_ema = talib.EMA(fastest_fast_diff, self.diff_ema_length)
        self.slow_ema = talib.EMA(fast_slow_diff, self.diff_ema_length)
        self.slowest_ema = talib.EMA(slow_slowest_diff, self.diff_ema_length)
        self.extremely_slow_ema = talib.EMA(slowest_extremely_slow_diff, self.diff_ema_length)

        # 判断差离线与零轴的位置(在零轴附近)
        self.fast_diff_deviate = self.on_diff_range(self.fast_ema, self.diff_deviate)
        self.slow_diff_deviate = self.on_diff_range(self.slow_ema, self.diff_deviate)
        self.slowest_diff_deviate = self.on_diff_range(self.slowest_ema, self.diff_deviate)
        self.extremely_slow_diff_deviate = self.on_diff_range(self.extremely_slow_ema, self.diff_deviate)

        # 判断差离线交叉情况（上穿,下穿）
        self.fast_slow_to = self.on_diff_to_up_down(self.fast_ema, self.slow_ema)
        self.fast_slowest_to = self.on_diff_to_up_down(self.fast_ema, self.slowest_ema)
        self.fast_extremely_slow_to = self.on_diff_to_up_down(self.fast_ema, self.extremely_slow_ema)
        self.slow_slowest_to = self.on_diff_to_up_down(self.slow_ema, self.slowest_ema)
        self.slow_extremely_to = self.on_diff_to_up_down(self.slow_ema, self.extremely_slow_ema)
        self.slowest_extremely_to = self.on_diff_to_up_down(self.slowest_ema, self.extremely_slow_ema)
        

        # 如果没有仓位，两条布林window一样
        if self.pos == 0:
            self.exit_long_nex = 0
            self.exit_long_last = 0
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
                self.boll_length_new = max(self.boll_length_new,10)

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
            close_short = am.close[-1] < am.close[-2] < am.close[-3]

            if close_short:
                self.boll_length_new -= 1
                self.boll_length_new = max(self.boll_length_new,10)

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

    def on_diff_range(self, diff_array, diff_deviate):
        """
        判断 diff 是否在一定范围内
        :param diff_array:
        :param range:
        :return:
        """

        for i in range(1, 6, 1):

            diff_up = diff_array[-i] > -diff_deviate
            diff_down = diff_array[-i] < diff_deviate

            if diff_up and diff_down:
                diff_range = True
            else:
                diff_range = False
            return diff_range

    def on_diff_to_up_down(self, fastdiffema, slowdiffema):
        """
        差离线上穿、下穿
        :param diff_ema:
        :return:
        """
        current_fast_diff = fastdiffema[-1]
        last_fast_diff = fastdiffema[-2]
        current_slow_diff = slowdiffema[-1]
        last_slow_diff = slowdiffema[-2]
        to_up_down = 0

        if current_fast_diff > current_slow_diff and last_fast_diff <= last_slow_diff:
            to_up_down = 1
        elif current_fast_diff < current_slow_diff and last_fast_diff >= last_slow_diff:
            to_up_down = -1
        else:
            to_up_down = 0

        return to_up_down