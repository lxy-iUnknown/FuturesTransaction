from transaction import Transaction
from data_io import load_data, save_data
from constants import COLUMN_NAMES
import pandas as pd

# https://pandas.pydata.org/docs/user_guide/indexing.html#indexing-view-versus-copy
pd.options.mode.chained_assignment = 'raise'
output = pd.DataFrame(columns=[
    COLUMN_NAMES.DATE, 'ATR', COLUMN_NAMES.HIGH, COLUMN_NAMES.LOW, COLUMN_NAMES.OPEN,
    COLUMN_NAMES.CLOSE, '入市时间', '入市类型', '入市ATR', '入市价格(元)', '多头持仓数量',
    '空头持仓数量', '前T日最高价(元)', '前T日最低价(元)', '本次入市以来最高利润(元)', '当前利润(元)',
    '离市类型', '离市时间', '离市利润'
])
transaction = Transaction(load_data(), output)
transaction.transact()
save_data(output)
