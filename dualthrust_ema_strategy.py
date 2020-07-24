# _*_coding : UTF-8 _*_
#开发团队 ：yunya
#开发人员 ：Administrator
#开发时间 : 2020/6/13 15:44
#文件名称 ：dualthrust_dc_strategy.py
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
from vnpy.trader.constant import Interval, Direction
from  vnpy.app.cta_strategy.new_strategy import NewBarGenerator

class DudlThrustEmaStrategy(CtaTemplate):
    """"""
    author = "yunyu"

    open_window = 5
    xminute_window = 30
    rolling_period = 70
    upper_open = 0.45
    lower_open = 0.45
    cci_length = 5
    ema_length = 60
    fixed_size = 1

    up = 0
    down = 0
    current_ema = 0
    last_ema = 0
    ema_mid = 0
    ema_new_value = 0
    ema_length_new = 0
    cci_value = 0
    exit_long_nex = 0
    exit_long_last = 0
    exit_short_nex = 0
    exit_short_last = 0
    current_close = 0
    last_close = 0
    front_close = 0
    exit_long = 0
    exit_short = 0

    ask = 0
    bid = 0

    
    parameters = [
                "open_window",
                "xminute_window",
                "rolling_period",
                "upper_open",
                "lower_open",
                "cci_length",
                "ema_length",
                "fixed_size",
                ]

    variables = [
                "up",
                "down",
                "current_ema",
                "last_ema",
                "ema_mid",
                "ema_new_value",
                "ema_length_new",
                "cci_value",
                "exit_long_nex",
                "exit_long_last",
                "exit_short_nex",
                "exit_short_last",
                "current_close",
                "last_close",
                "front_close",
                "exit_long",
                "exit_short",
                ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg_open = BarGenerator(on_bar=self.on_bar, window=self.open_window, on_window_bar=self.on_open_bar)
        self.am_open = ArrayManager()

        self.bg = NewBarGenerator(on_bar=self.on_bar,window=self.xminute_window,on_window_bar=self.on_xmin_bar)
        self.am = ArrayManager(300)
        

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(20)

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
        self.ask = tick.ask_price_1  # 卖一价
        self.bid = tick.bid_price_1  # 买一价

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)
        self.bg_open.update_bar(bar)


    def on_open_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.cancel_all()
        self.am_open.update_bar(bar)

        if not self.am.inited or not self.am_open.inited:
            return

        if self.pos == 0:
            self.cci_value = self.am.cci(self.cci_length)
            if self.cci_value > 0:
                self.buy(self.up, self.fixed_size, True)

            elif self.cci_value < 0:
                self.short(self.down, self.fixed_size, True)

        elif self.pos > 0:
            con1 = bar.close_price < self.current_ema
            con2 = bar.close_price >= self.last_ema
            if con1 and con2:
                self.exit_long_nex = bar.close_price  # 保存当前收盘价

                if self.exit_long_last == 0 or self.exit_long_nex > self.exit_long_last:
                    self.exit_long_last = self.exit_long_nex
                    self.ema_length_new = self.ema_length

                    self.exit_long = self.ema_mid

                else:
                    if bar.close_price > ((self.ema_mid + self.current_ema) / 2):
                        self.exit_long = bar.close_price

                    elif bar.close_price < self.ema_mid:
                        self.exit_long = bar.close_price

                    else:
                        self.exit_long = self.ema_mid
            else:
                self.exit_long = self.ema_mid

            self.sell(self.exit_long, abs(self.pos), True)

        elif self.pos < 0:
            con1 = bar.close_price > self.current_ema
            con2 = bar.close_price <= self.last_ema
            if con1 and con2:
                self.exit_short_nex = bar.close_price
                if self.exit_short_last == 0 or self.exit_short_nex < self.exit_short_last:
                    self.exit_short_last = self.exit_short_nex
                    self.ema_length_new = self.ema_length

                    self.exit_short = self.ema_mid

                else:
                    if bar.close_price < (self.ema_mid + self.current_ema / 2):
                        self.exit_short = bar.close_price

                    elif bar.close_price < self.ema_mid:
                        self.exit_short = bar.close_price

                    else:
                        self.exit_short = self.ema_mid
            else:
                self.exit_short = self.ema_mid

            self.cover(self.exit_short, abs(self.pos), True)

        self.put_event()
        self.sync_data()

    def on_xmin_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.am.update_bar(bar)

        if not self.am.inited:
            return

        #  计算海龟 上轨，下轨
        high_max = self.am.high[-self.rolling_period:].max()
        close_min = self.am.close[-self.rolling_period:].min()
        close_max = self.am.close[-self.rolling_period:].max()
        low_min = self.am.low[-self.rolling_period:].min()
        
        hc = high_max - close_min
        cl = close_max - low_min    
        dual = max(hc,cl)
        
        self.up = self.am.open[-2] + dual * self.upper_open 
        self.down = self.am.open[-2] - dual * self.upper_open 

        # print(f"up:{self.up},{self.down}")
        self.current_close = self.am.close[-1]
        self.last_close = self.am.close[-2]
        self.front_close = self.am.close[-3]
        
        if self.pos == 0:
            self.exit_long_nex = 0
            self.exit_long_last = 0
            self.exit_short_nex = 0
            self.exit_short_last = 0
            self.ema_length_new = self.ema_length
            
        elif self.pos > 0:
            close_long = self.current_close > self.last_close > self.front_close
            if close_long:
                self.ema_length_new -= 1
                self.ema_length_new = max(self.ema_length_new, 5)

        elif self.pos < 0:
            close_short = self.current_close < self.last_close < self.front_close
            if close_short:
                self.ema_length_new -= 1
                self.ema_length_new = max(self.ema_length_new, 5)

        self.ema_mid = self.am.ema(self.ema_length)
        ema_mid_new = self.am.ema(self.ema_length_new, True)

        self.current_ema = ema_mid_new[-1]
        self.last_ema = ema_mid_new[-2]

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        pass

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
        # self.put_event()

    def market_order(self):
        """"""
        pass
        # self.buy(self.last_tick.limit_up, 1)
        # self.write_log("执行市价单测试")

    def limit_order(self):
        """"""
        pass
        # self.buy(self.last_tick.limit_down, 1)
        # self.write_log("执行限价单测试")

    def stop_order(self):
        """"""
        pass
        # self.buy(self.last_tick.ask_price_1, 1, True)
        # self.write_log("执行停止单测试")







