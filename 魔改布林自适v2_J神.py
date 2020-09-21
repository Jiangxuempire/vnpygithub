import talib

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
from vnpy.app.cta_strategy.new_strategy import NewBarGenerator


def radio_array(array, boll_length, bar_length):
    """
    :param bar_length: 
    :param boll_length: 
    :param array: 
    :return: 
    """
    bar_lengths = bar_length * 2
    bar_array = array[-boll_length * bar_length:] / array[-boll_length * bar_lengths: -boll_length * bar_length] - 1

    return bar_array


class BollVixJStrategy(CtaTemplate):
    """
一、灵感来源
    我基于动量自适应布林短线策略的原始版本，做了非常小的修改，但回测效果惊人。

    「gcouple.j」动量自适应布林短线策略v1
    https://forum.quantclass.cn/d/1784-gcouplej-btc61eth1481

    1.1 自适应布林的原理：
    对于时间窗口参数是n1, 标准差倍数m的布林策略

    close:每周期收盘价

    ma(n1):时间窗口参数是n1的移动平均值

    std(n1):时间窗口参数是n1的标准差

    突破布林上轨的条件

    close > ma(n1) + m*std(n1)

    即:(close-ma(n1))/std(n1) > m

    突破布林下轨条件

    close < ma(n1) - m*std(n1)

    即:-(close-ma(n1))/std(n1) > m

    将布林突破上下轨的条件合并

    abs((close-ma(n1))/std(n1)) > m

    通过将m转为n的函数达到构建自适应布林的目的，即

    令 m=max(abs((close-ma(n1))/std(n1)))

    此处修改，令m=mean(abs((close-ma(n1))/std(n1)))

    由此，只需一个参数即可完成布林通道的构建。

1.2 对指标构建自适应布林通道
    通过对动量指标构建自适应布林通道，可以得到日内级别短线参数。

二、策略思路
    将
        df['m'] = df['z_score'].rolling(window=n1).max().shift(1)
    改成
        df['m'] = df['z_score'].rolling(window=n1).mean()

三、代码
    3.1、策略代码
        def adaptboll_with_mtm_v2(df, para=[90]):
          n1 = para[0]

          # 计算动量因子
          df['mtm'] = df['close'] / df['close'].shift(n1) - 1
          df['mtm_mean'] = df['mtm'].rolling(window=n1, min_periods=1).mean()


          # 基于价格atr，计算波动率因子wd_atr
          df['c1'] = df['high'] - df['low']
          df['c2'] = abs(df['high'] - df['close'].shift(1))
          df['c3'] = abs(df['low'] - df['close'].shift(1))
          df['tr'] = df[['c1', 'c2', 'c3']].max(axis=1)
          df['atr'] = df['tr'].rolling(window=n1, min_periods=1).mean()
          df['avg_price'] = df['close'].rolling(window=n1, min_periods=1).mean()
          df['wd_atr'] = df['atr'] / df['avg_price']

          # 参考ATR，对MTM指标，计算波动率因子
          df['mtm_l'] = df['low'] / df['low'].shift(n1) - 1
          df['mtm_h'] = df['high'] / df['high'].shift(n1) - 1
          df['mtm_c'] = df['close'] / df['close'].shift(n1) - 1
          df['mtm_c1'] = df['mtm_h'] - df['mtm_l']
          df['mtm_c2'] = abs(df['mtm_h'] - df['mtm_c'].shift(1))
          df['mtm_c3'] = abs(df['mtm_l'] - df['mtm_c'].shift(1))
          df['mtm_tr'] = df[['mtm_c1', 'mtm_c2', 'mtm_c3']].max(axis=1)
          df['mtm_atr'] = df['mtm_tr'].rolling(window=n1, min_periods=1).mean()

          # 参考ATR，对MTM mean指标，计算波动率因子
          df['mtm_l_mean'] = df['mtm_l'].rolling(window=n1, min_periods=1).mean()
          df['mtm_h_mean'] = df['mtm_h'].rolling(window=n1, min_periods=1).mean()
          df['mtm_c_mean'] = df['mtm_c'].rolling(window=n1, min_periods=1).mean()
          df['mtm_c1'] = df['mtm_h_mean'] - df['mtm_l_mean']
          df['mtm_c2'] = abs(df['mtm_h_mean'] - df['mtm_c_mean'].shift(1))
          df['mtm_c3'] = abs(df['mtm_l_mean'] - df['mtm_c_mean'].shift(1))
          df['mtm_tr'] = df[['mtm_c1', 'mtm_c2', 'mtm_c3']].max(axis=1)
          df['mtm_atr_mean'] = df['mtm_tr'].rolling(window=n1, min_periods=1).mean()

          indicator = 'mtm_mean'

          # mtm_mean指标分别乘以三个波动率因子
          df[indicator] = df[indicator] * df['mtm_atr']
          df[indicator] = df[indicator] * df['mtm_atr_mean']
          df[indicator] = df[indicator] * df['wd_atr']

          # 对新策略因子计算自适应布林
          df['median'] = df[indicator].rolling(window=n1).mean()
          df['std'] = df[indicator].rolling(n1, min_periods=1).std(ddof=0)  # ddof代表标准差自由度
          df['z_score'] = abs(df[indicator] - df['median']) / df['std']
          # df['m'] = df['z_score'].rolling(window=n1).max().shift(1)
          df['m'] = df['z_score'].rolling(window=n1).mean()
          df['up'] = df['median'] + df['std'] * df['m']
          df['dn'] = df['median'] - df['std'] * df['m']

          # 突破上轨做多
          condition1 = df[indicator] > df['up']
          condition2 = df[indicator].shift(1) <= df['up'].shift(1)
          condition = condition1 & condition2
          df.loc[condition, 'signal_long'] = 1

          # 突破下轨做空
          condition1 = df[indicator] < df['dn']
          condition2 = df[indicator].shift(1) >= df['dn'].shift(1)
          condition = condition1 & condition2
          df.loc[condition, 'signal_short'] = -1

          # 均线平仓(多头持仓)
          condition1 = df[indicator] < df['median']
          condition2 = df[indicator].shift(1) >= df['median'].shift(1)
          condition = condition1 & condition2
          df.loc[condition, 'signal_long'] = 0

          # 均线平仓(空头持仓)
          condition1 = df[indicator] > df['median']
          condition2 = df[indicator].shift(1) <= df['median'].shift(1)
          condition = condition1 & condition2
          df.loc[condition, 'signal_short'] = 0



          # ===由signal计算出实际的每天持有仓位
          # signal的计算运用了收盘价，是每根K线收盘之后产生的信号，到第二根开盘的时候才买入，仓位才会改变。
          df['signal_short'].fillna(method='ffill', inplace=True)
          df['signal_long'].fillna(method='ffill', inplace=True)
          df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1)
          df['signal'].fillna(value=0, inplace=True)
          # df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1,
          #                                                        skipna=True)  # 若你的pandas版本是最新的，请使用本行代码代替上面一行
          temp = df[df['signal'].notnull()][['signal']]
          temp = temp[temp['signal'] != temp['signal'].shift(1)]
          df['signal'] = temp['signal']

          df.drop(['signal_long', 'signal_short', 'atr', 'z_score'], axis=1,
                  inplace=True)
          return df

    3.2、策略参数组合
    # 策略参数组合
    def adaptboll_with_mtm_v2_para_list(m_list=range(1, 100, 1)):

        print('参数遍历范围：')
        print('m_list', list(m_list))

        para_list = []

        for m in m_list:
          para = [m]
          para_list.append(para)

        return para_list

    4.2、策略总体评价
        strategy_name	symbol	年化收益回撤比
        adaptboll_with_mtm_v2	BTC	14.415570606108213
        adaptboll_with_mtm_v2	ETH	38.00534253439086


    """

    author = "yunya"

    open_window = 15
    boll_length = 50
    fixed_size = 1

    atr_value = 0
    mtm_ma_current = 0
    mtm_ma_last = 0
    boll_up_current = 0
    boll_up_last = 0
    boll_down_current = 0
    boll_down_last = 0
    boll_mid_current = 0
    boll_mid_last = 0

    bar_length = 8

    parameters = [
            "open_window",
            "boll_length",
            "fixed_size",
    ]

    variables = [
            "atr_value",
            "mtm_ma_current",
            "mtm_ma_last",
            "boll_up_current",
            "boll_up_last",
            "boll_down_current",
            "boll_down_last",
            "boll_mid_current",
            "boll_mid_last",
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = NewBarGenerator(self.on_bar, self.open_window, self.on_xmin_bar)
        self.am = ArrayManager(int(self.boll_length) * (self.bar_length * 2))

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

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)

    def on_xmin_bar(self, bar: BarData):
        """
        m=mean(abs((close-ma(n1))/std(n1)))
        :param bar:
        :return:
        """
        self.cancel_all()

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        # 计算动量因子 MTM
        mtm_array = radio_array(am.close, self.boll_length, self.bar_length)
        mtm_ma = talib.MA(mtm_array, self.boll_length)

        # 计算atr 相对emaatr的波动率 计算波动率因子wd_atr
        atr_array = am.atr(self.boll_length, array=True)
        self.atr_value = atr_array[-1]

        atr_ma = talib.MA(atr_array, self.boll_length)
        wd_atr = atr_array / atr_ma

        # 参考ATR，对MTM指标，计算波动率因子
        mtm_high = radio_array(am.high, self.boll_length, self.bar_length)
        mtm_low = radio_array(am.low, self.boll_length, self.bar_length)
        mtm_close = radio_array(am.close, self.boll_length, self.bar_length)

        mtm_atr_array = talib.ATR(mtm_high, mtm_low, mtm_close, self.boll_length)
        mtm_atr_ma = talib.MA(mtm_atr_array, self.boll_length)

        # 参考ATR，对MTM mean指标，计算波动率因子
        mtm_high_mean = talib.MA(mtm_high, self.boll_length)
        mtm_low_mean = talib.MA(mtm_low, self.boll_length)
        mtm_close_mean = talib.MA(mtm_close, self.boll_length)

        mtm_atr_mean_array = talib.ATR(mtm_high_mean, mtm_low_mean, mtm_close_mean, self.boll_length)
        mtm_atr_meam_ma = talib.MA(mtm_atr_mean_array, self.boll_length)

        # mtm_mean指标分别乘以三个波动率

        mtm_ma = mtm_ma * wd_atr[-self.boll_length * self.bar_length:]
        mtm_ma = mtm_ma * mtm_atr_ma[-self.boll_length * self.bar_length:]
        mtm_ma = mtm_ma * mtm_atr_meam_ma[-self.boll_length * self.bar_length:]

        mtm_meam = talib.MA(mtm_ma, self.boll_length)
        mtm_std = talib.STDDEV(mtm_meam, self.boll_length)

        mtm_dev = abs(mtm_ma - mtm_meam) / mtm_std
        mtm_dev_me = talib.MA(mtm_dev, self.boll_length)

        boll_up = mtm_meam + mtm_std * mtm_dev_me
        boll_down = mtm_meam - mtm_std * mtm_dev_me

        # 值
        self.mtm_ma_current = mtm_ma[-1]
        self.mtm_ma_last = mtm_ma[-2]
        self.boll_up_current = boll_up[-1]
        self.boll_up_last = boll_up[-2]
        self.boll_down_current = boll_down[-1]
        self.boll_down_last = boll_down[-2]
        self.boll_mid_current = mtm_meam[-1]
        self.boll_mid_last = mtm_meam[-2]

        # 如果没有仓位，两条布林window一样
        if self.pos == 0:
            if self.mtm_ma_current > self.boll_up_current and self.mtm_ma_last <= self.boll_up_last:
                self.buy(bar.close_price, self.fixed_size)

            elif self.mtm_ma_current < self.boll_down_current and self.mtm_ma_last >= self.boll_down_last:
                self.short(bar.close_price, self.fixed_size)

        elif self.pos > 0:
            if self.mtm_ma_current < self.boll_mid_current and self.mtm_ma_last >= self.boll_mid_last:
                self.sell(bar.close_price, abs(self.pos))  # 要优化

        elif self.pos < 0:
            if self.mtm_ma_current > self.boll_mid_current and self.mtm_ma_last <= self.boll_mid_last:
                self.cover(bar.close_price, abs(self.pos))

        self.put_event()
        self.sync_data()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        self.put_event()
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        pass
        # if trade.direction == Direction.LONG:
        #     self.trade_price_long = trade.price  # 成交最高价
        #     self.long_stop_trade = self.trade_price_long - self.atr_multiple * self.atr_value
        # else:
        #     self.trade_price_short = trade.price
        #     self.short_stop_trade = self.trade_price_short + self.atr_multiple * self.atr_value
        #
        # self.sync_data()
        # self.put_event()

    