class Globals:
    LAGTIMESECONDS_OUTPUT_FILE = "mongosync_lag.txt"
    SERVER_SHUTDOWN = (
        "{mongo_shell_path} admin --port {port} --quiet --eval "
        "'db.shutdownServer()'"
    )

    EXPECTED_SERVER_SHUTDOWN_ERROR = (
        "MongoNetworkError: connection 3 to 127.0.0.1:28500 closed"
    )

    # MongoDB queries
    RS_INITIATE = "{mongo_shell_path} --port {port} --quiet --eval " \
                  "'rs.initiate()'"

    # SOCKET PATH
    MONGODB_SOCKET_FILE_PATH = "/tmp/mongodb-{port}.sock"


    EXPECTED_RS_INITIATE_ERROR = "MongoServerError: already initialized"

    # Config Server defaults
    CONFIG_SERVER_RS_NAME = "configRSDlpx"
    RESTOREINFO_TXT_NAME = "restoreInfo.txt"
    CONFIG_SERVER_RESTORE_INFO_TXT_PATH = f"c0m0/{RESTOREINFO_TXT_NAME}"

    # ERROR CODES
    ERR_SERVER_SHUTDOWN = "Failed to shutdown database running at port {port}."
    ERR_RS_INITIATE = "Failed to execute rs.initiate()."
    ERR_SH_STATUS = "Failed to execute sh.status()."
    ERR_NEW_FILE_CREATION = "Failed to create a new file {file_path}."


class SupportedFormats:
    OPS_CENTER_BACKUP = ("tar", "gz")
