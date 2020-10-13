"""
提示：
    1、代码注释部分，有“修改”、“不需修改”字样的，如果是小白，建议按注释执行。大佬就随意了。
    2、第111行代码（ <div id="main" style="width: 1200px;height:800px;"></div> ），其中的1200、800分别为宽、高，
    可根据自己屏幕的分辨率进行修改，
    3、然后，作图的数据源的df_draw，字段必须是这样，signal是图上出信号用的，那三个就是三条线，如果你增加字段就可以是四、五、六条了，字段名无所谓
    ['candle_begin_time', 'open', 'high', 'low', 'close', 'volume', 'median', 'upper', 'lower', 'signal']
    其中，df_draw的前几个字段必须是'candle_begin_time', 'open', 'high', 'low', 'close', 'volume'，顺序不要改变；
    signal字段必须有，最好放在最后。
    其它的字段，就是画图上的线。上面的是三条线：上中下轨。增加一个字段，就会增加一条线，数量可增加很多。
    函数执行完后，会生成一个my_echarts.html文件，用浏览器打开这个文件即可
"""

from datetime import datetime, timedelta
import pandas as pd
from pprint import pformat
import numpy as np

# --------------根据要画图的策略和参数进行修改，开始处---------------------------------------------
exchange = 'bitfinex'  # 只用于显示，可以是任意字符串，可修改
symbol = 'ETH/USD'  # 只用于显示，可以是任意字符串，可修改
file_path = r'D:\MyRepository\my_backtest\data\raw\ETH-USDT_5m.h5'  # 数据文件的位置，可修改，必填
start_time = '2019-11-10'  # 起始日期，可修改，必填
end_time = '2020-12-10'  # 终止日期，可修改，必填
strategy_name = 'signal_bolling'  # 策略函数名称，必须与策略函数名一致，可修改，必填
time_interval = '15T'  # 策略周期，可修改，必填
para = [100, 3]  # 策略参数，根据实际策略需要改，可以多参数，如[200, 2, 12, 3]等等，可修改，必填


# 策略函数，根据自己魔改的实际策略函数进行粘贴即可，可修改，必填
def signal_bolling(df, para=[200, 2]):
    """
    传统布林策略
    """
    n = int(para[0])
    m = float(para[1])

    # ===计算指标
    # 计算均线
    df['median'] = df['close'].rolling(n, min_periods=1).mean()
    # 计算上轨、下轨道
    df['std'] = df['close'].rolling(n, min_periods=1).std(ddof=0)
    df['upper'] = df['median'] + m * df['std']
    df['lower'] = df['median'] - m * df['std']

    # ===找出做多信号
    condition1 = (df['close'] > df['upper'])  # 当天的收盘价 > 上轨
    condition2 = (df['close'].shift() <= df['upper'].shift())  # 昨天的收盘价 <= 上轨
    df.loc[condition1 & condition2, 'signal_long'] = 1  # 将买入信号当天的signal设置为1

    # ===找出做空信号
    condition1 = (df['close'] < df['lower'])  # 当天的收盘价 < n1日的最低价，做空
    condition2 = (df['close'].shift() >= df['lower'].shift())
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # ===找出做多平仓
    condition1 = (df['close'] < df['median'])  # 当天的收盘价 < 中轨
    condition2 = (df['close'].shift() >= df['median'].shift())  # 昨天的收盘价 >= 中轨
    df.loc[condition1 & condition2, 'signal_long'] = 0  # 将卖出信号当天的signal设置为0

    # ===找出做空平仓
    condition1 = (df['close'] > df['median'])  # 当天的收盘价 > n2日的最高价，做空平仓
    condition2 = (df['close'].shift() <= df['median'].shift())
    df.loc[condition1 & condition2, 'signal_short'] = 0  # 将卖出信号当天的signal设置为0

    # ===将long和short合并为signal
    df['signal_short'].fillna(method='ffill', inplace=True)
    df['signal_long'].fillna(method='ffill', inplace=True)
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1)
    df['signal'].fillna(value=0, inplace=True)

    # ===将signal中的重复值删除
    temp = df[['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp

    # df.drop(['median', 'std', 'upper', 'lower', 'signal_long', 'signal_short'], axis=1, inplace=True)
    df.drop(['std', 'signal_long', 'signal_short'], axis=1, inplace=True)

    return df


# -------------根据要画图的策略和参数进行修改，结束处---------------------------------------------

# ========不需修改部分，开始处====================================================================
def transfer_to_period_data(df, rule_type='15T'):
    # =====转换为其他分钟数据
    period_df = df.resample(rule=rule_type, on='candle_begin_time', label='left', closed='left').agg(
        {'open': 'first',
         'high': 'max',
         'low': 'min',
         'close': 'last',
         'volume': 'sum',
         })
    period_df.dropna(subset=['open'], inplace=True)  # 去除一天都没有交易的周期
    period_df = period_df[period_df['volume'] > 0]  # 去除成交量为0的交易周期
    period_df.reset_index(inplace=True)
    df = period_df[['candle_begin_time', 'open', 'high', 'low', 'close', 'volume']]
    return df  #


def get_echart_html(symbol, trade_data, boll_data, signal_data, type):
    _df_list = np.array(trade_data).tolist()  # 把_df转成list
    str_df_list = pformat(_df_list)

    _df_boll_list = np.array(boll_data).transpose().tolist()  # 把_df_boll转成list
    str_df_boll_list = pformat(_df_boll_list)

    title = symbol.split('_')[0] + '_' + symbol.split('_')[1]
    my_list = list(boll_data.columns)
    my_list[0] = 'k线'

    echarts_data = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>ECharts</title>
        <!-- 引入 echarts.js -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/echarts/4.2.0-rc.2/echarts.min.js"></script>
    </head>
    <body>
        <!-- 为ECharts准备一个具备大小（宽高）的Dom -->
        <div id="main" style="width: 1920px;height:960px;"></div>
        <script type="text/javascript">

            // 基于准备好的dom，初始化echarts实例
            var myChart = echarts.init(document.getElementById('main'));
            var upColor = '#ec0000';
            var upBorderColor = '#8A0000';
            var downColor = '#00da3c';
            var downBorderColor = '#008F28';

            function splitData(rawData) {
                var categoryData = [];
                var values = []
                for (var i = 0; i < rawData.length; i++) {
                    categoryData.push(rawData[i].splice(0, 1)[0]);
                    values.push(rawData[i])
                }
                return {
                    categoryData: categoryData,
                    values: values
                };
            }
            var data0 = splitData(%s) // 1            
            var data1 = %s // 2


        option = {
            title: {
                text: '%s', // 3
                left: 0
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                },   
            },
            legend: {
                data: %s
            },
			grid: [
				{
					left: '10%%',
					right: '10%%',
					bottom: 190,
				},
				{
					left: '10%%',
					right: '10%%',
					height: 80,
					bottom: 80,
				}
			],
            xAxis: [{
                gridIndex: 0, 
                type: 'category',
                data: data0.categoryData,
                scale: true,
                boundaryGap : false,
                axisLine: {onZero: false},
                splitLine: {show: false},
                splitNumber: 20,
            },
            {
				gridIndex: 1,
				type: 'category',
				scale: true,
				boundaryGap: false,
				axisLine: {onZero: false},
				splitLine: {show: false},
				}
			],
            yAxis: [{
                gridIndex: 0, 
                scale: true,
                splitArea: {show: true}
            },
            {
				scale: true,
				gridIndex: 1,
				splitNumber: 2,
				axisLabel: {show: false},
				axisLine: {show: false},
				axisTick: {show: false},
				splitLine: {show: false},
				}
			],
            dataZoom: [
                {
                    type: 'inside',
                    start: 50,
                    end: 100
                },
                {
                    show: true,
                    type: 'slider',
                    y: '90%%',
                    start: 50,
                    end: 100
                }
            ],
            series: [
                {
                    name: 'k线',
                    type: 'candlestick',
                    xAxisIndex: 0,
					yAxisIndex: 0,
                    data: data0.values,
                    itemStyle: {
                        normal: {
                            color: upColor,
                            color0: downColor,
                            borderColor: upBorderColor,
                            borderColor0: downBorderColor
                        }
                    },
                    markPoint: {    
                        label: {    
                            normal: {   
                                show:true,
                                formatter: function (param) {   
                                    return param != null ? Math.round(param.value) : '';
                                }
                            }
                        },
                        data: %s //4
                        tooltip: {     
                            formatter: function (param) {
                                return param.name + '<br>' + (param.data.coord || '');
                            }
                        }
                    },                    
                },
    """ % (str_df_list, str_df_boll_list, title, str(my_list), signal_data)

    for i in range(len(boll_data.columns) - 1):
        echarts_data += """
                    {
                        name: '%s',
                        type: 'line',
                        xAxisIndex: %s,
					    yAxisIndex: %s,
                        data: data1[%s],
                        smooth: true,
                        lineStyle: {
                            normal: {opacity: 0.5}
                        }
                    },""" % (boll_data.columns[i + 1], str(type - 1), str(type - 1), i + 1)

    echarts_data += """
            ]
        };
                    // 使用刚指定的配置项和数据显示图表。
                myChart.setOption(option);
                window.onresize = myChart.resize;   
                document.write("%s<br>")
                </script>
            </body>
        </html>""" % symbol

    return echarts_data


def my_echarts(EX, symbol, type, strategy, time_interval, para, df):
    print(strategy)
    print(time_interval)
    print(para)

    JJJ = '%s_%s_%s_%s_%s' % (EX.upper(), symbol, strategy, time_interval, str(para))
    # rule_type = time_interval.replace('m', 'T')
    print(JJJ)

    # 把除了空值外为none的去除画图时才不会出错
    mylist = list(df.columns)
    mylist.remove('signal')
    df.dropna(axis=0, how='any', subset=mylist, inplace=True)

    # 取得指標的dataframe
    df['candle_begin_time'] = df['candle_begin_time'].apply(str)
    _df_boll = df.drop(['candle_begin_time', 'open', 'high', 'low', 'close', 'signal'], axis=1)
    # 取得開高低收的dataframe
    _df = df[['candle_begin_time', 'open', 'close', 'low', 'high']]
    # 把有信号的点标记出来
    signal = '['
    if 'signal' in df.columns.tolist():
        x = list(df[df['signal'].notnull()]['candle_begin_time'])  # 有信号的时间之list
        y = list(df[df['signal'].notnull()]['high'])  # 有信号的最高价之list, 标记在最高价才不会檔到k线
        z = list(df[df['signal'].notnull()]['signal'])
        signal = '['
        for i in zip(x, y, z):  # rgb(41,60,85)
            if i[2] == 1:
                temp = "{coord:['" + str(i[0]) + "'," + str(i[
                                                                1]) + "], label:{ normal: { formatter: function (param) { return \"买\";}} } ,itemStyle: {normal: {color: 'rgb(214,18,165)'}}},"
            elif i[2] == -1:
                temp = "{coord:['" + str(i[0]) + "'," + str(
                    i[
                        1]) + "] , label:{ normal: { formatter: function (param) { return \"卖\";}} } ,itemStyle: {normal: {color: 'rgb(0,0,255)'}}},"
            else:
                temp = "{coord:['" + str(i[0]) + "'," + str(
                    i[
                        1]) + "], label:{ normal: { formatter: function (param) { return \"平仓\";}} },itemStyle: {normal: {color: 'rgb(224,136,11)'}}},"

            signal += temp
    signal = signal.rstrip(',')
    signal += '],'  # 为 echarts_data 里面的 signal_data

    _html = get_echart_html(JJJ, _df, _df_boll, signal, type)

    with open('my_echarts.html', 'w', encoding='utf-8') as f:
        f.write(_html)
    return _html


def get_df_with_signal(df, strategy, rule_type):
    # 先去除起點之前的candle
    df = df[df['candle_begin_time'] >= pd.to_datetime(start_time)]
    df = df[df['candle_begin_time'] < pd.to_datetime(end_time)]
    df = df.sort_values(by='candle_begin_time', ascending=True)
    df.reset_index(inplace=True, drop=True)
    # 先把資料庫的data轉成實盤rule_type的分鐘k線
    df = transfer_to_period_data(df, rule_type)
    # 因為rasample過，所以最後一根不要取，會不完整
    df = df.iloc[0:-1, :]
    # 原始数据是utc的话，要加这一行，加8个小时
    df['candle_begin_time'] = df['candle_begin_time'] + timedelta(hours=8)
    df = eval(strategy + '(df.copy(), para)')
    print(df.tail())

    return df


# ========不需修改部分，结束处====================================================================


if __name__ == '__main__':
    df_data = pd.read_hdf(file_path, key='df')  # 读取数据文件，根据实际文件类型，可改为读csv、pkl类型的数据，可修改
    df_draw = get_df_with_signal(df_data.copy(), strategy_name, time_interval)  # 生成用于画图、带signal和上中下等多轨的df
    # ----可将修改df_draw字段和字段顺序的代码放在这里（也可以直接放在策略函数中），开始处-----------------------

    # ----可将修改df_draw字段和字段顺序的代码放在这里（也可以直接放在策略函数中），结束处-----------------------
    my_echarts(exchange, symbol, 1, strategy_name, time_interval, para, df_draw.copy())  # 画图主函数，生成html文件
