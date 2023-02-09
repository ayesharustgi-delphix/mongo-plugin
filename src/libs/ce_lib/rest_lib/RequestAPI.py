from .RestAPI import RestAPI


class RequestAPI(RestAPI):
    def __init__(self, connection, host, port):
        super().__init__()
        self.connection = connection
        self.host = host
        self.port = port