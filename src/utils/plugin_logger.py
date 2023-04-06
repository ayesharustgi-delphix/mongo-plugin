from utils import setup_logger
import threading
from typing import Callable
import sys
import os
import re

__lock = threading.Lock()


def _singleton_class(class_: Callable):
    """
    A decorator to make sure only one object of class `LoggingLogger` is created
    for one value of `unique_logger_name`.

    :param class_: The class definition/name
    :return: The decorated function definition
    """
    _singleton_instances = {}

    def get_instance(name=None, masked_password_len=10, password_keywords=[]
                     ) -> object:
        """
        The decorated function to return the `LoggingLogger` object with the
        `unique_logger_name` name.
        """
        global __lock
        nonlocal _singleton_instances
        with __lock:
            if name not in _singleton_instances:
                _singleton_instances[name] = class_(
                    name=name,
                    masked_password_len=masked_password_len,
                    password_keywords=password_keywords
                )  # noqa
        return _singleton_instances[name]

    return get_instance


@_singleton_class
class PluginLogger:
    def __init__(self, name=None, masked_password_len=10, password_keywords=[]):
        self.name = name
        self.masked_password_len = masked_password_len
        self.password_keywords = [
            ("pwd :  '", "'"),
            ("--password ", " "),
            ("mongodb://.*?:", "@")
        ]
        self.initialize_logger()

    def initialize_logger(self):
        self.logger_object = setup_logger._setup_logger(self.name)

    def mask_instance(self, log_msg, pass_key, pass_end_sep=None):
        key_search = [x for x in re.finditer(pass_key, log_msg)]
        if key_search:
            masked_log = ""
            for k_num in range(len(key_search) + 1):
                current_start = key_search[k_num].start() if k_num < len(
                    key_search) else None
                current_end = key_search[k_num].end() if k_num < len(
                    key_search) else None
                if k_num == 0:
                    masked_log += log_msg[:current_start]
                else:
                    prev_k = key_search[k_num - 1]
                    s = log_msg[prev_k.end():current_start] if current_start is not None else log_msg[prev_k.end():]
                    s_split = s.split(pass_end_sep, 1) if pass_end_sep else [s]
                    if len(s_split) > 1:
                        masked_s = "x" * self.masked_password_len + pass_end_sep + s_split[1]
                    else:
                        masked_s = "x" * self.masked_password_len
                    masked_log += masked_s
                if current_start is not None and current_end is not None:
                    masked_log += log_msg[current_start:current_end]
            return masked_log
        return log_msg

    def mask_password(self, log_msg):
        """
        This function will check all log messages and mask passwords for the
        following use cases.
        1. multiline dictionary
        2. Protected SQL filepath
        3. Access account_name and account_key for object storage container

        :param log_msg: original log message

        :return: masked log message
        """
        log_msg = f"{log_msg}".strip()
        masked_log_msg = log_msg

        for pwd_key, pwd_sep in self.password_keywords:
            masked_log_msg = self.mask_instance(
                masked_log_msg, pwd_key, pwd_sep
            )
        return masked_log_msg.strip()

    def get_file_details(self) -> dict:
        """
        This function backtraces to the first parent file encountered and
        returns the information related to that file.

        :return: dictionary of data required to log.
        :rtype: ``dict``
        """

        sys_obj = sys._getframe(3)

        data_dict = {
            "file_name": os.path.basename(sys_obj.f_code.co_filename),
            "line_no": sys_obj.f_lineno,
            "func_name": sys_obj.f_code.co_name,
            "local_params": sys_obj.f_locals,
        }
        return data_dict

    def format_log(self, log_msg):
        log_msg = self.mask_password(log_msg)

        data_dict = self.get_file_details()

        line_no = data_dict["line_no"]
        file_name = data_dict["file_name"]
        func_name = data_dict["func_name"]
        log_msg = "[{file_name}:{line_no}:{func_name}] {orignal_msg}".format(
            file_name=file_name,
            line_no=line_no,
            orignal_msg=log_msg,
            func_name=func_name,
        )
        return log_msg

    def info(self, msg, *args, **kwargs):
        msg = self.format_log(msg)
        self.logger_object.info(msg, *args, **kwargs)
        return msg

    def warning(self, msg, *args, **kwargs):
        msg = self.format_log(msg)
        self.logger_object.warning(msg, *args, **kwargs)
        return msg

    def debug(self, msg, *args, **kwargs):
        msg = self.format_log(msg)
        self.logger_object.debug(msg, *args, **kwargs)
        return msg

    def error(self, msg, *args, **kwargs):
        msg = self.format_log(msg)
        self.logger_object.error(msg, *args, **kwargs)
        return msg

    def exception(self, msg, *args, **kwargs):
        msg = self.format_log(msg)
        self.logger_object.exception(msg, *args, **kwargs)
        return msg