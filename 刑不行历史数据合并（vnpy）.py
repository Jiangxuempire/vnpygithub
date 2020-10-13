# _*_coding : utf_8 _*_
'''

批量读取交易所下载的一分钟数据，然后清理成vnpy能够使用的回测数据

'''

import pandas as  pd
import os

pd.set_option('expand_frame_repr', False)  # 当列太多时，不换行
pd.set_option('display.max_rows', 1000)  # 最多显示行数
pd.set_option('precision', 6)  # 浮点数的精度

# project_dir=os.path.dirname(os.path.dirname(__file__))  #获取当前文件路径
# print(project_dir)
# csv_dir=project_dir+'ETH/'      #拼接成保存CSV文件的路径

csv_dir = r"G:\历史数据\crypto-binance-candle_pro\binance\spot_1m"
csv_files = r"G:\历史数据\crypto-binance-candle_pro\binance\vnpy_spot_1m"

csv_files_path = []


def symbol_name_set():
    """
    # 获取历史数据中所有交易对名称
    :return:
    """
    symbol_name_set = set()

    for root, dirs, files in os.walk(csv_dir):  # 通过 os.walk 方法获取 文件路径，和文件名列表
        if files:
            for f in files:
                name = f.split("-")[0]
                symbol_name_set.add(name)

    return symbol_name_set


def symbol_files():
    """
    获取 历史数据地址列表
    :return:
    """
    for root, dirs, files in os.walk(csv_dir):  # 通过 os.walk 方法获取 文件路径，和文件名列表
        if files:
            for f in files:
                if f.endswith('.csv'):  # 选择csv文件
                    file_path = os.path.join(root, f)  # 获取每个文件路径以join格式保存到列表里
                    file_path = os.path.abspath(file_path)
                    csv_files_path.append(file_path)

    return csv_files_path


if __name__ == '__main__':

    symbol_name_set = symbol_name_set()
    symbol_name = list(symbol_name_set)

    csv_files_path = symbol_files()
    # print(csv_files_path)
    for name in symbol_name:

        all_df = pd.DataFrame()

        for file in sorted(csv_files_path):

            f = file.split("\\")[-1]  # 按 \\ 来切分
            f = f.split("-")[0]  # 按 - 来切分，获取到币种名称

            if f == name:
                df = pd.read_csv(file, skiprows=1, encoding='gbk')
                df.rename(columns={"candle_begin_time": 'datetime', "open": 'open', "high": 'high',
                                   "low": 'low', "close": 'close', "volume": 'volume'}, inplace=True)  # 重命名
                df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
                all_df = all_df.append(df, ignore_index=True)  # 把所有文件拼接起来

        if len(all_df) > 100:
            # 按照开盘时间去重
            all_df.drop_duplicates(subset=['datetime'], inplace=True, keep='first')

            # 按照时间排序  ascending=1 升序  0 降序  inplace=True直接替换原来的，或者使用all_df=all_dfsort_values(by=['开盘时间'],ascending=1)
            all_df.sort_values(by=['datetime'], ascending=1, inplace=True)

            all_df.set_index('datetime', inplace=True)
            file = csv_files + "/" + str(name) + '_1min.csv'
            all_df.to_csv(file)
            print(f"{name},保存成功")
    print("全部保存成功，运行结束！！")