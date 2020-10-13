# _*_coding : UTF-8 _*_
# 开发团队 ：yunya
# 开发人员 ：Administrator
# 开发时间 : 2020/5/7 23:18
# 文件名称 ：画图案例.py
# 开发工具 ： PyCharm

# 加载绘图模块
from mpl_finance import candlestick2_ohlc
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.gridspec as gridspec
import datetime as datetime
import numpy as np
import pandas as pd
import math
from datetime import datetime
from pytz import timezone
import talib as ta
pd.set_option('expand_frame_repr', False)  # 当列太多时清楚展示

'''

 jupyter notebook

 vnpy 框架上k线图表上显示的

 向上黄色三角为 开多信号    向下蓝色三角  开多信号
 向下黄色三角为  开空信号    向上蓝色三角  平空信号


'''

from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
from vnpy.app.cta_strategy.strategies.atr_rsi_strategy import (
    AtrRsiStrategy,
)
from vnpy.trader.constant import Interval, Direction, Offset


engine = BacktestingEngine()
engine.set_parameters(
    vt_symbol="btcusdt.BINANCE",
    interval="1m",
    start=datetime(2018, 1, 1),
    end=datetime(2018, 1, 18),
    rate=0.3 / 10000,
    slippage=0.2,
    size=300,
    pricetick=0.2,
    capital=1_000_000,
)
engine.add_strategy(AtrRsiStrategy, {})

engine.load_data()
engine.run_backtesting()
df = engine.calculate_result()
engine.calculate_statistics()
# engine.show_chart()
trades = engine.get_all_trades()

# 导出K线数据1分钟线
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

df = pd.DataFrame()
df["open"] = o
df["high"] = h
df["low"] = l
df["close"] = c
df.index = dt


def BOLL(close_array, n: int, dev: float):
    mid = ta.SMA(close_array, n)
    std = ta.STDDEV(close_array, n)

    up = mid + std * dev
    down = mid - std * dev

    return up[-1], down[-1]


boll_up_list = []
boll_down_list = []
atr_list = []
rsi_list = []
for t in range(1, len(df) + 1):
    if t < 1:
        boll_up_list.append(np.nan)
        boll_down_list.append(np.nan)
        atr_list.append(np.nan)
        rsi_list.append(np.nan)
    else:
        open_array = np.array(o[t - 1:t])
        high_array = np.array(h[t - 1:t])
        low_array = np.array(l[t - 1:t])
        close_array = np.array(c[t - 1:t])
        boll_up, boll_down = BOLL(close_array, 20, 2)  # 第二个参数是n日，第三个参数是std的倍数
        boll_up_list.append(boll_up)
        boll_down_list.append(boll_down)
        atr = ta.ATR(high_array, low_array, close_array, 22)
        rsi = ta.RSI(close_array, 5)
        atr_list.append(atr[-1])
        rsi_list.append(rsi[-1])

# 增加技术指标线
df['boll_up'] = boll_up_list
df['boll_down'] = boll_down_list
df['atr'] = atr_list
df['rsi'] = rsi_list

# 导出成交数据
# trade_records = pd.DataFrame(
#     columns=['instrument', 'datetime', 'time', 'direction', 'offset', 'trade_price', 'volume'])
trade_records = pd.DataFrame(
    columns=['instrument', 'datetime',  'direction', 'offset', 'trade_price', 'volume'])
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
    # trade_records.loc[i] = [trade.vt_symbol, trade.datetime.strftime("%d/%m/%Y %H:%M:%S"), trade.time, temp_direction,
    #                         temp_offset, trade.price, trade.volume]
    # if trade.direction.value == '多':
    #     trade_records.loc[i] = [trade.vt_symbol, trade.datetime, trade.time, temp_direction,
    #                             temp_offset, trade.price, trade.volume]
    # elif trade.direction.value == '空':
    #     trade_records.loc[i] = [trade.vt_symbol, trade.datetime, trade.time, temp_direction,
    #                             temp_offset, trade.price, trade.volume]
    if trade.direction.value == '多':
        trade_records.loc[i] = [trade.vt_symbol, trade.datetime,  temp_direction,
                                temp_offset, trade.price, trade.volume]
    elif trade.direction.value == '空':
        trade_records.loc[i] = [trade.vt_symbol, trade.datetime,  temp_direction,
                                temp_offset, trade.price, trade.volume]
trade_records = trade_records.set_index('datetime')
trade_records['open_long'] = trade_records.apply(
    lambda x: x['trade_price'] if x['direction'] == 'Long' and x['offset'] == 'open_position' else math.nan, axis=1)
trade_records['open_short'] = trade_records.apply(
    lambda x: x['trade_price'] if x['direction'] == 'Short' and x['offset'] == 'open_position' else math.nan, axis=1)
trade_records['close_long'] = trade_records.apply(
    lambda x: x['trade_price'] if x['direction'] == 'Long' and x['offset'] == 'close_position' else math.nan, axis=1)
trade_records['close_short'] = trade_records.apply(
    lambda x: x['trade_price'] if x['direction'] == 'Short' and x['offset'] == 'close_position' else math.nan, axis=1)

df = df.join(trade_records)
df = df.reset_index()
df = df.rename(columns={'index': 'datetime'})
print(df)
exit()
# 策略运行完之后，以下画图代码可以单独运行

tz = timezone('Asia/Shanghai')
plot_start = datetime(2018, 1, 17, 9, 30)  # 每次都可以修改，前闭区后开区间
plot_end = datetime(2018, 1, 17, 14, 45)  # 每次都可以修改，前闭区后开区间

plot_start = plot_start.replace(tzinfo=tz)
plot_end = plot_end.replace(tzinfo=tz)


start_index = df[df['datetime'] == plot_start].index.tolist()
start_index = start_index[0]
end_index = df[df['datetime'] == plot_end].index.tolist()
end_index = end_index[0]


def mydate(x, pos):
    try:
        return df.index[int(x)]
    except IndexError:
        return ''


# fig, ax = plt.subplots(figsize=(20, 10))
fig = plt.figure(figsize=(20, 12), dpi=100, facecolor="white")
# ax.xaxis.set_major_locator(ticker.MaxNLocator(6))
# ax.xaxis.set_major_formatter(ticker.FuncFormatter(mydate))

gs = gridspec.GridSpec(2, 1, left=0.08, bottom=0.15, right=0.99, top=0.96, wspace=None, hspace=0, height_ratios=[2, 1])
ax = fig.add_subplot(gs[0, :])
ax2 = fig.add_subplot(gs[1, :])

fig.autofmt_xdate()
fig.tight_layout()

candlestick2_ohlc(
    ax,
    df["open"][start_index:end_index],
    df["high"][start_index:end_index],
    df["low"][start_index:end_index],
    df["close"][start_index:end_index],
    width=0.4,
    # colorup='r',
    # colordown='green'
)
plt.grid()
ax.plot(df['open_long'][start_index:end_index].reset_index(drop=True), c="yellow", marker='^', label='open long',
        markersize=12)
ax.plot(df['close_long'][start_index:end_index].reset_index(drop=True), c="blue", marker='^', label='close long',
        markersize=12)
ax.plot(df['open_short'][start_index:end_index].reset_index(drop=True), c="yellow", marker='v', label='open short',
        markersize=12)
ax.plot(df['close_short'][start_index:end_index].reset_index(drop=True), c="blue", marker='v', label='close short',
        markersize=12)
ax.plot(df['boll_up'][start_index:end_index].reset_index(drop=True), c='green', label='Boll Up')
ax.plot(df['boll_down'][start_index:end_index].reset_index(drop=True), c='orange', label='Boll Down')
ax.legend(loc='upper left')
# ax.set_xticks(range(0, end_index - start_index+1), 10)
ax.set_xticklabels(df['datetime'][start_index:end_index].reset_index(drop=True), rotation=30)
ax.set_xlabel('Datetime')
ax.set_ylabel('Price')

ax2.plot(df['rsi'][start_index:end_index].reset_index(drop=True), c='blue', label='RSI')
ax2.set_xticklabels(df['datetime'][start_index:end_index].reset_index(drop=True), rotation=30)
ax2.set_ylabel('RSI')
plt.show()

df.to_csv('trade_report.csv', index=False)
