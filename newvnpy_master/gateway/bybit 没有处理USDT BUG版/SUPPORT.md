接口优化读取历史记录。

    def query_order(self, page: int = 1) -> Request:
        """"""
        if self.usdt_base:
            path = "/private/linear/order/list"
            symbols = symbols_usdt
        else:
            path = "/open-api/order/list"
            symbols = symbols_inverse

        for symbol in symbols:

            params = {
                "symbol": symbol,
                "limit": 50,
                "page": page,
                "order_status": "New,PartiallyFilled,Rejected,Cancelled"  # 增加订单状态判断，
            }

            self.add_request(
                "GET",
                path,
                callback=self.on_query_order,
                params=params
            )
