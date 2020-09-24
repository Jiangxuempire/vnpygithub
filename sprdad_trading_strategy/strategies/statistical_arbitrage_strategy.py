from vnpy.trader.constant import Interval
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


class StatisticalArbitrageStrategy(SpreadStrategyTemplate):
    """"""

    author = "用Python的交易员"

    open_window = 1
    boll_window = 40
    boll_dev = 4.9
    fixed_pos = 10
    payup = 10.0
    increase_price = 0.0        # 超价
    interval = 5

    spread_pos = 0.0
    boll_up = 0.0
    boll_down = 0.0
    boll_mid = 0.0

    parameters = [
        "boll_window",
        "boll_dev",
        "fixed_pos",
        "payup",
        "interval",
        "increase_price"
    ]
    variables = [
        "spread_pos",
        "boll_up",
        "boll_down",
        "boll_mid"
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

        self.bg = BarGenerator(self.on_open_spread_bar, self.open_window, self.on_open_spread_bar)
        self.am = ArrayManager()

        self.spread_pos = 0.0
        self.boll_up = 0.0
        self.boll_down = 0.0
        self.boll_mid = 0.0

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
        Callback when new spread bar data is generated.
        """
        self.bg.update_bar(bar)

    def on_open_spread_bar(self, bar: BarData):
        """
        Callback when spread bar data is generated.

        目前的策略逻辑：
        1、当价差价格大于布林上轨，以当前收盘加低10的价格下单（以市价下单保证成交），当价格跌破中轨时平仓 （做空）
        2、当价差价格小于布林下轨，以当前收盘价加10的价格下单，当价格高于中轨时平仓 （做多）

        策略优化方向：
        1、把目前在分钟价差K线逻辑移到 tick逻辑中实盘，增加细腻度
        2、仓位分为四次加减仓，第一次上穿时，开一份，第二次上穿的价格要高于第一次一定比较时，开第二份，一直到满四份。
        （这两个参数，一个是份数，一个是跨度（格距）），目的解决如果出现单边短时趋势抗单时爆仓（最后都会回归中轨）
        3、回到中轨全部平仓位

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
                    payup=self.payup,
                    interval=self.interval
                )
            elif bar.close_price <= self.boll_down:
                self.start_long_algo(
                    bar.close_price + self.increase_price,
                    self.fixed_pos,
                    payup=self.payup,
                    interval=self.interval
                )
        elif self.spread_pos < 0:
            if bar.close_price <= self.boll_mid:
                self.start_long_algo(
                    bar.close_price + self.increase_price,
                    abs(self.spread_pos),
                    payup=self.payup,
                    interval=self.interval
                )
        else:
            if bar.close_price >= self.boll_mid:
                self.start_short_algo(
                    bar.close_price - self.increase_price,
                    abs(self.spread_pos),
                    payup=self.payup,
                    interval=self.interval
                )
        self.put_event()
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
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback when new trade data is received.
        """
        pass

