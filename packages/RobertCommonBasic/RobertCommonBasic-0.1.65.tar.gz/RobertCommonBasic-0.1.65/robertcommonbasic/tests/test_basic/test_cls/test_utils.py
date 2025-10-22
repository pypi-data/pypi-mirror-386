import time
from threading import currentThread
from datetime import datetime
from robertcommonbasic.basic.cls.utils import function_thread, SimpleTimer, RepeatingTimer, set_timeout_wrapper, func_timeout, FunctionTimedOut


def test1(p1, p2):
    count = 10
    while count > 0:
        print(f"{datetime.now()} {p1} {p2}")
        time.sleep(1)
        count = count - 1


def test_function_thread():
    function_thread(test1, False, p1='1', p2='2').start()


def print_time(**kwargs):
    print(f"{kwargs} {datetime.now()}")


def test_timer():
    aa = SimpleTimer()
    aa.run(5, print_time, kwargs={'abc': 123, 'force': True})
    time.sleep(2)
    #aa.cancel()
    aa.run(2, print_time, kwargs={'abc': 1235, 'force': True})
    time.sleep(5)
    print()


def test_rep_timer():
    aa = RepeatingTimer(2, print_time, kwargs={'abc': 1235})
    aa.start()
    time.sleep(10)
    aa.cancel()


@set_timeout_wrapper(5)
def test_time_out():
    while True:
        time.sleep(1)
    return 123


def test_time_out1(interval):
    while True:
        print(f"{currentThread().ident} sleep {interval}")
        time.sleep(1)
        return 123
    return 123


while True:
    try:
        func_timeout(3, test_time_out1, kwargs={'interval': 3})
    except FunctionTimedOut:
        print(f' time out')
    except Exception as e:
        print(e.__str__())
    time.sleep(1)