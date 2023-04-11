
class MongoDBLibConstants:
    """
    Declares constants used by class MongoDB.
    """
    DB_VERSION_CMD = "EJSON.stringify(db.version())"
    BUILD_INFO_CMD = "EJSON.stringify(db.serverBuildInfo())"
    USER_DETAILS_CMD = "EJSON.stringify(db.getUser('{user}'))"
    SH_STATUS = "EJSON.stringify(sh.status())"
    SH_ADD_SHARD = "EJSON.stringify(sh.addShard('{replicaset_str}'))"
    SHOW_DBS = "JSON.stringify(db.adminCommand({listDatabases: 1, nameOnly: true}))"
    DROP_DATABASE = "JSON.stringify(db.getSiblingDB('{db_name}')" \
                    ".dropDatabase())"
    FSYNC_DUMP = "EJSON.stringify(db.runCommand({fsync: 1, lock: false}))"
    GET_TIMESTAMP = "EJSON.stringify(ISODate())"

    RUN_MONGODB_CMD = '{mongo_shell_path} "{host_details}" --quiet --eval "{cmd}"'

    CLUSTERSYNC_RESERVED_DATABASE = "mongosync_reserved_for_internal_use"

    
    STANDARD_CONN_STRING_FORMAT = "mongodb://{username}:{password}@{host_conn_string}/{database}?{additional_auth_params}"


class MongoSyncConstants:
    """
    Declares constants used by MongoSync class.
    """
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
                          'port: {mongosync_port}\n'

    mongosync_conf_id_data = 'id: "{shard_id}"'

    mongosync_start_cmd = "nohup bash -c '{mongosync_path} --config " \
                          "{conf_path}' > /dev/null 2>&1 &"

    pause_api = "api/v1/pause"
    pause_api_params = {}

    start_api = "api/v1/start"
    start_api_params = {"source": "cluster0", "destination": "cluster1"}

    progress_api = "api/v1/progress"

    resume_api = "api/v1/resume"
    resume_api_params = {}

    commit_api = "api/v1/commit"
    commit_api_params = {}

    curl_connection_refused_code = 7
