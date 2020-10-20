import talib as ta
import pandas as pd

pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数

# ACOS反余弦函数
'''
这是一个基本的数学操作函数，用于对一个ndarray对象做反余弦函数处理，最后返回一个角度值。
'''
# 设置数据
# data = {'1': [0.2, 0.3, 0.4], '2': [-1, 0.3, 0.5]}
# df = pd.DataFrame(data)
# print(df)
# df['ACOS_1'] = ta.ACOS(df['1'])  # 返回角度值
# df['ACOS_2'] = ta.ACOS(df['2'])  # 返回角度值
# print(df)

# AD线随机指标
'''
AD指标主要测量资金流向，向上的AD表示买方占据优势，而向下的AD表示卖方占优势；
此外，AD与价格的背离可视为买卖信号，底背离考虑买入，顶背离考虑卖出。
AD的缺陷是忽略了跳空缺口的影响，可能会导致信号偏差，需综合其他指标考虑。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_后复权'] = df['复权因子'] * (df.iloc[0]['收盘价'] / df.iloc[0]['复权因子'])
# 计算复权
# df['开盘价_后复权'] = df['开盘价'] / df['收盘价'] * df['收盘价_后复权']
# df['最高价_后复权'] = df['最高价'] / df['收盘价'] * df['收盘价_后复权']
# df['最低价_后复权'] = df['最低价'] / df['收盘价'] * df['收盘价_后复权']
# df['AD'] = ta.AD(df['最高价_后复权'], df['最低价_后复权'], df['收盘价_后复权'], df['成交量'])
# print(df[['AD']])

# ADD加法
'''
也是一个基础数学操作函数—加法操作，用于两个ndarray的相加，返回两者的和。
'''
# data = {'1': [1, 2, 3], '2': [3, 4, 5]}
# df = pd.DataFrame(data)
# print(df)
# df['AD'] = ta.ADD(df['1'], df['2'])
# print(df)

# ADOSC佳庆指标
'''
佳庆指标是根据AD指标改良而来的。为了反映市场的内在动能，则成交量是一个必须被考虑在内的指标之一。
佳庆指标以中间价位基准，中间价即最高价与最低价的平均值，如果收盘价高于当日的中间价，则成交量视为正值，越接近当日最高价，多头越强；
反之，如果收盘价低于当日中间价，则当日成交量视为负值，且越接近当日最低价，空头越强。
佳庆指标需要配合其他指标如超买超卖指标等效果会更好，佳庆指标由负值向上穿越0轴时(股价位于90日均线之上)，为买进信号;
由正值向下穿越0轴时(股价位于90日均线之下)，为卖出信号。佳庆指标与股价发生背离时，可视为反转信号。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_后复权'] = df['复权因子'] * (df.iloc[0]['收盘价'] / df.iloc[0]['复权因子'])
# 计算复权
# df['开盘价_后复权'] = df['开盘价'] / df['收盘价'] * df['收盘价_后复权']
# df['最高价_后复权'] = df['最高价'] / df['收盘价'] * df['收盘价_后复权']
# df['最低价_后复权'] = df['最低价'] / df['收盘价'] * df['收盘价_后复权']
# fastperiod = 3
# slowperiod = 12
# df['ADOSC'] = ta.ADOSC(df['最高价_后复权'], df['最低价_后复权'], df['收盘价_后复权'], df['成交量'],
#                        fastperiod=fastperiod, slowperiod=slowperiod)
# print(df[['ADOSC']])


# ADX平均趋向指数
'''
ADX平均趋向指数是一种常用的趋势衡量指标。ADX不是帮你来判断趋势的方向，而是用来衡量趋势的强度。
ADX读数越大，趋势越明显。在衡量趋势强度时，需要将一段时间的ADX读数进行对比，观察整体趋势是上升还是下降。
如果ADX读数上升，意味着趋势开始转强，如果ADX读数下降，意味着趋势开始转弱。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_后复权'] = df['复权因子'] * (df.iloc[0]['收盘价'] / df.iloc[0]['复权因子'])
# 计算复权
# df['开盘价_后复权'] = df['开盘价'] / df['收盘价'] * df['收盘价_后复权']
# df['最高价_后复权'] = df['最高价'] / df['收盘价'] * df['收盘价_后复权']
# df['最低价_后复权'] = df['最低价'] / df['收盘价'] * df['收盘价_后复权']
# timeperiod = 14
# df['ADX'] = ta.ADX(df['最高价_后复权'], df['最低价_后复权'], df['收盘价_后复权'], timeperiod=timeperiod)
# print(df[['ADX']])

# ADXR评估指数
'''
ADXR评估指数是ADX的“评估指数”，其计算方法是将当日的ADX值与14日前的ADX相加之后除以2得出。
ADXR的波动一般较ADX平缓，ADXR与ADX相交，意味着随后的行情来势汹汹，应早做打算。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_后复权'] = df['复权因子'] * (df.iloc[0]['收盘价'] / df.iloc[0]['复权因子'])
# 计算复权
# df['开盘价_后复权'] = df['开盘价'] / df['收盘价'] * df['收盘价_后复权']
# df['最高价_后复权'] = df['最高价'] / df['收盘价'] * df['收盘价_后复权']
# df['最低价_后复权'] = df['最低价'] / df['收盘价'] * df['收盘价_后复权']
# timeperiod = 14
# df['ADXR'] = ta.ADXR(df['最高价_后复权'], df['最低价_后复权'], df['收盘价_后复权'], timeperiod=timeperiod)
# print(df[['ADXR']])

# APO绝对价格震荡指数
'''
APO绝对价格震荡指数是一个与MACD指数非常相似的指标，它和MACD一样衡量了两条移动平均线的差距，
但是APO使用百分比来显示来显示两者的差距，这种方法的好处就是可以忽略实际价格，得到一个绝对比例。
操作方法与MACD类似。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_后复权'] = df['复权因子'] * (df.iloc[0]['收盘价'] / df.iloc[0]['复权因子'])
# fastperiod = 12
# slowperiod = 26
# matype = 0  # 默认为0
# df['APO'] = ta.APO(df['收盘价_后复权'], fastperiod=fastperiod, slowperiod=slowperiod, matype=matype)
# print(df[['APO']])

# AROON阿隆指标
'''
AROON阿隆指标通过计算自价格达到近期最高值和最低值以来所经过的期间数，
阿隆指标帮助你预测价格趋势到趋势区域(或者从趋势区域到趋势)的变化情况。
当AROONUP线达到100时，说明市场处于强势期，处于70-100之间，说明处于一个上升趋势。
同理，如果AROONDOWN线达到0，表明市场处于弱势，如果处于0-30之间，表明处于下跌趋势。
如果两者都处于极值水平，则表明一个更强的趋势。
AROONDOWN上穿AROONUP表示潜在弱势形成，价格可能趋于下降；反之则趋于上升。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# timeperiod = 14
# df['AROONDOWN'], df['AROONUP'] = ta.AROON(df['最高价'], df['最低价'], timeperiod=timeperiod)
# print(df[['AROONDOWN', 'AROONUP']])

# AROONOSC阿隆震荡线
'''
AROONOSC阿隆震荡线指标主要用来衡量AROONUP与AROONDOWN之间的差额。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# timeperiod = 14
# df['AROONOSC'] = ta.AROONOSC(df['最高价'], df['最低价'], timeperiod=timeperiod)
# print(df[['AROONOSC']])

# ASIN反正弦函数
'''
这是一个基本的数学操作函数，用于对一个ndarray对象做反正弦函数处理，最后返回一个角度值。
'''
# 设置数据
# data = {'1': [0.2, 0.3, 0.4], '2': [-1, 0.3, 0.5]}
# df = pd.DataFrame(data)
# print(df)
# df['ASIN_1'] = ta.ASIN(df['1'])  # 返回角度值
# df['ASIN_2'] = ta.ASIN(df['2'])  # 返回角度值
# print(df)

# ATAN反正切函数
'''
这是一个基本的数学操作函数，用于对一个ndarray对象做反正切函数处理，最后返回一个角度值。
'''
# 设置数据
# data = {'1': [0.2, 0.3, 0.4], '2': [-1, 0.3, 0.5]}
# df = pd.DataFrame(data)
# print(df)
# df['ATAN_1'] = ta.ATAN(df['1'])  # 返回角度值
# df['ATAN_2'] = ta.ATAN(df['2'])  # 返回角度值
# print(df)


# ATR平均真实波幅
'''
ATR平均真实波幅是取一定时间周期内的股价波动幅度的移动平均值，是衡量波动性的方法。
较高的ATR值通常出现在“恐慌”性抛盘的市场底部，较低的ATR值通常出现在延伸的水平运动期间。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_后复权'] = df['复权因子'] * (df.iloc[0]['收盘价'] / df.iloc[0]['复权因子'])
# 计算复权
# df['开盘价_后复权'] = df['开盘价'] / df['收盘价'] * df['收盘价_后复权']
# df['最高价_后复权'] = df['最高价'] / df['收盘价'] * df['收盘价_后复权']
# df['最低价_后复权'] = df['最低价'] / df['收盘价'] * df['收盘价_后复权']
# timeperiod = 14
# df['ATR'] = ta.ATR(df['最高价_后复权'], df['最低价_后复权'], df['收盘价_后复权'], timeperiod=timeperiod)
# print(df[['ATR']])


# AVGPRICE平均价格
'''
AVGPRICE平均价格指标是用来衡量经过开盘价、最高价、最低价、收盘价调整后的平均价格。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_后复权'] = df['复权因子'] * (df.iloc[0]['收盘价'] / df.iloc[0]['复权因子'])
# 计算复权
# df['开盘价_后复权'] = df['开盘价'] / df['收盘价'] * df['收盘价_后复权']
# df['最高价_后复权'] = df['最高价'] / df['收盘价'] * df['收盘价_后复权']
# df['最低价_后复权'] = df['最低价'] / df['收盘价'] * df['收盘价_后复权']
# df['AVGPRICE'] = ta.AVGPRICE(df['开盘价_后复权'], df['最高价_后复权'], df['最低价_后复权'], df['收盘价_后复权'])
# print(df)
# print(df[['AVGPRICE']])

# BBANDS布林带
'''
BBANDS布林带就是我们常说的布林通道，其中upperband,middleband,lowerband分别是上轨，中轨，下轨。
通常我们认为收盘价突破上轨是多头趋势走强的信号，突破下轨是空头趋势走强的信号。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_后复权'] = df['复权因子'] * (df.iloc[0]['收盘价'] / df.iloc[0]['复权因子'])
# 计算布林带
# timeperiod = 20
# nbdevup = 2
# nbdevdn = 2
# matype = 0  # 默认0
# df['UPPERBAND'], df['MIDDLEBAND'], df['LOWERBAND'] = ta.BBANDS(df['收盘价_后复权'], timeperiod=timeperiod,
#                                                                nbdevup=nbdevup, nbdevdn=nbdevdn, matype=matype)
# print(df[['UPPERBAND', 'MIDDLEBAND', 'LOWERBAND']])

# BETA 指数
'''
BETA指数用来衡量一列数据相对于另一列数据的波动性情况，通常是以上证指数作为基准计算贝塔指数。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# timeperiod = 5
# df['BETA'] = ta.BETA(df['开盘价'], df['收盘价'], timeperiod=timeperiod)
# print(df[['BETA']])

# BOP均势指标
'''
BOP均势指标主要用于观测价格趋向某个极值时买卖双方的力量对比状况，
该指标在判断交易介入时机以及趋势是否已成强弩之末时非常有效，同时也可以判断走势是否将进入一段震荡区间。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_后复权'] = df['复权因子'] * (df.iloc[0]['收盘价'] / df.iloc[0]['复权因子'])
# 计算复权
# df['开盘价_后复权'] = df['开盘价'] / df['收盘价'] * df['收盘价_后复权']
# df['最高价_后复权'] = df['最高价'] / df['收盘价'] * df['收盘价_后复权']
# df['最低价_后复权'] = df['最低价'] / df['收盘价'] * df['收盘价_后复权']
# df['BOP'] = ta.BOP(df['开盘价_后复权'], df['最高价_后复权'], df['最低价_后复权'], df['收盘价_后复权'])
# print(df[['BOP']])

# CCI顺势指标
'''
CCI顺势指标是属于测量市场超卖超卖情况的一种指标。
CCI指标相对于其他衡量超卖超卖的指标的特殊之处在于其没有0-100的上下限，
它的范围是从负无穷到正无穷，从而对于某些暴涨暴跌的行情不会发生指标钝化的情况。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_后复权'] = df['复权因子'] * (df.iloc[0]['收盘价'] / df.iloc[0]['复权因子'])
# 计算复权
# df['开盘价_后复权'] = df['开盘价'] / df['收盘价'] * df['收盘价_后复权']
# df['最高价_后复权'] = df['最高价'] / df['收盘价'] * df['收盘价_后复权']
# df['最低价_后复权'] = df['最低价'] / df['收盘价'] * df['收盘价_后复权']
# timeperiod = 14
# df['CCI'] = ta.CCI(df['最高价_后复权'], df['最低价_后复权'], df['收盘价_后复权'], timeperiod=timeperiod)
# print(df[['CCI']])

# CEIL取整函数
'''
CEIL取整函数用于返回大于或等于指定表达式的最小整数。
'''
# 设置数据
# data = {'1': [0.2, 1.6, 5.4], '2': [-1.1, -3.3, -1.9]}
# df = pd.DataFrame(data)
# print(df)
# df['CEIL_1'] = ta.CEIL(df['1'])
# df['CEIL_2'] = ta.CEIL(df['2'])
# print(df[['CEIL_1', 'CEIL_2']])

# CMO钱德动量摆动指标
'''
CMO钱德动量摆动指标也是用来测算超卖超卖情况的指标。
当CMO大于50时，处于超买状态；当CMO小于-50时处于超卖状态。
CMO的绝对值越高，表明趋势越强。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_后复权'] = df['复权因子'] * (df.iloc[0]['收盘价'] / df.iloc[0]['复权因子'])
# timeperiod = 14
# df['CMO'] = ta.CMO(df['收盘价_后复权'], timeperiod=timeperiod)
# print(df[['CMO']])

# CORREL皮尔森相关系数
'''
CORREL皮尔森相关系数用来反映两个变量相关程度的统计量。
取值在-1与1之间，若>0,表明两个变量正相关，若<0,表明两个变量负相关。若=0，表明相关性不强。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# timeperiod = 30
# df['CORREL'] = ta.CORREL(df['开盘价'], df['收盘价'], timeperiod=timeperiod)
# print(df[['CORREL']])

# COS函数
'''
COS余弦函数是一个基本的数学操作函数，用于对一列数据取余弦操作。
'''
# 设置数据
# data = {'1': [0.2, 1.6, 5.4], '2': [-1.1, -3.3, -1.9]}
# df = pd.DataFrame(data)
# print(df)
# df['COS'] = ta.COS(df['1'])
# print(df[['COS']])

# COSH双曲余弦函数
'''
COSH双曲余弦函数用来返回一列数据取双曲余弦操作。
'''
# 设置数据
# data = {'1': [0.2, 1.6, 5.4], '2': [-1.1, -3.3, -1.9]}
# df = pd.DataFrame(data)
# print(df)
# df['COSH'] = ta.COSH(df['1'])
# print(df[['COSH']])

# DEMA双指数移动平均线
'''
DEMA双指数移动平均线是一个更平滑更快速的移动平均线，与普通移动平均线相比，它可以减少滞后时间。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_后复权'] = df['复权因子'] * (df.iloc[0]['收盘价'] / df.iloc[0]['复权因子'])
# timeperiod = 30
# df['DEMA'] = ta.DEMA(df['收盘价_后复权'], timeperiod=timeperiod)
# print(df[['DEMA']])

# DIV取整
'''
DIV是一个基本的数学操作函数，用于两列数据的整除操作。
'''
# 设置数据
# data = {'1': [8, 1.6, 5.4], '2': [1.5, -3.3, -1.9]}
# df = pd.DataFrame(data)
# print(df)
# df['DIV'] = ta.DIV(df['1'], df['2'])
# print(df[['DIV']])

# DX 动向指数
'''
DX动向指数是一个用来判断趋势的技术性指标，
其原理是分析股票价格在上升及下跌过程中供需关系的均衡点，
也就是供需关系受到价格影响而发生均衡到失衡之间的往复循环。
其操作方法与ADX类似。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_后复权'] = df['复权因子'] * (df.iloc[0]['收盘价'] / df.iloc[0]['复权因子'])
# 计算复权
# df['开盘价_后复权'] = df['开盘价'] / df['收盘价'] * df['收盘价_后复权']
# df['最高价_后复权'] = df['最高价'] / df['收盘价'] * df['收盘价_后复权']
# df['最低价_后复权'] = df['最低价'] / df['收盘价'] * df['收盘价_后复权']
# timeperiod = 14
# df['DX'] = ta.DX(df['最高价_后复权'], df['最低价_后复权'], df['收盘价_后复权'], timeperiod=timeperiod)
# print(df[['DX']])

# EMA指数移动平均线
'''
EMA指数移动平均线是一个更平滑更快速的移动平均线，
主要用于比较均线的趋势快慢，它可以用来平滑和美观曲线。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_后复权'] = df['复权因子'] * (df.iloc[0]['收盘价'] / df.iloc[0]['复权因子'])
# timeperiod = 30
# df['EMA'] = ta.EMA(df['收盘价_后复权'], timeperiod=timeperiod)
# print(df[['EMA']])

# EXP指数函数
'''
EXP指数函数是基本数学操作函数，用来求以自然函数e为底的指数函数值。
'''
# 设置数据
# data = {'1': [1, 1.6, 2], '2': [1.5, -3.3, -1.9]}
# df = pd.DataFrame(data)
# print(df)
# df['EXP'] = ta.EXP(df['1'])
# print(df[['EXP']])

# FLOOR指数函数
'''
FLOOR向下取整是取不大于X的最大整数。
'''
# 设置数据
# data = {'1': [0.3, 1.6, 2.7], '2': [-1.5, -3.3, -1.9]}
# df = pd.DataFrame(data)
# print(df)
# df['FLOOR'] = ta.FLOOR(df['1'])
# print(df[['FLOOR']])

# HT_DCPERIOD希尔伯特变换（主周期）
'''
HT_DCPERIOD希尔伯特变换（主周期）主要将股票价格或者市场指数这种非周期信号转换成有“周期”的信号，实际使用请参照券商相关研报。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# df['HT_DCPERIOD'] = ta.HT_DCPERIOD(df['收盘价_前复权'])
# print(df[['HT_DCPERIOD']])

# HT_DCPHASE希尔伯特变换（主阶段）
'''
HT_DCPHASE希尔伯特变换（主阶段）主要将股票价格或者市场指数这种非周期信号转换成有“周期”的信号，实际使用请参照券商相关研报。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# df['HT_DCPHASE'] = ta.HT_DCPHASE(df['收盘价_前复权'])
# print(df[['HT_DCPHASE']])

# HT_PHASOR希尔伯特变换（相成分）
'''
HT_PHASOR希尔伯特变换（相成分）主要将股票价格或者市场指数这种非周期信号转换成有“周期”的信号，实际使用请参照券商相关研报。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# df['HT_PHASOR_inphase'], df['HT_PHASOR_quadrature'] = ta.HT_PHASOR(df['收盘价_前复权'])
# print(df[['HT_PHASOR_inphase', 'HT_PHASOR_quadrature']])  # 返回同向和正交成分

# HT_SINE希尔伯特变换（正弦波）
'''
HT_SINE希尔伯特变换（正弦波）主要将股票价格或者市场指数这种非周期信号转换成有“周期”的信号，实际使用请参照券商相关研报。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# df['HT_SINE_sine'], df['HT_SINE_leadsine'] = ta.HT_SINE(df['收盘价_前复权'])
# print(df[['HT_SINE_sine', 'HT_SINE_leadsine']])

# HT_TRENDLINE希尔伯特变换（瞬时趋势）
'''
HT_TRENDLINE希尔伯特变换（瞬时趋势）主要将股票价格或者市场指数这种非周期信号转换成有“周期”的信号，实际使用请参照券商相关研报。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# df['HT_TRENDLINE'] = ta.HT_TRENDLINE(df['收盘价_前复权'])
# print(df[['HT_TRENDLINE']])

# HT_TRENDMODE希尔伯特变换（趋势与周期模式）
'''
HT_TRENDMODE希尔伯特变换（趋势与周期模式）主要将股票价格或者市场指数这种非周期信号转换成有“周期”的信号，实际使用请参照券商相关研报。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# df['HT_TRENDMODE'] = ta.HT_TRENDMODE(df['收盘价_前复权'])
# print(df[['HT_TRENDMODE']])

# KAMA适应性移动平均线
'''
KAMA适应性移动平均线相比于其他的移动平均线有个明显优势，就是它不仅考虑方向，还考虑了市场波动率。
KAMA的简单策略即均线突破策略，如收盘价上穿KAMA线时为买入信号，下穿KAMA时为卖出信号。
当然，KAMA也容易出现均线纠缠，
实际使用需要配合其他信号进行甄别。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 30
# df['KAMA'] = ta.KAMA(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['KAMA']])

# LINEARREG线性回归
'''
LINERAGGEG线性回归是用于回归分析中广泛使用的建模类型，请结合券商研报分析使用。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 14
# df['LINEARREG'] = ta.LINEARREG(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['LINEARREG']])

# LINEARREG_ANGLE线性回归的角度
'''
LINEARREG_ANGLE计算线性回归的角度，请结合券商研报分析使用。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 14
# df['LINEARREG_ANGLE'] = ta.LINEARREG_ANGLE(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['LINEARREG_ANGLE']])

# LINEARREG_INTERCEPT线性回归的截距
'''
LINEARREG_INTERCEPT计算线性回归的截距，请结合券商研报分析使用。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 14
# df['LINEARREG_INTERCEPT'] = ta.LINEARREG_INTERCEPT(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['LINEARREG_INTERCEPT']])

# LINEARREG_SLOPE线性回归斜率
'''
LINEARREG_SLOPE计算线性回归斜率，请结合券商研报分析使用。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 14
# df['LINEARREG_SLOPE'] = ta.LINEARREG_SLOPE(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['LINEARREG_SLOPE']])

# LN自然对数
'''
LN自然对数是一个基本数学操作函数，作用是取以e为底的自然对数。
'''
# data = {'1': [1, 1.4, 2], '2': [2.4, 3.5, 6.9]}
# df = pd.DataFrame(data)
# print(df)
# df['LN'] = ta.LN(df['1'])
# print(df[['LN']])

# LOG10对数函数
'''
LOG10对数函数是一个基本数学操作函数，作用是取以10为底的对数。
'''
# data = {'1': [100, 1000, 10], '2': [2.4, 3.5, 6.9]}
# df = pd.DataFrame(data)
# print(df)
# df['LOG10'] = ta.LOG10(df['1'])
# print(df[['LOG10']])

# MA移动平均线
'''
MA移动平均线即最普通的移动平均线，通过滚动计算一定时期的价格均值得到。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 30
# matype = 0
# df['MA'] = ta.MA(df['收盘价_前复权'], timeperiod=timeperiod, matype=matype)
# print(df[['MA']])

# MACD指数平滑平均线
'''
MACD指数平滑移动平均线是利用收盘价的短期（一般为12日）指数移动平均线与长期（一般为26日）指数移动平均线之间的聚合与分离情况，从而判断买卖时机的一种指标。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# fastperiod = 12
# slowperiod = 26
# signalperiod = 9
# df['DIF'], df['DEA'], df['MACDmini'] = ta.MACD(df['收盘价_前复权'], fastperiod=fastperiod,
#                                                slowperiod=slowperiod, signalperiod=signalperiod)
# df['MACD'] = df['MACDmini'] * 2
# print(df[['MACD']])

# MACDEXT,MA型可控MACD
'''
MACDEXT,MA型可控MACD是对MACD的一种变型的动量研究指标，具体参见券商研报。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# fastperiod = 12
# fastmatype = 0
# slowperiod = 26
# slowmatype = 0
# signalperiod = 9
# signalmatype = 0
# df['DIF'], df['DEA'], df['MACDEXTmini'] = ta.MACDEXT(df['收盘价_前复权'], fastperiod=fastperiod,
#                                                      fastmatype=fastmatype, slowperiod=slowperiod,
#                                                      slowmatype=slowmatype,
#                                                      signalperiod=signalperiod, signalmatype=signalmatype)
# df['MACDEXT'] = df['MACDEXTmini'] * 2
# print(df[['MACDEXT']])

# MACDFIX 移动平均收敛/发散修复 12/26
'''
MACDFIX移动平均收敛/发散修复是动量研究中的一种指标，具体参见券商研报。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# signalperiod = 9
# df['DIF'], df['DEA'], df['MACDFIXmini'] = ta.MACDFIX(df['收盘价_前复权'],  signalperiod=signalperiod)
# df['MACDFIX'] = df['MACDFIXmini'] * 2
# print(df[['MACDFIX']])

# MAMA,MESA移动平均线
'''
MAMA,MESA移动平均线是一种特殊的移动平均线指标，用于重叠研究。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# fastlimit = 0.5
# slowlimit = 0.05
# df['MAMA'], df['MESA'] = ta.MAMA(df['收盘价_前复权'], fastlimit=fastlimit, slowlimit=slowlimit)
# print(df[['MAMA', 'MESA']])

# MAVP变周期均值
'''
MAVP变周期均值返回随周期变化的两列数据的平均值，也用于重叠研究。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# # 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# 计算复权
# df['开盘价_前复权'] = df['开盘价'] / df['收盘价'] * df['收盘价_前复权']
# df['最高价_前复权'] = df['最高价'] / df['收盘价'] * df['收盘价_前复权']
# df['最低价_前复权'] = df['最低价'] / df['收盘价'] * df['收盘价_前复权']
# minperiod = 2
# maxperiod = 30
# matype = 0
# df['MAVP'] = ta.MAVP(df['收盘价_前复权'], df['最高价_前复权'], minperiod=minperiod, maxperiod=maxperiod, matype=matype)
# print(df[['MAVP']])

# MAX最大值
'''
MAX最大值用来返回一列数据的最大值。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 30
# df['MAX'] = ta.MAX(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['MAX']])

# MAXINDEX最大值索引
'''
MAXINDEX最大值索引用来返回一段期间最大值的索引。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 30
# df['MAXINDEX'] = ta.MAXINDEX(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['MAXINDEX']])

# MEDPRICE中位数价格
'''
MEDPRICE中位数价格用来返回两列数据的中位数价格。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# 计算复权
# df['开盘价_前复权'] = df['开盘价'] / df['收盘价'] * df['收盘价_前复权']
# df['最高价_前复权'] = df['最高价'] / df['收盘价'] * df['收盘价_前复权']
# df['最低价_前复权'] = df['最低价'] / df['收盘价'] * df['收盘价_前复权']
# df['MEDPRICE'] = ta.MEDPRICE(df['最高价_前复权'], df['最低价_前复权'])
# print(df[['MEDPRICE']])

# MFI货币流量指数
'''
MFI货币流量指数属于一种量价类指标，可以反映市场的运行趋势。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# 计算复权
# df['开盘价_前复权'] = df['开盘价'] / df['收盘价'] * df['收盘价_前复权']
# df['最高价_前复权'] = df['最高价'] / df['收盘价'] * df['收盘价_前复权']
# df['最低价_前复权'] = df['最低价'] / df['收盘价'] * df['收盘价_前复权']
# timeperiod = 14
# df['MFI'] = ta.MFI(df['最高价_前复权'], df['最低价_前复权'], df['收盘价_前复权'], df['成交量'], timeperiod=timeperiod)
# print(df[['MFI']])

# MIDPOINT中点
'''
MIDPOINT中点用来返回一列数据在一段期间的中点。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 14
# df['MIDPOINT'] = ta.MIDPOINT(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['MIDPOINT']])

# MIDPRICE中点价格
'''
MIDPRICE中点价格用来计算两列数据一段期间的中点价格。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# 计算复权
# df['开盘价_前复权'] = df['开盘价'] / df['收盘价'] * df['收盘价_前复权']
# df['最高价_前复权'] = df['最高价'] / df['收盘价'] * df['收盘价_前复权']
# df['最低价_前复权'] = df['最低价'] / df['收盘价'] * df['收盘价_前复权']
# timeperiod = 14
# df['MIDPRICE'] = ta.MIDPRICE(df['最高价_前复权'], df['最低价_前复权'], timeperiod=timeperiod)
# print(df[['MIDPRICE']])

# MIN最小值
'''
MIN最小值返回一列数据在一段期间的最小值。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 30
# df['MIN'] = ta.MIN(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['MIN']])

# MININDEX最小值索引
'''
MININDEX最小值索引返回该最小值的索引。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 30
# df['MININDEX'] = ta.MININDEX(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['MININDEX']])

# MINMAX最小最大值
'''
MINMAX最小值最大值用来计算一列数据一段时间内的最小值和最大值。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 30
# df['MIN'], df['MAX'] = ta.MINMAX(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['MIN', 'MAX']])

# MINMAXINDEX最小最大值索引
'''
MINMAXINDEX最小最大值索引返回最小值和最大值的索引。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 30
# df['MINIDX'], df['MAXIDX'] = ta.MINMAXINDEX(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['MINIDX', 'MAXIDX']])

# MINUS_DI负向指标
'''
MINUS_DI负向指标通过分析股票价格在涨跌过程中买卖双方力量对比均衡点的变化情况，
即多空的力量变化受价格波动的影响而发生由均衡到失衡的循环过程，从而提供对趋势判断依据的一种技术指标。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# 计算复权
# df['开盘价_前复权'] = df['开盘价'] / df['收盘价'] * df['收盘价_前复权']
# df['最高价_前复权'] = df['最高价'] / df['收盘价'] * df['收盘价_前复权']
# df['最低价_前复权'] = df['最低价'] / df['收盘价'] * df['收盘价_前复权']
# timeperiod = 14
# df['MINUS_DI'] = ta.MINUS_DI(df['最高价_前复权'], df['最低价_前复权'], df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['MINUS_DI']])

# MINUS_DM负向运动
'''
MINUS_DM负向运动通过分析股票价格在涨跌过程中买卖双方力量均衡点的变化情况，
即多空双方的力量的变化受价格波动的影响而发生由均衡到失衡的循环过程，从而提供对趋势依据的一种技术指标。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# 计算复权
# df['开盘价_前复权'] = df['开盘价'] / df['收盘价'] * df['收盘价_前复权']
# df['最高价_前复权'] = df['最高价'] / df['收盘价'] * df['收盘价_前复权']
# df['最低价_前复权'] = df['最低价'] / df['收盘价'] * df['收盘价_前复权']
# timeperiod = 14
# df['MINUS_DM'] = ta.MINUS_DM(df['最高价_前复权'], df['最低价_前复权'], timeperiod=timeperiod)
# print(df[['MINUS_DM']])

# MOM动量
'''
MOM动量指标是指股票持续增长的能力，赢家组合在牛市中存在着正的动量效应，输家组合存在负的动量效应。
一般以12日为周期，当MOM>2时，预示着上升趋势将减弱，当MOM<-2时，预示着下降趋势将减弱；
25日MOM动量上穿0轴，代表中期多头走势确立；下穿0轴，代表中期空头走势确立。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 12
# df['MOM'] = ta.MOM(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['MOM']])

# MULT乘法
'''
MULT乘法用来计算两列数据的积。
'''
# 设置数据
# data = {'1': [0.2, 1.6, 1.8], '2': [5, 5, 5]}
# df = pd.DataFrame(data)
# print(df)
# df['MULT'] = ta.MULT(df['1'], df['2'])
# print(df[['MULT']])

# NATR归一化平均值范围
'''
NATR归一化平均值范围是一个波动指标，用来衡量市场波动的大小变化。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# # 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# 计算复权
# df['开盘价_前复权'] = df['开盘价'] / df['收盘价'] * df['收盘价_前复权']
# df['最高价_前复权'] = df['最高价'] / df['收盘价'] * df['收盘价_前复权']
# df['最低价_前复权'] = df['最低价'] / df['收盘价'] * df['收盘价_前复权']
# timeperiod = 14
# df['NATR'] = ta.NATR(df['最高价_前复权'], df['最低价_前复权'], df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['NATR']])

# OBV能量潮
'''
OBV能量潮是一个成交量指标，技术分析理论认为价格的有效变动需要量的配合，
所谓“量在价先”，OBV可以用来验证价格走势的可靠性，也可以用来捕捉趋势可能反转的信号。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# df['OBV'] = ta.OBV(df['收盘价_前复权'], df['成交量'])
# print(df[['OBV']])

# PLUS_DI正方向指示器
'''
PLUS_DI正方向指示器是一种动量指标，请结合券商相关研报深入分析。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# # 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# 计算复权
# df['开盘价_前复权'] = df['开盘价'] / df['收盘价'] * df['收盘价_前复权']
# df['最高价_前复权'] = df['最高价'] / df['收盘价'] * df['收盘价_前复权']
# df['最低价_前复权'] = df['最低价'] / df['收盘价'] * df['收盘价_前复权']
# timeperiod = 14
# df['PLUS_DI'] = ta.PLUS_DI(df['最高价_前复权'], df['最低价_前复权'], df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['PLUS_DI']])

# PLUS_DM定向运动
'''
PLUS_DM定向运动是动量研究中的一种指标，具体参见券商研报。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# # 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# 计算复权
# df['最高价_前复权'] = df['最高价'] / df['收盘价'] * df['收盘价_前复权']
# df['最低价_前复权'] = df['最低价'] / df['收盘价'] * df['收盘价_前复权']
# timeperiod = 14
# df['PLUS_DM'] = ta.PLUS_DM(df['最高价_前复权'], df['最低价_前复权'], timeperiod=timeperiod)
# print(df[['PLUS_DM']])

# PPO价格振荡器
'''
PPO价格震荡百分比是对MACD值除以较长的移动平均值，结果再乘以100相当于百分比显示。PPO反映两条移动平均线的收敛和发散。
当较短均线在较长均线之上时，PPO为正，当该指标进一步扩大时，反映了较强的上涨势头；反之亦然。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# fastperiod = 12
# slowperiod = 26
# matype = 0
# df['PPO'] = ta.PPO(df['收盘价_前复权'], fastperiod=fastperiod, slowperiod=slowperiod, matype=matype)
# print(df[['PPO']])

# ROC变动率指标
'''
ROC变动率指标是以今天的收盘价与N天前的收盘价的差除以N天前的收盘价，并以百分比表示。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 10
# df['ROC'] = ta.ROC(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['ROC']])

# ROCP价格变化率
'''
ROCP价格变化率是当天价格与N天前的价格的差除以N天前的价格。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 10
# df['ROCP'] = ta.ROCP(df['收盘价_前复权'], timeperiod=timeperiod)
# df['ROCP'] = df['ROCP'].apply(lambda x: format(x, '.2%'))
# print(df[['ROCP']])

# ROCR价格变化率
'''
ROCR价格变化率是当天的价格除以N天前的价格。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 10
# df['ROCR'] = ta.ROCR(df['收盘价_前复权'], timeperiod=timeperiod)
# df['ROCR'] = df['ROCR'].apply(lambda x: format(x, '.2%'))
# print(df[['ROCR']])

# ROCR100价格变化率
'''
ROCR100是当天的价格除以N天前的价格再乘以100以百分比形式表示。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 10
# df['ROCR100'] = ta.ROCR100(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['ROCR100']])

# RSI相对强弱指标
'''
RSI相对强弱指标是一个反映市场景气程度的指标。一般而言，RSI超过80为超买信号，低于20为超卖信号。
当RSI与价格背离时，一般是趋势反转的信号，如价格创新低而RSI不处于新低，通常表明市场将探底回升。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 14
# df['RSI'] = ta.RSI(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['RSI']])

# SAR抛物线转向
'''
SAR抛物线转向指标也被称为停损点转向指标，当股价从SAR曲线下方开始向上突破SAR曲线时，表示可能在酝酿新一波上升行情；
当股价突破SAR曲线同时SAR曲线也向上运动时，表明上升趋势强劲。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# 计算复权
# df['最高价_前复权'] = df['最高价'] / df['收盘价'] * df['收盘价_前复权']
# df['最低价_前复权'] = df['最低价'] / df['收盘价'] * df['收盘价_前复权']
# acceleration = 0.02
# maximum = 0.2
# df['SAR'] = ta.SAR(df['最高价_前复权'], df['最低价_前复权'], acceleration=acceleration, maximum=maximum)
# print(df[['SAR']])

# SAREXT增强型抛物线转向
'''
SAREXT增强型抛物线转向与SAR用法相似。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# 计算复权
# df['最高价_前复权'] = df['最高价'] / df['收盘价'] * df['收盘价_前复权']
# df['最低价_前复权'] = df['最低价'] / df['收盘价'] * df['收盘价_前复权']
# startvalue = 0
# offsetonreverse = 0
# accelerationinitlong = 0.02
# accelerationlong = 0.02
# accelerationmaxlong = 0.2
# accelerationinitshort = 0.02
# accelerationshort = 0.02
# accelerationmaxshort = 0.2
# df['SAREXT'] = ta.SAREXT(df['最高价_前复权'], df['最低价_前复权'], startvalue=startvalue, offsetonreverse=offsetonreverse,
#                          accelerationinitlong=accelerationinitlong, accelerationlong=accelerationlong,
#                          accelerationmaxlong=accelerationmaxlong,
#                          accelerationinitshort=accelerationinitshort, accelerationshort=accelerationshort,
#                          accelerationmaxshort=accelerationmaxshort)
# print(df[['SAREXT']])

# SIN正弦值
'''
SIN正弦值用来计算一列数据的正弦值。
'''
# 设置数据
# data = {'1': [1.65, 2.3, 3.14], '2': [-1.1, -3.3, -1.9]}
# df = pd.DataFrame(data)
# print(df)
# df['SIN'] = ta.SIN(df['1'])
# print(df[['SIN']])

# SINH双曲正弦函数
'''
SINH双曲正弦函数用来计算一类数据的双曲正弦值。
'''
# 设置数据
# data = {'1': [1.85, 2.67, 3.14], '2': [-1.1, -3.3, -1.9]}
# df = pd.DataFrame(data)
# print(df)
# df['SINH'] = ta.SINH(df['1'])
# print(df[['SINH']])

# SMA简单移动平均
'''
SMA简单移动平均用来计算一段周期的移动平均线。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 30
# df['SMA'] = ta.SMA(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['SMA']])

# SQRT平方根
'''
SQRT平方根是一个基本的数学操作函数，用来计算一列数据的平方根。
'''
# 设置数据
# data = {'1': [4, 16, 25], '2': [-1.1, -3.3, -1.9]}
# df = pd.DataFrame(data)
# print(df)
# df['SQRT'] = ta.SQRT(df['1'])
# print(df[['SQRT']])

# STDDEV标准偏差
'''
STDDEV标准偏差是一种通过将价格范围与其移动平均线联系起来来衡量价格波动的方法。
指标值越大，价格与移动平均线的价差越大，分析标的的波动性越大，一般需要结合其他指标如布林带进行综合分析。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 5
# nbdev = 1
# df['STDDEV'] = ta.STDDEV(df['收盘价_前复权'], timeperiod=timeperiod, nbdev=nbdev)
# print(df[['STDDEV']])

# STOCH指标
'''
STOCH指标就是我们常用的KDJ指标中的KD指标，是由一条快速确认线和一条慢速主干线组成。
一般而言，当STOCH指标下穿20并减小到10以下，之后快线又上穿慢线并超过20，买入信号形成；
当STOCH指标上穿80并增加到90以上，之后快线又下穿慢线并低于80，卖出信号形成。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# 计算复权
# df['最高价_前复权'] = df['最高价'] / df['收盘价'] * df['收盘价_前复权']
# df['最低价_前复权'] = df['最低价'] / df['收盘价'] * df['收盘价_前复权']
# fastk_period = 5
# slowk_period = 3
# slowk_matype = 0
# slowd_period = 3
# slowd_matype = 0
# df['SLOWK'], df['SLOWD'] = ta.STOCH(df['最高价_前复权'], df['最低价_前复权'], df['收盘价_前复权'], fastk_period=fastk_period,
#                                     slowk_period=slowk_period, slowk_matype=slowk_matype, slowd_period=slowd_period,
#                                     slowd_matype=slowd_matype)
# print(df[['SLOWK', 'SLOWD']])

# STOCHF快速STOCH指标
'''
STOCHF快速STOCH指标是用法与STOCH指标相似。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# 计算复权
# df['最高价_前复权'] = df['最高价'] / df['收盘价'] * df['收盘价_前复权']
# df['最低价_前复权'] = df['最低价'] / df['收盘价'] * df['收盘价_前复权']
# fastk_period = 5
# fastd_period = 3
# fastd_matype = 0
# df['FASTK'], df['FASTD'] = ta.STOCHF(df['最高价_前复权'], df['最低价_前复权'], df['收盘价_前复权'],
#                                      fastk_period=fastk_period,
#                                      fastd_period=fastd_period, fastd_matype=fastd_matype)
# print(df[['FASTK', 'FASTD']])

# STOCHRSI随机强弱指数
'''
STOCHRSI随机强弱指标是一个特别适用于震荡市分析的波幅分析指标，它是基于RSI指标演变而来，
一般认为，当STOCHRSI的值大于0.8时，即现在的RSI相当接近过去一段时间最高的RSI，这是典型的超买信号；
反之，若STOCHRSI的值小于0.2表明RSI接近历史底部，形成超卖信号，可考虑分阶段择机买入。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 14
# fastk_period = 5
# fastd_period = 3
# fastd_matype = 0
# df['FASTK'], df['FASTD'] = ta.STOCHRSI(df['收盘价_前复权'], timeperiod=timeperiod, fastk_period=fastk_period,
#                                        fastd_period=fastd_period, fastd_matype=fastd_matype)
# print(df[['FASTK', 'FASTD']])

# SUB减法
'''
SUB是基本的数学操作函数，用来返回两列数的差。
'''
# 设置数据
# data = {'1': [100, 200, 300], '2': [50, 150, 250]}
# df = pd.DataFrame(data)
# print(df)
# df['SUB'] = ta.SUB(df['1'], df['2'])
# print(df[['SUB']])

# SUM加法
'''
SUM是一个基本数学操作函数，用来返回两列数的和。
'''
# 设置数据
# data = {'1': [100, 200, 300], '2': [150, 50, -50]}
# df = pd.DataFrame(data)
# print(df)
# df['SUM'] = ta.SUM(df['1'], df['2'])
# print(df[['SUM']])

# T3三指数移动平均
'''
T3是一种采用信号处理方法计算均线的方法，它的目的是既可以准确反映股价的走势，又不会有严重的滞后性。
T3使用方法和普通移动均线相似。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 5
# vfactor = 0.7
# df['T3'] = ta.T3(df['收盘价_前复权'], timeperiod=timeperiod, vfactor=vfactor)
# print(df[['T3']])

# TAN正切
'''
TAN正切是一个基本的数学操作函数，用来计算一列数据的正切值。
'''
# 设置数据
# data = {'1': [0.75, 1.2, 2], '2': [2, 1.4, 1.8]}
# df = pd.DataFrame(data)
# print(df)
# df['TAN'] = ta.TAN(df['1'])
# print(df[['TAN']])

# TANH双曲正切函数
'''
TANH双曲正切函数是一个基本的数学操作函数，用来计算一列数据的双曲正切值。
'''
# 设置数据
# data = {'1': [0.75, 1.2, 2], '2': [2, 1.4, 1.8]}
# df = pd.DataFrame(data)
# print(df)
# df['TANH'] = ta.TANH(df['1'])
# print(df[['TANH']])

# TEMA三重指数移动平均线
'''
TEMA三重指数移动平均线是一个比普通EMA更平滑且更快速的版本，根据TEMA进行交易方法与DEMA指标进行交易相似。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 30
# df['TEMA'] = ta.TEMA(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['TEMA']])

# TRANGE真实范围
'''
TRANGE真实范围计算一个真正的范围，请结合券商相关研报进一步分析。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# 计算复权
# df['最高价_前复权'] = df['最高价'] / df['收盘价'] * df['收盘价_前复权']
# df['最低价_前复权'] = df['最低价'] / df['收盘价'] * df['收盘价_前复权']
# df['TRANGE'] = ta.TRANGE(df['最高价_前复权'], df['最低价_前复权'], df['收盘价_前复权'])
# print(df[['TRANGE']])

# TRIMA三角移动平均线
'''
TRIMA三角移动平均线是一种相对平滑和快速的移动平均线，用法与普通移动平均线相似。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 30
# df['TRIMA'] = ta.TRIMA(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['TRIMA']])

# TRIX三重指数平滑平均线
'''
TRIX三重指数平滑平均线比较适用于长线操作，一般用法为，TRIX向上交叉其TMA线时，选择买入；
TRIX向下交叉其TMA均线时，选择卖出。TRIX与价格发生背离时，可能趋势即将终结。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 30
# df['TRIX'] = ta.TRIX(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['TRIX']])

# TSF时间序列预测
'''
TSF用于时间序列研究，请结合券商相关研报进一步分析。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 14
# df['TSF'] = ta.TSF(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['TSF']])

# TYPPRICE典型价格
'''
TYPPRICE典型价格用来计算每日价格的平均值，一般作为趋势指标的参考。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# 计算复权
# df['最高价_前复权'] = df['最高价'] / df['收盘价'] * df['收盘价_前复权']
# df['最低价_前复权'] = df['最低价'] / df['收盘价'] * df['收盘价_前复权']
# df['TYPPRICE'] = ta.TYPPRICE(df['最高价_前复权'], df['最低价_前复权'], df['收盘价_前复权'])
# print(df[['TYPPRICE']])

# ULTOSC极限振子
'''
ULTOSC极限振子是一种动量指标，请结合券商研报进一步分析。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# 计算复权
# df['最高价_前复权'] = df['最高价'] / df['收盘价'] * df['收盘价_前复权']
# df['最低价_前复权'] = df['最低价'] / df['收盘价'] * df['收盘价_前复权']
# timeperiod1 = 7
# timeperiod2 = 14
# timeperiod3 = 28
# df['ULTOSC'] = ta.ULTOSC(df['最高价_前复权'], df['最低价_前复权'], df['收盘价_前复权'])
# print(df[['ULTOSC']])

# VAR指标
'''
VAR指标基于移动平均线，它是附带噪声滤波器的移动平均线。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 5
# nbdev = 1
# df['VAR'] = ta.VAR(df['收盘价_前复权'], timeperiod=timeperiod, nbdev=nbdev)
# print(df[['VAR']])

# WCLPRICE加权收盘价
'''
WCLPRICE加权收盘价是对各段时间的收盘价予以权重，从而可以过滤掉极端数据的一种指标。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# 计算复权
# df['最高价_前复权'] = df['最高价'] / df['收盘价'] * df['收盘价_前复权']
# df['最低价_前复权'] = df['最低价'] / df['收盘价'] * df['收盘价_前复权']
# df['WCLPRICE'] = ta.WCLPRICE(df['最高价_前复权'], df['最低价_前复权'], df['收盘价_前复权'])
# print(df[['WCLPRICE']])

# WILLR威廉指标
'''
WILLR威廉指标是一种用来判断市场是否处于超买或超卖状态的指标。
一般而言，当威廉指标高于85时，表明市场当前处于超卖状态；当威廉指标低于15时，市场处于超买状态。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# 计算复权
# df['最高价_前复权'] = df['最高价'] / df['收盘价'] * df['收盘价_前复权']
# df['最低价_前复权'] = df['最低价'] / df['收盘价'] * df['收盘价_前复权']
# timeperiod = 14
# df['WILLR'] = ta.WILLR(df['最高价_前复权'], df['最低价_前复权'], df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['WILLR']])

# WMA 加权移动平均线
'''
WMA加权移动平均线是根据距离当日天数加权计算后的移动平均线，距离当前价格越近的日期权重越大。
'''
# df = pd.read_csv('sh600000.csv', skiprows=1, parse_dates=['交易日期'], encoding='utf-8')
# print(df)
# 计算复权因子
# df['复权因子'] = (df['收盘价'] / df['前收盘价']).cumprod()
# df['收盘价_前复权'] = df['复权因子'] * (df.iloc[-1]['收盘价'] / df.iloc[-1]['复权因子'])
# timeperiod = 30
# df['WMA'] = ta.WMA(df['收盘价_前复权'], timeperiod=timeperiod)
# print(df[['WMA']])