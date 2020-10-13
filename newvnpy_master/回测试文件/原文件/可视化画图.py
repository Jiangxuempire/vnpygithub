import pandas as pd
from copy import copy
from datetime import datetime
from pytz import timezone
from vnpy.app.cta_strategy.base import BacktestingMode

pd.set_option('expand_frame_repr', False)  # 当列太多时清楚展示
# pd.set_option('display.max_rows', 1000)

from vnpy.app.cta_strategy.backtesting import BacktestingEngine
from vnpy.trader.constant import Interval, Direction
from vnpy.strategy.vnpygithub.back_file import my_echarts

from vnpy.strategy.vnpygithub.back_file.原文件.aberration_bias_strategy import AberrationBiasStrategy


def get_df_with_signal(df, strategy, rule_type=None):
    # 先去除起點之前的candle
    # df = df[df['candle_begin_time'] >= pd.to_datetime(start_time)]
    # df = df[df['candle_begin_time'] < pd.to_datetime(end_time)]
    df = df.sort_values(by='candle_begin_time', ascending=True)
    df.reset_index(inplace=True, drop=True)
    # 先把資料庫的data轉成實盤rule_type的分鐘k線
    # df = transfer_to_period_data(df, rule_type)
    # 因為rasample過，所以最後一根不要取，會不完整
    df = df.iloc[0:-1, :]
    # 原始数据是utc的话，要加这一行，加8个小时
    # df['candle_begin_time'] = df['candle_begin_time'] + timedelta(hours=8)
    # df = eval(strategy + '(df.copy(), para)')
    print(df.tail())

    return df


def generate_trade_pairs(trades: list) -> list:
    """"""
    long_trades = []
    short_trades = []
    trade_pairs = []

    for trade in trades:
        trade = copy(trade)

        if trade.direction == Direction.LONG:
            same_direction = long_trades
            opposite_direction = short_trades
        else:
            same_direction = short_trades
            opposite_direction = long_trades

        while trade.volume and opposite_direction:
            open_trade = opposite_direction[0]

            close_volume = min(open_trade.volume, trade.volume)
            d = {
                "open_dt": open_trade.datetime,
                "open_price": open_trade.price,
                "close_dt": trade.datetime,
                "close_price": trade.price,
                "direction": open_trade.direction,
                "offset": trade.offset,
                "volume": close_volume,
            }
            trade_pairs.append(d)

            open_trade.volume -= close_volume
            if not open_trade.volume:
                opposite_direction.pop(0)

            trade.volume -= close_volume

        if trade.volume:
            same_direction.append(trade)

    return trade_pairs


if __name__ == '__main__':
    # --------------根据要画图的策略和参数进行修改，开始处---------------------------------------------
    exchange = 'bitfinex'  # 只用于显示，可以是任意字符串，可修改
    symbol = 'ETH/USD'  # 只用于显示，可以是任意字符串，可修改
    file_path = r'D:\MyRepository\my_backtest\data\raw\ETH-USDT_5m.h5'  # 数据文件的位置，可修改，必填
    start_time = '2019-11-10'  # 起始日期，可修改，必填
    end_time = '2020-12-10'  # 终止日期，可修改，必填
    time_interval = '15T'  # 策略周期，可修改，必填
    para = [100, 3]  # 策略参数，根据实际策略需要改，可以多参数，如[200, 2, 12, 3]等等，可修改，必填

    strategy_name: str
    time_interval: time_interval

    engine = BacktestingEngine()
    engine.set_parameters(
        vt_symbol="btcusdt.BINANCE",  # 交易的标的
        interval=Interval.MINUTE,
        start=datetime(2020, 1, 1),  # 开始时间
        end=datetime(2020, 4, 1),  # 结束时间
        rate=2 / 1000,  # 手续费
        slippage=0.5,  # 交易滑点
        size=1,  # 合约乘数
        pricetick=0.5,  # 8500.5 8500.01
        capital=100000,  # 初始资金
        mode=BacktestingMode.BAR
    )
    engine.add_strategy(AberrationBiasStrategy, {})

    engine.load_data()
    engine.run_backtesting()
    df = engine.calculate_result()
    engine.calculate_statistics()

    #   获取策略指标数据
    df_ar = pd.DataFrame()
    df_ar["candle_begin_time"] = engine.strategy.plot_echarts['datetime']
    df_ar["open"] = engine.strategy.plot_echarts["open"]
    df_ar["high"] = engine.strategy.plot_echarts["high"]
    df_ar["low"] = engine.strategy.plot_echarts["low"]
    df_ar["close"] = engine.strategy.plot_echarts["close"]
    df_ar["volume"] = engine.strategy.plot_echarts["volume"]
    df_ar["boll_up"] = engine.strategy.plot_echarts["boll_up"]
    df_ar["boll_down"] = engine.strategy.plot_echarts["boll_down"]
    df_ar["boll_mid"] = engine.strategy.plot_echarts["boll_mid"]
    df_ar["boll_mid_new"] = engine.strategy.plot_echarts["boll_mid_new"]
    df_ar["bias"] = engine.strategy.plot_echarts["bias"]
    df_ar["bias_value"] = engine.strategy.plot_echarts["bias_value"]
    # df_ar["signal"] = None
    print(df_ar.head())
    # #   调用画图工具
    # strategy_name = engine.strategy.strategy_name
    # exchange = engine.exchange.value
    # symbol = engine.vt_symbol
    # para = [engine.strategy.boll_length, engine.strategy.boll_dev, engine.strategy.bias]
    # print(strategy_name)
    # time_interval = engine.strategy.open_window
    # df1 = get_df_with_signal(df=df_ar, strategy=strategy_name)
    # my_echarts(exchange, symbol, 1, strategy_name, time_interval, para, df_ar.copy())
    # print("图已经画完！")
    # exit()

    # df_ar.to_csv("布林带", index="candle_begin_time", mode='a')

    #   获取交易记录明细
    trades = engine.get_all_trades()

    trade_records = pd.DataFrame(
        columns=['instrument', 'candle_begin_time', 'direction', 'offset', 'trade_price', 'signal'])
    i = -1
    for trade in trades:

        i = i + 1
        if trade.direction.value == '多':
            temp_direction = 'Long'
        elif trade.direction.value == '空':
            temp_direction = 'Short'
        if trade.offset.value == '开':
            temp_offset = 'open_position'
        elif trade.offset.value == '平':
            temp_offset = 'close_position'

        if trade.direction.value == '多':
            trade_records.loc[i] = [trade.vt_symbol, trade.datetime, temp_direction,
                                    temp_offset, trade.price, trade.volume]
        elif trade.direction.value == '空':
            trade_records.loc[i] = [trade.vt_symbol, trade.datetime, temp_direction,
                                    temp_offset, trade.price, trade.volume]

    # trade_records = trade_records.set_index('candle_begin_time')
    # trade_records['open_long'] = trade_records.apply(
    #     lambda x: x['trade_price'] if x['direction'] == 'Long' and x['offset'] == 'open_position' else math.nan, axis=1)
    # trade_records['open_short'] = trade_records.apply(
    #     lambda x: x['trade_price'] if x['direction'] == 'Short' and x['offset'] == 'open_position' else math.nan,
    #     axis=1)
    # trade_records['close_long'] = trade_records.apply(
    #     lambda x: x['trade_price'] if x['direction'] == 'Long' and x['offset'] == 'close_position' else math.nan,
    #     axis=1)
    # trade_records['close_short'] = trade_records.apply(
    #     lambda x: x['trade_price'] if x['direction'] == 'Short' and x['offset'] == 'close_position' else math.nan,
    #     axis=1)

    condition1 = trade_records['offset'] == 'open_position'
    condition2 = trade_records['direction'] == 'Long'
    trade_records.loc[condition1 & condition2, 'signal_long'] = 1

    condition1 = trade_records['offset'] == 'close_position'
    condition2 = trade_records['direction'] == 'Long'
    trade_records.loc[condition1 & condition2, 'signal_short'] = 0

    condition1 = trade_records['offset'] == 'open_position'
    condition2 = trade_records['direction'] == 'Short'
    trade_records.loc[condition1 & condition2, 'signal_short'] = -1

    condition1 = trade_records['offset'] == 'close_position'
    condition2 = trade_records['direction'] == 'Short'
    trade_records.loc[condition1 & condition2, 'signal_long'] = 0

    condition1 = trade_records['offset'] == 'open_position'
    condition2 = trade_records['direction'] == 'Long'
    trade_records.loc[condition1 & condition2, 'signal'] = 1

    condition1 = trade_records['offset'] == 'open_position'
    condition2 = trade_records['direction'] == 'Short'
    trade_records.loc[condition1 & condition2, 'signal'] = -1

    condition1 = trade_records['offset'] == 'close_position'
    trade_records.loc[condition1, 'signal'] = 0

    trade_records.drop(['instrument', 'direction', 'offset', 'trade_price'], axis=1, inplace=True)
    # trade_records.to_csv("信号多空独立", index=False, mode='a')
    trade_records = trade_records.set_index("candle_begin_time")
    print(trade_records.tail(10))

    #   读取数据库历史数据
    dt = []
    o = []
    h = []
    l = []
    c = []
    v = []

    for bar in engine.history_data:
        dt.append(bar.datetime)
        o.append(bar.open_price)
        h.append(bar.high_price)
        l.append(bar.low_price)
        c.append(bar.close_price)
        v.append(bar.volume)

    df = pd.DataFrame()
    df["candle_begin_time"] = dt
    df["open"] = o
    df["high"] = h
    df["low"] = l
    df["close"] = c
    df["volume"] = v
    df = df.set_index("candle_begin_time")

    df = pd.merge(
        left=df,
        right=trade_records,
        left_on='candle_begin_time',
        right_on='candle_begin_time',
        suffixes=['_left', '_right'],
        how='left',  # 'left', 'right', 'outer' 默认是'inner'
    )
    print(df.head(10))
    df['open'] = df['open'].resample(rule='15T').first()
    # df['high'] = df['high'].resample(rule="15T").max()
    # df['low'] = df['low'].resample(rule='15T').min()
    # df['volume'] = df['volume'].resample(rule='15T').sum()
    df['signal'] = df['signal'].resample(rule='15T').max()
    df.dropna(subset=['open'], inplace=True)
    df = df[['signal']]
    print(df)

    df = pd.merge(
        left=df_ar,
        right=df,
        left_on='candle_begin_time',
        right_on='candle_begin_time',
        suffixes=['_left', '_right'],
        how='left',  # 'left', 'right', 'outer' 默认是'inner'
    )
    print(df)

    #   调用画图工具
    strategy_name = engine.strategy.strategy_name
    exchange = engine.exchange.value
    symbol = engine.vt_symbol
    para = [engine.strategy.boll_length, engine.strategy.boll_dev, engine.strategy.bias]
    print(strategy_name)
    time_interval = engine.strategy.open_window
    df = get_df_with_signal(df=df, strategy=strategy_name)
    my_echarts(exchange, symbol, 1, strategy_name, time_interval, para, df.copy())
    print("图已经画完！")
    exit()
    exit()

    df = pd.merge(
        left=df3,
        right=df1,
        left_on='candle_begin_time',
        right_on='candle_begin_time',
        suffixes=['_left', '_right'],
        how='left',  # 'left', 'right', 'outer' 默认是'inner'
    )
    df.to_csv("1分钟K")
    df.iloc[df['candle_begin_time'] == trade_records['candle_begin_time'], "signal"] = trade_records["signal"]
    print(df)
    exit()
    df_merged = pd.merge(
        left=df,
        right=trade_records,
        left_on='candle_begin_time',
        right_on='candle_begin_time',
        suffixes=['_left', '_right'],
        how='left',  # 'left', 'right', 'outer' 默认是'inner'
    )
    print(df_merged)

    print(trade_records.head())
    exit()
    # print(df_ar.head())
    tz = timezone('Asia/Shanghai')
    plot_start = datetime(2020, 1, 19, 10, 30)
    plot_start = plot_start.replace(tzinfo=tz)

    # df_ar = df_ar[df_ar['candle_begin_time'] >= pd.to_datetime(plot_start)]
    print(df_ar.head())

    con1 = df_ar['candle_begin_time'].shift(1) < trade_records["candle_begin_time"]
    con2 = df_ar['candle_begin_time'].shift >= trade_records["candle_begin_time"]
    df_ar = df_ar[con1 & con2, "signal"] = trade_records["signal"]
    print(df_ar)

    # df_merged = pd.merge(
    #     left=df_ar,
    #     right=trade_records,
    #     left_on='candle_begin_time',
    #     right_on='candle_begin_time',
    #     suffixes=['_left', '_right'],
    #     how='left'
    #     # how='left',  # 'left', 'right', 'outer' 默认是'inner'
    # )
    # print(df_merged)

    # tz = timezone('Asia/Shanghai')
    # plot_start = datetime(2020, 1, 19, 10, 30)
    # plot_start = plot_start.replace(tzinfo=tz)
    #
    # df_ar = df_ar[df_ar['candle_begin_time'] >= pd.to_datetime(plot_start)]

    exit()

    #   调用画图工具
    strategy_name = engine.strategy.strategy_name
    exchange = engine.exchange.value
    symbol = engine.vt_symbol
    para = [engine.strategy.boll_length, engine.strategy.boll_dev, engine.strategy.bias]
    print(strategy_name)
    time_interval = engine.strategy.open_window
    df1 = get_df_with_signal(df=df_ar, strategy=strategy_name)
    my_echarts(exchange, symbol, 1, strategy_name, time_interval, para, df_merged.copy())
    print("图已经画完！")
    exit()

    #   读取数据库历史数据
    dt = []
    o = []
    h = []
    l = []
    c = []
    v = []

    for bar in engine.history_data:
        dt.append(bar.datetime)
        o.append(bar.open_price)
        h.append(bar.high_price)
        l.append(bar.low_price)
        c.append(bar.close_price)
        v.append(bar.volume)

    df = pd.DataFrame()
    df["candle_begin_time"] = dt
    df["open"] = o
    df["high"] = h
    df["low"] = l
    df["close"] = c
    df["volume"] = v

    df_merged = pd.merge(
        left=df,
        right=trade_records,
        left_on='candle_begin_time',
        right_on='candle_begin_time',
        suffixes=['_left', '_right'],
        how='left',  # 'left', 'right', 'outer' 默认是'inner'
    )
    print(df_merged)

    tz = timezone('Asia/Shanghai')
    plot_start = datetime(2020, 1, 19, 10, 40)
    plot_start = plot_start.replace(tzinfo=tz)

    df_merged = df_merged[df_merged['candle_begin_time'] >= pd.to_datetime(plot_start)]
    print(df_merged)
    exit()

    period_df = df_merged.resample(rule="15T", on='candle_begin_time', label='left', closed='left').agg(
        {'open': 'first',
         'high': 'max',
         'low': 'min',
         'close': 'last',
         'volume': 'sum',
         "signal": "sum"
         })
    period_df.dropna(subset=['open'], inplace=True)  # 去除一天都没有交易的周期
    period_df = period_df[period_df['volume'] > 0]  # 去除成交量为0的交易周期
    period_df.reset_index(inplace=True)
    df = period_df[['candle_begin_time', 'open', 'high', 'low', 'close', 'volume', 'signal']]
    # print(df)
    tz = timezone('Asia/Shanghai')
    plot_start = datetime(2020, 1, 19, 10, 40)
    plot_start = plot_start.replace(tzinfo=tz)

    df = df[df['candle_begin_time'] >= pd.to_datetime(plot_start)]
    # df = df[df['candle_begin_time'] < pd.to_datetime(end_time)]
    print(df)

    exit()
