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
    # print(strategy)
    # print(time_interval)
    # print(para)

    JJJ = '%s_%s_%s_%s_%s' % (EX.upper(), symbol, strategy, time_interval, str(para))
    # rule_type = time_interval.replace('m', 'T')
    # print(JJJ)

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


def get_df_with_signal(df, strategy, rule_type=None):
    """

    """
    df = df.sort_values(by='candle_begin_time', ascending=True)
    df.reset_index(inplace=True, drop=True)
    df = df.iloc[0:-1, :]

    print(df.tail())

    return df


def get_trade(trades):
    """
    回测引擎获取成交记录后,
    """
    trade_records = pd.DataFrame(
        columns=['instrument', 'candle_begin_time', 'direction', 'offset', 'trade_price', 'signal'])
    i = -1
    for trade in trades:

        i = i + 1
        if trade.direction.value == '多':
            temp_direction = 'Long'
        elif trade.direction.value == '空':
            temp_direction = 'Short'
        if trade.offset.value == '开':
            temp_offset = 'open_position'
        elif trade.offset.value == '平':
            temp_offset = 'close_position'

        if trade.direction.value == '多':
            trade_records.loc[i] = [trade.vt_symbol, trade.datetime, temp_direction,
                                    temp_offset, trade.price, trade.volume]
        elif trade.direction.value == '空':
            trade_records.loc[i] = [trade.vt_symbol, trade.datetime, temp_direction,
                                    temp_offset, trade.price, trade.volume]

    condition1 = trade_records['offset'] == 'open_position'
    condition2 = trade_records['direction'] == 'Long'
    trade_records.loc[condition1 & condition2, 'signal'] = 1

    condition1 = trade_records['offset'] == 'open_position'
    condition2 = trade_records['direction'] == 'Short'
    trade_records.loc[condition1 & condition2, 'signal'] = -1

    condition1 = trade_records['offset'] == 'close_position'
    trade_records.loc[condition1, 'signal'] = 0

    trade_records.drop(['instrument', 'direction', 'offset', 'trade_price'], axis=1, inplace=True)
    # trade_records.to_csv("信号多空独立", index=False, mode='a')
    trade_records = trade_records.set_index("candle_begin_time")

    return trade_records


def get_history_data(data):
    dt = []
    o = []
    h = []
    l = []
    c = []
    v = []

    for bar in data:
        dt.append(bar.datetime)
        o.append(bar.open_price)
        h.append(bar.high_price)
        l.append(bar.low_price)
        c.append(bar.close_price)
        v.append(bar.volume)

    df = pd.DataFrame()
    df["candle_begin_time"] = dt
    df["open"] = o
    df["high"] = h
    df["low"] = l
    df["close"] = c
    df["volume"] = v
    df = df.set_index("candle_begin_time")

    return df


def get_merge(df1, df2):
    df = pd.merge(
        left=df1,
        right=df2,
        left_on='candle_begin_time',
        right_on='candle_begin_time',
        suffixes=['_left', '_right'],
        how='left',  # 'left', 'right', 'outer' 默认是'inner'
    )

    return df


def get_resample(df, rule='15T'):
    df['open'] = df['open'].resample(rule=rule).first()
    df['signal'] = df['signal'].resample(rule=rule).max()
    df.dropna(subset=['open'], inplace=True)
    df = df[['signal']]

    return df

