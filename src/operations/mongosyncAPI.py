from operations.rest_lib.RestAPI import RestAPI


class MongosyncAPILib:
    def __init__(self, connection, host, port, api_type="CurlAPI"):
        self.rest_obj = RestAPI.get_rest_api_lib(connection, host, port, api_type)

    def get_progress(self, timeout=30):
        result = self.rest_obj.request_get(api_path="api/v1/progress",
                                           timeout=timeout)
        return result
