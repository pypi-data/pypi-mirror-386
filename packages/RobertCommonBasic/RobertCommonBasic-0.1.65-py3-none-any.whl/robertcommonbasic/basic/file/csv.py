import csv
import pandas as pd
from io import StringIO, BytesIO
from typing import Union, Optional
from ..os.file import check_file_exist, get_file_folder
from ..os.path import create_dir_if_not_exist


def read_csv(path: Union[str, BytesIO, StringIO], chunksize: Optional[int] = None, parse_dates: bool = False, keep_default_na: bool = True, na_values: Optional[list] = None, names: Optional[list] = None, sep: Optional[str] = None, true_values: Optional[list] = None, false_values: Optional[list] = None, is_dict: bool = True) -> list:
    datas = pd.read_csv(path, chunksize=chunksize, low_memory=False, parse_dates=parse_dates, names=names, sep=sep, true_values=true_values, false_values=false_values, keep_default_na=keep_default_na, na_values=na_values)
    if chunksize is not None:
        return [row.to_dict() if is_dict else list(row) for data in datas for index, row in data.iterrows()]
    else:
        return [row.to_dict() if is_dict else list(row) for index, row in datas.iterrows()]


def csv_to_values(path: str, is_transpose: bool = False, is_dict: bool = True,  **kwargs) -> list:
    if check_file_exist(path) is True:
        datas = pd.read_csv(path, **kwargs) if is_transpose is False else pd.read_csv(path, **kwargs).T
        if 'chunksize' in kwargs.items():
            return [row.to_dict() if is_dict else list(row) for data in datas for index, row in data.iterrows()]
        else:
            return [row.to_dict() if is_dict else list(row) for index, row in datas.iterrows()]


def values_to_csv(values: Union[dict, list], path: str, is_append: bool = False, is_transpose: bool = False,  **kwargs):
    mode = 'a' if is_append is True else 'w'
    if check_file_exist(path) is False:
        create_dir_if_not_exist(get_file_folder(path))
        if is_transpose is False:
            pd.DataFrame(values).to_csv(path, mode=mode, encoding='utf_8_sig', **kwargs)
        else:
            pd.DataFrame(values).T.to_csv(path, mode=mode, encoding='utf_8_sig', **kwargs)
    else:
        if is_transpose is False:
            pd.DataFrame(values).to_csv(path, mode=mode, encoding='utf_8_sig', **kwargs)
        else:
            pd.DataFrame(values).T.to_csv(path, mode=mode, encoding='utf_8_sig', **kwargs)


def read_csv_rows(path: str, mode: Optional[str] = 'r', encoding: Optional[str] = None, is_dict: bool = False):
    with open(path, mode=mode, encoding=encoding) as f:
        reader = csv.reader(f) if is_dict is False else csv.DictReader(f)
        return [row for row in reader]


# 写CSV
def write_csv_rows(path: str, mode: str, values: list, encoding: Optional[str] = None, is_dict: bool = False, header_list: Optional[list] = []):
    create_dir_if_not_exist(get_file_folder(path))

    with open(path, mode=mode, encoding=encoding) as f:
        writer = csv.writer(f) if is_dict is False else csv.DictWriter(f, header_list)
        if isinstance(values, list):
            writer.writerows(values)
