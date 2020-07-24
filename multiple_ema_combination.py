# _*_coding : UTF-8 _*_
#开发团队 ：yunya
#开发人员 ：Administrator
#开发时间 : 2020/6/26 22:46
#文件名称 ：multiple_ema_combination.py
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
import talib
from  vnpy.app.cta_strategy.new_strategy import NewBarGenerator
from vnpy.trader.constant import Direction, Interval


class Multiple_Ema_CombinationStrategy(CtaTemplate):
    """"""

    author = "云崖"

    open_window = 2
    xhour_window = 15
    boll_length = 20
    boll_dev = 2.0
    dc_length = 60
    first_ema_length = 20
    second_ema_length = 60
    third_ema_length = 100
    trailing_tax = 3.0
    fixed_size = 1

    macd_inited = 0
    ema_inited = 0
    exit_long = 0
    exit_short = 0
    long_stop = 0
    short_stop = 0
    boll_mid = 0
    boll_mid_new = 0
    boll_up = 0
    boll_down = 0
    boll_up_new = 0
    boll_down_new = 0
    boll_length_new = 0
    boll_len = 0

    intra_trade_high = 0
    intra_trade_low = 0

    exit_up_nex = 0
    exit_up_last = 0
    exit_down_nex = 0
    exit_dwon_last = 0

    parameters = [
                "open_window",
                "xhour_window",
                "fast_macd",
                "show_macd",
                "boll_length",
                "boll_dev",
                "dc_length",
                "first_ema_length",
                "second_ema_length",
                "third_ema_length",
                "trailing_tax",
                "fixed_size",
                ]


    variables = [
                "macd_inited",
                "ema_inited",
                "boll_up",
                "boll_down",
                "exit_long",
                "exit_short",
                "long_stop",
                "short_stop",
                    ]

    def __init__(self, cta_engine, strategy_nam_xminutee, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_nam_xminutee, vt_symbol, setting)

        self.bg_open = NewBarGenerator(self.on_bar, self.open_window, self.on_open_bar)
        self.am_open = ArrayManager()

        self.bg_xminute = NewBarGenerator(self.on_bar, self.xhour_window, self.on_xminute_bar,interval=Interval.MINUTE)
        self.am_xminute = ArrayManager(300)

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.boll_length_new = self.boll_length

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
        self.bg_xminute.update_tick(tick)
        self.ask = tick.ask_price_1  # 卖一价
        self.bid = tick.bid_price_1  # 买一价

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg_xminute.update_bar(bar)
        self.bg_open.update_bar(bar)

    def on_open_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        self.am_open.update_bar(bar)
        if not self.am_xminute.inited or not self.am_open.inited :
            return

        if self.pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price
            self.atr_value = self.am_xminute.atr(14)

            self.long_stop = 0
            self.short_stop = 0

            if self.macd_inited > 0 and self.ema_inited > 0 :
                self.buy(self.boll_up, self.fixed_size)

            elif self.macd_inited < 0 and self.ema_inited < 0:
                self.short(self.boll_down, self.fixed_size)

        elif self.pos > 0:
            if self.macd_inited < 0:
                self.sell(bar.close_price - 10,abs(self.pos))

            else:
                self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
                self.intra_trade_low = bar.low_price

                long_high = self.intra_trade_high * (1 - self.trailing_tax / 100)
                self.long_stop = max(self.exit_long,long_high)

                self.sell(self.long_stop, abs(self.pos), True)

        elif self.pos < 0:

                self.intra_trade_high = bar.high_price
                self.intra_trade_low = min(self.intra_trade_low, bar.low_price)

                stop_low = self.intra_trade_low * (1 + self.trailing_tax / 100)
                self.short_stop = min(self.exit_short,stop_low)

                self.cover(self.short_stop, abs(self.pos), True)

        self.put_event()

    def on_xminute_bar(self, bar: BarData):
        """"""

        self.am_xminute.update_bar(bar)
        if not self.am_xminute.inited:
            return

        # 计算dc移动止损位
        self.exit_short, self.exit_long = self.am_xminute.donchian(self.dc_length)

        # 计算ema diff 信号 20与60，60与120均线差比值
        first_ema_value = self.am_xminute.ema(self.first_ema_length,True)
        second_ema_value = self.am_xminute.ema(self.second_ema_length,True)
        third_ema_value = self.am_xminute.ema(self.third_ema_length,True)

        short_diff = (first_ema_value[-3:] - second_ema_value[-3:]) / second_ema_value[-3:] * 100
        long_diff = (second_ema_value[-3:] - third_ema_value[-3:]) / third_ema_value[-3:] * 100

        if short_diff[-1] > long_diff[-1] and short_diff[-2] <= long_diff[-2]:
            self.ema_inited = 1
        elif short_diff[-2] < long_diff[-1] and short_diff[-2] >= long_diff[-2]:
            self.ema_inited = -1

        # 如果没有仓位，两条布林window一样
        if self.pos == 0:
            self.boll_length_new = self.boll_length
            self.exit_up_nex = 0
            self.exit_up_last = 0
            self.exit_down_nex = 0
            self.exit_dwon_last = 0

        # 如果有仓位，连续上涨或下跌，新布林window 减一
        else:
            # 上涨或下跌时，布林中轨均值减1
            close_long = self.am_xminute.close[-1] > self.am_xminute.close[-2] > self.am_xminute.close[-3]
            close_shour = self.am_xminute.close[-1] < self.am_xminute.close[-2] < self.am_xminute.close[-3]
            if close_long or close_shour:
                self.boll_length_new -= 1
                self.boll_len = max(self.boll_length_new,20)
                print(f"boll_len : {self.boll_len},boll_length:{self.boll_length}")

        # 计算新的布林带
        self.boll_mid_new ,self.boll_up_new,self.boll_down_new = self.newboll(
                                                                       close= self.am_xminute.close,
                                                                       n = self.boll_len,
                                                                       dev = self.boll_dev,
                                                                        array = True
                                                                        )

        # 计算原布林带
        self.boll_mid,self.boll_up,self.boll_down = self.newboll(
                                                            close= self.am_xminute.close,
                                                            n=self.boll_length,
                                                            dev=self.boll_dev,
                                                            array=True
                                                        )
        # 仓位是short 时，如果价格上穿新布林中轨
        con1 = self.am_xminute.close[-1] > self.boll_mid_new[-1]
        con2 = self.am_xminute.close[-2] <= self.boll_mid_new[-2]
        if con1 and con2:
            # 如果上穿布林中轨的收盘价 高于 前一次上穿中轨的价格时， 从新开始缩小布林均线长度
            self.exit_up_nex = self.am_xminute.close[-1] # 保存当前收盘价
            if self.exit_up_nex < self.exit_up_last or self.exit_up_last == 0:  #判断上穿时价格是否小于前一次上穿的价格（把第一次考虑进去）
                self.exit_up_last = self.exit_up_nex # 缓存本次上穿的收盘价
                self.boll_length_new = self.boll_length # 重新开始

        # 仓位是 long 时，如果价格下穿新布林中轨
        con1 = self.am_xminute.close[-1] < self.boll_mid_new[-1]
        con2 = self.am_xminute.close[-2] >= self.boll_mid_new[-2]
        if con1 and con2:
            self.exit_down_nex = self.am_xminute.close[-1]
            if self.exit_down_nex > self.exit_dwon_last or self.exit_dwon_last == 0:
                self.exit_dwon_last = self.exit_down_nex
                self.boll_length_new = self.boll_length

        self.exit_long = max(self.am_xminute.close,self.exit_long)

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        self.put_event()

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        if trade.direction == Direction.LONG:
            self.long_entry = trade.price  # 成交最高价
            self.long_stop_trade = self.long_entry - 2 * self.atr_value
        else:
            self.short_entry = trade.price
            self.short_stop_trade = self.short_entry + 2 * self.atr_value

        self.sync_data()
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        self.put_event()

    def newboll(self,close, n: int,dev:float, array: bool = False
    ):
        """
        返回均线的布林带
        """
        mid = talib.SMA(close, n)
        std = talib.STDDEV(close, n)

        up = mid + std * dev
        down = mid - std * dev

        if array:
            return mid, up, down
        return mid[-1], up[-1], down[-1]

