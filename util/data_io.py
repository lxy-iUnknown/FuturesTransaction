import pandas as pd
import traceback

from data.data_dir import DATA_DIR
from util.constants import DATE, OPEN, CLOSE, LOW, HIGH, TR

DATA_FILE_NAME = DATA_DIR.joinpath('data.xlsx')
OUTPUT_FILE_NAME = DATA_DIR.joinpath('output.xlsx')

DATE_TIME_FORMAT = 'YYYY-MM-DD'


def load_data():
    # noinspection PyTypeChecker
    return (pd.read_excel(DATA_FILE_NAME, usecols=(DATE, OPEN, CLOSE, LOW, HIGH, TR))
            .dropna(axis=0, subset=(DATE,)))


def save_data(output: pd.DataFrame):
    with pd.ExcelWriter(OUTPUT_FILE_NAME, datetime_format=DATE_TIME_FORMAT) as writer:
        # https://github.com/pandas-dev/pandas/issues/44284
        try:
            writer._datetime_format = DATE_TIME_FORMAT
        except AttributeError as e:
            print('AttributeError occurred')
            traceback.print_exception(e)
        output.convert_dtypes().to_excel(writer, index=False)
