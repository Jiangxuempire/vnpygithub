from typing import Any
import numpy as np
import talib

from vnpy.app.cta_strategy import (
	CtaTemplate,
	BarGenerator,
	ArrayManager,
	TickData,
	OrderData,
	BarData,
	TradeData,
	StopOrder
)
from vnpy.app.cta_strategy.new_strategy import NewBarGenerator
from vnpy.trader.constant import Interval


class RsiAdaptStrategy(CtaTemplate):
	"""
	策略逻辑：
	一、、过虑信号  （小时周期）
	使用rsiboll来判断信号强弱

	二、开单信号 （分钟周期）
	1、使用布林上下轨作为开单条件

	三、止损
	使用动态布林中轨止损

	"""
	author = "yunya"

	min_window = 15
	open_window = 5
	rsi_length = 15
	boll_length = 80
	boll_dev = 2.0
	trading_size = 1

	rsi_value = 0
	rsi_up = 0
	rsi_dow = 0
	rsi_entry = 0
	boll_up = 0
	boll_down = 0
	boll_mid = 0
	boll_length_new = 0
	current_boll_mid = 0
	last_boll_mid = 0
	current_close = 0
	last_close = 0
	front_close = 0
	exit_long = 0
	exit_short = 0
	exit_long_nex = 0
	exit_long_last = 0
	exit_short_nex = 0
	exit_short_last = 0
	

	parameters = [
			"min_window",
			"open_window",
			"rsi_length",
			"boll_length",
			"boll_dev",
			"trading_size",
	]

	variables = [
			"rsi_value",
			"rsi_up",
			"rsi_dow",
			"rsi_entry",
			"boll_up",
			"boll_down",
			"boll_mid",
			"boll_length_new",
			"current_boll_mid",
			"last_boll_mid",
			"current_close",
			"last_close",
			"front_close",
			"exit_long",
			"exit_short",
			"exit_long_nex",
			"exit_long_last",
			"exit_short_nex",
			"exit_short_last",
	]

	def __init__(
			self,
			cta_engine: Any,
			strategy_name: str,
			vt_symbol: str,
			setting: dict,
	):
		""""""
		super().__init__(cta_engine, strategy_name, vt_symbol, setting)

		self.atr_stop_array = np.zeros(10)

		self.bg_xminute = NewBarGenerator(
			on_bar=self.on_bar,
			window=self.min_window,
			on_window_bar=self.on_xminute_bar
		)
		self.am_xminute = ArrayManager(self.boll_length + 100)

		self.bg_open = NewBarGenerator(
			on_bar=self.on_bar,
			window=self.open_window,
			on_window_bar=self.on_5min_bar
		)
		self.am_open = ArrayManager()

	def on_init(self):
		"""
		Callback when strategy is inited.
		"""
		self.write_log("策略初始化。。")
		self.load_bar(10)

		self.put_event()

	def on_start(self):
		"""
		Callback when strategy is started.
		"""
		self.write_log("策略启动。。")
		self.put_event()

	def on_stop(self):
		"""
		Callback when strategy is stopped.
		"""
		self.write_log("策略停止。。")
		self.put_event()

	def on_tick(self, tick: TickData):
		"""
		Callback of new tick data update.
		"""
		self.bg_open.update_tick(tick)

	def on_bar(self, bar: BarData):
		"""
		Callback of new bar data update.
		"""
		self.bg_xminute.update_bar(bar)
		self.bg_open.update_bar(bar)

	def on_5min_bar(self, bar: BarData):
		"""
		:param bar: 
		:type bar: 
		:return: 
		:rtype: 
		"""
		self.cancel_all()
		self.am_open.update_bar(bar)

		if not self.am_open.inited or not self.am_xminute.inited:
			return

		if not self.pos:
			if self.rsi_entry > 0:
				self.buy(self.boll_up, self.trading_size, True)
			# print(bar.datetime, self.boll_up, self.trading_size)
			# print(bar.datetime, self.entry_up, self.trading_size, bar)

			elif self.rsi_entry < 0:
				self.short(self.boll_down, self.trading_size, True)

		elif self.pos > 0:
			# 仓位是long 时，如果价格下穿新布林中轨
			con1 = bar.close_price < self.current_boll_mid
			con2 = bar.close_price >= self.last_boll_mid
			if con1 and con2:
				self.exit_long_nex = bar.close_price  # 保存当前收盘价

				if self.exit_long_last == 0 or self.exit_long_nex > self.exit_long_last:
					self.exit_long_last = self.exit_long_nex
					self.boll_length_new = self.boll_length

					# 下穿新均线，以原布林均线挂出停止单，避免快速下跌而无法止损
					self.exit_long = self.boll_mid

				else:
					# 收盘价在两条均线平均价上方，以当前收盘价挂出限价单
					if bar.close_price > ((self.boll_mid + self.current_boll_mid) / 2):
						self.exit_long = bar.close_price

					elif bar.close_price < self.boll_mid:
						self.exit_long = bar.close_price

					else:
						self.exit_long = self.boll_mid
			# print(f"我是多单，收盘价在两个中轨均值下方，以原中轨挂止损单:{self.exit_long},")
			else:
				self.exit_long = self.boll_mid
			self.sell(self.exit_long, abs(self.pos), True)

		elif self.pos < 0:
			# 仓位是short 时，如果价格上穿新布林中轨
			con1 = bar.close_price > self.current_boll_mid
			con2 = bar.close_price <= self.last_boll_mid
			if con1 and con2:
				self.exit_short_nex = bar.close_price
				if self.exit_short_last == 0 or self.exit_short_nex < self.exit_short_last:
					self.exit_short_last = self.exit_short_nex
					self.boll_length_new = self.boll_length

					self.exit_short = self.boll_mid

				else:
					if bar.close_price < (self.boll_mid + self.current_boll_mid / 2):
						self.exit_short = bar.close_price

					elif bar.close_price < self.boll_mid:
						self.exit_short = bar.close_price

					else:
						self.exit_short = self.boll_mid
			else:
				self.exit_short = self.boll_mid
			self.cover(self.exit_short, abs(self.pos), True)

		self.sync_data()
		self.put_event()

	def on_xminute_bar(self, bar: BarData):
		"""
		:param bar:
		:return:
		"""
		self.am_xminute.update_bar(bar)
		if not self.am_xminute.inited:
			return

		rsi_array = talib.RSI(self.am_xminute.close[:-1], self.rsi_length)
		ema_array = talib.EMA(self.am_xminute.close, self.rsi_length)

		dev_array = abs(self.am_xminute.close[:-1] - ema_array[:-1]) / rsi_array

		rsi_up_array = rsi_array + rsi_array * dev_array
		rsi_dow_array = rsi_array - rsi_array * dev_array

		self.rsi_value = self.am_xminute.rsi(self.rsi_length)
		self.rsi_up = rsi_up_array[-1]
		self.rsi_dow = rsi_dow_array[-1]

		current_rsi_up = rsi_up_array[-1]
		current_rsi_down = rsi_dow_array[-1]

		if self.rsi_value > current_rsi_up:
			self.rsi_entry = 1
		elif self.rsi_value < current_rsi_down:
			self.rsi_entry = -1

		self.boll_up, self.boll_down = self.am_xminute.boll(self.boll_length, self.boll_dev)
		self.boll_mid = self.am_xminute.sma(self.boll_length)

		self.current_close = self.am_xminute.close[-1]
		self.last_close = self.am_xminute.close[-2]
		self.front_close = self.am_xminute.close[-3]

		if self.pos == 0:
			self.exit_long_nex = 0
			self.exit_long_last = 0
			self.exit_short_nex = 0
			self.exit_short_last = 0
			self.boll_length_new = self.boll_length

		elif self.pos > 0:
			# 上涨或下跌时，布林中轨均值减1
			close_long = self.current_close > self.last_close > self.front_close
			if close_long:
				self.boll_length_new -= 1
				self.boll_length_new = max(self.boll_length_new, 5)

		elif self.pos < 0:
			close_short = self.current_close < self.last_close < self.front_close
			if close_short:
				self.boll_length_new -= 1
				self.boll_length_new = max(self.boll_length_new, 5)

		boll_mid_new = self.am_xminute.sma(self.boll_length_new,True)
		self.current_boll_mid = boll_mid_new[-1]
		self.last_boll_mid = boll_mid_new[-2]

		self.sync_data()

	def on_trade(self, trade: TradeData):
		"""
		有成交时
		Callback of new trade data update.
		"""
		self.put_event()

	def on_order(self, order: OrderData):
		"""
		订单更新回调
		Callback of new order data update.
		"""

		self.put_event()

	def on_stop_order(self, stop_order: StopOrder):
		"""
		Callback of stop order update.
		"""
		self.put_event()

