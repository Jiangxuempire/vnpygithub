from vnpy.trader.constant import Interval
from datetime import datetime
import pandas as pd
from vnpy.app.cta_strategy.base import BacktestingMode

# 使用原版回测引行
from vnpy.app.cta_strategy.backtesting import BacktestingEngine

# 使用自动修改的回测引行
# from vnpy.app.cta_strategy.Newbacktesting import

pd.set_option('expand_frame_repr', False)

# 导入策略
# from vnpy.strategy.vnpygithub.rsidcvix import RsiDcVixStrategy
# from vnpy.strategy.vnpygithub.魔改布林自适v2_J神 import BollVixJStrategy
# from vnpy.strategy.vnpygithub.rsidcvix import RsiDcVixStrategy
# from vnpy.strategy.vnpygithub.aberration_strategy import AberrationStrategy
# from vnpy.strategy.vnpygithub.布林魔改小组.魔改布林J神V3 import IndicatorStrategy
# from vnpy.strategy.vnpygithub.boll_vix import BollVix
# from vnpy.strategy.vnpygithub.adapt_boll_strategy import AdaptBollStrategy

from vnpy.strategy.vnpygithub.back_file.原文件.aberration_bias_strategy import AberrationBiasStrategy

if __name__ == '__main__':
    # 回测引擎初始化
    engine = BacktestingEngine()

    # 设置交易对产品的参数
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

    # 添加策略
    # engine.add_strategy(EmaHlc3, {})
    # engine.add_strategy(Atr_Stop, {    "max_window" :35,
    #                                     "min_window" :10,
    #                                     "open_window" :5,
    #                                     "art_leng" :14,
    #                                     "nloss_singnal" :3.8,
    #                                     "ema_window" :19,
    #                                     "tr_leng" :34,
    #                                     "sl_multiplier" :2.5,
    #                                     "fixd_size" : 1
    #                                    })

    # 传入参数，实例化一个策略，相当于执行了DoubleMaStrategy(strategy_name,vt_symbol, setting)
    engine.add_strategy( AberrationBiasStrategy, {})

    # 加载  最终的结果是通过数据库的ORM取出DbBarData，遍历DbBarData，通过to_tick或to_bar方法生成tick或Bar，
    # 最终得到self.history_data（里面保存tick或bar）
    engine.load_data()

    # 运行回测
    engine.run_backtesting()

    # 统计结果
    df = engine.calculate_result()

    # 计算策略的统计指标 Sharp ratio, drawdown
    de = engine.calculate_statistics()
    de = pd.DataFrame([de])
    # print(de)
    de = de.rename(columns={
        'start_date': "首个交易日",
        'end_date': '最后交易日',
        'total_days': '总交易日',
        'profit_days': '盈利交易日',
        'loss_days': '亏损交易日',
        'capital': '起始资金',
        'end_balance': '结束资金',
        'max_drawdown': '最大回撤',
        'max_ddpercent': '百分比最大回撤',
        'max_drawdown_duration': '最长回撤天数',
        'total_net_pnl': '总盈亏',
        'daily_net_pnl': '日均盈亏',
        'total_commission': '总手续费',
        'daily_commission': '日均手续费',
        'total_slippage': '总滑点',
        'daily_slippage': '日均滑点',
        'total_turnover': '总成交金额',
        'daily_turnover': '日均成交金额',
        'total_trade_count': '总成交笔数',
        'daily_trade_count': '日均成交笔数',
        'total_return': '总收益率',
        'annual_return': '年化收益',
        'daily_return': '日均收益率',
        'return_std': '收益标准差',
        'sharpe_ratio': 'Sharpe Ratio',
        'return_drawdown_ratio': '收益回撤比'
    })
    de = de[['首个交易日', '最后交易日', '总交易日', '盈利交易日',
             '亏损交易日', '起始资金', '结束资金', '总收益率', '年化收益',
             '最大回撤', '百分比最大回撤', '最长回撤天数', '总盈亏', '总手续费',
             '总滑点', '总成交金额', '总成交笔数', '日均盈亏', '日均手续费', '日均滑点',
             '日均成交金额', '日均成交笔数', '日均收益率', '收益标准差',
             'Sharpe Ratio', '收益回撤比']]

    # de = pd.DataFrame(pd.Series(de))

    print(de)

    # 绘制图表
    engine.show_chart()
