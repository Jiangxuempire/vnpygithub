from datetime import datetime
from typing import List, Tuple, Dict

import numpy as np
import pyqtgraph as pg
import talib
import copy

from vnpy.trader.ui import create_qapp, QtCore, QtGui, QtWidgets
from vnpy.trader.database import database_manager
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData

from vnpy.chart import ChartWidget, VolumeItem, CandleItem
from vnpy.chart.item import ChartItem
from vnpy.chart.manager import BarManager
from vnpy.chart.base import NORMAL_FONT


class LineItem(CandleItem):
    """"""

    def __init__(self, manager: BarManager):
        """"""
        super().__init__(manager)

        self.white_pen: QtGui.QPen = pg.mkPen(color=(255, 255, 255), width=1)

    def _draw_bar_picture(self, ix: int, bar: BarData) -> QtGui.QPicture:
        """"""
        last_bar = self._manager.get_bar(ix - 1)

        # Create objects
        picture = QtGui.QPicture()
        painter = QtGui.QPainter(picture)

        # Set painter color
        painter.setPen(self.white_pen)

        # Draw Line
        end_point = QtCore.QPointF(ix, bar.close_price)

        if last_bar:
            start_point = QtCore.QPointF(ix - 1, last_bar.close_price)
        else:
            start_point = end_point

        painter.drawLine(start_point, end_point)

        # Finish
        painter.end()
        return picture


class SmaItem(CandleItem):
    """"""

    def __init__(self, manager: BarManager):
        """"""
        super().__init__(manager)

        self.blue_pen: QtGui.QPen = pg.mkPen(color=(100, 100, 255), width=2)

        self.sma_window = 10
        self.sma_data: Dict[int, float] = {}

    def get_sma_value(self, ix: int) -> float:
        """"""
        if ix < 0:
            return 0

        # When initialize, calculate all rsi value
        if not self.sma_data:
            bars = self._manager.get_all_bars()
            close_data = [bar.close_price for bar in bars]
            sma_array = talib.SMA(np.array(close_data), self.sma_window)

            for n, value in enumerate(sma_array):
                self.sma_data[n] = value

        # Return if already calcualted
        if ix in self.sma_data:
            return self.sma_data[ix]

        # Else calculate new value
        close_data = []
        for n in range(ix - self.sma_window, ix + 1):
            bar = self._manager.get_bar(n)
            close_data.append(bar.close_price)

        sma_array = talib.SMA(np.array(close_data), self.sma_window)
        sma_value = sma_array[-1]
        self.sma_data[ix] = sma_value

        return sma_value

    def _draw_bar_picture(self, ix: int, bar: BarData) -> QtGui.QPicture:
        """"""
        sma_value = self.get_sma_value(ix)
        last_sma_value = self.get_sma_value(ix - 1)

        # Create objects
        picture = QtGui.QPicture()
        painter = QtGui.QPainter(picture)

        # Set painter color
        painter.setPen(self.blue_pen)

        # Draw Line
        start_point = QtCore.QPointF(ix-1, last_sma_value)
        end_point = QtCore.QPointF(ix, sma_value)
        painter.drawLine(start_point, end_point)

        # Finish
        painter.end()
        return picture

    def get_info_text(self, ix: int) -> str:
        """"""
        if ix in self.sma_data:
            sma_value = self.sma_data[ix]
            text = f"SMA {sma_value:.1f}"
        else:
            text = "SMA -"

        return text


class RsiItem(ChartItem):
    """"""

    def __init__(self, manager: BarManager):
        """"""
        super().__init__(manager)

        self.white_pen: QtGui.QPen = pg.mkPen(color=(255, 255, 255), width=1)
        self.yellow_pen: QtGui.QPen = pg.mkPen(color=(255, 255, 0), width=2)

        self.rsi_window = 14
        self.rsi_data: Dict[int, float] = {}

    def get_rsi_value(self, ix: int) -> float:
        """"""
        if ix < 0:
            return 50

        # When initialize, calculate all rsi value
        if not self.rsi_data:
            bars = self._manager.get_all_bars()
            close_data = [bar.close_price for bar in bars]
            rsi_array = talib.RSI(np.array(close_data), self.rsi_window)

            for n, value in enumerate(rsi_array):
                self.rsi_data[n] = value

        # Return if already calcualted
        if ix in self.rsi_data:
            return self.rsi_data[ix]

        # Else calculate new value
        close_data = []
        for n in range(ix - self.rsi_window, ix + 1):
            bar = self._manager.get_bar(n)
            close_data.append(bar.close_price)

        rsi_array = talib.RSI(np.array(close_data), self.rsi_window)
        rsi_value = rsi_array[-1]
        self.rsi_data[ix] = rsi_value

        return rsi_value

    def _draw_bar_picture(self, ix: int, bar: BarData) -> QtGui.QPicture:
        """"""
        rsi_value = self.get_rsi_value(ix)
        last_rsi_value = self.get_rsi_value(ix - 1)

        # Create objects
        picture = QtGui.QPicture()
        painter = QtGui.QPainter(picture)

        # Draw RSI line
        painter.setPen(self.yellow_pen)

        end_point = QtCore.QPointF(ix, rsi_value)
        start_point = QtCore.QPointF(ix - 1, last_rsi_value)
        painter.drawLine(start_point, end_point)

        # Draw oversold/overbought line
        painter.setPen(self.white_pen)

        painter.drawLine(
            QtCore.QPointF(ix, 70),
            QtCore.QPointF(ix - 1, 70),
        )

        painter.drawLine(
            QtCore.QPointF(ix, 30),
            QtCore.QPointF(ix - 1, 30),
        )

        # Finish
        painter.end()
        return picture

    def boundingRect(self) -> QtCore.QRectF:
        """"""
        # min_price, max_price = self._manager.get_price_range()
        rect = QtCore.QRectF(
            0,
            0,
            len(self._bar_picutures),
            100
        )
        return rect

    def get_y_range( self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        """  """
        return 0, 100

    def get_info_text(self, ix: int) -> str:
        """"""
        if ix in self.rsi_data:
            rsi_value = self.rsi_data[ix]
            text = f"RSI {rsi_value:.1f}"
            # print(text)
        else:
            text = "RSI -"

        return text


def to_int(value: float) -> int:
    """"""
    return int(round(value, 0))

""" 将y方向的显示范围扩大到1.1 """
def adjust_range(in_range:Tuple[float, float])->Tuple[float, float]:
    ret_range:Tuple[float, float]
    diff = abs(in_range[0] - in_range[1])
    ret_range = (in_range[0]-diff*0.05,in_range[1]+diff*0.05)
    return ret_range

class MacdItem(ChartItem):
    """"""
    _values_ranges: Dict[Tuple[int, int], Tuple[float, float]] = {}

    last_range:Tuple[int, int] = (-1,-1)    # 最新显示K线索引范围

    def __init__(self, manager: BarManager):
        """"""
        super().__init__(manager)

        self.white_pen: QtGui.QPen = pg.mkPen(color=(255, 255, 255), width=1)
        self.yellow_pen: QtGui.QPen = pg.mkPen(color=(255, 255, 0), width=1)
        self.red_pen: QtGui.QPen = pg.mkPen(color=(255, 0, 0), width=1)
        self.green_pen: QtGui.QPen = pg.mkPen(color=(0, 255, 0), width=1)

        self.short_window = 12
        self.long_window = 26
        self.M = 9

        self.macd_data: Dict[int, Tuple[float,float,float]] = {}

    def get_macd_value(self, ix: int) -> Tuple[float,float,float]:
        """"""
        if ix < 0:
            return (0.0,0.0,0.0)

        # When initialize, calculate all macd value
        if not self.macd_data:
            bars = self._manager.get_all_bars()
            close_data = [bar.close_price for bar in bars]

            diffs,deas,macds = talib.MACD(np.array(close_data),
                                    fastperiod=self.short_window,
                                    slowperiod=self.long_window,
                                    signalperiod=self.M)

            for n in range(0,len(diffs)):
                self.macd_data[n] = (diffs[n],deas[n],macds[n])

        # Return if already calcualted
        if ix in self.macd_data:
            return self.macd_data[ix]

        # Else calculate new value
        close_data = []
        for n in range(ix-self.long_window-self.M+1, ix + 1):
            bar = self._manager.get_bar(n)
            close_data.append(bar.close_price)

        diffs,deas,macds = talib.MACD(np.array(close_data),
                                            fastperiod=self.short_window,
                                            slowperiod=self.long_window,
                                            signalperiod=self.M)
        diff,dea,macd = diffs[-1],deas[-1],macds[-1]
        self.macd_data[ix] = (diff,dea,macd)

        return (diff,dea,macd)

    def _draw_bar_picture(self, ix: int, bar: BarData) -> QtGui.QPicture:
        """"""
        macd_value = self.get_macd_value(ix)
        last_macd_value = self.get_macd_value(ix - 1)

        # # Create objects
        picture = QtGui.QPicture()
        painter = QtGui.QPainter(picture)

        # # Draw macd lines
        if np.isnan(macd_value[0]) or np.isnan(last_macd_value[0]):
            # print("略过macd lines0")
            pass
        else:
            end_point0 = QtCore.QPointF(ix, macd_value[0])
            start_point0 = QtCore.QPointF(ix - 1, last_macd_value[0])
            painter.setPen(self.white_pen)
            painter.drawLine(start_point0, end_point0)

        if np.isnan(macd_value[1]) or np.isnan(last_macd_value[1]):
            # print("略过macd lines1")
            pass
        else:
            end_point1 = QtCore.QPointF(ix, macd_value[1])
            start_point1 = QtCore.QPointF(ix - 1, last_macd_value[1])
            painter.setPen(self.yellow_pen)
            painter.drawLine(start_point1, end_point1)

        if not np.isnan(macd_value[2]):
            if (macd_value[2]>0):
                painter.setPen(self.red_pen)
                painter.setBrush(pg.mkBrush(255,0,0))
            else:
                painter.setPen(self.green_pen)
                painter.setBrush(pg.mkBrush(0,255,0))
            painter.drawRect(QtCore.QRectF(ix-0.3,0,0.6,macd_value[2]))
        else:
            # print("略过macd lines2")
            pass

        painter.end()
        return picture

    def boundingRect(self) -> QtCore.QRectF:
        """"""
        min_y, max_y = self.get_y_range()
        rect = QtCore.QRectF(
            0,
            min_y,
            len(self._bar_picutures),
            max_y
        )
        return rect

    def get_y_range(self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        #   获得3个指标在y轴方向的范围
        #   hxxjava 修改，2020-6-29
        #   当显示范围改变时，min_ix,max_ix的值不为None，当显示范围不变时，min_ix,max_ix的值不为None，

        offset = max(self.short_window,self.long_window) + self.M - 1

        if not self.macd_data or len(self.macd_data) < offset:
            return 0.0, 1.0

        # print("len of range dict:",len(self._values_ranges),",macd_data:",len(self.macd_data),(min_ix,max_ix))

        if min_ix != None:          # 调整最小K线索引
            min_ix = max(min_ix,offset)

        if max_ix != None:          # 调整最大K线索引
            max_ix = min(max_ix, len(self.macd_data)-1)

        last_range = (min_ix,max_ix)    # 请求的最新范围

        if last_range == (None,None):   # 当显示范围不变时
            if self.last_range in self._values_ranges:
                # 如果y方向范围已经保存
                # 读取y方向范围
                result = self._values_ranges[self.last_range]
                # print("1:",self.last_range,result)
                return adjust_range(result)
            else:
                # 如果y方向范围没有保存
                # 从macd_data重新计算y方向范围
                min_ix,max_ix = 0,len(self.macd_data)-1

                macd_list = list(self.macd_data.values())[min_ix:max_ix + 1]
                ndarray = np.array(macd_list)
                max_price = np.nanmax(ndarray)
                min_price = np.nanmin(ndarray)

                # 保存y方向范围，同时返回结果
                result = (min_price, max_price)
                self.last_range = (min_ix,max_ix)
                self._values_ranges[self.last_range] = result
                # print("2:",self.last_range,result)
                return adjust_range(result)

        """ 以下为显示范围变化时 """

        if last_range in self._values_ranges:
            # 该范围已经保存过y方向范围
            # 取得y方向范围，返回结果
            result = self._values_ranges[last_range]
            # print("3:",last_range,result)
            return adjust_range(result)

        # 该范围没有保存过y方向范围
        # 从macd_data重新计算y方向范围
        macd_list = list(self.macd_data.values())[min_ix:max_ix + 1]
        ndarray = np.array(macd_list)
        max_price = np.nanmax(ndarray)
        min_price = np.nanmin(ndarray)

        # 取得y方向范围，返回结果
        result = (min_price, max_price)
        self.last_range = last_range
        self._values_ranges[self.last_range] = result
        # print("4:",self.last_range,result)
        return adjust_range(result)


    def get_info_text(self, ix: int) -> str:
        # """"""
        if ix in self.macd_data:
            diff,dea,macd = self.macd_data[ix]
            words = [
                f"diff {diff:.3f}"," ",
                f"dea {dea:.3f}"," ",
                f"macd {macd:.3f}"
                ]
            text = "\n".join(words)
        else:
            text = "diff - \ndea - \nmacd -"

        return text



class NewChartWidget(ChartWidget):
    """"""
    MIN_BAR_COUNT = 100

    def __init__(self, parent: QtWidgets.QWidget = None):
        """"""
        super().__init__(parent)

        self.last_price_line: pg.InfiniteLine = None

    def add_last_price_line(self):
        """"""
        plot = list(self._plots.values())[0]
        color = (255, 255, 255)

        self.last_price_line = pg.InfiniteLine(
            angle=0,
            movable=False,
            label="{value:.1f}",
            pen=pg.mkPen(color, width=1),
            labelOpts={
                "color": color,
                "position": 1,
                "anchors": [(1, 1), (1, 1)]
            }
        )
        self.last_price_line.label.setFont(NORMAL_FONT)
        plot.addItem(self.last_price_line)

    def update_history(self, history: List[BarData]) -> None:
        """
        Update a list of bar data.
        """
        self._manager.update_history(history)

        for item in self._items.values():
            item.update_history(history)

        self._update_plot_limits()

        self.move_to_right()

        self.update_last_price_line(history[-1])

    def update_bar(self, bar: BarData) -> None:
        """
        Update single bar data.
        """
        self._manager.update_bar(bar)

        for item in self._items.values():
            item.update_bar(bar)

        self._update_plot_limits()

        if self._right_ix >= (self._manager.get_count() - self._bar_count / 2):
            self.move_to_right()

        self.update_last_price_line(bar)

    def update_last_price_line(self, bar: BarData) -> None:
        """"""
        if self.last_price_line:
            self.last_price_line.setValue(bar.close_price)


if __name__ == "__main__":
    app = create_qapp()

    # bars = database_manager.load_bar_data(
    #     "IF888",
    #     Exchange.CFFEX,
    #     interval=Interval.MINUTE,
    #     start=datetime(2019, 7, 1),
    #     end=datetime(2019, 7, 17)
    # )

    symbol = "btcusdt"
    exchange = Exchange.BINANCE
    interval=Interval.MINUTE
    start=datetime(2020, 6, 1)
    end=datetime(2020, 6, 30)

    dynamic = False  # 是否动态演示
    n = 200          # 缓冲K线根数


    bars = database_manager.load_bar_data(
        symbol=symbol,
        exchange=exchange,
        interval=interval,
        start=start,
        end=end
    )

    widget = NewChartWidget()
    widget.setWindowTitle(f"K线图表——{symbol}.{exchange.value},{interval},{start}-{end}")
    widget.add_plot("candle", hide_x_axis=True)
    widget.add_plot("volume", maximum_height=150)
    widget.add_plot("rsi", maximum_height=150)
    widget.add_plot("macd", maximum_height=150)
    widget.add_item(CandleItem, "candle", "candle")
    widget.add_item(VolumeItem, "volume", "volume")

    widget.add_item(LineItem, "line", "candle")
    widget.add_item(SmaItem, "sma", "candle")
    widget.add_item(RsiItem, "rsi", "rsi")
    widget.add_item(MacdItem, "macd", "macd")
    widget.add_last_price_line()
    widget.add_cursor()

    if dynamic:
        history = bars[:n]      # 先取得最早的n根bar作为历史
        new_data = bars[n:]     # 其它留着演示
    else:
        history = bars[-n:]     # 先取得最新的n根bar作为历史
        new_data = []           # 演示的为空

    widget.update_history(history)

    def update_bar():
        if new_data:
            bar = new_data.pop(0)
            widget.update_bar(bar)

    timer = QtCore.QTimer()
    timer.timeout.connect(update_bar)
    if dynamic:
        timer.start(100)

    widget.show()
    app.exec_()