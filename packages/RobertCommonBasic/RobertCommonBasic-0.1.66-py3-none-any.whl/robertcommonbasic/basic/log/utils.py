import logging
import sys
import time
from datetime import datetime
from colorama import init
from inspect import stack
from re import search
from typing import Any, Optional
from traceback import StackSummary, walk_stack
from logging.handlers import TimedRotatingFileHandler

from ..os.path import create_dir_if_not_exist
from ..os.file import get_file_folder, get_file_name


LOG_FORMAT = '[%(asctime)s] level: [%(levelname)s] module: [%(filename)s] func: [%(funcName)s] lineno: [%(lineno)d] msg: [%(message)s]'
LOG_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


class MyLoggerHandler(logging.Handler):

    def __init__(self, *args, **kargs):
        logging.Handler.__init__(self, *args, **kargs)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
        except Exception:
            self.handleError(record)


class MyLogLevel:
    CRITICAL = 50
    FATAL = CRITICAL
    ERROR = 40
    WARNING = 30
    WARN = WARNING
    INFO = 20
    DEBUG = 10
    NOTSET = 0


class MyLogRecord(object):
  
    def __init__(self, msg, log_level: int = MyLogLevel.INFO, fmt: str = LOG_FORMAT, log_time_fmt: str = LOG_TIME_FORMAT, **kwargs):
        self.fmt = fmt
        self.tm = time.time()
        self.utc = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(int(self.tm)))
        _stack = kwargs.get('stack')
        _stack = _stack if isinstance(_stack, list) and len(_stack) >= 4 else stack(0)[1]   # [0, filename, funcName, lineno]
        self.record = {'level': log_level, 'levelname': '{0:<5s}'.format(logging.getLevelName(log_level))[:5], 'utc': self.utc, 'asctime': time.strftime(log_time_fmt, time.localtime(self.tm)) if kwargs.get('is_utc', False) is False else self.utc, 'message': msg, 'filename': get_file_name(_stack[1]), 'funcName': _stack[3], 'lineno': _stack[2], **kwargs}

    def format_msg(self, fmt: Optional[str] = None) -> str:
        return f"{self.fmt % self.record}" if fmt is None else f"{fmt % self.record}"

    def format_source_msg(self, fmt: str = '[%(asctime)s] level: [%(levelname)s] module: [%(filename)s] msg: [%(message)s] source: [%(source)s]') -> str:
        return f"{fmt % self.record}"

    def get_msg(self, key: str = 'message'):
        return str(self.record.get(key))

    def get_record(self, columns: Optional[dict] = None) -> dict:
        record = {}
        if isinstance(columns, dict) and len(columns) > 0:
            for k, v in columns.items():
                record[v] = self.record.get(k)
        else:
            record = self.record
        return record

    def print_str(self, simple_fmt: str = '[%(asctime)s] level: [%(levelname)s] module: [%(filename)s] msg: [%(message)s]', source_fmt: str = '[%(asctime)s] level: [%(levelname)s] module: [%(filename)s] msg: [%(message)s] source: [%(source)s]') -> str:
        source = self.record.get('source')
        if source is None:      # 通讯日志
            return self.format_source_msg(simple_fmt)
        else:       # 点位日志
            return self.format_source_msg(source_fmt)

    def print(self, simple_fmt: str = '[%(asctime)s] level: [%(levelname)s] module: [%(filename)s] msg: [%(message)s]', source_fmt: str = '[%(asctime)s] level: [%(levelname)s] module: [%(filename)s] msg: [%(message)s] source: [%(source)s]'):
        print(self.print_str(simple_fmt, source_fmt))


class MyStdout:

    def __init__(self, autoreset: bool = True):
        init(autoreset=autoreset)
        self.stdout_bak = sys.stdout
        self.stderr_bak = sys.stderr
        self.stdout = self
        self.stderr = self

    def write(self, info):
        if info.find('[INFO ]') >= 0:
            info = f"\033[1;30m{info}\033[0m"
        elif info.find('DEBUG') >= 0:
            info = f"\033[1;34m{info}\033[0m"
        elif info.find('[WARNI]') >= 0:
            info = f"\033[1;33m{info}\033[0m"
        elif info.find('[ERROR]') >= 0:
            info = f"\033[1;31m{info}\033[0m"
        else:
            info = f"\033[1;30m{info}\033[0m"
        self.stdout_bak.write(info)

    def flush(self):
        pass


def utc(sec, what):
    return datetime.utcnow().timetuple()


def init_log(file_path: str, log_level: int, log_interval: int = 1, log_backup: int = 30, log_time_fmt: str = LOG_TIME_FORMAT, attach_handles: list = [], log_format: str = LOG_FORMAT, **kwargs):
    file_folder = get_file_folder(file_path)
    if create_dir_if_not_exist(file_folder) is True:
        handler_file = TimedRotatingFileHandler(filename=file_path, when="D", interval=log_interval, backupCount=log_backup, utc=kwargs.get('is_utc', False))
        handler_file.suffix = "%Y-%m-%d_%H-%M.log"
        handler_file.setLevel(log_level)
        attach_handles.append(handler_file)
        if kwargs.get('is_utc', False) is True:
            logging.Formatter.converter = utc
        return logging.basicConfig(level=log_level, format=log_format, datefmt=log_time_fmt, handlers=attach_handles)


def convert_msg(log_content: str, default_fmt: str = r'\[(?P<asctime>.*?)] level: \[(?P<level>.*?)] module: \[(?P<module>.*?)] func: \[(?P<func>.*?)] lineno: \[(?P<lineno>.*?)] msg: \[(?P<msg>.*)]', source_fmt: str = r'\[(?P<asctime>.*?)] level: \[(?P<level>.*?)] module: \[(?P<module>.*?)] source: \[(?P<source>.*?)] msg: \[(?P<msg>.*)]'):
    if log_content.find('] level: [') > 0:
        if log_content.find('] source: [') > 0:     #点错误
            result = search(source_fmt, log_content)
        else:
            result = search(default_fmt, log_content)
        if result is not None:
            return result.groupdict()
    return log_content


def format_log(log_content: Any):
    func = stack()[1]
    return {'file': get_file_name(func[1]), 'func': func[3], 'lineno': func[2], 'msg': log_content}


def _get_normalized_locals_text(locals_dict) -> str:
    var_text_list = []
    for var_name, var_value in locals_dict.items():
        if var_name.startswith('__') or var_name == 'self':
            continue
        var_text_list.append(f"{var_name}={str(var_value)[:200]}")
    return ', '.join(var_text_list)


def log_unhandled_error(**kwargs):
    stacks = StackSummary.extract(walk_stack(None), limit=kwargs.get('limit', 2), capture_locals=kwargs.get('capture_locals', True))
    stack_len = len(stacks)
    if stack_len == 0:
        locals_text = "NO_STACK"
    elif stack_len == 1:
        locals_text = _get_normalized_locals_text(stacks[0].locals)
    else:
        locals_text = _get_normalized_locals_text(stacks[1].locals)
    logging.error(f"Unhandled exception! Locals: {locals_text}.", exc_info=kwargs.get('exc_info', False), stack_info=kwargs.get('stack_info', False))
