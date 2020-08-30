针对现货买入扣币为手续造成self.pos与实盘买到的币数量不等（少手续费量），按照self.pos量下单时被交易所拒单问题。

1、在 trader 里的 constant 常最中增加：
    class ExchangeMaterial(Enum):
    """
    Exchange.
    """
    OKEX_MATERIAL = "OKEX_MATERIAL"  # okex现货标记
    NONE = "None"

2、在 object 中的  TradeData 增加手续费 fee 字段
        @dataclass
    class TradeData(BaseData):
        """
        Trade data contains information of a fill of an order. One order
        can have several trade fills.
        """

        symbol: str
        exchange: Exchange
        orderid: str
        tradeid: str
        direction: Direction = None

        offset: Offset = Offset.NONE
        price: float = 0
        volume: float = 0
        fee: float = 0      #增加手续费
        datetime: datetime = None

        def __post_init__(self):
            """"""
            self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
            self.vt_orderid = f"{self.gateway_name}.{self.orderid}"
            self.vt_tradeid = f"{self.gateway_name}.{self.tradeid}"

3、在okex 交易所现货接口 OkexWebsocketApi 类中的 on_order 中的 trade返回字段 增加手续费返回

            trade = TradeData(
            symbol=order.symbol,
            exchange=order.exchange,
            orderid=order.orderid,
            tradeid=tradeid,
            direction=order.direction,
            price=float(d["last_fill_px"]),
            volume=float(trade_volume),
            datetime=generate_datetime(d["last_fill_time"]),
            gateway_name=self.gateway_name,
            fee=float(d["fee"]),        # 增加手续
        )

4、CTA 策略模版 template 的 CtaTemplate 的 __init__ 增加变更 
    self.exchangematerial = ExchangeMaterial.NONE # 增加判断现货接口逻辑

5、在策略里 重新返回 self.exchangematerial 字段

6、在cat策略引擎 CtaEngine 中  
    a 、定义变量 
        # 增加判断现货交易所
        EXCHANGE_MATERIAL = set([ExchangeMaterial.OKEX_MATERIAL,])
    b、在函数 process_trade_event中增加判断
            def process_trade_event(self, event: Event):
                """"""
                trade = event.data

                # Filter duplicate trade push
                if trade.vt_tradeid in self.vt_tradeids:
                    return
                self.vt_tradeids.add(trade.vt_tradeid)

                self.offset_converter.update_trade(trade)

                strategy = self.orderid_strategy_map.get(trade.vt_orderid, None)
                if not strategy:
                    return

                # Update strategy pos before calling on_trade method
                if trade.direction == Direction.LONG:
                    # 加入手续费
                    if strategy.exchangematerial in EXCHANGE_MATERIAL:
                    # if strategy.exchangematerial == ExchangeMaterial.OKEX_MATERIAL:
                        strategy.pos += (trade.volume + trade.fee)      # 加入手续费
                    else:
                        strategy.pos += trade.volume
                else:
                    strategy.pos -= trade.volume

                self.call_strategy_func(strategy, strategy.on_trade, trade)

                # Sync strategy variables to data file
                self.sync_strategy_data(strategy)

                # Update GUI
                self.put_strategy_event(strategy)

    c、在下单函数  send_order 中 对 volume 精度处理       
            def send_order(
                self,
                strategy: CtaTemplate,
                direction: Direction,
                offset: Offset,
                price: float,
                volume: float,
                stop: bool,
                lock: bool
            ):
                """
                """
                contract = self.main_engine.get_contract(strategy.vt_symbol)
                if not contract:
                    self.write_log(f"委托失败，找不到合约：{strategy.vt_symbol}", strategy)
                    return ""

                # Round order price and volume to nearest incremental value
                price = round_to(price, contract.pricetick)
                # volume = round_to(volume, contract.min_volume)
                # 判断是现货交易所，下单量的精度调整
                if strategy.exchangematerial in EXCHANGE_MATERIAL:
                    # 如果在列表里，下单量就不做任何四舍五入处理（原样）
                    pass
                else:
                    volume = round_to(volume, contract.min_volume)

                if stop:
                    if contract.stop_supported:
                        return self.send_server_stop_order(strategy, contract, direction, offset, price, volume, lock)
                    else:
                        return self.send_local_stop_order(strategy, direction, offset, price, volume, lock)
                else:
                    return self.send_limit_order(strategy, contract, direction, offset, price, volume, lock)  