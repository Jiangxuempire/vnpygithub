"""
火币合约接口
"""

import re
import urllib
import base64
import json
import zlib
import hashlib
import hmac
import sys
from copy import copy
from datetime import datetime, timedelta
from threading import Lock
from typing import Sequence, Tuple
import pytz
from typing import Dict, List, Any

from vnpy.event import Event
from vnpy.api.rest import RestClient, Request
from vnpy.api.websocket import WebsocketClient
from vnpy.trader.constant import (
    Direction,
    Offset,
    Exchange,
    Product,
    Status,
    OrderType,
    Interval
)
from vnpy.trader.gateway import BaseGateway
from vnpy.trader.object import (
    TickData,
    OrderData,
    TradeData,
    BarData,
    AccountData,
    PositionData,
    ContractData,
    OrderRequest,
    CancelRequest,
    SubscribeRequest,
    HistoryRequest
)
from vnpy.trader.event import EVENT_TIMER

REST_HOST = "https://api.hbdm.com"
WEBSOCKET_DATA_HOST = "wss://api.hbdm.com/swap-ws"  # Market Data
WEBSOCKET_TRADE_HOST = "wss://api.hbdm.com/swap-notification"  # Account and Order

STATUS_HUOBIS2VT: Dict[int, Status] = {
    3: Status.NOTTRADED,
    4: Status.PARTTRADED,
    5: Status.CANCELLED,
    6: Status.ALLTRADED,
    7: Status.CANCELLED,
}


ORDERTYPE_VT2HUOBIS: Dict[OrderType, Any] = {
    OrderType.MARKET: "opponent",
    OrderType.LIMIT: "limit",
    OrderType.FOK: "fok",
    OrderType.FAK: "ioc"
}
ORDERTYPE_HUOBIS2VT: Dict[Any, OrderType] = {v: k for k, v in ORDERTYPE_VT2HUOBIS.items()}
ORDERTYPE_HUOBIS2VT[1] = OrderType.LIMIT
ORDERTYPE_HUOBIS2VT[3] = OrderType.MARKET
ORDERTYPE_HUOBIS2VT[4] = OrderType.MARKET
ORDERTYPE_HUOBIS2VT[5] = OrderType.STOP
ORDERTYPE_HUOBIS2VT[6] = OrderType.LIMIT
ORDERTYPE_HUOBIS2VT["lightning"] = OrderType.MARKET
ORDERTYPE_HUOBIS2VT["optimal_5"] = OrderType.MARKET
ORDERTYPE_HUOBIS2VT["optimal_10"] = OrderType.MARKET
ORDERTYPE_HUOBIS2VT["optimal_20"] = OrderType.MARKET


ORDERTYPE_HUOBIS2VT: Dict[Any, OrderType] = {v: k for k, v in ORDERTYPE_VT2HUOBIS.items()}
ORDERTYPE_HUOBIS2VT[1] = OrderType.LIMIT
ORDERTYPE_HUOBIS2VT[3] = OrderType.MARKET
ORDERTYPE_HUOBIS2VT[4] = OrderType.MARKET
ORDERTYPE_HUOBIS2VT[5] = OrderType.STOP
ORDERTYPE_HUOBIS2VT[6] = OrderType.LIMIT
ORDERTYPE_HUOBIS2VT["lightning"] = OrderType.MARKET
ORDERTYPE_HUOBIS2VT["optimal_5"] = OrderType.MARKET
ORDERTYPE_HUOBIS2VT["optimal_10"] = OrderType.MARKET
ORDERTYPE_HUOBIS2VT["optimal_20"] = OrderType.MARKET


print(ORDERTYPE_HUOBIS2VT["optimal_20"])