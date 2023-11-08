import pandas as pd

from util.constants import DATE, HIGH, LOW, LOW_MIN, HIGH_MAX, OPEN, CLOSE, ATR
from data.data_io import load_data, save_data
from core.transaction import Transaction

output = pd.DataFrame(columns=[
    DATE, ATR, HIGH, LOW, OPEN, CLOSE, '入市时间', '入市类型', '入市ATR', '入市价格(元)', '多头持仓数量',
    '空头持仓数量', LOW_MIN, HIGH_MAX, '本次入市以来最高利润(元)', '当前利润(元)', '离市类型', '离市时间',
    '离市利润'
])
transaction = Transaction(load_data(), output)
transaction.transact()
save_data(output)
