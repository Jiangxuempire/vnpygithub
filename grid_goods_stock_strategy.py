# _*_coding : UTF-8 _*_
#开发团队 ：yunya
#开发人员 ：Administrator
#开发时间 : 2020/7/13 15:35
#文件名称 ：grid_goods_stock_strategy.py
#开发工具 ： PyCharm


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
from  vnpy.app.cta_strategy.new_strategy import NewBarGenerator

class GridGoodsStockStrategy(CtaTemplate):
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

    grid_start = 102
    grid_price = 0.2
    grid_volume = 1
    pay_up = 10


    max_fixed_size = 3000
    fixed_size = 100  # USDT数量
    grid_distance_percentage = 1.0
    distance_retracement = 0.1
    size_accuracy = 4      # 根据币的最小购买数量来调下单精度


    position_size = 0.0
    transaction_price = 0.0
    transaction_time = 0
    distance_up = 0
    distance_down = 0
    intra_trade_high = 0
    inira_trade_low = 0
    long_stop = 0
    short_stop = 0
    pos_value = 0
    grid_count = 0
    active_orderids = set()

    price_change = 0
    current_grid = 0
    max_target = 0
    min_target = 0
    i = 0

    parameters = [
        "grid_start", "grid_price", "grid_volume", "pay_up"
    ]

    variables = [
        "price_change", "current_grid", "max_target", "min_target"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = NewBarGenerator(self.on_bar)

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
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """

        """
        # 如果仓位这空，就买入当前收盘价买入第一笔
        if self.pos == 0:
            self.grid_count = 0  # 清空计数器
            self.intra_trade_high = bar.high_price
            self.inira_trade_low = bar.low_price
            self.position_size = float(format(self.fixed_size / bar.close_price,f'.{self.size_accuracy}f'))
            self.send_buy_orders(self, bar.close_price,bar.close_price,self.position_size)
            # print(f"初始当前下价格：{bar.close_price},时间：{bar.datetime}")
            self.grid_count += 1   # 下单次数加1

        else:
            # print(f"当前成交价格：{self.transaction_price}，时间：{ self.transaction_time}" + "\n")
            # 计算网格间距
            self.distance_up = self.transaction_price * (1 + self.grid_distance_percentage / 100)
            self.distance_down = self.transaction_price * (1 - self.grid_distance_percentage / 100)

            if bar.close_price > self.distance_up:
                self.intra_trade_high = max(bar.high_price,self.intra_trade_high)
                # 回撤一定比例止盈
                long_transaction_price = self.transaction_price * \
                                         (1 + (self.grid_distance_percentage - self.distance_retracement) / 100)

                long_stop_high = self.intra_trade_high * (1 - self.distance_retracement / 100 )
                self.long_stop = max(long_stop_high,long_transaction_price,)

                if self.pos > 0:
                    # 如果计算器等于，卖出量为当前持仓量，如果大于1，取持计数器持仓量份之一
                    if self.grid_count <= 0:
                        self.pos_value = self.pos

                    elif self.grid_count >= 1:
                        # print(f"pos:{self.pos}" )
                        # print(f"count:{self.grid_count}")
                        self.pos_value = self.pos / self.grid_count
                        # print(f"pos_value:{self.pos_value}" + "\n")

                    self.sell(self.long_stop,abs(self.pos_value))
                    self.grid_count -= 1  # 下单次数减1
                    # print(f"平仓：{bar.close_price},时间：{bar.datetime}")
                    # print(f"结束计算值：{self.grid_count}")

            elif bar.close_price < self.distance_down:
                if self.grid_count < self.grid_number:
                    self.inira_trade_low = min(bar.low_price,self.inira_trade_low)
                    short_transaction_price = self.transaction_price * \
                                             (1 - (self.grid_distance_percentage - self.distance_retracement) / 100)

                    short_stop_low = self.inira_trade_low * (1 - self.distance_retracement / 100)
                    self.short_stop = min(short_stop_low, short_transaction_price, )

                    self.position_size = float(format(self.fixed_size / bar.close_price, f'.{self.size_accuracy}f'))
                    self.buy(self.short_stop , self.position_size)
                    print(f"加仓下单：{self.short_stop},时间：{bar.datetime}")
                    self.grid_count += 1  # 下单次数加1

        # 更新图形界面
        self.put_event()

    def send_buy_orders(self, price,close,size):
        """"""
        t = self.pos / (self.max_fixed_size / close)
        if t == 0:
            self.buy(price, size)
        if t < 1:
            self.buy(price + self.atr_value * 0.5, self.fixed_size, True)

        if t < 3:
            self.buy(price + self.atr_value, self.fixed_size, True)

        if t < 4:
            self.buy(price + self.atr_value * 1.5, self.fixed_size, True)


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

    # def check_order_finished(self):
    #     """"""
    #     if self.active_orderids:
    #         return False
    #     else:
    #         return True
    #
    # def cancel_all_orders(self):
    #     """"""
    #     for vt_orderid in self.active_orderids:
    #         self.cancel_order(vt_orderid)
    #

    # def send_buy_orders(self, price):
    #     """"""
    #     t = self.pos / self.fixed_size
    #
    #     if t < 1:
    #         self.buy(price, self.fixed_size, True)
    #
    #     if t < 2:
    #         self.buy(price + self.atr_value * 0.5, self.fixed_size, True)
    #
    #     if t < 3:
    #         self.buy(price + self.atr_value, self.fixed_size, True)
    #
    #     if t < 4:
    #         self.buy(price + self.atr_value * 1.5, self.fixed_size, True)
    #
    # def send_short_orders(self, price):
    #     """"""
    #     t = self.pos / self.fixed_size
    #
    #     if t > -1:
    #         self.short(price, self.fixed_size, True)
    #
    #     if t > -2:
    #         self.short(price - self.atr_value * 0.5, self.fixed_size, True)
    #
    #     if t > -3:
    #         self.short(price - self.atr_value, self.fixed_size, True)
    #
    #     if t > -4:
    #         self.short(price - self.atr_value * 1.5, self.fixed_size, True)

        # if order.direction == Direction.LONG:
        #     self.order_price = order.price
        #     self.order_value = order.volume
        #     self.order_vt_id = order.vt_orderid
        #     self.order_id = order.orderid
        #
        #     print(f"内部委托价格：{self.order_price}" + "\n")
        #     print(f"内部委托量：{self.order_value}" + "\n")
        #     print(f"内部委托vtid：{self.order_vt_id}" + "\n")
        #     print(f"内部委托oid：{self.order_id}" + "\n")

        # self.transaction_value = trade.volume
        # self.transaction_vt_orderid = trade.vt_orderid
        # self.transaction_tradeid = trade.tradeid
        # print(f"成交定单：{self.transaction_price}" + "\n")
        # print(f"成交量：{self.transaction_value}" + "\n")
        # print(f"成交vt_orderid：{self.transaction_vt_orderid}" + "\n")
        # print(f"成交tradeid ：{self.transaction_tradeid}" + "\n")
        #


        # if not self.check_order_finished():
        #     self.cancel_all_orders()
        #     return
