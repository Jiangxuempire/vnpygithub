# _*_coding : UTF-8 _*_
# 开发团队 ：yunya
# 开发人员 ：Administrator
# 开发时间 : 2020/8/24 22:31
# 文件名称 ：协整分析.py
# 开发工具 ： PyCharm

# 加载模块
from datetime import datetime

# 统计分析
import pandas as pd
import numpy as np
from statsmodels.api import OLS
from statsmodels.tsa.stattools import coint

# 画图
import plotly.graph_objects as go

# 读数据
from vnpy.trader.database import database_manager
from vnpy.trader.utility import extract_vt_symbol
from vnpy.trader.constant import Interval


# 定义函数 读取合约代码  k 最高最低价是没意义的，只要收盘和开盘价
def load_symbol_data(vt_symbol, start, end):
	"""
	从数据库读取数据
	:param vt_symbol:
	:param start:
	:param end:
	:return:
	"""
	symbol, exchange = extract_vt_symbol(vt_symbol)		# XBTUSD.BITMEX 分离
	start = datetime.strptime(start, "%Y%m%d")
	end = datetime.strptime(end, "%Y%m%d")
	interval = Interval.MINUTE
	data = database_manager.load_bar_data(symbol, exchange, interval, start, end)  # 数据库读取数据

	dt_list = []
	close_list = []
	for bar in data:
		dt_list.append(bar.datetime)
		close_list.append(bar.close_price)

	s = pd.Series(close_list, index=dt_list)
	return s

def load_portfolio_data(vt_symbols, start, end):
	"""
	按时间对齐两个标的
	:param vt_symbols:
	:param start:
	:param end:
	:return:
	"""
	df = pd.DataFrame()
	for vt_symbol in vt_symbols:
		s = load_symbol_data(vt_symbol, start, end)
		df[vt_symbol] = s
	return df

def run_plotly(vt_symbols):
	"""
	# 绘制两个标的原始价格图表
	:param vt_symbols:
	:return:
	"""
	fig = go.Figure()

	for vt_symbol in vt_symbols:
		line = go.Scatter(y=df[vt_symbol], mode='lines', name=vt_symbol)
		fig.add_trace(line)

	fig.show()

if __name__ == '__main__':
	# 加载数据  如果 有少数据 df = df.dropna()
	# vt_symbols = ["XBTUSD.BITMEX", "btcusdt.BINANCE"]
	# vt_symbols = ["ethusdt.BINANCE", "btcusdt.BINANCE"]
	vt_symbols = ["BCH-USD-200925.OKEX", "BCH-USD-201225.OKEX"]
	start = "20200701"
	end = "20200825"

	# 读取数据
	print(f"读取数据。。{vt_symbols}")
	df = load_portfolio_data(vt_symbols, start, end)
	print(df)

	## 绘制两个标的原始价格图表
	run_plotly(vt_symbols)

	# 执行回归分析 最小二乘法  前面是y 后面是 x  y = ax + b
	# 使用np isnan 和isinf 来处理空值
	df[np.isnan(df)] = 0
	df[np.isinf(df)] = 0
	print(df)
	result = OLS(df[vt_symbols[0]], df[vt_symbols[-1]]).fit()
	print(result.summary())

	coef = 0.9994
	# 对残差绘图
	df["spread"] = df[vt_symbols[0]] - coef * df[vt_symbols[-1]]

	fig = go.Figure()
	line = go.Scatter(x=df.index, y=df["spread"], mode='lines', name="Spread")
	fig.add_trace(line)

	fig.show()

	# 执行协整检验
	# p-value如果小于0.05，则可以明确证明协整关系，但在实践中非常少见。
	# 价差整体上还是存在大量的均值偏移情况，但只要震荡回归的次数足够多，即使不满足协整也能通过交易盈利。
	score, pvalue, _ = coint(df[vt_symbols[0]], df[vt_symbols[-1]])
	print(f"p-value如果小于0.05，则可以明确证明协整关系，协整分析的p-value为：{pvalue}")