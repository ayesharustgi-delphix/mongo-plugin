from dlpx.virtualization import libs
from .RestAPI import RestAPI
import configparser
import os
from typing import Tuple, Union, List, Dict

from dlpx.virtualization.common import RemoteConnection
from ce_lib.resource import Resource
from ce_lib.plugin_exception.plugin_error import CurlException




class CurlAPI(RestAPI):
    """Implements functions to access Rest API using curl utility."""
    def __init__(self, connection: RemoteConnection, host: str, port: int,
                 resource: Resource) -> None:
        """
        Initialise CurlAPI object with API server parameters.
        The Parameters are pulled from function parameters and 'CurlAPI.ini'.

        :param connection: Connection object of API server host
        :type connection: ``dlpx.virtualization.common.RemoteConnection``
        :param host: Host address where API server can be reached
        :type host: ``str``
        :param port: Port where API server can be reached
        :type port: ``int``
        :param resource: Resource object
        :type resource: :class:``ce_lib.resource.Resource``

        :return: None
        :rtype: ``NoneType``
        """
        super().__init__()
        self.connection = connection
        self.host = host
        self.port = port
        self.curl_params = configparser.ConfigParser()
        self.curl_params.read(
            os.path.join(
                os.path.dirname(__file__),
                f"{self.__class__.__name__}.ini"
            )
        )
        self.resource = resource
        self.logger = self.resource.logger

    def request_get(
            self,
            api_path: str,
            timeout: int = 30
    ) -> Tuple[int, str, Union[None, Dict[str, Union[List, str, int]]]]:
        """
        Call GET API using Curl Utility.

        :param api_path: Path of API to be called
        :type api_path: ``str``
        :param timeout: Timeout for the GET API
        :type: ``int``

        :return: Tuple containing http_code, output string_response,
                    output json_response
        :rtype: ``Tuple[int, str, Union[None,
                    Dict[str, Union[List, str, int]]]]``
        """
        api_cmd = self.curl_params["GET"]["base_url"].format(
            timeout=timeout,
            host=self.host,
            port=self.port,
            api_path=api_path
        )
        res = self.resource.execute_bash(cmd=api_cmd, raise_exception=False)
        if res.exit_code:
            raise CurlException(exit_code=res.exit_code ,message=f"Cannot execute API, failed with error: "
                               f"{res.stderr}")
        else:
            response, http_code = res.stdout.split("DLPX_API_HTTP_CODE=")
            http_code = int(http_code)
            return http_code, response, self.__class__.decode_json_response(
                response)

    def request_post(
            self,
            api_path: str,
            params: Dict,
            timeout: int = 30
    ) -> Tuple[int, str, Union[None, Dict[str, Union[List, str, int]]]]:
        """
        Call POST API using Curl Utility.

        :param api_path: Path of API to be called
        :type api_path: ``str``
        :param params: Dictionary containing parameters for POST API
        :type params: ``Dict``
        :param timeout: Timeout for the POST API
        :type: ``int``

        :return: Tuple containing http_code, output string_response,
                    output json_response
        :rtype: ``Tuple[int, str, Dict[str, Union[List, str, int]]]``
        """
        param_string = f"{params}".replace("'", '"')
        api_cmd = self.curl_params["POST"]["base_url"].format(
            timeout=timeout,
            host=self.host,
            port=self.port,
            api_path=api_path,
            data_params=param_string
        )
        res = self.resource.execute_bash(cmd=api_cmd, raise_exception=False)
        if res.exit_code:
            raise CurlException(exit_code=res.exit_code ,message=f"Cannot execute API, failed with error: "
                               f"{res.stderr}")
        else:
            response, http_code = res.stdout.split("DLPX_API_HTTP_CODE=")
            http_code = int(http_code)
            return http_code, response, self.__class__.decode_json_response(
                response)
