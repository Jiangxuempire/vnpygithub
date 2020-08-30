from vnpy.trader.constant import Status, Direction
from vnpy.trader.utility import BarGenerator, ArrayManager
from vnpy.app.spread_trading import (
    SpreadStrategyTemplate,
    SpreadAlgoTemplate,
    SpreadData,
    OrderData,
    TradeData,
    TickData,
    BarData
)

class StatisticalArbitrageGridStrategy(SpreadStrategyTemplate):
    """
    算法逻辑是在统计算法基础上增加加仓位逻辑
    """

    author = "yunya"

    boll_window = 60
    boll_dev = 4.0
    fixed_pos = 10
    max_pos = 4
    price_proportion = 2.0
    pay_up = 5
    increase_price = 0.0        # 超价
    interval = 5

    spread_pos = 0
    boll_up = 0
    boll_down = 0
    boll_mid = 0
    grid_count = 0
    buy_grid_count = 0
    short_grid_count = 0
    long_price = 0
    short_price = 0

    parameters = [
        "boll_window",
        "boll_dev",
        "fixed_pos",
        "max_pos",
        "price_proportion",
        "pay_up",
        "interval",
        "increase_price"
    ]
    variables = [
            "spread_pos",
            "boll_up",
            "boll_down",
            "boll_mid",
            "grid_count",
            "buy_grid_count",
            "short_grid_count",
            "long_price",
            "short_price",
    ]

    def __init__(
        self,
        strategy_engine,
        strategy_name: str,
        spread: SpreadData,
        setting: dict
    ):
        """"""
        super().__init__(
            strategy_engine, strategy_name, spread, setting
        )

        self.bg = BarGenerator(self.on_spread_bar)
        self.am = ArrayManager()

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(5)

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
        self.put_event()

    def on_spread_data(self):
        """
        Callback when spread price is updated.
        收到差价推送后，合成价差TICK数据
        """
        #这里的价差tick
        tick = self.get_spread_tick()
        self.on_spread_tick(tick)

    def on_spread_tick(self, tick: TickData):
        """
        Callback when new spread tick data is generated.
        """
        self.bg.update_tick(tick)

    def on_spread_bar(self, bar: BarData):
        """
        Callback when spread bar data is generated.
        """
        # 把老算法先停止，
        self.stop_all_algos()

        self.am.update_bar(bar)
        if not self.am.inited:
            return

        self.boll_mid = self.am.sma(self.boll_window)
        self.boll_up, self.boll_down = self.am.boll(
            self.boll_window, self.boll_dev)

        if not self.spread_pos:
            if bar.close_price >= self.boll_up:
                self.start_short_algo(
                    bar.close_price - self.increase_price,
                    self.fixed_pos,
                    payup=self.pay_up,
                    interval=self.interval
                )
            elif bar.close_price <= self.boll_down:
                self.start_long_algo(
                    bar.close_price + self.increase_price,
                    self.fixed_pos,
                    payup=self.pay_up,
                    interval=self.interval
                )
        elif self.spread_pos < 0:
            if bar.close_price <= self.boll_mid:
                self.start_long_algo(
                    bar.close_price + self.increase_price,
                    abs(self.spread_pos),
                    payup=self.pay_up,
                    interval=self.interval
                )
                self.buy_grid_count = 0
            else:
                # 加仓
                grid_count = self.buy_grid_count < self.max_pos
                bar_change = bar.close_price > self.long_price * (1 + self.price_proportion / 1000)

                if grid_count and bar_change:
                    if bar.close_price >= self.boll_up:
                        self.start_short_algo(
                            bar.close_price - self.increase_price,
                            self.fixed_pos,
                            payup=self.pay_up,
                            interval=self.interval
                        )
        else:
            if bar.close_price >= self.boll_mid:
                self.start_short_algo(
                    bar.close_price - self.increase_price,
                    abs(self.spread_pos),
                    payup=self.pay_up,
                    interval=self.interval
                )
                self.short_grid_count = 0
            else:
                # 加仓
                grid_count = self.short_grid_count < self.max_pos
                bar_change = bar.close_price < self.short_price * (1 - self.price_proportion / 1000)
                if grid_count and bar_change:
                    if bar.close_price <= self.boll_down:
                        self.start_long_algo(
                            bar.close_price + self.increase_price,
                            self.fixed_pos,
                            payup=self.pay_up,
                            interval=self.interval
                        )

    def on_spread_pos(self):
        """
        Callback when spread position is updated.
        """
        self.spread_pos = self.get_spread_pos()
        self.put_event()

    def on_spread_algo(self, algo: SpreadAlgoTemplate):
        """
        Callback when algo status is updated.
        """
        pass

    def on_order(self, order: OrderData):
        """
        Callback when order status is updated.
        """
        if order.status == Status.ALLTRADED:
            if order.direction == Direction.LONG:
                self.buy_grid_count += 1
            else:
                self.short_grid_count += 1

    def on_trade(self, trade: TradeData):
        """
        Callback when new trade data is received.
        """
        if trade.direction == Direction.LONG:
            self.long_price = trade.price
        else:
            self.short_price = trade.price


