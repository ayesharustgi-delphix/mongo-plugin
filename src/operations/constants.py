
class Globals:
    SERVER_SHUTDOWN = "{mongo_shell_path} admin --port {port} --quiet --eval " \
                      "'db.shutdownServer()'"

    EXPECTED_SERVER_SHUTDOWN_ERROR = "MongoNetworkError: connection 3 to 127.0.0.1:28500 closed"

    RS_INITIATE = "{mongo_shell_path} --port {port} --quiet --eval " \
                  "'rs.initiate()'"

    EXPECTED_RS_INITIATE_ERROR = "MongoServerError: already initialized"

    # ERROR CODES
    ERR_SERVER_SHUTDOWN = "Failed to shutdown database running at port {port}."
    ERR_RS_INITIATE = "Failed to execute rs.initiate()."
