# _*_coding : UTF-8 _*_
# 开发团队 ：yunya
# 开发人员 ：yunya
# 开发时间 : 2020/8/12 16:14
# 文件名称 ：gridstock.py
# 开发工具 ： PyCharm


from vnpy.trader.utility import round_to
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
from vnpy.app.cta_strategy.base import EngineType
from vnpy.trader.constant import Direction, Interval, Status, ExchangeMaterial
import datetime

class GridStockCtaStrategy(CtaTemplate):
    """
    策略逻辑：
    1、网格数量： 21  ，网格总限量资金： 3000
	2、网格操作区间： 10%
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
    position_proportion = 1.0  # 每次加仓比例
    grid_amount = 20      # 网格最大量
    grid_usdt_size = 5          # 首次使用多少USDT购买币
    grid_usdt_capital = 200   # 网格最多使用的资金量USDT
    grid_buy_price = 1.0      # 网格距离
    grid_sell_price = 1.0
    pay_up = 2            # 偏移pricetick
    buy_callback = 0.5      # 买入回调幅度
    sell_callback = 0.5    # 卖出回调幅度
    grid_amplitude = 5.0    # 振幅超过比例停止策略8小时
    stop_time = 8         # 策略暂停时间

    price_change = 0      # 网格基准线（每次成交价）
    current_grid = 0
    max_target = 0         # 当前网格最大最
    current_volume = 0   # 当前下单币的数量
    target_pos = 0
    buy_benchmark = 0
    sell_benchmark = 0
    buy_price = 0           # 买入成交价
    sell_price = 0          # 平仓成交价
    grid_usdt_volume = 0
    cumulative_usdt_volume = 0   # 累计使用金额
    grid_count = 0          # 网格次数
    intra_trade_high = 0    # 最高价
    trade_high = 0
    intra_trade_low = 0     # 最低价
    trade_low = 0
    amplitude = 0           # 振幅
    tick_price = 0
    time_stop = 0             # 计算得到的重新启动时间
    buy_fixed_size = 0
    sell_fixed_size = 0
    amplitude_inited = False  # 振幅标签
    first_time_inited = False   # 判断是否是首次启动，如果是首次启动，清空初始化数据

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
            "intra_trade_low",
            "trade_low",
            "amplitude",
            "tick_price",
            "time_stop",
            "amplitude_inited",
            "first_time_inited",
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting,)

        self.exchangematerial = ExchangeMaterial.OKEX_MATERIAL
        self.bg_open = BarGenerator(self.on_bar,self.open_window,self.on_open_bar)
        self.am_open = ArrayManager()

        self.bg_minute = BarGenerator(self.on_bar,self.xminute_window,self.on_mintue_bar)
        self.am_minute = ArrayManager()

        self.bg_xhour = BarGenerator(self.on_bar, self.xhour_window, self.on_xhour_bar, Interval.HOUR)
        self.am_xhour = ArrayManager()

        # 计算每次使用资金量
        self.cumulative_usdt_volume = 0
        self.target_pos = 0
        self.grid_usdt_volume = 0
        self.amplitude = 0
        self.tick_price = 0
        self.engine_type = self.get_engine_type()  #测试还是实盘
        self.vt_orderids = []

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
        if not self.first_time_inited:
            self.grid_count = 0
            self.current_volume = 0
            self.cumulative_usdt_volume = 0
            self.first_time_inited = True

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
        if self.position_proportion > 0 and self.grid_count > 0:
            self.grid_usdt_volume = self.grid_usdt_size * (1 + (self.position_proportion / 100) * self.grid_count)
        else:
            self.grid_usdt_volume = self.grid_usdt_size
        self.current_volume = self.grid_usdt_volume / bar.close_price
        self.tick_price = self.get_pricetick()

        if not self.pos:
            """
            1、如果空仓，以当前价格买入一份做为底仓
            2、总网格次数减一
            """
            self.buy_price = bar.close_price - self.tick_price * self.pay_up
            # 取四舍五入
            self.current_volume = round_to(self.current_volume, 3)
            
            vt_orderid = self.buy(self.buy_price, self.current_volume)
            # 把挂单信息添加到列表末尾
            self.vt_orderids.extend(vt_orderid)

            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            # 清空
            self.cumulative_usdt_volume = 0
            self.grid_count = 0
            self.current_volume = 0

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

                    if self.trade_low < self.buy_benchmark:
                        self.buy_price = self.trade_low
                    else:
                        self.buy_price = self.buy_benchmark
                    # 取四舍五入
                    self.current_volume = round_to(self.current_volume, 3)

                    vt_orderid = self.buy(self.buy_price, self.current_volume)
                    self.vt_orderids.extend(vt_orderid)

            elif bar.close_price > self.sell_benchmark:
                if self.pos > 0:
                    """
                    卖在最高位
                    """
                    self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
                    self.intra_trade_low = bar.low_price
                    self.trade_high = self.intra_trade_high * (1 - self.sell_callback / 100)

                    if self.trade_high > self.sell_benchmark:
                        self.sell_price = self.trade_high
                    else:
                        self.sell_price = self.sell_benchmark

                    # 判断 如果理论（不含手续费）self.pos 比交易所成交反馈回来的量小时，使用交易所反馈回来的量下单，同时把理论值设置为零
                    if self.pos > self.current_volume * 1.2:
                        self.sell_fixed_size = self.current_volume
                    else:
                        self.sell_fixed_size = self.pos

                    vt_orderid = self.sell(self.sell_price, abs(self.sell_fixed_size))
                    self.vt_orderids.extend(vt_orderid)

        # 更新图形界面
        self.put_event()

    def on_mintue_bar(self, bar: BarData):
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

    def on_xhour_bar(self, bar: BarData):
        """
        :return:
        """
        self.am_xhour.update_bar(bar)

        if not self.am_xhour.inited:
            return
        pass

    def on_order(self, order: OrderData):
        """
        判断是否完全成交，如果成交获取成交数量，计数器加减
        移除成交、拒绝、撤单的订单号
        """
        if order.vt_orderid in self.vt_orderids:
            if order.status == Status.ALLTRADED:
                if order.direction == Direction.LONG:
                    self.target_pos = order.traded
                    self.grid_count += 1
                    self.cumulative_usdt_volume += self.grid_usdt_volume
                    # 买入时，实际得到币量为总买量减手续费
                    msg = f"开仓，成交量为：{self.target_pos}"
                    self.write_log(msg)
                    self.target_pos = 0
                else:
                    self.target_pos = -order.traded
                    self.grid_count -= 1
                    self.cumulative_usdt_volume += self.grid_usdt_volume
                    msg = f"平仓，成交量为：{self.target_pos}"
                    self.write_log(msg)
                    self.target_pos = 0

            if not order.is_active():
                self.vt_orderids.remove(order.vt_orderid)

        self.sync_data()

    def on_trade(self, trade: TradeData):
        """
        获取交易价格做为基准线
        """
        if trade.direction == Direction.LONG:
            self.price_change = trade.price  # 成交最高价
            msg = f"开仓，成交价格为：{self.price_change}"
            self.write_log(msg)
        else:
            self.price_change = trade.price
            msg = f"开仓，成交价格为：{self.price_change}"
            self.write_log(msg)
        # 计算当前网格买入价格和卖出价格
        self.buy_benchmark = self.price_change * (1 - self.grid_buy_price / 100)
        self.sell_benchmark = self.price_change * (1 + self.grid_sell_price / 100)
        msg = f"下个网格加仓价格线为：{self.buy_benchmark},平仓位价格线为： {self.sell_benchmark}"
        self.write_log(msg)

        self.sync_data()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
