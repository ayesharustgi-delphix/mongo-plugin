
class MongoDBLibConstants:
    DB_VERSION_CMD = "db.version()"
    BUILD_INFO_CMD = "db.serverBuildInfo()"
    MODULES_CMD = f"{BUILD_INFO_CMD}.modules"
    USER_DETAILS_CMD = "EJSON.stringify(db.getUser('{user}'))"
    SH_STATUS = "EJSON.stringify(sh.status())"
    SH_ADD_SHARD = "EJSON.stringify(sh.addShard('{replicaset_str}'))"

    RUN_MONGODB_CMD = '{mongo_shell_path} "{host_details}" --quiet --eval "{cmd}"'

    STANDARD_CONN_STRING_ENCODING = {":": "%3A",
                                "/": "%2F",
                                "?": "%3F",
                                "#": "%23",
                                "[": "%5B",
                                "]": "%5D",
                                "@": "%40"
                                     }
    #standard_conn_string_format = "mongodb://{username}:{password}@{host_conn_string}?{additional_auth_params}/{database}"
    STANDARD_CONN_STRING_FORMAT = "mongodb://{username}:{password}@{host_conn_string}/{database}?{additional_auth_params}"


class MongoSyncConstants:
    api_method = "CurlAPI"

    mongosync_supported_version = "1.0.0"
    mongosync_supported_version_checking = "=="
    mongodb_supported_version = "6.0"
    mongodb_supported_version_checking = ">="
    mongodb_supported_type = "enterprise"

    supported_engine = "wiredTiger"

    source_user_mandatory_roles = {"readAnyDatabase", "clusterMonitor", "backup"}

    mongosync_conf_data = 'cluster0: "{src_conn_string}"\n' \
                          'cluster1: "{dst_conn_string}"\n' \
                          'logPath: "{mongosync_log_path}"\n' \
                          'port: {mongosync_port}'

    mongosync_start_cmd = "nohup bash -c '{mongosync_path} --config " \
                          "{conf_path}' > /tmp/mongosync_startup.log &"

    pause_api = "api/v1/pause"
    pause_api_params = {}

    start_api = "api/v1/start"
    start_api_params = {"source": "cluster0", "destination": "cluster1"}

    progress_api = "api/v1/progress"

    resume_api = "api/v1/resume"
    resume_api_params = {}

    commit_api = "api/v1/commit"
    commit_api_params = {}
