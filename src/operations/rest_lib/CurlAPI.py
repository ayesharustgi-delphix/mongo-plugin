from dlpx.virtualization import libs
from .RestAPI import RestAPI
import configparser
import os


class CurlAPI(RestAPI):
    def __init__(self, connection, host, port):
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

    def request_get(self, api_path, timeout=30):
        api_cmd = self.curl_params["GET"]["base_url"].format(
            timeout=timeout,
            host=self.host,
            port=self.port,
            api_path=api_path
        )
        res = libs.run_bash(self.connection, api_cmd, {})
        if res.exit_code:
            raise RuntimeError(f"Cannot execute API, failed with error: "
                               f"{res.stderr}")
        else:
            response, http_code = res.stdout.split("DLPX_API_HTTP_CODE=")
            http_code = int(http_code)
            return http_code, response, self.__class__.decode_json_response(
                response)

    def request_post(self, api_path, params, timeout=30):
        api_cmd = self.curl_params["POST"]["base_url"].format(
            timeout=timeout,
            host=self.host,
            port=self.port,
            api_path=api_path,
            data_params=params
        )
        res = libs.run_bash(self.connection, api_cmd, {})
        if res.exit_code:
            raise RuntimeError(f"Cannot execute API, failed with error: "
                               f"{res.stderr}")
        else:
            response, http_code = res.stdout.split("DLPX_API_HTTP_CODE=")
            http_code = int(http_code)
            return http_code, response, self.__class__.decode_json_response(
                response)
