# _*_coding : UTF-8 _*_
#开发团队 ：yunya
#开发人员 ：Administrator
#开发时间 : 2020/7/12 15:18
#文件名称 ：meandeviationstrategy.py
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

from  vnpy.app.cta_strategy.new_strategy import NewBarGenerator
import talib

from vnpy.trader.constant import Interval,Exchange
from vnpy.trader.object import Direction

class MeanDeviationStrategy(CtaTemplate):
    """
    策略逻辑：
    1、通过计算ema 均线 10 30 60 120 180 四条均线的差离值
    2、计算四条线的交叉情况
    3、计算四条线的黏合情况  （四条线的差值在非常小的范围 如： 0.01）
    4、 计算四条线中的价背离情况 价格新低，但指标线没有新低，并且前三条线都拐头： 多头拐头： ema10_ema30[-1] > ema10_ema30[-2] > ema10_ema30[-3]

    """
    author = "yunya"

    exchange = "BYBIT"
    open_window = 2
    xminute_window = 15
    minimum_length = 10
    short_length = 30
    medium_length = 60
    long_length = 120
    longest_length = 180
    width_limit = 1.0
    turn_length = 5

    fixed_size = 1

    turn_min_short = 0
    turn_short_mdeiun = 0
    turn_mdeiun_long = 0
    turn_long_longest = 0
    min_short_inited = 0
    short_mdeiun_inited = 0
    medium_long_initde = 0
    long_longest_inited = 0


    current_close = 0
    last_close = 0
    first_close = 0
    fourth_close = 0

    current_close_min = 0
    last_close_min = 0
    first_close_min = 0
    fourth_close_min = 0

    current_min_short = 0
    last_min_short = 0
    first_min_short = 0
    fourth_min_short = 0

    current_short_mdeium = 0
    last_short_mdeium = 0
    first_short_mdeium = 0
    fourth_short_mdeium = 0

    current_mdeium_long = 0
    last_mdeium_long = 0
    first_mdeium_long = 0
    fourth_mdeium_long = 0

    current_long_longest = 0
    last_long_longest = 0
    first_long_longest = 0
    fourth_long_longest = 0











    boll_length = 80
    boll_dev = 2.0
    cci_length = 6
    cci_exit = 10.0


    boll_up = 0
    boll_down = 0
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

                ]

    variables = [

                ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg_open = NewBarGenerator(self.on_bar, self.open_window, self.on_open_bar,interval=Interval.MINUTE)
        self.am_open = ArrayManager()

        self.bg_xminute = NewBarGenerator(self.on_bar, self.xminute_window, self.on_xminute_bar,interval=Interval.MINUTE)
        self.am_xminute = ArrayManager(int(self.longest_length) + 100)

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        # 判断是那个交易所，使用那种初始化方式
        self.load_bar_exchange(days=15)

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
        self.bg_open.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg_xminute.update_bar(bar)
        self.bg_open.update_bar(bar)

    def on_open_bar(self,bar:BarData):
        """
        """
        self.am_open.update_bar(bar)

    def on_xminute_bar(self, bar: BarData):
        """"""
        # self.cancel_all()

        am_xminute = self.am_xminute
        am_xminute.update_bar(bar)
        if not am_xminute.inited:
            return

        min_ema = am_xminute.ema(self.minimum_length,True)
        short_ema = am_xminute.ema(self.short_length,True)
        mdeium_ema = am_xminute.ema(self.medium_length,True)
        long_ema = am_xminute.ema(self.long_length,True)
        longest_ema = am_xminute.ema(self.longest_length,True)
        
        # 计算 c_m  m_s  s_md  md_l  l_lt 五条线的差离值数组
        close_min_array = am_xminute.close - min_ema
        min_short_array = min_ema - short_ema
        short_mdeium_array = short_ema - mdeium_ema
        mdeium__long_array = mdeium_ema - long_ema
        long_longest_array = long_ema - longest_ema

        # 取值
        current_close = am_xminute.close[-1]
        last_close = am_xminute.close[-2]
        first_close = am_xminute.close[-3]
        fourth_close = am_xminute.close[-4]
        fifth_close = am_xminute.close[-5]

        current_close_min = close_min_array[-1]
        last_close_min = close_min_array[-2]
        first_close_min = close_min_array[-3]
        fourth_close_min = close_min_array[-4]
        fifth_close_min = close_min_array[-5]

        current_min_short = min_short_array[-1]
        last_min_short = min_short_array[-2]
        first_min_short = min_short_array[-3]
        fourth_min_short = min_short_array[-4]
        fifth_min_short = min_short_array[-5]

        current_short_mdeium = short_mdeium_array[-1]
        last_short_mdeium = short_mdeium_array[-2]
        first_short_mdeium = short_mdeium_array[-3]
        fourth_short_mdeium = short_mdeium_array[-4]
        fifth_short_mdeium = short_mdeium_array[-5]

        current_mdeium_long = mdeium__long_array[-1]
        last_mdeium_long = mdeium__long_array[-2]
        first_mdeium_long = mdeium__long_array[-3]
        fourth_mdeium_long = mdeium__long_array[-4]
        fifth_mdeium_long = mdeium__long_array[-5]

        current_long_longest = long_longest_array[-1]
        last_long_longest = long_longest_array[-2]
        first_long_longest = long_longest_array[-3]
        fourth_long_longest = long_longest_array[-4]
        fifth_long_longest = long_longest_array[-5]
        
        # 计算拐头 turn 值为 -1 向下拐头， 值为 1 向上拐头
        self.turn_min_short = self.ema_turn(min_short_array)
        self.turn_short_mdeiun = self.ema_turn(short_mdeium_array)
        self.turn_mdeiun_long = self.ema_turn(mdeium__long_array)
        self.fturn_long_longest = self.ema_turn(long_longest_array)

        # 判断拐头有效方式 确认短周期拐后，中周期拐，大周期也拐
        # 中周期拐时，短周保持拐后方向，大周期拐时，短，中周期保持别后方向
        if self.turn_min_short > 0:
            self.min_short_inited = 1  # 做多
        elif self.turn_min_short < 0:
            self.min_short_inited = -1

        if self.turn_short_mdeiun > 0:
            self.short_mdeiun_inited = 1
        elif self.turn_short_mdeiun < 0:
            self.short_mdeiun_inited = -1

        if self.turn_mdeiun_long > 0:
            self.medium_long_initde = 1
        elif self.turn_mdeiun_long < 0:
            self.medium_long_initde = -1

        con1 = (self.medium_long_initde > 0) and (self.short_mdeiun_inited > 0) and (self.min_short_inited > 0)
        con2 = (self.turn_min_short > 0) and (self.turn_short_mdeiun > 0) \
               and (self.turn_mdeiun_long > 0) and (self.fturn_long_longest > 0)

        con3 = (self.medium_long_initde < 0) and (self.short_mdeiun_inited < 0) and (self.min_short_inited < 0)
        con4 = (self.turn_min_short < 0) and (self.turn_short_mdeiun < 0) \
               and (self.turn_mdeiun_long < 0) and (self.fturn_long_longest < 0)

        if con1 and con2:
            print(f"开多单")
        elif con3 and con4:
            print(f"开空单")


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

    def ema_turn(self,turn_value,leng,limit):
        """
        判断均线拐头
        """
        max_turn_value = turn_value[-leng:-1].max()
        min_turn_value = turn_value[-leng:-1].min()
        current_value = turn_value[-1]

        return ema_turn

    # def ema_turn(self,turn_value):
    #     """
    #     判断均线拐头
    #     """
    #     current_value = turn_value[-1]
    #     last_value = turn_value[-2]
    #     first_value = turn_value[-3]
    #     fourth_value = turn_value[-4]
    #     fifth_value = turn_value[-5]
    #     # 向下拐头
    #     con0 = first_value > max(current_value, last_value, fourth_value, fifth_value)  # 确认第三是最大值
    #     con1 = first_value > fourth_value > fifth_value  # 第三大于第四大于第五
    #     con2 = first_value > last_value > current_value  # 第三大于第二大于第一
    #
    #     # 向上拐头
    #     con4 = first_value > min(current_value, last_value, fourth_value, fifth_value)  # 确认第三是最小值
    #     con5 = first_value < fourth_value < fifth_value  # 第三小于第四小于第五
    #     con6 = first_value < last_value< current_value  # 第三小于第二小于第一
    #
    #     if con0 and con1 and con2:
    #         ema_turn = -1  # 向下拐头 做空
    #     elif con4 and con5 and con6:
    #         ema_turn = 1   # 向上拐头 做多
    #     else:
    #         ema_turn = 0
    #     return ema_turn
    #

    # def on_xmin_bar(self, bar: BarData):
    #     """"""
    #     self.cancel_all()
    #
    #     am = self.am
    #     am.update_bar(bar)
    #     if not am.inited:
    #         return
    #
    #     # 计算原布林带
    #     self.boll_up, self.boll_down = self.am.boll(self.boll_length, self.boll_dev)
    #     self.boll_mid = am.sma(self.boll_length)
    #     self.cci_value = am.cci(self.cci_length)
    #
    #     # 如果没有仓位，两条布林window一样
    #     if self.pos == 0:
    #         self.exit_long_nex = 0
    #         self.exit_long_last = 0
    #         self.exit_short_nex = 0
    #         self.exit_short_last = 0
    #         self.boll_length_new = self.boll_length
    #
    #         if self.cci_value > self.cci_exit:
    #             self.buy(self.boll_up, self.fixed_size, True)
    #
    #         if self.cci_value < -self.cci_exit:
    #             self.short(self.boll_down, self.fixed_size, True)
    #
    #     elif self.pos > 0:
    #         # 上涨或下跌时，布林中轨均值减1
    #         close_long = am.close[-1] > am.close[-2] > am.close[-3]
    #
    #         if close_long:
    #             self.boll_length_new -= 1
    #             self.boll_length_new = max(self.boll_length_new, 10)
    #
    #         # 计算新的布林带
    #         self.boll_mid_new = am.sma(self.boll_length_new, True)
    #
    #         # 仓位是long 时，如果价格上穿新布林中轨
    #         con1 = am.close[-1] < self.boll_mid_new[-1]
    #         con2 = am.close[-2] >= self.boll_mid_new[-2]
    #
    #         if con1 and con2:
    #             self.exit_long_nex = am.close[-1]  # 保存当前收盘价
    #             if self.exit_long_nex > self.exit_long_last or self.exit_long_last == 0:
    #                 self.exit_long_last = self.exit_long_nex
    #                 self.boll_length_new = self.boll_length
    #                 # 下穿新均线，以原布林均线挂出停止单，避免快速下跌而无法止损
    #                 self.exit_long = self.boll_mid
    #                 # print(f"我是多单，exitlast:{self.exit_short_last},重置布林中轨参数，止损挂{self.exit_long}：")
    #             else:
    #                 # 收盘价在两条均线平均价上方，以当前收盘价挂出限价单
    #                 if self.am.close[-1] > ((self.boll_mid + self.boll_mid_new[-1]) / 2):
    #                     self.exit_long = bar.close_price
    #                     # print(f"我是多单，收盘价在两个中轨均值上方，以收盘价挂止损单:{self.exit_long}")
    #                 elif bar.close_price < self.boll_mid:
    #                     self.exit_long = bar.close_price
    #                 else:
    #                     self.exit_long = self.boll_mid
    #                     # print(f"我是多单，收盘价在两个中轨均值下方，以原中轨挂止损单:{self.exit_long},")
    #         else:
    #             self.exit_long = self.boll_mid
    #             # print(f"我是多单，收盘价在新中轨上方，以原中轨挂止损单:{self.exit_long}")
    #
    #         self.sell(self.exit_long, abs(self.pos), True)
    #
    #     elif self.pos < 0:
    #         close_short = am.close[-1] < am.close[-2] < am.close[-3]
    #
    #         if close_short:
    #             self.boll_length_new -= 1
    #             self.boll_length_new = max(self.boll_length_new, 10)
    #
    #         # 计算新的布林带
    #         self.boll_mid_new = am.sma(self.boll_length_new, True)
    #
    #         # 仓位是short 时，如果价格上穿新布林中轨
    #         con3 = am.close[-1] > self.boll_mid_new[-1]
    #         con4 = am.close[-2] <= self.boll_mid_new[-2]
    #
    #         if con3 and con4:
    #             self.exit_short_nex = am.close[-1]
    #             if self.exit_short_nex < self.exit_short_last or self.exit_short_last == 0:
    #                 self.exit_short_last = self.exit_short_nex
    #                 self.boll_length_new = self.boll_length
    #
    #                 self.exit_short = self.boll_mid
    #             else:
    #                 if self.am.close[-1] < (self.boll_mid + self.boll_mid_new[-1] / 2):
    #                     self.exit_short = bar.close_price
    #
    #                 elif bar.close_price > self.boll_mid:
    #                     self.exit_short = bar.close_price
    #
    #                 else:
    #                     self.exit_short = self.boll_mid
    #
    #         else:
    #             self.exit_short = self.boll_mid
    #
    #         self.cover(self.exit_short, abs(self.pos), True)
    #
    #     self.put_event()
    #     self.sync_data()
