import pathlib
import pandas as pd
import traceback

from constants import COLUMN_NAMES

DATA_DIR = pathlib.Path(__file__).parent.joinpath('data')

DATA_FILE_NAME = DATA_DIR.joinpath('data.xlsx')
OUTPUT_FILE_NAME = DATA_DIR.joinpath('output.xlsx')

DATE_TIME_FORMAT = 'YYYY-MM-DD'
DATE_TIME_FORMAT_ATTR = '_datetime_format'


def load_data():
    return pd.read_excel(DATA_FILE_NAME, usecols=COLUMN_NAMES)\
        .dropna(axis=0, subset=(COLUMN_NAMES.DATE,))


def save_data(output: pd.DataFrame):
    with pd.ExcelWriter(OUTPUT_FILE_NAME, datetime_format=DATE_TIME_FORMAT) as writer:
        # https://github.com/pandas-dev/pandas/issues/44284
        try:
            if not getattr(writer, DATE_TIME_FORMAT_ATTR) == DATE_TIME_FORMAT:
                setattr(writer, DATE_TIME_FORMAT_ATTR, DATE_TIME_FORMAT)
        except AttributeError as e:
            print('AttributeError occurred')
            traceback.print_exception(e)
        output.convert_dtypes().to_excel(writer, index=False)
