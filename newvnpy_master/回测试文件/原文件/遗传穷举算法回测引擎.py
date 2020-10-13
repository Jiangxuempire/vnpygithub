# _*_coding : UTF-8 _*_
# 开发团队 ：yunya
# 开发人员 ：Administrator
# 开发时间 : 2020/6/16 15:49
# 文件名称 ：遗传算法回测引擎.py
# 开发工具 ： PyCharm
from datetime import datetime
from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting

import pandas as pd

pd.set_option('expand_frame_repr', False)
from vnpy.strategy.vnpygithub.back_file import Backtest

# 导入策略


from vnpy.strategy.vnpygithub.boll_vix import BollVix


##############################################################################
def backtests(backtest: Backtest, setting):
    if backtest == "DNA":
        result = engine.run_ga_optimization(setting)  # 遗传算法
    elif backtest == "EX":
        result = engine.run_optimization(setting)  # 穷举算法
    else:
        print("算法类型不对！！")
        exit()
    return result


# 定义使用的函数
def run_backtesting(strategy_class, setting, vt_symbol, interval, start, end, rate, slippage, size, pricetick, capital,
                    inverse):
    engine.set_parameters(
        vt_symbol=vt_symbol,
        interval=interval,
        start=start,
        end=end,
        rate=rate,
        slippage=slippage,
        size=size,
        pricetick=pricetick,
        capital=capital,
        inverse=False  # 正反向合约
    )
    engine.add_strategy(strategy_class, setting)
    engine.load_data()


#####################################################################################

# backtest = "DNA"  # 遗传算法类型
backtest = "EX"  # 穷举算法类型

class_name = "total_net_pnl"  # 总收益
# "sharpe_ratio , total_return , return_drawdown_ratio"
# #自己需要自由度跑的结果在回测引擎的cta_strategy的back_testing.py文件里查找

#####################################################################################

版本号 = 1.0
升级内容 = "动态止盈止损"

strategy_class = BollVix  # 策略名称
exchange = "BINANCE"
symbol = "eosusdt"
start = datetime(2019, 1, 1)  # 开始时间
end = datetime(2020, 7, 1)  # 结束时间
rate = 2 / 1000  # 手续费
slippage = 0.001  # 滑点
size = 1  # 合约乘数
pricetick = 0.001  # 一跳
inverse = False  # 正反向合约
interval = "1m"  # k线周期
capital = 10000  # 初始资金
vt_symbol = symbol + "." + exchange  # 交易对

description = f"回测数据基于{exchange}交易所的{symbol}的{interval}分钟数据,开始时间为：{start},结束时间为：{end}，'\n'" \
              f"交易手续费设置为：{rate},滑点为：{slippage},合约乘数为：{size},盘口一跳为：{pricetick},合约方向：{inverse}(注：F 正向，T 反向)。'\n'" \
              f"策略名为：{strategy_class.__qualname__},回测指标为：{class_name}。'\n'" \
              f"回测时间为：{datetime.now().strftime('%Y-%m-%d')} ，算法类型：{backtest}" '\n' \
              f"版本号：{版本号}，本次版本升级内容为：{升级内容} '\n"

#####################################################################################

if __name__ == '__main__':
    engine = BacktestingEngine()

    # 设置交易对产品的参数
    run_backtesting(
        strategy_class=strategy_class,
        setting={},
        vt_symbol=vt_symbol,
        interval=interval,
        start=start,
        end=end,
        rate=rate,
        slippage=slippage,
        size=size,
        pricetick=pricetick,
        capital=capital,
        inverse=inverse,  # 正反向合约
    )

    """
    open_window = 15
    boll_length = 80
    boll_dev = 2.0
    bias = 2.0
    cci_length = 6
    cci_exit = 10.0
    atr_window = 16
    atr_multiple = 2.0
    long_trailing = 4.0
    short_trailing = 4.0
    """

    setting = OptimizationSetting()
    setting.set_target(f"{class_name}")
    # setting.add_parameter("open_window", 15, 60, 15)
    # setting.add_parameter("rsi_window", 10, 150, 10)
    # setting.add_parameter("exit_window", 30, 80, 5)
    # setting.add_parameter("ema_window", 30, 80, 5)
    # setting.add_parameter("pos_trailing", 2, 3, 0.2)


    # setting.add_parameter("open_window", 15, 15, 15)
    # setting.add_parameter("fast_length", 20, 140, 5)
    # setting.add_parameter("slow_length", 20, 300, 20)

    # setting.add_parameter("open_window", 30, 30, 30)
    # setting.add_parameter("boll_length", 100, 600, 20)
    # setting.add_parameter("boll_dev", 1.4, 3, 0.1)
    # setting.add_parameter("bias", 0.1, 0.5, 0.03)

    # setting.add_parameter("open_window", 30, 30, 30)
    setting.add_parameter("boll_window", 20, 1200, 10)


    # 调用算法类型（遗传，穷举）
    result = backtests(backtest, setting)

    to_csv_result(
        result=result,
        signal_name=str(strategy_class.__qualname__),  # 策略名称
        class_name=class_name,  # 计算指标类型
        symbol=symbol,  # 交易对
        exchange=exchange,  # 交易所
        tag=datetime.now().strftime('%Y-%m-%d'),  # 当前时间
        description=description,  # 说明
        backtest=backtest  # 算法类型
    )
