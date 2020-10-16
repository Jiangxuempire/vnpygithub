from numpy.ma import ceil, floor

from vnpy.trader.constant import Direction

from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator
)


class GridCta_V1(CtaTemplate):
    """"""
    author = "用Python的交易员"


    grid_total = 20
    grid_distance = 2  # 每格之间的距离 如果BTC 100usdt
    grid_volume = 10  # 单量
    pay_up = 10  # 跳

    grid_start = 0
    price_change = 0
    current_grid = 0
    max_target = 0
    min_target = 0
    price_tick = 0
    pos_grid = 0
    len_tick_decimal = 0

    parameters = [
        "grid_total", "grid_distance", "grid_volume", "pay_up"
    ]

    variables = [
        "grid_start", "price_change", "current_grid", "max_target", "min_target"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        contract = self.cta_engine.main_engine.get_contract(self.vt_symbol)
        min_volume = contract.min_volume
        self.len_tick_decimal = len(str(min_volume).split(".")[1])
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
        self.bg.update_tick(tick)
        self.price_tick = self.get_pricetick()

    def on_bar(self, bar: BarData):
        """
        1、 计算价格相对初始位置的距离， 距离 = 格距 * 格数(总格数 当前价格为中心点)
        2、 计算当前价格到结束位的距离  price_change = 指定的最高位  - Decimal(str(bar.close_price))

        """
        self.cancel_all()  # 全撤之前的委托

        # 计算网格交易信号
        if not self.pos:
            # 以当前价格为中心轴，布一个指标大小的网，计算出启始位！
            self.grid_start = bar.close_price * (1 + int(self.grid_total / 2) * self.grid_distance / 100)

        self.price_change = bar.close_price - self.grid_start
        self.current_grid = self.price_change * (self.grid_distance / 100)  # 最大变动距离 除以 每格的变动价格（百分比） 总格数

        current_volume = self.grid_volume / bar.close_price  # 计算每份USDT可以买入多少币
        self.max_target = ceil(-self.current_grid) * current_volume  # 总量（最大）  = 总格数 X 每格购买量
        self.min_target = floor(-self.current_grid) * current_volume  # 总量（最小）  = 总格数 X 每格购买量

        self.max_target = float(format(self.max_target, f".{self.len_tick_decimal}f"))
        self.min_target = float(format(self.min_target, f".{self.len_tick_decimal}f"))

        self.write_log(f"price_change:{self.price_change}")
        self.write_log(f"current_grid:{self.current_grid}")
        self.write_log(f"max:{self.max_target}")
        self.write_log(f"min:{self.min_target}")
        self.write_log(f"current_volume:{current_volume}")

        self.pos_grid = float(format(self.pos, f".{self.len_tick_decimal}f"))

        # 做多，检查最小持仓，和当前持仓的差值
        long_volume = self.min_target - self.pos
        if long_volume > 0:
            long_price = bar.close_price + (self.price_tick * self.pay_up)

            if self.pos_grid >= 0:
                self.write_log(f"买入：{self.vt_symbol},价格：{long_price},数量：{long_volume}")
                self.buy(long_price, long_volume)

        short_volume = self.max_target - self.pos
        if short_volume < 0:
            short_price = bar.close_price - (self.price_tick * self.pay_up)
            if self.pos_grid > 0:
                self.sell(short_price, abs(short_volume))
                self.write_log(f"卖出：{self.vt_symbol},价格：{short_price},数量：{short_volume}")
        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        if order.direction == Direction.LONG:

            # 买入时，实际得到币量为总买量减手续费
            order_pos_long = order.traded
            msg = f"开仓，成交量为：{order_pos_long}"
            self.write_log(msg)
        else:
            target_pos_short = -order.traded
            msg = f"平仓，成交量为：{target_pos_short}"
            self.write_log(msg)

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        if trade.direction == Direction.LONG:
            self.price_change = trade.price  # 成交最高价
            msg = f"开仓，成交价格为：{self.price_change}"
            self.write_log(msg)
        else:
            self.price_change = trade.price
            msg = f"平仓，成交价格为：{self.price_change}"
            self.write_log(msg)

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
