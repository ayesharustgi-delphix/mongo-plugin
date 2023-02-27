from abc import ABC, abstractmethod
import json
import os
import sys
from typing import Union
from dlpx.virtualization.common import RemoteConnection
from ce_lib.resource import Resource


class RestAPI(ABC):
    """Abstract Class defining base functions for RestAPI."""
    def __init__(self):
        pass

    @abstractmethod
    def request_get(self, api_path: str, timeout: int = 30):
        """Abstract method for GET API."""
        pass

    @abstractmethod
    def request_post(self, api_path: str, params: dict, timeout: int = 30):
        """Abstract method for POST API."""
        pass

    @staticmethod
    def decode_json_response(response: str) -> Union[dict, None]:
        """
        Decode string into JSON object dictionary.

        :param response: string to be JSON decoded
        :type response: ``str``

        :return: json object corresponding to string
        :rtype: ``Union[dict, None]``
        """
        try:
            json_response = json.loads(response)
            return json_response
        except ValueError:
            return None

    @staticmethod
    def get_rest_api_lib(connection: RemoteConnection,
                         host: str,
                         port: int,
                         api_type: str,
                         resource: Resource
                         ):
        """
        Generates RestAPI interface class corresponding to api_type.

        :param connection: Connection object of API host
        :type connection: ``dlpx.virtualization.common.RemoteConnection``
        :param host: host address for API server
        :type host: ``str``
        :param port: Port number for API server
        :type port: ``int``
        :param api_type: string defining type of API interface
        :type api_type: ``str``
        :param resource: Resource object
        :type resource: :class:``ce_lib.resource.Resource``

        :return: RestAPI interface object corresponding to api_type.
        :rtype: ``Union[CurlAPI, RequestAPI]``
        """
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
        return api_class(connection, host, port, resource)
