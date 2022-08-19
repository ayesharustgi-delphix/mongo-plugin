from utils import setup_logger
import threading
from typing import Callable
import sys
import os

__lock = threading.Lock()


def _singleton_class(class_: Callable) -> Callable[[str], object]:
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
            ("--password ", " ")
        ]
        self.initialize_logger()

    def initialize_logger(self):
        self.logger_object = setup_logger._setup_logger(self.name)

    def mask_instance(self, log_msg, pass_key, pass_end_sep=None):
        if pass_key in log_msg:
            masked_log = ""
            pwd_split = log_msg.split(pass_key)

            masked_log += pwd_split[0]
            if pass_end_sep:
                for s in pwd_split[1:]:
                    pwd = s.split(pass_end_sep, 1)[0]
                    s = pass_key + s
                    masked_pwd = pass_key + "x" * self.masked_password_len
                    masked_str = s.replace(pass_key+pwd, masked_pwd)
                    masked_log += masked_str
            else:
                for s in pwd_split[1:]:
                    masked_pwd = "x" * self.masked_password_len
                    masked_log += masked_pwd + s

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
        msg = self.mask_password(msg)
        msg = self.format_log(msg)
        self.logger_object.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        msg = self.mask_password(msg)
        msg = self.format_log(msg)
        self.logger_object.warning(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        msg = self.mask_password(msg)
        msg = self.format_log(msg)
        self.logger_object.debug(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        msg = self.mask_password(msg)
        msg = self.format_log(msg)
        self.logger_object.error(msg, *args, **kwargs)
