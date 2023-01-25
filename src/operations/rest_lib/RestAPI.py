from abc import ABC, abstractmethod
import json
import os
import sys


class RestAPI(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def request_get(self, api_path, timeout=30):
        pass

    @abstractmethod
    def request_post(self, api_path, params, timeout=30):
        pass

    @staticmethod
    def decode_json_response(response):
        try:
            json_response = json.loads(response)
            return json_response
        except ValueError:
            return None

    @staticmethod
    def get_rest_api_lib(connection, host, port, api_type):
        try:
            rest_lib_path = os.path.relpath(
                os.path.dirname(__file__),
                os.getcwd() if sys.path[0] == "" else sys.path[0]
            ).replace("/", ".")
            from_path = rest_lib_path.split(".")[0]
            api_module = __import__(f"{rest_lib_path}.{api_type}",
                                    fromlist=[from_path])
        except ImportError:
            raise RuntimeError(f"Invalid api_type:{api_type}")
        api_class = getattr(api_module, api_type)
        return api_class(connection, host, port)
