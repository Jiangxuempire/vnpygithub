# _*_coding : UTF-8 _*_
#开发团队 ：yunya
#开发人员 ：Administrator
#开发时间 : 2020/7/25 21:20
#文件名称 ：vnpy小班培训课程回顾重点.py
#开发工具 ： PyCharm
"""
1、导入数据时，vnpy会自动检查原有数据去重，

2、适用CTA策略的品种：数字货币、期货、股票

3、期货 888 产品来回测

4、回测时，使用总收益和日均盈亏  回撤比会过拟合

5、交易所如果关机维护，策略也关闭停止自动交易功能，避免中间出现数据问题

6、策略可以二次继承  参考 TargetPosTemplate（官方案例）

7、策略实盘 on_init 中的 初始化 self.boad_bar(10) 最好多加几天，因实盘时是交易日（扣掉假期）

8、数据容器 写在策略类的 init 里面 如果： self.atr_stop_array = np.zeros(50)

9、 on_stop 可以增加把成交记录写到 on_stop函数

10、get_engine_type 查询状态，实盘、回测

11、 get_priretick   当前一跳函数

12、vnpy默认合成为被60整除，如果小时，不能使用 60分钟，

13、 使用 计数方式来判断 np容器是否初始化完
        self.count += 1
        if not self.inited and self.count >= self.size:
            self.inited = True

        self.open_array[:-1] = self.open_array[1:]

14、mongodb 默认是可以不用设置密码的，如果部署在服务器上，要增加密码和修改默认端口，来保证安全！

15、最大回撤是来考虑实盘时的初始仓位，假设一开始就亏损，如果最大回撤是30%，那本金回撤30%的假设。用来计算初始设置的使用资金量

16、样本内占 三分二或四分三  样本外 三分一

17、资金曲线  稳定向上   前期向上后期走平  前期走平后期向上     前期向上后期走平 这个策略最不合适实盘   最好的是稳定向上

18、先用前8年的数据优化出结果，使用后2年的数据验证；实盘的时候再使用最近8年的数据验证没问题后上实盘

19、sync_data 函数保存当前计算指标数据到硬盘里  variables 这里定义的才保存

20、 vt_orderid = buy(bar.close.price,self.pos,True)
     print(bar.datetime, self.entry_up, self.trading_size, bar)
     可以通过vt_orderid区分，下单时候在on_order获取，然后on_trade时候比对区分 下停止单后那些是成交的，那些没有成交

21、最后一笔成交价 做为固定止损价的位置
    if trade.direction == Direction.LONG:
            self.long_entry = trade.price  # 成交最高价
            self.long_stop = self.long_entry - 2 * self.atr_value
        else:
            self.short_entry = trade.price
            self.short_stop = self.short_entry + 2 * self.atr_value

        self.sync_data()

22、正向反向合约参数：

           def set_parameters(
        self,
        vt_symbol: str,
        interval: Interval,
        start: datetime,
        rate: float,
        slippage: float,
        size: float,
        pricetick: float,
        capital: int = 0,
        end: datetime = None,
        mode: BacktestingMode = BacktestingMode.BAR,
        inverse: bool = False   # 默认正向合约，True为反向合约
    ):

23、如果交易所接口请求次数被限制，那么在交易所接口 BybitGateway 类的 process_timer_event 函数 中增加计算
        count = 0
        def process_timer_event(self, event):
        """"""
            self.count +=1
            if self.count >=2:
                self.query_position()
                self.count = 0


24、 布林带新思路 刑不行分享会的 吕洋分享在论坛上
1、进场过滤，就是现在收盘价比之前第N跟K线的收盘的大还是小，如果做多，那就应该是大。反之亦然，以此来达到简单过滤的目地。
   不要小看这一个逻辑，屏蔽掉大约20%虚假信号，我算过。
2、进场并不是收盘价上穿上轨，下一个K线的开盘价开多的模式。而是在过滤后，最高价大于前一个K线的布林上轨，按照上轨价格发单开多，
    如果遇到第一个K开盘跳空那种，直接追多，按照开盘和前一个K线的布林上轨最大值开多。
3、出场中轨加速度，当没有持仓时候不变，当有多单的时候，参数liqPoint 减去一，每一个新K，liqPoint都减去一，假设我们有多单，
    在早上开盘后，9：15之后 第一个15分钟K刷新了，假设我们的liqPoint初始是20然后减去一，是19。逐次往后推，如果上涨的趋势一直都在，
    并且很流畅，那么每一个新K线后，18、17、16、15…… 这个数字会越来越小，当然了，会有一个下限，有可能一直到这个下限，如果行情很完美配合的话。
    那么这个均线就会越来越敏感，因为周期变小了吗啊。以此达到加速中轨止盈止损的目地。

self.cta_engine.main_engine.get_account("xxx")  # XXXX 是 要查的vt_vt_symbol


from vnpy.app.cta_strategy.base import StopOrderStatus
    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        self.long_stop_orderids = []       #多开活动停止单ID列表
    #------------------------------------------------------------------------------------
    def on_tick(self, tick: TickData):
        #提供多开下单基于委托ID的细粒度控制，其他方向下单相似
        if not self.pos:
            if not self.long_stop_orderids :
                stop_orderid= self.buy(tick.last_price,self.fixed_size,True)
                if stop_orderid:
                    self.long_stop_orderids.extend(stop_orderid)
    #------------------------------------------------------------------------------------
    def on_stop_order(self, stop_order: StopOrder):
        """
        收到停止单回报
        """
        #委托列表删除停止单ID
        if stop_order.status != StopOrderStatus.WAITING:
            if stop_order.stop_orderid in self.long_stop_orderids:
                self.long_stop_orderids .remove(stop_order.stop_orderid)

"""

# _*_coding : utf_8 _*_


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
import talib
from vnpy.trader.constant import Interval, Direction

from time import time
from vnpy.app.cta_strategy.new_strategy import NewBarGenerator
# 判断是实盘还是回测
from vnpy.app.cta_strategy.base import EngineType

from vnpy.app.cta_strategy.base import StopOrderStatus


class TestStrategy(CtaTemplate):
    """"""
    author = " "
    # 定义类的属性是所有实例之间共享，  如： atr_length = 10
    # 实例属性是类方法的属性，只能在当前实例中使用
    # 如果要单独在实例中使用的属性，请在 init 中去定义  如：self.trades = []


    parameters = [

    ]# 策略参数


    variables = [

    ]# 定义的变量名




    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.long_stop_orderids = []  # 多开活动停止单ID列表

        #  如：我把成交记录全部记录下来，然后在点停止策略时保存到本地 策略内部要用到的，并不想在图形页面上看到，
        #  可以写到init 函数里面 因python类的可变和不可变对象问题，所以在init里写，可以保证不会差错
        self.trades = []

    def on_init(self):
        """
        图形界面上点策略 初始化 时，运行init这个函数

        这里写所有要 初始化 时要运行的内容


        Callback when strategy is inited.

        okex 火币等只能获取一天一分钟K线的交易所，

        1、用DataRecorder录制行情到数据库

        2、load_bar 可选参数 use_database=True，强制从数据库载入
        """
        # 如：
        self.rsi_buy = 50 + self.rsi_entry
        self.rsi_buy = 50 - self.rsi_entry

        self.load_bar(10)

        self.write_log("策略初始化")

        # 强制清空初始化的持仓
        self.target_pos = 0

    def on_start(self):
        """
        图形页面点 策略启动  时运行 start

        Callback when strategy is started.
        1、启动策略时，可以调用python 支持的任意外部数据
        """
        # 如：可以链接一个  redis 数据库 或 联接交易所获取交易所数据。
        # 这里都可以写
        self.redis()


        self.write_log("策略启动")
        self.send_email()



    def on_stop(self):
        """
        点停止时，把成交记录保存到本地
        Callback when strategy is stopped.
        """
        #如：我把成交记录全部记录下来，然后在点停止策略时保存到本地 策略内部要用到的，并不想在图形页面上看到，

        with open("trade_result.txt") as f:
            for trade in self.trades:
                f.write(str(trade)) # 以字符串形式保存

        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        交易所每次成交推送

        Callback of new tick data update.
        """

        # self.bg.update_tick(tick)

        #提供多开下单基于委托ID的细粒度控制，其他方向下单相似
        if not self.pos:
            if not self.long_stop_orderids :
                stop_orderid= self.buy(tick.last_price,self.fixed_size,True)
                if stop_orderid:
                    self.long_stop_orderids.extend(stop_orderid)




        if self.test_all_done:
            return

        self.last_tick = tick

        self.tick_count += 1
        if self.tick_count >= self.test_trigger:
            self.tick_count = 0

            if self.funcs:
                test_func = self.funcs.pop(0)

                start = time()
                test_func()
                time_cost = (time() - start) * 1000
                self.write_log("耗时%s毫秒" % (time_cost))
            else:
                self.write_log("测试已全部完成")
                self.test_all_done = True

        self.put_event()

    def on_bar(self, bar: BarData):
        """
        每分钟推送一根 k 线
        Callback of new bar data update.

        一、使用 max min 来整合移动止损和其他价格。如在币林带策略中，
        使用K线最高价回撤一定比例来止损，同时使用价格回到中轨止盈，可以整合到一起

        二、锚定真实开仓位  基于 on_trade 推送的成交数据来实盘

        三、如果使用长期发出信号，短周期下单，要增加判断长周期信号是否生成，代码如下：

        if not self.long_initde or not self.short_initde :
            return

        四、 在K线合成先后顺序上，如果希望长周期出信号后立即下单，就把长周期合成放在前面，先合成 如下：
        def on_bar(self, bar: BarData):

            self.bg15.update_bar(bar)
            self.bg5.update_bar(bar)

        五、把止损位的值在空仓时，重新初始化
        if self.pos == 0:
            self.long_stop = 0
            self.short_stop = 0

        六、判断是实盘还是回测
            if self.engine_type != EngineType.LIVE:
                return

            if self.engine_type == EngineType.BACKTESTING:
                self.buy(bar.close_price + 5, self.trading_size)
            else:
                self.target_pos = self.trading_size

        """

        pass

    def on_order(self, order: OrderData):
        """
         交易所委托推送，如果是本地还没推送到交易所，显示 提交中，如果交易所已经收到委托，返回显示 未成交   如有部分成交，显示  部份成交
        如果订单提交的数据不满足交易所要求，会显示 拒单
        Callback of new order data update.
        在策略里，创建一个参数，比如my_pos
        在on_trade里，基于trade.direction和trade.volume，来计算这个my_pos
        然后下单做逻辑判断的时候，都用这个my_pos，而不是自带的self.pos
        my_pos可以在图形界面直接修改

        """

        pass
        # self.put_event()

    def on_trade(self, trade: TradeData):
        """
        交易所成交推送
        Callback of new trade data update.
        """
        if self.pos != 0:
            if trade.direction == Direction.LONG:
                self.long_entry = trade.price
                self.long_tp = self.long_entry + self.fixed_tp
            else:
                self.short_entry = trade.price
                self.short_tp = self.short_entry - self.fixed_tp

        # 如：我把成交记录全部记录下来，然后在点停止策略时保存到本地
        self. trades.append(trade)


        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        """
        收到停止单回报
        """
        # 委托列表删除停止单ID
        if stop_order.status != StopOrderStatus.WAITING:
            if stop_order.stop_orderid in self.long_stop_orderids:
                self.long_stop_orderids.remove(stop_order.stop_orderid)

    def market_order(self):
        """"""
        pass
        # self.buy(self.last_tick.limit_up, 1)
        # self.write_log("执行市价单测试")

    def limit_order(self):
        """"""
        pass
        # self.buy(self.last_tick.limit_down, 1)
        # self.write_log("执行限价单测试")

    def stop_order(self):
        """"""
        pass
        # self.buy(self.last_tick.ask_price_1, 1, True)
        # self.write_log("执行停止单测试")

    def cancel_all(self):
        """"""
        pass
        # self.cancel_all()
        # self.write_log("执行全部撤单测试")











