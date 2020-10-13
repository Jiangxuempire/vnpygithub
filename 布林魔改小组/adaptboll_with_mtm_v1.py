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
from vnpy.trader.constant import Interval
import pandas as pd
import numpy as np
import talib

class AdaptBollWithMtmV1(CtaTemplate):
    """"""
    author = "will"

    n1 = 14
    # n2 = 35* n1
    trading_size = 1
    indicator_value = 0
    m_value = 0
    up_value = 0
    dn_value = 0  

    parameters = [
       "n1", 'trading_size'
    ]

    variables = [
        "indicator_value", "m_value", "up_value", "dn_value"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(
            self.on_bar, 1, self.on_hour_bar, interval=Interval.HOUR)

        self.am = ArrayManager(int(self.n1 * 5 + 5))
        # self.cta_engine.main_engine.get_account('')
    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(10, use_database=True)

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
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)

    def on_hour_bar(self, bar: BarData):
        """"""
        self.cancel_all()  # 删除所有挂单

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return
        # # 母布林
        # self.median = am.sma(self.n2)
        # self.std = am.std(self.n2)
        # self.z_score = (am.close - self.median)/self.std

        # 计算动量因子
        self.mtm = (am.close[self.n1:] / am.close[:-self.n1]) - 1
        self.mtm_mean = pd.Series(self.mtm).rolling(self.n1, min_periods=1).mean().values #talib.SMA(self.mtm, self.n1) #

        # 波动率因子wd_atr
        # self.c1 = (am.high - am.low)[1:]
        # self.c2 = np.abs(am.high[1:] - am.close[:-1])
        # self.c3 = np.abs(am.low[1:] - am.close[:-1])
        # self.tr = np.array([self.c1, self.c2, self.c3]).max(axis=0)
        # self.atr = talib.SMA(self.tr, self.n1)

        self.atr = talib.ATR(am.high, am.low, am.close, self.n1)
        self.average_price = am.sma(self.n1,True)
        self.wd_atr = self.atr / self.average_price

        # MTMT 指标的 波动率因子
        mtm_l = (am.close[self.n1:] / am.close[:-self.n1]) - 1
        mtm_h = (am.high[self.n1:] / am.high[:-self.n1]) - 1
        mtm_c = (am.close[self.n1:] / am.close[:-self.n1]) - 1
        self.mtm_atr = talib.ATR(mtm_h, mtm_l, mtm_c, self.n1)

        # mtm_c1 = mtm_h - mtm_l
        # mtm_c2 = np.abs(mtm_h[1:] - mtm_c[:-1])
        # mtm_c3 = np.abs(mtm_l[1:] - mtm_c[:-1])
        # mtm_tr = np.array([mtm_c1, mtm_c2, mtm_c3]).max(axis=0)
        # mtm_atr = talib.SMA(mtm_tr, self.n1)

        # 对MTM mean 指标计算波动率
        mtm_l_mean = talib.SMA(mtm_l, self.n1)
        mtm_h_mean = talib.SMA(mtm_h, self.n1)
        mtm_c_mean = talib.SMA(mtm_c, self.n1)
        self.mtm_atr_mean = talib.ATR(mtm_l_mean, mtm_h_mean, mtm_c_mean, self.n1)

        # mtm_c1_mean = mtm_h_mean - mtm_l_mean
        # mtm_c2_mean = np.abs(mtm_h_mean[1:] - mtm_c_mean[:-1])
        # mtm_c3_mean = np.abs(mtm_l_mean[1:] - mtm_c_mean[:-1])
        # mtm_tr_mean = np.array([mtm_c1_mean, mtm_c2_mean, mtm_c3_mean]).max(axis=0)
        # mtm_atr_mean = talib.SMA(mtm_tr_mean, self.n1)

        #  指标波动率调整
        indicator = self.mtm_mean
        self.indicator_final = (indicator[-len(self.mtm_atr_mean):] *
                                self.mtm_atr[-len(self.mtm_atr_mean):] *
                                self.wd_atr[-len(self.mtm_atr_mean):] *
                                self.mtm_atr_mean)

        # 使用指标计算自适应布林
        median = talib.SMA(self.indicator_final, self.n1)
        #std = talib.STDDEV(self.indicator_final, self.n1)
        std = pd.Series(self.indicator_final).rolling(self.n1,min_periods=1).std(ddof=0).values
        z_score = np.abs((self.indicator_final[-len(median):]-median)/std)
        m = talib.MAX(z_score, self.n1)[-5:-1]

        up = median[-4:] + std[-4:] * m
        dn = median[-4:] - std[-4:] * m

        #raise
        self.indicator_value = self.indicator_final[-1]
        self.m_value = m[-1]
        self.up_value = up[-1]
        self.dn_value = dn[-1]

        if self.pos == 0:# 开仓
            # 开多条件
            condition1 = self.indicator_final[-1] > up[-1]
            condition2 = self.indicator_final[-2] <= up[-2]
            # 开空条件
            condition3 = self.indicator_final[-1] < dn[-1]
            condition4 = self.indicator_final[-2] >= up[-2]

            if condition1 & condition2:
                self.buy(bar.close_price+10, self.trading_size, False)
            elif condition3 & condition4:
                self.short(bar.close_price-10, self.trading_size, False)

        elif self.pos > 0:  # 多头平仓
            condition1 = self.indicator_final[-1] < median[-1]
            condition2 = self.indicator_final[-2] >= median[-2]
            self.sell(bar.close_price-10, abs(self.pos), False)

        elif self.pos < 0:  # 空头平仓
            condition3 = self.indicator_final[-1] > median[-1]
            condition4 = self.indicator_final[-2] <= median[-2]
            self.cover(bar.close_price+10, abs(self.pos), False)

        self.put_event()   # 推送数据到ui

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        msg = f" 新的成交，策略{self.strategy_name}，方向{trade.direction}，开平{trade.offset}，当前仓位{self.pos}"
        self.send_email(msg)

        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
