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
from vnpy.trader.constant import Interval, Direction


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

	min_window = 45
	open_window = 15
	rsi_length = 23
	kk_length = 80
	kk_dev = 2.0
	trading_size = 1
	atr_length = 30

	rsi_entry = 0
	kk_up = 0
	kk_down = 0
	long_stop = 0
	short_stop = 0
	rsi_value = 0
	rsi_up = 0
	rsi_dow = 0
	ema_mid = 0
	ema_length_new = 0
	current_ema_mid = 0
	last_ema_mid = 0
	current_close = 0
	last_close = 0
	front_close = 0
	exit_long = 0
	exit_short = 0
	long_entry = 0
	short_entry = 0
	long_stop_trade = 0
	short_stop_drade = 0
	exit_long_nex = 0
	exit_long_last = 0
	exit_short_nex = 0
	exit_short_last = 0
	atr_value = 0
	

	parameters = [
			"min_window",
			"open_window",
			"rsi_length",
			"ema_length",
			"trading_size",
			"atr_length",
	]

	variables = [
			"rsi_entry",
			"long_stop",
			"short_stop",
			"rsi_value",
			"rsi_up",
			"rsi_dow",
			"ema_mid",
			"ema_length_new",
			"current_ema_mid",
			"last_ema_mid",
			"current_close",
			"last_close",
			"front_close",
			"exit_long",
			"exit_short",
			"long_entry",
			"short_entry",
			"long_stop_trade",
			"short_stop_drade",
			"exit_long_nex",
			"exit_long_last",
			"exit_short_nex",
			"exit_short_last",
			"atr_value",
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

		self.bg_xminute = NewBarGenerator(
			on_bar=self.on_bar,
			window=self.min_window,
			on_window_bar=self.on_xminute_bar
		)
		self.am_xminute = ArrayManager(self.kk_length + 100)

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
		self.load_bar(30)

	def on_start(self):
		"""
		Callback when strategy is started.
		"""
		self.write_log("策略启动。。")

	def on_stop(self):
		"""
		Callback when strategy is stopped.
		"""
		self.write_log("策略停止。。")

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

		ema_mid_array = self.am_open.ema(self.kk_length,True)
		atr = self.am_open.atr(self.kk_length,True)
		kk_up_array = ema_mid_array + atr * self.kk_dev
		kk_down_array = ema_mid_array - atr * self.kk_dev

		self.ema_mid = ema_mid_array[-1]
		self.kk_up = kk_up_array[-1]
		self.kk_down = kk_down_array[-1]


		self.current_close = self.am_open.close[-1]
		self.last_close = self.am_open.close[-2]
		self.front_close = self.am_open.close[-3]

		if not self.pos:
			self.exit_long_nex = 0
			self.exit_long_last = 0
			self.exit_short_nex = 0
			self.exit_short_last = 0
			self.ema_length_new = self.kk_length

			self.atr_value = self.am_open.atr(self.atr_length)

			if self.rsi_entry > 0:
				self.buy(self.kk_up, self.trading_size, True)
				self.write_log(f"下多单：{bar.datetime}, {self.kk_up}, {self.trading_size}")

			elif self.rsi_entry < 0:
				self.short(self.kk_down, self.trading_size, True)
				self.write_log(f"下多单：{bar.datetime}, {self.kk_down}, {self.trading_size}")

		elif self.pos > 0:
			close_long = self.current_close > self.last_close > self.front_close
			if close_long:
				self.ema_length_new -= 1
				self.ema_length_new = max(self.ema_length_new, 5)

			ema_mid_new = self.am_xminute.sma(self.ema_length_new, True)
			self.current_ema_mid = ema_mid_new[-1]
			self.last_ema_mid = ema_mid_new[-2]
			# 仓位是long 时，如果价格下穿新布林中轨
			con1 = bar.close_price < self.current_ema_mid
			con2 = bar.close_price >= self.last_ema_mid
			if con1 and con2:
				self.exit_long_nex = bar.close_price  # 保存当前收盘价

				if self.exit_long_last == 0 or self.exit_long_nex > self.exit_long_last:
					self.exit_long_last = self.exit_long_nex
					self.ema_length_new = self.kk_length

					# 下穿新均线，以原布林均线挂出停止单，避免快速下跌而无法止损
					self.exit_long = self.ema_mid

				else:
					# 收盘价在两条均线平均价上方，以当前收盘价挂出限价单
					if bar.close_price > ((self.ema_mid + self.current_ema_mid) / 2):
						self.exit_long = bar.close_price

					elif bar.close_price < self.ema_mid:
						self.exit_long = bar.close_price

					else:
						self.exit_long = self.ema_mid
			# print(f"我是多单，收盘价在两个中轨均值下方，以原中轨挂止损单:{self.exit_long},")
			else:
				self.exit_long = self.ema_mid
			self.long_stop = max(self.exit_long,self.long_stop_trade)
			self.sell(self.long_stop, abs(self.pos), True)

		elif self.pos < 0:
			close_short = self.current_close < self.last_close < self.front_close
			if close_short:
				self.ema_length_new -= 1
				self.ema_length_new = max(self.ema_length_new, 5)

			ema_mid_new = self.am_xminute.sma(self.ema_length_new, True)
			self.current_ema_mid = ema_mid_new[-1]
			self.last_ema_mid = ema_mid_new[-2]

			# 仓位是short 时，如果价格上穿新布林中轨
			con1 = bar.close_price > self.current_ema_mid
			con2 = bar.close_price <= self.last_ema_mid
			if con1 and con2:
				self.exit_short_nex = bar.close_price
				if self.exit_short_last == 0 or self.exit_short_nex < self.exit_short_last:
					self.exit_short_last = self.exit_short_nex
					self.ema_length_new = self.kk_length

					self.exit_short = self.ema_mid

				else:
					if bar.close_price < (self.ema_mid + self.current_ema_mid / 2):
						self.exit_short = bar.close_price

					elif bar.close_price < self.ema_mid:
						self.exit_short = bar.close_price

					else:
						self.exit_short = self.ema_mid
			else:
				self.exit_short = self.ema_mid

			self.short_stop = min(self.exit_short,self.short_stop_drade)
			self.cover(self.short_stop, abs(self.pos), True)

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

		ema_array = talib.EMA(self.am_xminute.close, self.rsi_length)
		std_array = talib.EMA(self.am_xminute.close, self.rsi_length)

		dev_array = abs(self.am_xminute.close[:-1] - ema_array[:-1]) / std_array[:-1]
		dev_max = max(dev_array[-self.rsi_length:])

		rsi_array = talib.RSI(self.am_xminute.close[:-1], self.rsi_length)
		rsi_up_array = rsi_array + rsi_array * dev_max
		rsi_dow_array = rsi_array - rsi_array * dev_max

		self.rsi_value = self.am_xminute.rsi(self.rsi_length,True)
		self.rsi_up = rsi_up_array[-1]
		self.rsi_dow = rsi_dow_array[-1]

		current_rsi = self.rsi_value[-1]
		last_rsi = self.rsi_value[-2]
		current_rsi_up = rsi_up_array[-1]
		last_rsi_up = rsi_up_array[-2]
		current_rsi_down = rsi_dow_array[-1]
		last_rsi_down = rsi_dow_array[-2]
		
		con1 = current_rsi > current_rsi_up 
		con2 = last_rsi <= last_rsi_up
		con3 = current_rsi < current_rsi_down
		con4 = last_rsi >= last_rsi_down

		if con1 > con2:
			self.rsi_entry = 1		
		elif con3 and con4:
			self.rsi_entry = -1

		self.sync_data()

	def on_trade(self, trade: TradeData):
		"""
        Callback of new trade data update.
        """
		if trade.direction == Direction.LONG:
			self.long_entry = trade.price  # 成交最高价
			self.long_stop_trade = self.long_entry - 2 * self.atr_value
		else:
			self.short_entry = trade.price
			self.short_stop_drade = self.short_entry + 2 * self.atr_value

		self.sync_data()

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

