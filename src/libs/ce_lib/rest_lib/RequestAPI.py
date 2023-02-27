from .RestAPI import RestAPI
from dlpx.virtualization.common import RemoteConnection


class RequestAPI(RestAPI):
    """Implements functions to access Rest API using requests python module."""
    def __init__(self, connection: RemoteConnection, host: str, port: int
                 ) -> None:
        """
        Initialise CurlAPI object with API server parameters.
        The Parameters are pulled from function parameters and 'CurlAPI.ini'.

        :param connection: Connection object of API server host
        :type connection: ``dlpx.virtualization.common.RemoteConnection``
        :param host: Host address where API server can be reached
        :type host: ``str``
        :param port: Port where API server can be reached
        :type port: ``int``

        :return: None
        :rtype: ``NoneType``
        """
        super().__init__()
        self.connection = connection
        self.host = host
        self.port = port
