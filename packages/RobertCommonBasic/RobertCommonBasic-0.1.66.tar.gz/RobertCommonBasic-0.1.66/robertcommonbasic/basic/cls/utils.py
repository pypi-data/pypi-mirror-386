import logging
import inspect
import ctypes

from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
from func_timeout import func_timeout
from func_timeout.exceptions import FunctionTimedOut
from multiprocessing import Pool
from queue import Queue
from threading import Thread, Lock, Timer, Condition, enumerate as thread_enumerate, currentThread
from time import time, sleep
from typing import Callable, Optional, Union, Any


class Singleton(type):
    _instance_lock = Lock()

    def __call__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            with Singleton._instance_lock:
                if not hasattr(cls, '_instance'):
                    cls._instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instance


'''
#元类
class SingClass(metaclass=Singleton):
    def __init__(self):
        pass
'''


class SingleInstance(object):
    _instance_lock = Lock()
    _instance = None

    @classmethod
    def instance(cls, *args, **kwargs):
        if not hasattr(SingleInstance, '_instance'):
            with SingleInstance._instance_lock:
                if not hasattr(SingleInstance, '_instance'):
                    SingleInstance._instance = SingleInstance(*args, **kwargs)
        return SingleInstance._instance


def async_raise(tid, exctype):
    if not inspect.isclass(exctype):
        raise TypeError("Only types can be raised (not instances)")
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread_id: Union[int, Thread]):
    if isinstance(thread_id, Thread):
        if thread_id.is_alive() is False:
            return
        thread_id = thread_id.ident
    else:
        for thread in thread_enumerate():
            if thread.ident == thread_id:
                if thread.is_alive() is False:
                    return
                break
    async_raise(thread_id, SystemExit)


def daemon_thread(fn: Callable) -> Callable[..., Thread]:

    @wraps(fn)
    def _wrap(*args, **kwargs) -> Thread:
        return Thread(target=fn, args=args, kwargs=kwargs, daemon=True, name='daemon_thread')

    return _wrap


def function_thread(fn: Callable, daemon: bool, *args, **kwargs):
    return Thread(target=fn, args=args, kwargs=kwargs, daemon=daemon, name='function_thread')


def retry(func: Callable, retry_count: int = 3, sleep_seconds: float = 1.0, *args, **kwargs) -> Any:
    retry = 0
    result = None
    while True:
        try:
            result = func(args=args, kwargs=kwargs)
            break
        except Exception as e:
            retry += 1
            if retry >= retry_count:
                raise Exception(f'retry failed, error: {str(e)}')
            logging.warning(f'Failed at attempt: {retry}, error: {str(e)}')
            sleep(sleep_seconds)
    return result


def set_timeout_wrapper(timeout):
    def inner_set_timeout_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func_timeout(timeout, func, args=args, kwargs=kwargs)
            except FunctionTimedOut:
                raise Exception(f'func({func.__name__}) time out')
            except Exception as e:
                raise e
        return wrapper
    return inner_set_timeout_wrapper


def get_current_thread() -> tuple:
    return currentThread().ident, currentThread().getName()


def get_threads() -> dict:
    """获取线程"""
    return {item.ident: item.getName() for item in thread_enumerate()}


class RepeatingTimer:

    def __init__(self, interval, function, args=None, kwargs=None):
        self.interval = interval
        self.function = function
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}
        self._should_continue = False
        self.is_running = False
        self.thread = None

    def is_alive(self):
        return self._should_continue

    def _handle_function(self):
        self.is_running = True
        self.function(self.args, self.kwargs)
        self.is_running = False
        self._start_timer()

    def _start_timer(self):
        if self._should_continue:  # Code could have been running when cancel was called.
            self.thread = Timer(self.interval, self._handle_function)
            self.thread.start()

    def start(self):
        if not self._should_continue and not self.is_running:
            self._should_continue = True
            self._start_timer()

    def cancel(self):
        if self.thread is not None:
            self._should_continue = False  # Just in case thread is running and cancel fails.
            self.thread.cancel()


class SimpleTimer:

    def __init__(self):
        self.timer = None

    def is_running(self):
        return self.timer and self.timer.is_alive()

    def run(self, interval: int, function: Callable, *args, **kwargs):
        if self.is_running():
            if kwargs.get('force', False) is False:
                raise Exception(f"timer is running, please cancel")
            else:
                self.cancel()
        self._run_timer(interval, function, args, kwargs)

    def _run_timer(self, interval: int, function: Callable, *args, **kwargs):
        self.timer = Timer(interval, function, args, kwargs)
        self.timer.start()

    def cancel(self):
        if self.is_running():
            self.timer.cancel()
        self.timer = None


class RepeatThreadPool:

    def __init__(self, size: int, fun: Optional[Callable] = None, done_callback: Optional[Callable] = None, thread_name_prefix: str = '', **kwargs):
        self.kwargs = kwargs
        self.pool_size = size              # 线程池大小
        self.pool_fun = fun                # 线程函数
        self.pools = ThreadPoolExecutor(self.pool_size, thread_name_prefix)  # 线程池
        self.done_callback = done_callback              # 线程执行回调函数

        self.task_queue = Queue()               # 待处理队列
        self.task_cache = {}                    # 全部任务
        self.task_running = {}                  # 正在处理任务
        self.pool_status = 'running'
        self.task_finish: int = 0               # 已完成任务

    def __del__(self):
        self.pools.shutdown()
        self.pool_status = 'shutdown'

    def process_task(self):
        if self.task_queue.empty() is False and len(self.task_running) <= self.pool_size:
            task_index = self.task_queue.get()
            if isinstance(task_index, int) and task_index > 0:
                task_info = self.task_cache.get(task_index)
                if isinstance(task_info, dict):
                    task_info['process'] = time()
                    future = self.pools.submit(task_info.get('task'), *(task_info.get('args')))
                    self.task_running[future] = task_index
                    future.add_done_callback(self.future_callback)

    def add_task(self, task, task_back, *args, **kwargs) -> int:
        index = len(self.task_cache) + 1
        self.task_cache[index] = {'index': index, 'create': time(), 'task': task, 'task_back': task_back, 'args': args, 'kwargs': kwargs}
        self.task_queue.put(index)
        return index

    def submit_task(self, task: Optional[Callable], task_back: Optional[Callable], *args, **kwargs) -> int:
        if len(args) > 0:
            task = task if task else self.pool_fun
            task_back = task_back if task_back else self.done_callback
            task_index = self.add_task(task, task_back, *args, **kwargs)
            self.process_task()
            return task_index
        return 0

    def reactive_task(self, future):
        if future is not None and future in self.task_running.keys():
            del self.task_running[future]

        # 触发响应
        self.process_task()

    def future_callback(self, future):
        self.task_finish = self.task_finish + 1
        if future in self.task_running.keys():
            task_info = self.task_cache.get(self.task_running[future])
            if isinstance(task_info, dict):
                task_info['future'] = future
                task_info['result'] = future.result()
                task_info['end'] = time()
                task_info['cost'] = '{:.3f}'.format(task_info['end'] - task_info['process'])
                done_callback = task_info.get('task_back')
                if done_callback:
                    done_callback(task_info)

    def finish(self) -> bool:
        if self.task_queue.empty() is True and len(self.task_running) == 0:
            self.pool_status = 'finish'
            return True
        return False

    def done(self):
        while self.finish() is False:
            sleep(1)

    def status(self):
        return self.pool_status

    def info(self):
        return {'total': len(self.task_cache), 'running': len(self.task_running), 'finish': self.task_finish}


class SimpleThreadPool:

    def __init__(self, size: int, fun: Optional[Callable] = None, done_callback: Optional[Callable] = None, thread_name_prefix: str = '', **kwargs):
        self.kwargs = kwargs
        self.pool_size = size              # 线程池大小
        self.pool_fun = fun                # 线程函数
        self.pools = ThreadPoolExecutor(self.pool_size, thread_name_prefix)  # 线程池
        self.done_callback = done_callback              # 线程执行回调函数
        self.task_future = []

    def submit_task(self, task: Optional[Callable], *args, **kwargs):
        task = task if task else self.pool_fun
        if task is not None:
            self.task_future.append(self.pools.submit(task, *args, **kwargs))

    def done(self, dict_result: bool = True):
        results_dict = {}
        results_list = []
        for future in as_completed(self.task_future):
            result = future.result()
            if result is not None:
                if isinstance(result, dict):
                    results_dict.update(result)
                elif isinstance(result, list):
                    results_list.extend(result)
                else:
                    results_list.append(result)
        return results_dict if dict_result else results_list


class ThreadPool:

    def __init__(self, pool_size: int, pool_fun: Callable, fun_params: list, thread_name_prefix: str = ''):
        self.pool_size = pool_size
        self.pool_fun = pool_fun
        self.fun_params = fun_params
        self.thread_name_prefix = thread_name_prefix
        self.pool_cost = 0

    def run(self, dict_result: bool = True):
        start = time()
        with ThreadPoolExecutor(self.pool_size, self.thread_name_prefix) as executor:
            futures = [executor.submit(self.pool_fun, *fun_param) for fun_param in self.fun_params]

        results_dict = {}
        results_list = []
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                if isinstance(result, dict):
                    results_dict.update(result)
                elif isinstance(result, list):
                    results_list.extend(result)
                else:
                    results_list.append(result)

        self.pool_cost = '{:.3f}'.format(time() - start)
        return results_dict if dict_result else results_list

    def cost(self):
        return self.pool_cost


class MultiPool:

    def __init__(self, pool_size: int, pool_fun: Callable, fun_params: list):
        self.pool_size = pool_size
        self.pool_fun = pool_fun
        self.fun_params = fun_params
        self.pool_cost = 0

    def run(self, dict_result: bool = True):
        start = time()
        results_dict = {}
        results_list = []
        with Pool(self.pool_size) as p:
            p.map(self.pool_fun, self.fun_params)

            for result in p.imap_unordered(self.pool_fun, self.fun_params):
                if result is not None:
                    if isinstance(result, dict):
                        results_dict.update(result)
                    elif isinstance(result, list):
                        results_list.extend(result)
                    else:
                        results_list.append(result)

        self.pool_cost = '{:.3f}'.format(time() - start)
        return results_dict if dict_result else results_list

    def cost(self):
        return self.pool_cost


class WaitQueue:

    def __init__(self, lock=None):
        self.condition = Condition(lock)
        self.values = []

    def wait(self, timeout: Union[int, float, None] = None):
        with self.condition:
            return self._wait(timeout)

    def _wait(self, timeout: Union[int, float, None] = None):
        self.condition.wait(timeout)

    def notify_all(self, value=None):
        with self.condition:
            if value is not None:
                self.values.append(value)
            self.condition.notify_all()

    def notify(self, value=None, n: int = 1):
        with self.condition:
            if value is not None:
                self.values.append(value)
            self.condition.notify(n)
