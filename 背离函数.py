from typing import Callable
from vnpy.app.cta_strategy import (
    CtaTemplate,
    TickData,
    BarData,
    BarGenerator,
    ArrayManager,
)
from vnpy.trader.constant import Interval

"""
1、背离逻辑计算方式，放到 ArrayManager 内
2、在策略里要使用np.array 容器缓存 self.source_high_upper, self.bar_high_upper结果
3、判断容器缓存前后两次是否背离，或三重背离（价格新低，指标没有新低）
"""

def bar_section(self, source):
    """
    :param source:
    :return:
    """
    # 判断底
    con1 = source[-5] > source[-3] and source[-4] > source[-3] \
           and source[-3] < source[-2] and source[-3] < source[-1]

    # 判断顶
    con2 = source[-5] < source[-3] and source[-4] < source[-3] \
           and source[-3] > source[-2] and source[-3] > source[-1]

    if con1:
        return 1

    elif con2:
        return -1

    else:
        return 0


def bar_deviation_upper(self, source, section_upper=0.2):
    """
    判断 指标最高位位置，及对应的最高位价
    """

    source_sections = self.bar_section(source)
    if source_sections < 0:  # 顶
        if self.high[-1] >= section_upper:
            self.source_high_upper = source[-5:].max()
            self.bar_high_upper = self.high[-5:].max()
        else:
            self.source_high_upper = 0
            self.bar_high_upper = 0
    return self.source_high_upper, self.bar_high_upper


def bar_deviation_down(self, source, section_down=0.2):
    """
    判断 指标最低位，及对应的最低价

    """

    bar_sections = self.bar_section(source)
    if bar_sections > 0:
        if self.low[-1] <= section_down:
            self.source_low_down = source[-5:].min()
            self.bar_low_down = self.low[-5:].min()
        else:
            self.source_low_down = 0
            self.bar_low_down = 0

    return self.source_low_down, self.bar_low_down

