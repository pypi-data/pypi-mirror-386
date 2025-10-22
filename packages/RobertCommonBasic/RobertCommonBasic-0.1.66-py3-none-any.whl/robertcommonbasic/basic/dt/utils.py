import math
import pytz
import logging
import pandas as pd

from datetime import datetime, timedelta, tzinfo
from enum import Enum, unique
from typing import Union, NamedTuple, Tuple, Optional, Any, List
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from ..error.utils import InputDataError
from ..validation import input
from ..base.constant import DATETIME_FMT_FULL, DATETIME_FMT_DATE


@unique
class TimeInterval(Enum):
    """
    We do not follow common naming convention for the sake of IOT tradition.
    """
    s1 = 's1'
    m1 = 'm1'
    m5 = 'm5'
    h1 = 'h1'
    d1 = 'd1'
    M1 = 'M1'
    TIME_INTERVAL_RANKS = dict(s1=10, m1=20, m5=30, h1=40, d1=50, M1=60)

    def __gt__(self, other):
        other = input.assert_not_none_enum('other', other, TimeInterval)
        this_rank = self.TIME_INTERVAL_RANKS[self.value]
        that_rank = self.TIME_INTERVAL_RANKS[other.value]
        return this_rank > that_rank

    def __ge__(self, other):
        other = input.assert_not_none_enum('other', other, TimeInterval)
        this_rank = self.TIME_INTERVAL_RANKS[self.value]
        that_rank = self.TIME_INTERVAL_RANKS[other.value]
        return this_rank >= that_rank

    @property
    def delta(self):
        if self == self.s1:
            return relativedelta(seconds=1)
        if self == self.m1:
            return relativedelta(minutes=1)
        if self == self.m5:
            return relativedelta(minutes=5)
        if self == self.h1:
            return relativedelta(hours=1)
        if self == self.d1:
            return relativedelta(days=1)
        if self == self.M1:
            return relativedelta(months=1)
        raise NotImplementedError()

    @property
    def timedelta(self):
        if self == self.s1:
            return timedelta(seconds=1)
        if self == self.m1:
            return timedelta(minutes=1)
        if self == self.m5:
            return timedelta(minutes=5)
        if self == self.h1:
            return timedelta(hours=1)
        if self == self.d1:
            return timedelta(days=1)
        if self == self.M1:
            return timedelta(days=30)
        raise NotImplementedError()

    @property
    def pandas_freq(self):
        result: str = ''
        if self == self.s1:
            result = '1S'
        elif self == self.m1:
            result = '1T'
        elif self == self.m5:
            result = '5T'
        elif self == self.h1:
            result = '1H'
        elif self == self.d1:
            result = '1D'
        elif self == self.M1:
            result = '1MS'
        else:
            raise NotImplementedError()
        return result


class DateRange(NamedTuple):
    start_time: datetime
    end_time: datetime
    interval: TimeInterval


class TimeWindow(NamedTuple):
    start: datetime
    end: datetime


def time_slice(start_1: datetime, end_1: datetime, start_2: datetime, end_2: datetime, delta: timedelta) -> Tuple[Optional[TimeWindow], Optional[TimeWindow], Optional[TimeWindow]]:
    """
    Let tw_1 = TimeWindow(start_1, end_1)
    Let tw_2 = TimeWindow(start_2, end_2)
    Use tw_2 to slice tw_1 into at most 3 pieces:
        * piece before tw_2
        * piece inside tw_2
        * piece after tw_2
    """
    max_start = max(start_1, start_2)
    min_end = min(end_1, end_2)
    tw_before_2 = None
    tw_inside_2 = None
    tw_after_2 = None
    if start_1 < start_2:
        # Cases that tw_before_2 exist
        # 1: [ ]     | [   ]   | [     ]
        # 2:     [ ] |   [   ] |   [ ]
        end_before_2 = min(start_2 - delta, end_1)
        tw_before_2 = TimeWindow(start_1, end_before_2)
    if max_start <= min_end:
        # Cases that tw_inside_2 exist
        # 1: [   ]   | [     ] |   [   ] |   [ ]
        # 2:   [   ] |   [ ]   | [   ]   | [     ]
        tw_inside_2 = TimeWindow(max_start, min_end)
    if end_1 > end_2:
        # Cases that tw_after_2 exist
        # 1: [     ] |   [   ] |     [ ]
        # 2:   [ ]   | [   ]   | [ ]
        start_after_2 = max(end_2 + delta, start_1)
        tw_after_2 = TimeWindow(start_after_2, end_1)
    return tw_before_2, tw_inside_2, tw_after_2


def parse_delta(s: str, raise_on_error: bool = True):
    err_msg = f"Invalid delta str '{s}'"
    try:
        if not s:
            raise ValueError(err_msg)
        if len(s) < 2:
            raise ValueError(err_msg)
        amount = int(s[:-1])
        unit = s[-1]
        if unit == 'y':
            return relativedelta(years=amount)
        if unit == 'M':
            return relativedelta(months=amount)
        if unit == 'w':
            return relativedelta(weeks=amount)
        if unit == 'd':
            return relativedelta(days=amount)
        if unit == 'h':
            return relativedelta(hours=amount)
        if unit == 'm':
            return relativedelta(minutes=amount)
        if unit == 's':
            return relativedelta(seconds=amount)
        raise ValueError(err_msg)
    except ValueError:
        if raise_on_error:
            raise
        else:
            return None


def parse_time(s: str):
    return parse(s)


def get_datetime(time_zone: Optional[str] = None) -> datetime:
    return datetime.now() if time_zone is None or len(time_zone) == '' else datetime.now(pytz.timezone(time_zone))


def get_datetime_str(time_zone: Optional[str] = None) -> str:
    return datetime.now().strftime(DATETIME_FMT_FULL) if time_zone is None or len(time_zone) == '' else datetime.now(pytz.timezone(time_zone)).strftime(DATETIME_FMT_FULL)


def get_date(time_zone: Optional[str] = None) -> str:
    return get_datetime(time_zone).strftime(DATETIME_FMT_DATE)


def get_datetime_stamp(time_zone: Optional[str] = None) -> float:
    return get_datetime(time_zone).timestamp()


def get_datetime_from_stamp(timestamp, time_zone: Optional[str] = None):
    return datetime.fromtimestamp(timestamp) if time_zone is None else datetime.fromtimestamp(timestamp, pytz.timezone(time_zone))


def get_timezone(tz_name: str, fallback_tz_name: Optional[str] = None) -> Tuple[Any, str]:
    final_tz_name = None
    tz = None
    try:
        tz = pytz.timezone(tz_name)
        final_tz_name = tz_name
    except pytz.exceptions.UnknownTimeZoneError:
        logging.error(f"Unknown timezone {tz_name}! Fallback to {fallback_tz_name}.")

    if not tz:
        if fallback_tz_name:
            try:
                tz = pytz.timezone(fallback_tz_name)
                final_tz_name = fallback_tz_name
            except pytz.exceptions.UnknownTimeZoneError:
                logging.error(f"Unknown fallback timezone {fallback_tz_name}!")
    if not tz:
        raise InputDataError(
            f'Unknown timezone {tz_name} and fallback timezone {fallback_tz_name}'
        )

    return tz, final_tz_name


def convert_str_to_datetime(tm: str, fmt: str, time_zone: Optional[str] = None):
    tm = datetime.strptime(tm, fmt)
    if time_zone is not None:
        tm = tm.replace(tzinfo=get_timezone(str(time_zone))[0])
    return tm


def convert_time_with_timezone(tm: datetime, target_tz: str):
    target_tz = get_timezone(str(target_tz))[0]
    return tm.replace(tzinfo=target_tz)


def convert_time_by_timezone(original_time: datetime, original_tz: Union[str, tzinfo], target_tz: Union[str, tzinfo]) -> datetime:
    if not isinstance(original_time, datetime):
        raise InputDataError(f"orignial_time must be datetime object!")
    if not original_tz:
        raise InputDataError(f"original_tz cannot be None.")
    if not target_tz:
        raise InputDataError(f"target_tz cannot be None.")
    if not isinstance(original_tz, tzinfo):
        original_tz = get_timezone(str(original_tz))[0]
    if not isinstance(target_tz, tzinfo):
        target_tz = get_timezone(str(target_tz))[0]
    converted_time = original_tz.localize(original_time).astimezone(target_tz).replace(tzinfo=None)
    return converted_time


def convert_stamp(stamp: int, original_tz: Union[str, tzinfo], target_tz: Union[str, tzinfo]) -> datetime:
    if not isinstance(stamp, int):
        raise InputDataError(f"stamp must be int object!")
    if not original_tz:
        raise InputDataError(f"original_tz cannot be None.")
    if not target_tz:
        raise InputDataError(f"target_tz cannot be None.")
    if not isinstance(original_tz, tzinfo):
        original_tz = get_timezone(str(original_tz))[0]
    if not isinstance(target_tz, tzinfo):
        target_tz = get_timezone(str(target_tz))[0]

    return convert_time_by_timezone(get_datetime_from_stamp(stamp), original_tz, target_tz)


def convert_time(tm: Union[int, str, datetime], original_tz: Union[str, tzinfo, None], target_tz: Union[str, tzinfo, None], with_zone: bool = False) -> datetime:
    if isinstance(tm, str):
        tm = parse_time(tm)
    elif isinstance(tm, int):
        if isinstance(original_tz, str):
            tm = get_datetime_from_stamp(tm, original_tz)
        elif isinstance(original_tz, tzinfo):
            tm = get_datetime_from_stamp(tm, original_tz.zone)
        else:
            tm = get_datetime_from_stamp(tm)
    if original_tz and not isinstance(original_tz, tzinfo):
        original_tz = get_timezone(str(original_tz))[0]
    if target_tz and not isinstance(target_tz, tzinfo):
        target_tz = get_timezone(str(target_tz))[0]
    if not tm.tzinfo and isinstance(original_tz, tzinfo):
        tm = original_tz.localize(tm)
    if isinstance(target_tz, tzinfo):
        tm = tm.astimezone(target_tz)
    return tm if with_zone else tm.replace(tzinfo=None)


def convert_values_property_time(values: Union[dict, list, datetime], original_tz: Union[str, None], target_tz: Union[str, None]):
    """替换数据里的datetime"""
    if isinstance(values, list):
        vs = []
        for i, v in enumerate(values):
            vs.append(convert_values_property_time(v, original_tz, target_tz))
        return vs
    elif isinstance(values, dict):
        vs = {}
        for k, v in values.items():
            vs[k] = convert_values_property_time(v, original_tz, target_tz)
        return vs
    elif isinstance(values, datetime):
        return convert_time(values, original_tz, target_tz)
    return values


def align_time(input: datetime, interval: str) -> datetime:
    """时间对齐"""
    input = input.replace(second=0, microsecond=0)
    if interval == TimeInterval.m1:
        return input

    if interval == TimeInterval.m5:
        minute = int(5 * (math.floor(input.minute / 5)))
        input = input.replace(minute=minute)
        return input

    input = input.replace(minute=0)
    if interval == TimeInterval.h1:
        return input

    input = input.replace(hour=0)
    if interval == TimeInterval.d1:
        return input

    input = input.replace(day=1)
    if interval == TimeInterval.M1:
        return input

    raise ValueError(f'Invalid time interval: {interval}')


def normalize_dataframe(df: pd.DataFrame, interval: str):
    # formalize input dataframe time index
    if not isinstance(df.index, pd.DatetimeIndex):
        if 'time' in df:
            df = df.set_index('time')
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)

    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError(f'Invalid DataFrame index, {type(df.index)}, DatetimeIndex required')

    index_floor = '5T'
    if interval == TimeInterval.s1:
        index_floor = 'S'
    elif interval == TimeInterval.m1:
        index_floor = 'T'

    changes: List[str] = []
    idx = df.index.floor(index_floor)
    diff = df.index != idx
    if diff.any():
        change_map = pd.DataFrame(df.index[diff].values, index=idx[diff].values, columns=['t'])
        changes = [f"{str(t)} <= {', '.join((str(t) for t in g['t']))}" for t, g in change_map.groupby(level=0)]
        df = df.set_index(idx)

    if df.index.duplicated().any():
        changes = [f"removed: {str(t)}" for t in df[df.index.duplicated()].index]
        df = df.groupby(level=0).last()

    return df, changes