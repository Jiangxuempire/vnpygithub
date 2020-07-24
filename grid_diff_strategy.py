# _*_coding : UTF-8 _*_
#开发团队 ：yunya
#开发人员 ：Administrator
#开发时间 : 2020/7/15 15:13
#文件名称 ：grid_diff_strategy.py
#开发工具 ： PyCharm


# _*_coding : UTF-8 _*_
# 开发团队 ：yunya
# 开发人员 ：Administrator
# 开发时间 : 2020/7/13 15:35
# 文件名称 ：grid_goods_stock_strategy.py
# 开发工具 ： PyCharm


from math import ceil, floor
from decimal import Decimal
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
from datetime import time, datetime, timedelta

from vnpy.app.cta_strategy.new_strategy import NewBarGenerator


class GridDiffStrategy(CtaTemplate):
    """
    启动时获取单前账号可使用的资金（USDT）
    1、启动策略时，以单前价格买入第一笔，把成交价格作为第二个网格的基准数
    2、每笔投入的资金（参数）
    3、回调幅度  如果上涨到卖出格时，在卖出格下方设置止盈点，每上涨一部分就上移止盈点，因数最高价格回撤多少止损
    4、设置买入区间 （格子宽度）
    5、振幅达到5%-8%时停止策略下单，取消所有挂单，8小时后重新启动
    6、按固定比例固定距离下单，或按每比增加上一笔的1%来增加金额下单，同样使用固定距离

    """

    """
    1、启动策略时，以单前价格买入第一笔，把成交价格作为第二个网格的基准数
    2、每笔投入的资金（参数）固定的数量（USDT）
    3、设置固定购买区间，如价格跌2%为区间
    4、越跌越买，按顺序买入，按最后买的最先卖（这里要做数据本地保存）
    5、过滤大波动行情

    """
    author = "yunya"

    max_fixed_size = 30   # 最大使用资金 USDT
    grid_number = 15        # 网格格数
    fast_window = 15
    slow_window = 30
    exit_window = 0.1
    grid_d_percentage = 2.0
    size_accuracy = 3  # 根据币的最小购买数量来调下单精度
    stop_tr = 5
    stop_hour = 12



    grid_count = 0
    last_close = 0
    fixed_size = 0
    tr_value = 0
    stop_time = 0
    grid_dp_count = 0
    time_initde = False


    parameters = [
                "max_fixed_size",
                "grid_number",
                "fast_window",
                "slow_window ",
                "exit_window",
                "grid_d_percentage",
                "size_accuracy",
                "stop_tr",
                "stop_hour",
    ]

    variables = [
                "grid_count",
                "last_close",
                "fixed_size",
                "tr_value",
                "stop_time",
                "grid_dp_count",
                "time_initde",
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg_5 = BarGenerator(on_bar=self.on_bar,window=5,on_window_bar=self.on_5min_bar)
        self.am_5 = ArrayManager()

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(1)
        self.grid_count = 0

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
        self.bg_5.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        """
        self.bg_5.update_bar(bar)

    def on_5min_bar(self,bar:BarData):
        """"
        """
        self.am_5.update_bar(bar)
        if not self.am_5.inited:
            return

        if self.time_initde:
            if bar.datetime < self.stop_time:
                return
            else:
                self.time_initde = False
                # print(f"延时8小时，重新启动策略，{bar.datetime}")

        self.tr_value = (self.am_5.high[-1] - self.am_5.low[-1]) / self.am_5.high[-1]
        if self.tr_value > (self.stop_tr / 100):
            self.cancel_all()
            self.stop_time = bar.datetime + timedelta(hours=self.stop_hour)
            self.time_initde = True
            # print(f"波动太大：{self.tr_value},暂停下单：{bar.datetime}")
            return

        ema_fast = self.am_5.ema(self.fast_window,True)
        ema_slow = self.am_5.ema(self.slow_window,True)
        ema_diff = ema_fast - ema_slow

        ema_turn,turn_max,turn_min = self.ema_turn(ema_diff)

        # 如果拐头小于阀值
        if turn_min < (-self.exit_window) and ema_turn > 0:
            self.fixed_size = float(
                format(int(self.max_fixed_size / self.grid_number) / bar.close_price, f'.{self.size_accuracy}f'))
            if self.pos == 0:
                self.grid_count = 0
                self.buy(bar.close_price,self.fixed_size)
                # 把当前下单价格保存
                self.last_close = bar.close_price
                self.grid_count += 1
            else:
                if self.grid_count < self.grid_number:
                    # 当前价格是否低于网格距离，达到格距建仓
                    if self.grid_count > 4:
                        self.grid_dp_count = (0.1 * self.grid_count)
                    else:
                        self.grid_dp_count = 0

                    if bar.close_price < self.last_close * (1 - (self.grid_d_percentage + self.grid_dp_count) / 100):
                        self.buy(bar.close_price,self.fixed_size)
                        self.last_close = bar.close_price
                        self.grid_count += 1
                        print("#" * 100)
                        # print(f"加仓一次：{self.grid_count},{bar.close_price}")
                        print(f"加仓一次：{self.grid_count}")
                        print("#" * 100)
                else:
                    pass

        elif turn_max > self.exit_window and ema_turn < 0:

            self.fixed_size = float(
                format(int(self.max_fixed_size / self.grid_number) / bar.close_price, f'.{self.size_accuracy}f'))
            if self.pos > 0:
                if bar.close_price > self.last_close * (1 + self.grid_d_percentage / 100):
                    if self.fixed_size > self.pos:
                        self.fixed_size = self.pos

                    self.sell(bar.close_price,self.fixed_size)
                    self.last_close = bar.close_price
                    self.grid_count -= 1
                    print("*" * 100)
                    # print(f"减仓一次：{self.grid_count},{bar.close_price}")
                    print(f"减仓一次：{self.grid_count}")
                    print("*" * 100)

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        委托定单
        """
        # 保存活动委托的委托号
        if order.is_active():
            self.active_orderids.add(order.vt_orderid)
        # 移除已结束（撤单、全成）委托的委托号
        elif order.vt_orderid in self.active_orderids:
            self.active_orderids.remove(order.vt_orderid)

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        成交订单
        """

        if trade.direction == Direction.LONG:
            self.transaction_price = trade.price  # 成交最高价
            self.transaction_time = trade.datetime

        self.sync_data()
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass


    def ema_turn(self,turn_value):
        """
        判断均线拐头
        """
        current_value = turn_value[-1]
        last_value = turn_value[-2]
        first_value = turn_value[-3]
        fourth_value = turn_value[-4]
        fifth_value = turn_value[-5]
        # 向下拐头
        con_max = max(current_value, last_value, fourth_value, fifth_value)
        con0 = first_value > con_max # 确认第三是最大值
        con1 = first_value > fourth_value > fifth_value  # 第三大于第四大于第五
        con2 = first_value > last_value > current_value  # 第三大于第二大于第一

        # 向上拐头
        con_min = min(current_value, last_value, fourth_value, fifth_value)
        con4 = first_value < con_min  # 确认第三是最小值
        con5 = first_value < fourth_value < fifth_value  # 第三小于第四小于第五
        con6 = first_value < last_value< current_value  # 第三小于第二小于第一

        if con0 and con1 and con2:
            ema_turn = -1  # 向下拐头 做空
        elif con4 and con5 and con6:
            ema_turn = 1   # 向上拐头 做多
        else:
            ema_turn = 0
        return ema_turn,con_max,con_min
