# _*_coding : UTF-8 _*_
# 开发团队 ：yunya
# 开发人员 ：yunya
# 开发时间 : 2020/8/12 16:14
# 文件名称 ：gridstock.py
# 开发工具 ： PyCharm
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
from vnpy.app.cta_strategy.base import EngineType
from vnpy.gateway.alpaca.alpaca_gateway import UTC_TZ
from vnpy.trader.constant import Interval, Direction, ExchangeMaterial, Status, OrderType
import datetime


class GridStockCta_v1(CtaTemplate):
    """
    1、如果没有仓位，以当前价格买入一个单位
    2、获取最后一个成交 价格，计算出卖出价格和买入价格。
    3、然后价格高于卖出价，马上挂出miker卖单。
    """
    author = "yunya"

    grid_amount = 20  # 网格最大量
    grid_usdt_size = 20  # 首次使用多少USDT购买币
    grid_usdt_capital = 200  # 网格最多使用的资金量USDT
    grid_buy_price = 1.0  # 网格距离
    grid_sell_price = 1.0
    position_inited = False
    position_proportion = 1.0  # 每次加仓比例

    grid_count = 0
    cumulative_usdt_volume = 0
    buy_benchmark = 0
    sell_benchmark = 0

    buy_price = 0
    sell_price = 0
    buy_tick = 0
    short_tick = 0
    current_volume = 0
    sell_fixed_size = 0
    price_change = 0
    min_volume = 0
    len_tick_decimal = 0

    parameters = [
            "grid_amount",
            "grid_usdt_size",
            "grid_usdt_capital",
            "grid_buy_price",
            "grid_sell_price",
            "position_inited",
            "position_proportion",
    ]

    variables = [
        "grid_count",
        "buy_benchmark",
        "sell_benchmark",
        "grid_usdt_volume",
        "cumulative_usdt_volume",
        "position_inited"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting, )

        self.exchangematerial = ExchangeMaterial.OKEX_MATERIAL
        self.bg_open = BarGenerator(self.on_bar, 2, self.on_open_bar)
        self.am_open = ArrayManager()

        # 计算每次使用资金量
        self.cumulative_usdt_volume = 0
        self.target_pos = 0
        self.grid_usdt_volume = 0
        self.vt_orderids = []

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        contract = self.cta_engine.main_engine.get_contract(self.vt_symbol)
        self.min_volume = contract.min_volume
        self.len_tick_decimal = len(str(self.min_volume).split(".")[1])
        self.load_bar(1)

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
        self.buy_tick = tick.bid_price_1
        self.short_tick = tick.ask_price_1

    def on_bar(self, bar: BarData):
        """"""
        self.bg_open.update_bar(bar)

    def on_open_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        self.am_open.update_bar(bar)

        if not self.am_open.inited:
            return

        #   判断是否动态加仓
        if self.position_inited:
            if self.position_proportion > 0 and self.grid_count > 0:
                self.grid_usdt_volume = self.grid_usdt_size * (1 + (self.position_proportion / 100) * self.grid_count)
        else:
            self.grid_usdt_volume = self.grid_usdt_size
        self.current_volume = self.grid_usdt_volume / bar.close_price

        #   判断是否已有成交记录,如果没有成交记录，就买入第一单
        if not self.buy_benchmark and not self.sell_benchmark:

            # self.buy_price = bar.close_price - self.tick_price * self.pay_up
            vt_orderid = self.buy(self.buy_price, self.current_volume)

            self.vt_orderids.extend(vt_orderid)

            # 清空
            self.cumulative_usdt_volume = 0
            self.grid_count = 0
            self.current_volume = 0
        else:
            if bar.close_price < self.buy_benchmark:

                con1 = self.grid_count < self.grid_amount
                con2 = self.cumulative_usdt_volume < self.grid_usdt_capital

                if con1 or con2:
                    # 取四舍五入
                    self.current_volume = float(format(self.current_volume, f".{self.len_tick_decimal}f"))
                    vt_orderid = self.buy(self.buy_tick, self.current_volume, order_type=OrderType.MakerPostOnly)
                    self.vt_orderids.extend(vt_orderid)
                else:
                    self.write_log("达到最大仓位！停止加仓！")

            elif bar.close_price > self.sell_benchmark:

                # 判断 如果理论（不含手续费）self.pos 比交易所成交反馈回来的量小时，使用交易所反馈回来的量下单，同时把理论值设置为零
                if self.pos > self.current_volume * 1.2:
                    self.sell_fixed_size = self.current_volume
                else:
                    self.sell_fixed_size = self.pos

                vt_orderid = self.sell(self.sell_price, abs(self.sell_fixed_size),order_type=OrderType.MakerPostOnly)
                self.vt_orderids.extend(vt_orderid)

        self.put_event()

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
                    self.cumulative_usdt_volume -= self.grid_usdt_volume
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
            msg = f"平仓，成交价格为：{self.price_change}"
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
