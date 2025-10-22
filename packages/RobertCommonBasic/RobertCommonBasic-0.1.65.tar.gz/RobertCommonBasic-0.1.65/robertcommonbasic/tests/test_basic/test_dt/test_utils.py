from robertcommonbasic.basic.dt.utils import datetime, convert_time, get_datetime, convert_time_by_timezone, get_timezone, parse_time, get_datetime_from_stamp, convert_time_with_timezone
from datetime import timezone
import pytz


def test_time():
    nt = datetime.now()
    print(nt.tzinfo)

    nt = datetime.utcnow()
    print(nt.tzinfo)

    t1 = get_datetime('Asia/Shanghai')
    print(t1.tzinfo)

    t2 = t1.astimezone(get_timezone(str('UTC'))[0])
    print(t2.tzinfo)


def test_parse_time():
    dt1 = parse_time('03/17/2022 10:33:00 AM')
    print(dt1)

    dt2 = parse_time('03/17/2022 10:33:00 PM')
    print(dt2)

    print()


def test_timestamp():
    t = get_datetime('Etc/GMT+7')
    tt = parse_time('2022-06-06T12:15:00-07:00')

    now = datetime(2022, 6, 7, 9, 45)
    t1 = convert_time(now, 'Asia/Shanghai', 'Etc/GMT+7').replace(second=0)
    t2 = convert_time(1709554952188, None, 'Etc/GMT+7').replace(second=0)
    t3 = datetime.now().astimezone(tz=pytz.timezone('Etc/GMT+7')).replace(second=0, microsecond=0)
    tm = 1653039214
    data_time = convert_time(tm, get_timezone(str('UTC'))[0], 'Asia/Shanghai').replace(second=0).strftime("%Y-%m-%d %H:%M:%S")

    data_time1 = datetime.fromtimestamp(tm, tz=timezone.utc).replace(second=0).astimezone( tz=pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")

    print(convert_time(get_datetime(), 'Asia/Shanghai', 'UTC'))
    print(convert_time(get_datetime('UTC'), 'Asia/Shanghai', 'Asia/Shanghai'))
    print(convert_time(get_datetime('Asia/Shanghai'), 'UTC', 'UTC'))
    print(convert_time(get_datetime('Asia/Shanghai'), 'Asia/Shanghai', 'UTC'))
    print(convert_time('03/17/2022 10:33:00 AM', 'Asia/Shanghai', 'UTC'))


    tm = 1650508996
    dt = get_datetime_from_stamp(tm)
    dt1 = convert_time_by_timezone(dt, 'Asia/Shanghai', 'UTC')
    print(dt1)

    print(convert_time(1650508996, 'Asia/Shanghai', 'UTC'))


def test_timestamp1():
    tm = int(1709554952188 / 1000)
    data_time = convert_time(tm, 'Asia/Shanghai', 'Asia/Shanghai').replace(second=0).strftime("%Y-%m-%d %H:%M:%S")
    print(data_time)


def test_zone():
    print(datetime.now())
    print(get_datetime())
    print(get_datetime('Asia/Shanghai'))
    print(get_datetime('UTC'))


test_zone()