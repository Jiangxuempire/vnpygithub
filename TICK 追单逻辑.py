# _*_coding : UTF-8 _*_
# 开发团队 ：yunya
# 开发人员 ：yunya
# 开发时间 : 2020/8/8 17:04
# 文件名称 ：TICK 追单逻辑.py
# 开发工具 ： PyCharm

"""
第一步：修改 orderdata

		@dataclass
		class OrderData(BaseData):
		    """
		    # Order data contains information for tracking lastest status
		    # of a specific order.
		    """
		
		    symbol: str
		    exchange: Exchange
		    orderid: str
		
		    type: OrderType = OrderType.LIMIT
		    direction: Direction = Direction.NET  # 净持仓
		    offset: Offset = Offset.NONE
		    price: float = 0
		    volume: float = 0
		    traded: float = 0
		    status: Status = Status.SUBMITTING   # 提交交中
		    datetime: datetime = None
		
		    cancel_time: str = ""
		    def __post_init__(self):
		        """"""
		        self.vt_symbol = f"{self.symbol}_{self.exchange.value}/{self.gateway_name}"
		        self.vt_orderid = f"{self.gateway_name}_{self.orderid}"
		        #未成交量
		        self.untrade = self.volume - self.traded
		
		    def is_active(self) -> bool:
		        """
		        # Check if the order is active.
		        """
		        if self.status in ACTIVE_STATUSES:
		            return True
		        else:
		            return False
		
		    def create_cancel_request(self) -> "CancelRequest":
		        """
		        # Create cancel request object from order.
		        """
		        req = CancelRequest(
		            orderid=self.orderid, symbol=self.symbol, exchange=self.exchange
		        )
		        return req
		        
第二步： 策略init初始化参数
		#状态控制初始化
        self.chase_long_trigger = False
        self.chase_sell_trigger = False
        self.chase_short_trigger = False
        self.chase_cover_trigger = False  
        self.cancel_status = False
        self.long_trade_volume = 0
        self.short_trade_volume = 0
        self.sell_trade_volume = 0
        self.cover_trade_volume = 0 
        self.chase_interval   =    10    #拆单间隔:秒
        
        
第三步：

	 def on_tick(self, tick: TickData):
        working_order_dict = self.get_position_detail(tick.vt_symbol).active_orders
        #working_order_dict = self.order_dict
        if working_order_dict:
            #委托完成状态
            order_finished = False
            vt_orderid = list(working_order_dict.items())[0][0]         #委托单vt_orderid
            working_order = list(working_order_dict.items())[0][1]      #委托单字典 
            #开平仓追单，部分交易没有平仓指令(Offset.NONE)
            # """获取到未成交委托单后检查未成交委托量>0,tick.datetime - 未成交委托单的datetime>追单间隔(chase_interval),同时chase_long_trigger状态未触发和有vt_orderid的判定(之前有收过空vt_orderid,所有要加个过滤),撤销该未成交委托单,赋值chase_long_trigger为True.chase_long_trigger为True且没有未成交委托单时执行追单,如有未成交委托单则调用cancel_surplus_order取消所有未成交委托单,追单的委托单发送出去后初始化chase_long_trigger.其他方向的撤单追单也是一样的流程"""
            if working_order.offset in (Offset.NONE,Offset.OPEN):
                if working_order.direction == Direction.LONG:
                    self.long_trade_volume = working_order.untrade
                    if (tick.datetime - working_order.datetime).seconds > self.chase_interval and self.long_trade_volume > 0 and (not self.chase_long_trigger) and vt_orderid:
                        #撤销之前发出的未成交订单
                        self.cancel_order(vt_orderid)
                        self.chase_long_trigger = True
                elif working_order.direction == Direction.SHORT:
                    self.short_trade_volume = working_order.untrade
                    if (tick.datetime - working_order.datetime).seconds > self.chase_interval and self.short_trade_volume > 0 and (not self.chase_short_trigger) and vt_orderid:  
                        self.cancel_order(vt_orderid)
                        self.chase_short_trigger = True
            #平仓追单
            elif working_order.offset in (Offset.CLOSE,Offset.CLOSETODAY):
                if working_order.direction == Direction.SHORT: 
                    self.sell_trade_volume = working_order.untrade
                    if (tick.datetime - working_order.datetime).seconds > self.chase_interval and self.sell_trade_volume > 0 and (not self.chase_sell_trigger) and vt_orderid: 
                        self.cancel_order(vt_orderid)
                        self.chase_sell_trigger = True                                                    
                if working_order.direction == Direction.LONG:
                    self.cover_trade_volume = working_order.untrade
                    if (tick.datetime - working_order.datetime).seconds > self.chase_interval and self.cover_trade_volume > 0 and (not self.chase_cover_trigger) and vt_orderid:                                                       
                        self.cancel_order(vt_orderid)
                        self.chase_cover_trigger = True   
        else:
            order_finished = True
            self.cancel_status = False
        if self.chase_long_trigger:
            if order_finished:
                self.buy(tick.ask_price_1,self.long_trade_volume)
                self.chase_long_trigger = False  
            else:
                self.cancel_surplus_order(list(working_order_dict))
        elif self.chase_short_trigger:
            if  order_finished:
                self.short(tick.bid_price_1,self.short_trade_volume)
                self.chase_short_trigger = False 
            else:
                self.cancel_surplus_order(list(working_order_dict))
        elif self.chase_sell_trigger:
            if order_finished:
                self.sell(tick.bid_price_1,self.sell_trade_volume)
                self.chase_sell_trigger = False                      
            else:
                self.cancel_surplus_order(list(working_order_dict))
        elif self.chase_cover_trigger:
            if order_finished:
                self.cover(tick.ask_price_1,self.cover_trade_volume)
                self.chase_cover_trigger = False
            else:
                self.cancel_surplus_order(list(working_order_dict))
    #------------------------------------------------------------------------------------
    def cancel_surplus_order(self,orderids:list):
        """
        # 撤销剩余活动委托单
        """
        if not self.cancel_status:
            for vt_orderid in  orderids:
                self.cancel_order(vt_orderid)
            self.cancel_status = True

"""







from typing import Any
import numpy as np
from vnpy.trader.constant import Direction, Interval, Offset

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


class AtrStop_Ut(CtaTemplate):
	""""""
	author = "yunya"

	atrstop_window = 46
	open_window = 5
	nloss_singnal = 2.7
	trailing_tax = 2.0
	risk_level = 5000
	exit_dc_length = 50
	atr_length = 30

	atrstop_entry = 0
	current_atr_stop = 0.0
	last_atr_stop = 0.0
	intra_trade_high = 0
	intra_trade_low = 0
	nloss_array = 0.0
	long_stop = 0
	short_stop = 0
	trading_size = 0
	exit_down = 0
	exit_up = 0
	ask = 0
	bid = 0
	atr_value = 0
	count = 0

	parameters = [
		"atrstop_window",
		"open_window",
		"nloss_singnal",
		"trailing_tax",
		"risk_level",
		"exit_dc_length",
		"atr_length"
	]

	variables = [
		"atrstop_entry",
		"current_atr_stop",
		"last_atr_stop",
		"intra_trade_high",
		"intra_trade_low",
		"long_stop",
		"short_stop",
		"exit_down",
		"exit_up",
		"trading_size",
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

		self.bg_xmin = NewBarGenerator(
			self.on_bar,
			window=self.atrstop_window,
			on_window_bar=self.on_xmin_bar,
			interval=Interval.MINUTE
		)
		self.am_xmin = ArrayManager()

		self.bg_5min = BarGenerator(
			self.on_bar,
			window=self.open_window,
			on_window_bar=self.on_5min_bar
		)
		self.am_5min = ArrayManager(self.exit_dc_length * int(self.atr_length / self.open_window) + 10)

		self.inited_atr_stop = False

		# 状态控制初始化
		self.chase_long_trigger = False
		self.chase_sell_trigger = False
		self.chase_short_trigger = False
		self.chase_cover_trigger = False
		self.cancel_status = False
		self.long_trade_volume = 0
		self.short_trade_volume = 0
		self.sell_trade_volume = 0
		self.cover_trade_volume = 0
		self.chase_interval = 10  # 拆单间隔:秒

	def on_init(self):
		"""
		Callback when strategy is inited.
		"""
		self.write_log("策略初始化。。")
		self.load_bar(10)

	# self.put_event()

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
		working_order_dict = self.get_position_detail(tick.vt_symbol).active_orders
		# working_order_dict = self.order_dict
		if working_order_dict:
			# 委托完成状态
			order_finished = False
			vt_orderid = list(working_order_dict.items())[0][0]  # 委托单vt_orderid
			working_order = list(working_order_dict.items())[0][1]  # 委托单字典
			# 开平仓追单，部分交易没有平仓指令(Offset.NONE)
			"""获取到未成交委托单后检查未成交委托量>0,tick.datetime - 未成交委托单的datetime>追单间隔(chase_interval),
			同时chase_long_trigger状态未触发和有vt_orderid的判定(之前有收过空vt_orderid,所有要加个过滤),撤销该未成交委托单,
			赋值chase_long_trigger为True.chase_long_trigger为True且没有未成交委托单时执行追单,
			如有未成交委托单则调用cancel_surplus_order取消所有未成交委托单,追单的委托单发送出去后初始化chase_long_trigger.
			其他方向的撤单追单也是一样的流程"""
			if working_order.offset in (Offset.NONE, Offset.OPEN):
				if working_order.direction == Direction.LONG:
					self.long_trade_volume = working_order.untrade
					if (
							tick.datetime - working_order.datetime).seconds > self.chase_interval and self.long_trade_volume > 0 and (
					not self.chase_long_trigger) and vt_orderid:
						# 撤销之前发出的未成交订单
						self.cancel_order(vt_orderid)
						self.chase_long_trigger = True
				elif working_order.direction == Direction.SHORT:
					self.short_trade_volume = working_order.untrade
					if (
							tick.datetime - working_order.datetime).seconds > self.chase_interval and self.short_trade_volume > 0 and (
					not self.chase_short_trigger) and vt_orderid:
						self.cancel_order(vt_orderid)
						self.chase_short_trigger = True
			# 平仓追单
			elif working_order.offset in (Offset.CLOSE, Offset.CLOSETODAY):
				if working_order.direction == Direction.SHORT:
					self.sell_trade_volume = working_order.untrade
					if (
							tick.datetime - working_order.datetime).seconds > self.chase_interval and self.sell_trade_volume > 0 and (
					not self.chase_sell_trigger) and vt_orderid:
						self.cancel_order(vt_orderid)
						self.chase_sell_trigger = True
				if working_order.direction == Direction.LONG:
					self.cover_trade_volume = working_order.untrade
					if (
							tick.datetime - working_order.datetime).seconds > self.chase_interval and self.cover_trade_volume > 0 and (
					not self.chase_cover_trigger) and vt_orderid:
						self.cancel_order(vt_orderid)
						self.chase_cover_trigger = True
		else:
			order_finished = True
			self.cancel_status = False
		if self.chase_long_trigger:
			if order_finished:
				self.buy(tick.ask_price_1, self.long_trade_volume)
				self.chase_long_trigger = False
			else:
				self.cancel_surplus_order(list(working_order_dict))
		elif self.chase_short_trigger:
			if order_finished:
				self.short(tick.bid_price_1, self.short_trade_volume)
				self.chase_short_trigger = False
			else:
				self.cancel_surplus_order(list(working_order_dict))
		elif self.chase_sell_trigger:
			if order_finished:
				self.sell(tick.bid_price_1, self.sell_trade_volume)
				self.chase_sell_trigger = False
			else:
				self.cancel_surplus_order(list(working_order_dict))
		elif self.chase_cover_trigger:
			if order_finished:
				self.cover(tick.ask_price_1, self.cover_trade_volume)
				self.chase_cover_trigger = False
			else:
				self.cancel_surplus_order(list(working_order_dict))

	# ------------------------------------------------------------------------------------
	def cancel_surplus_order(self, orderids: list):
		"""
		撤销剩余活动委托单
		"""
		if not self.cancel_status:
			for vt_orderid in orderids:
				self.cancel_order(vt_orderid)
			self.cancel_status = True

	def on_bar(self, bar: BarData):
		"""
		Callback of new bar data update.
		"""
		self.bg_xmin.update_bar(bar)
		self.bg_5min.update_bar(bar)

	def on_5min_bar(self, bar: BarData):

		self.cancel_all()
		self.am_5min.update_bar(bar)

		if not self.am_5min.inited or not self.am_xmin.inited:
			return
		if self.atr_stop_array[-3] == 0:
			return

		self.exit_up, self.exit_down = self.am_5min.donchian(
			self.exit_dc_length * int(self.atr_length / self.open_window))

		# print(f"dc上轨：{self.exit_up},下轨：{self.exit_down}")

		if not self.pos:
			self.intra_trade_high = bar.high_price
			self.intra_trade_low = bar.low_price

			if self.atrstop_entry > 0:
				self.buy(self.current_atr_stop, self.trading_size, True)

			elif self.atrstop_entry < 0:
				self.short(self.current_atr_stop, self.trading_size, True)

		elif self.pos > 0:
			self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
			long_high = self.intra_trade_high * \
			            (1 - self.trailing_tax / 100)
			self.long_stop = max(self.exit_down, long_high)
			self.sell(self.long_stop, abs(self.pos), True)

		else:
			self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
			short_low = self.intra_trade_low * \
			            (1 + self.trailing_tax / 100)
			self.short_stop = min(self.exit_up, short_low)
			self.cover(self.short_stop, abs(self.pos), True)

		self.put_event()

	def on_xmin_bar(self, bar: BarData):
		""""""
		am_xmin = self.am_xmin
		am_xmin.update_bar(bar)

		self.atr_stop_array[:-1] = self.atr_stop_array[1:]

		if not am_xmin.inited:
			return

		# 计算轨道线 nloss
		self.nloss_array = am_xmin.atr(30, array=True) * self.nloss_singnal

		# 计算轨道线
		self.atr_stop_array = self.atrstop(
			am_xmin.close,
			self.atr_stop_array,
			self.nloss_array
		)

		# 初始化 atr_stop_array 保证前三个有值
		if self.count < 4:
			self.count += 1
			return

		self.current_atr_stop = self.atr_stop_array[-1]
		self.last_atr_stop = self.atr_stop_array[-2]
		current_bar = self.am_xmin.close[-1]

		if self.current_atr_stop > self.last_atr_stop and current_bar > self.current_atr_stop:
			self.atrstop_entry = 1
		elif self.current_atr_stop < self.last_atr_stop and current_bar < self.current_atr_stop:
			self.atrstop_entry = -1
		else:
			self.atrstop_entry = 0

		if self.pos == 0:
			self.atr_value = self.am_xmin.atr(self.atr_length)
			self.trading_size = max(int(self.risk_level / self.atr_value), 1)

		self.sync_data()
		self.put_event()

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

	def atrstop(self, close, atrstop, nlossatr):

		# 计算轨道线
		if (close[-1] > atrstop[-2]) and (close[-2] > atrstop[-2]):
			atrstop[-1] = max(atrstop[-2], close[-1] - nlossatr[-1])

		elif (close[-1] < atrstop[-2]) and (close[-2] < atrstop[-2]):
			atrstop[-1] = min(atrstop[-2], close[-1] + nlossatr[-1])

		elif (close[-1] > atrstop[-2]):
			atrstop[-1] = (close[-1] - nlossatr[-1])

		else:
			atrstop[-1] = (close[-1] + nlossatr[-1])

		return atrstop


