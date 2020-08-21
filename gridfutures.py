# _*_coding : UTF-8 _*_
# 开发团队 ：yunya
# 开发人员 ：yunya
# 开发时间 : 2020/8/12 16:14
# 文件名称 ：gridstock.py
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
from vnpy.trader.constant import Direction, Interval
import datetime

class GridStockCtaStrategy(CtaTemplate):
    """
    期货网格策略逻辑：
        1、支持正向合约和反向合约交易逻辑（设置正向和反向标记来转换）
        2、网格格数设置50格，多空各25格（参数）
        3、网格总限量资金： 3000USDT 或 合约张数
        4、网格操作区间： 10%

        3、网格跟踪指标 ： 首次成交价格
        4、网格上限： 网格跟踪指标 * （1 + 网格操作区间）
        5、网格下限： 网格跟踪指标 * （ 1 - 网格操作区间）
        6、网格步进 ：（ 网格上限 - 网格下限 ） / 网格数量
        7、仓位单元 ： 网格总限量 / 网格数量
        8、网格启动、停止开关：振幅超过百分比例，网格暂时停止，等待8小时后重新启动

    """
    author = "yunya"

    open_window = 2
    xminute_window = 5
    xhour_window = 1
    position_proportion = 1  # 每次加仓比例
    grid_amount = 20      # 网格最大量
    grid_usdt_size = 10          # 首次使用多少USDT购买币
    grid_usdt_capital = 1000   # 网格最多使用的资金量USDT
    grid_buy_price = 0.2      # 网格距离
    grid_sell_price = 0.25
    pay_up = 2            # 偏移pricetick
    buy_callback = 2      # 买入回调幅度
    sell_callback = 2     # 卖出回调幅度
    grid_amplitude = 5    # 振幅超过比例停止策略8小时
    stop_time = 8         # 策略暂停时间

    # active_orderids = set()  # 保存不重复的订单号
    price_change = 0      # 网格基准线（每次成交价）
    current_grid = 0
    max_target = 0         # 当前网格最大最
    current_volume = 0   # 当前下单币的数量
    buy_benchmark = 0
    sell_benchmark = 0
    buy_price = 0           # 买入成交价
    sell_price = 0          # 平仓成交价
    grid_usdt_volume = 0
    cumulative_usdt_volume = 0   # 累计使用金额
    grid_count = 0          # 网格次数
    intra_trade_high = 0    # 最高价
    trade_high = 0
    last_trade_high = 0
    intra_trade_low = 0     # 最低价
    trade_low = 0
    last_trade_low = 0
    amplitude = 0           # 振幅
    tick_price = 0
    amplitude_inited = False  # 振幅标签
    time_stop = 0             # 计算得到的重新启动时间


    parameters = [
            "open_window",
            "xminute_window",
            "xhour_window",
            "position_proportion",
            "grid_amount",
            "grid_usdt_size",
            "grid_usdt_capital",
            "grid_buy_price",
            "grid_sell_price",
            "pay_up",
            "buy_callback",
            "sell_callback",
            "grid_amplitude",
            "stop_time",
    ]

    variables = [
            "price_change",
            "current_grid",
            "max_target",
            "current_volume",
            "buy_benchmark",
            "sell_benchmark",
            "buy_price",
            "sell_price",
            "grid_usdt_volume",
            "cumulative_usdt_volume",
            "grid_count",
            "intra_trade_high",
            "trade_high",
            "last_trade_high",
            "intra_trade_low",
            "trade_low",
            "last_trade_low",
            "amplitude",
            "tick_price",
            "amplitude_inited",
            "time_stop",
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg_open = BarGenerator(self.on_bar,self.open_window,self.on_open_bar)
        self.am_open = ArrayManager()

        self.bg_minute = BarGenerator(self.on_bar,self.xminute_window,self.on_mintue_bar)
        self.am_minute = ArrayManager()

        self.bg_xhour = BarGenerator(self.on_bar, self.xhour_window, self.on_xhour_bar, Interval.HOUR)
        self.am_xhour = ArrayManager()

        # 计算每次使用资金量
        self.cumulative_usdt_volume = 0
        self.grid_usdt_volume = 0
        self.amplitude = 0
        self.tick_price = 0
        # self.active_orderids = set()

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
        self.bg_open.update_tick(tick)

    def on_bar(self, bar: BarData):
        """"""
        self.bg_open.update_bar(bar)
        self.bg_minute.update_bar(bar)
        self.bg_xhour.update_bar(bar)

    def on_open_bar(self, bar: BarData):
        """"""
        self.am_open.update_bar(bar)

        if not self.am_open.inited:
            return

        self.cancel_all()

        # 判断 休眠时间
        if self.amplitude_inited:
            if bar.datetime > self.time_stop:
                self.amplitude_inited = False
            return

        # 根据网格次数加仓 , 根据USDT量和价格计算出可购买的币数量
        if self.position_proportion > 0 or self.grid_count > 0:
            self.grid_usdt_volume = self.grid_usdt_size * (1 + (self.position_proportion / 100) * self.grid_count)
        else:
            self.grid_usdt_volume = self.grid_usdt_size

        self.current_volume = self.grid_usdt_volume / bar.close_price

        self.write_log(f"使用 {self.grid_usdt_volume} 枚USDT,可购买 {self.current_volume} 枚币")

        self.tick_price = self.get_pricetick()
        if not self.pos:
            """
            1、如果空仓，以当前价格买入一份做为底仓
            2、总网格次数减一
            """
            msg = f"tick_price:{self.tick_price}"
            self.write_log(msg=msg)

            buy_price = bar.close_price - self.tick_price * self.pay_up
            self.buy(buy_price, self.current_volume)

            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            self.grid_count += 1
            self.cumulative_usdt_volume += self.grid_usdt_volume

        else:
            if bar.close_price < self.buy_benchmark:
                """
                当前收盘价低于下个网格买入价格时，判断买入时机：
                1、价格在上次买入后，中间没有卖出的过程，
                2、
                """
                if self.cumulative_usdt_volume < self.grid_usdt_capital:
                    """
                    买在最低位
                    """
                    self.intra_trade_high = bar.high_price
                    self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
                    self.trade_low = self.intra_trade_low * (1 + self.buy_callback / 100)

                    if self.trade_low <= self.buy_benchmark:
                        if self.last_trade_low > 0:
                            self.last_trade_low = min(self.trade_low, self.last_trade_low)
                        else:
                            self.last_trade_low = self.trade_low

                    if bar.close_price <= self.last_trade_low:
                        self.buy_price = self.last_trade_low
                    else:
                        self.buy_price = bar.close_price + self.tick_price * self.pay_up  # 加价保证成交

                    self.buy(self.buy_price, self.current_volume)
                    self.grid_count += 1
                    self.cumulative_usdt_volume += self.grid_usdt_volume
                    self.last_trade_low = self.trade_low

            elif bar.close_price > self.sell_benchmark:
                if self.pos > 0:
                    """
                    卖在最高位
                    """
                    self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
                    self.intra_trade_low = bar.low_price
                    self.trade_high = self.intra_trade_high * (1 - self.sell_callback / 100)

                    if self.trade_high >= self.sell_benchmark:
                        if self.last_trade_high > 0:
                            self.last_trade_high = max(self.trade_high, self.last_trade_high)
                        else:
                            self.last_trade_high = self.trade_high

                    if bar.close_price >= self.last_trade_high:
                        self.sell_price = self.last_trade_high
                    else:
                        self.sell_price = bar.close_price - self.tick_price * self.pay_up

                    # 判断 最后一次全部卖完
                    if self.pos > self.current_volume * 1.2:
                        self.cover(self.sell_price, abs(self.current_volume))
                        self.grid_count -= 1
                        self.cumulative_usdt_volume -= self.grid_usdt_volume
                    else:
                        self.cover(self.sell_price, abs(self.pos))
                        self.grid_count -= 1
                        self.cumulative_usdt_volume -= self.grid_usdt_volume
        # 更新图形界面
        self.put_event()

    def on_mintue_bar(self, bar:BarData):
        """
        :return:
        """
        self.am_minute.update_bar(bar)

        if not self.am_minute.inited:
            return
        # 计算振幅
        self.amplitude = (bar.high_price - bar.low_price) / bar.high_price

        # 如果振幅超过指定值，策略撤掉所有挂单，并且进入休眠状态
        if self.amplitude > self.grid_amplitude / 100:
            self.amplitude_inited = True
            self.time_stop = bar.datetime + datetime.timedelta(hours=self.stop_time)
            self.write_log(f"当前市场波动较大，"
                           f"振幅为：{self.amplitude},超过设置值，策略进入休眠，"
                           f"休眠到：{self.time_stop.strftime('%Y-%m-%d %H:%M:%S')}时重新启动策略")

    def on_xhour_bar(self, bar:BarData):
        """
        :return:
        """
        self.am_xhour.update_bar(bar)

        if not self.am_xhour.inited:
            return
        pass

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass
        # # 保存活动委托的委托号
        # if order.is_active():
        #     self.active_orderids.add(order.vt_orderid)
        # # 移除已结束（撤单、全成）委托的委托号
        # elif order.vt_orderid in self.active_orderids:
        #     self.active_orderids.remove(order.vt_orderid)
        #
        # self.put_event()

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        if trade.direction == Direction.LONG:
            self.price_change = trade.price  # 成交最高价
        else:
            self.price_change = trade.price

        # 计算当前网格买入价格和卖出价格
        self.buy_benchmark = self.price_change * (1 - self.grid_buy_price)
        self.sell_benchmark = self.price_change * (1 + self.grid_sell_price)

        self.sync_data()

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

