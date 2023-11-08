import pathlib
import pandas as pd
import traceback

from util.constants import DATE, OPEN, CLOSE, LOW, HIGH, TR

USE_COLUMNS = (DATE, OPEN, CLOSE, LOW, HIGH, TR)
DATA_DIR = pathlib.Path(__file__).parent
DATA_FILE = DATA_DIR.joinpath('data.xlsx')
OUTPUT_FILE = DATA_DIR.joinpath('output.xlsx')

DATE_TIME_FORMAT = 'YYYY-MM-DD'


def load_data():
    # noinspection PyTypeChecker
    return pd.read_excel(DATA_FILE, usecols=USE_COLUMNS).dropna(axis=0, subset=(DATE,))


def save_data(output: pd.DataFrame):
    with pd.ExcelWriter(OUTPUT_FILE, datetime_format=DATE_TIME_FORMAT) as writer:
        # https://github.com/pandas-dev/pandas/issues/44284
        try:
            writer._datetime_format = DATE_TIME_FORMAT
        except AttributeError as e:
            print('AttributeError occurred')
            traceback.print_exception(e)
        output.to_excel(writer, index=False)
