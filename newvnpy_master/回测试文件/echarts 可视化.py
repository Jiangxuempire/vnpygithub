import pandas as pd
from datetime import datetime
from vnpy.app.cta_strategy.base import BacktestingMode

pd.set_option('expand_frame_repr', False)  # 当列太多时清楚展示
pd.set_option('display.max_rows', 100)

from vnpy.app.cta_strategy.backtesting import BacktestingEngine
from vnpy.trader.constant import Interval
from vnpy.strategy.vnpygithub.back_file.back_base.plot_echarts import (my_echarts,
                                                                       get_df_with_signal)

from vnpy.strategy.vnpygithub.back_file.原文件.aberration_bias_strategy import AberrationBiasStrategy

if __name__ == '__main__':
    vt_symbol = "btcusdt.BINANCE"
    start_time = datetime(2019, 11, 1)  # 起始日期，可修改，必填
    end_time = datetime(2020, 9, 29)  # 终止日期，可修改，必填
    slippage = 0.5  # 交易滑点
    size = 1  # 合约乘数
    rate = 2 / 1000  # 手续费
    pricetick = 0.5 # 一跳
    capital = 100000

    engine = BacktestingEngine()
    engine.set_parameters(
        vt_symbol=vt_symbol,  # 交易的标的
        interval=Interval.MINUTE,
        start=start_time,  # 开始时间
        end=end_time,  # 结束时间
        rate=rate,  # 手续费
        slippage=slippage,  # 交易滑点
        size=size,  # 合约乘数
        pricetick=pricetick,  # 8500.5 8500.01
        capital=capital,  # 初始资金
        mode=BacktestingMode.BAR
    )
    engine.add_strategy(AberrationBiasStrategy, {})

    engine.load_data()
    engine.run_backtesting()
    df = engine.calculate_result()
    engine.calculate_statistics()

    #   获取策略名
    strategy_name = engine.strategy.strategy_name
    exchange = engine.exchange.value
    symbol = engine.vt_symbol

    #   获取指标周期
    time_interval = engine.strategy.open_window
    # time_interval = 15
    #   策略参数
    para = [engine.strategy.boll_length, engine.strategy.boll_dev, engine.strategy.bias]

    #   获取策略指标数据 这里添加
    df_ar = pd.DataFrame()
    df_ar["candle_begin_time"] = engine.strategy.plot_echarts["datetime"]
    df_ar["open"] = engine.strategy.plot_echarts["open"]
    df_ar["high"] = engine.strategy.plot_echarts["high"]
    df_ar["low"] = engine.strategy.plot_echarts["low"]
    df_ar["close"] = engine.strategy.plot_echarts["close"]
    df_ar["volume"] = engine.strategy.plot_echarts["volume"]
    df_ar["boll_up"] = engine.strategy.plot_echarts["boll_up"]
    df_ar["boll_down"] = engine.strategy.plot_echarts["boll_down"]
    df_ar["boll_mid"] = engine.strategy.plot_echarts["boll_mid"]
    df_ar["boll_mid_new"] = engine.strategy.plot_echarts["boll_mid_new"]
    df_ar["signal"] = engine.strategy.plot_echarts["signal"]
    # df_ar["bias"] = engine.strategy.plot_echarts["bias"]
    # df_ar["bias_value"] = engine.strategy.plot_echarts["bias_value"]

    df_plot = get_df_with_signal(df=df_ar, strategy=strategy_name)
    my_echarts(exchange, symbol, 1, strategy_name, time_interval, para, df_plot.copy())
    print("图已经画完！")
