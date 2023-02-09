import json
import os
import time

from ce_lib.rest_lib.RestAPI import RestAPI
from ce_lib.os_lib.os_lib import OSLib
from ce_lib.resource import Resource
from ce_lib.plugin_exception import plugin_error
from mongodb_lib.MongoDB import MongoDB

from helpers import helpers


class MongoSync:
    def __init__(self,
                 staged_source,
                 repository,
                 mongosync_host
                 ):
        self.staged_source = staged_source
        self.repository = repository
        self.mongosync_host = mongosync_host

        self.rest_obj = RestAPI.get_rest_api_lib(
            connection=self.staged_source.staged_connection,
            host=self.mongosync_host,
            port=self.staged_source.parameters.mongosync_port,
            api_type="CurlAPI"
        )

        self.resource = Resource(
            connection=self.staged_source.staged_connection,
            hidden_directory=""
        )
        self.os_lib_obj = OSLib(resource=self.resource)
        self.mongodb_obj = MongoDB(
            repository=self.repository,
            resource=self.resource
        )
        self.logger = self.resource.logger

        self.check_input_parameters()

    def check_input_parameters(self):
        self.check_staging_parameters()
        self.check_source_parameters()

    def check_staging_parameters(self):
        # mongosync path in repository should not be empty
        if not self.repository.mongosync_path:
            error_msg = "MongoSync Path is not discovered for this repository."
            raise plugin_error.RepositoryNotValid(error_msg)

        # check if mongosync path exists
        if not self.os_lib_obj.check_file_dir_exists(
                path=self.repository.mongosync_path,
                is_directory=False
        ):
            error_msg = f"Mongosync path: " \
                        f"'{self.repository.mongosync_path}' is invalid."
            raise plugin_error.RepositoryNotValid(error_msg)

        # mongosync version == 1.0.0
        mongosync_version = self.os_lib_obj.get_binary_version(
            binary_path=self.repository.mongosync_path
        ).split("\n")[0].split(" ")[1]
        if helpers.compare_version(mongosync_version, "1.0.0") != 0:
            error_msg = f"Mongosync version: {mongosync_version} not " \
                        f"supported. Only v1.0.0 supported."
            # raise plugin_error.RepositoryNotValid(error_msg)

        # mongodb version >= 6.0.x
        mongod_version = self.repository.version[1:]
        self.logger.debug(f"mongod_version: {mongod_version}")
        if helpers.compare_version(mongod_version, "6.0") < 0:
            error_msg = "MongoDB version less than 6.0.0 not supported with " \
                        f"cluster to cluster sync. " \
                        f"Current MongoDB version: {mongod_version}"
            raise plugin_error.RepositoryNotValid(error_msg)

        # mongodb should be enterprise edition
        mongod_build_info = json.loads(self.os_lib_obj.get_binary_version(
            binary_path=self.repository.mongo_install_path
        ).split("Build Info:")[1].strip())
        mongod_type = mongod_build_info["modules"]
        self.logger.debug(f"modules= {mongod_type}")
        if "enterprise" not in mongod_type:
            error_msg = "Selected MongoDB repository does not seem to be " \
                        "enterprise version. MongoDB enterprise version " \
                        "required for Cluster to Cluster Sync."
            raise plugin_error.RepositoryNotValid(error_msg)

        # storage engine should be wiredTiger
        if self.staged_source.parameters.storage_engine != "wiredTiger":
            error_msg = f"Storage Engine : " \
                        f"{self.staged_source.parameters.storage_engine} " \
                        f"not supported for Cluster to Cluster Sync. " \
                       f"It should be wiredTiger."
            raise plugin_error.InvalidParametersProvided(error_msg)

        # mongosync port number is available
        if not self.os_lib_obj.check_port_available(
                self.staged_source.parameters.mongosync_port
        ):
            error_msg = f"Port number: " \
                        f"{self.staged_source.parameters.mongosync_port} " \
                        f"not available on staging host for Mongosync utility."
            raise plugin_error.InvalidParametersProvided(error_msg)

    def check_source_parameters(self):
        # mongodb version >= 6.0.x
        mongodb_version = self.mongodb_obj.get_version(
            host=self.staged_source.parameters.src_mongo_host_conn.split(":")[0],
            port=self.staged_source.parameters.src_mongo_host_conn.split(":")[1],
            username=self.staged_source.parameters.src_db_user,
            password=self.staged_source.parameters.src_db_password
        )
        if helpers.compare_version(mongodb_version, self.repository.version[1:]) != 0:
            error_msg = f"Source database version {mongodb_version} does " \
                        f"not match Staging Repository version selected " \
                        f"{self.repository.version[1:]}."
            raise plugin_error.InvalidParametersProvided(error_msg)

        # mongodb should be enterprise edition
        if "enterprise" not in self.mongodb_obj.get_type(
            host=self.staged_source.parameters.src_mongo_host_conn.split(":")[0],
            port=self.staged_source.parameters.src_mongo_host_conn.split(":")[1],
            username=self.staged_source.parameters.src_db_user,
            password=self.staged_source.parameters.src_db_password
        ):
            error_msg = " Source database provided is not Enterprise." \
                        "Cluster to cluster Sync is only supported in " \
                        "Enterprise version."
            raise plugin_error.InvalidParametersProvided(error_msg)

        # TODO: storage engine wiredTiger

        # verify source database user RBAC
        mandatory_roles = {"readAnyDatabase", "clusterMonitor", "backup"}
        user_roles = json.loads(self.mongodb_obj.get_user_roles(
            host=self.staged_source.parameters.src_mongo_host_conn.split(":")[0],
            port=self.staged_source.parameters.src_mongo_host_conn.split(":")[1],
            username=self.staged_source.parameters.src_db_user,
            password=self.staged_source.parameters.src_db_password,
            user_check=self.staged_source.parameters.src_db_user
        ))
        present_roles = {x["role"] for x in user_roles["roles"]}

        if ("root" not in present_roles and
                len(mandatory_roles-present_roles) > 0):
            error_string = f"User privilege invalid. " \
                           f"Required roles are {mandatory_roles} while " \
                           f"roles present are {present_roles}"
            raise plugin_error.InvalidParametersProvided(error_string)

        self.logger.debug(f"user rbac : {present_roles}")

        # TODO: verify if source is sharded and not replicaset.

    def get_mongosync_conf_path(self):
        conf_path = os.path.join(self.staged_source.parameters.mount_path,
                                 ".delphix",
                                 "mongosync.conf")
        return conf_path

    def create_mongosync_conf(self):
        conf_path = self.get_mongosync_conf_path()
        src_conn_string = self.mongodb_obj.get_jdbc_conn_string(
            host=self.staged_source.parameters.src_mongo_host_conn.split(":")[
                0],
            port=self.staged_source.parameters.src_mongo_host_conn.split(":")[
                1],
            username=self.staged_source.parameters.src_db_user,
            password=self.staged_source.parameters.src_db_password
        )
        dst_conn_string = self.mongodb_obj.get_jdbc_conn_string(
            host=self.staged_source.parameters.mongo_host,
            port=self.staged_source.parameters.mongos_port,
            username=self.staged_source.parameters.mongo_db_user,
            password=self.staged_source.parameters.mongo_db_password
        )
        conf_data = f'cluster0: "{src_conn_string}"' \
                    f'cluster1: "{dst_conn_string}"' \
                    f'logPath: "{conf_path.replace(".conf",".log")}"\n' \
                    f'port: {self.staged_source.parameters.mongosync_port}'

        self.os_lib_obj.dump_to_file(content=conf_data, file_path=conf_path)

    def start_mongosync(self, create_conf=True):
        if create_conf:
            self.create_mongosync_conf()
        conf_path = self.get_mongosync_conf_path()
        start_cmd = f"nohup bash -c '{self.repository.mongosync_path} " \
                    f"--config {conf_path}' > /tmp/mongosync_startup.log &"
        res = self.resource.execute_bash(start_cmd, raise_exception=False)
        if res.exit_code != 0:
            # TODO: fetch logs from error
            raise plugin_error.PluginError(f"Mongosync start failed with "
                                           f"error : {res.stderr}")

    def stop_mongosync(self, force_stop=False):
        if not force_stop:
            self.rest_obj.request_post(
                api_path="api/v1/pause",
                params={}
            )
        kill_cmd = f"ps -eaf | grep {self.repository.mongosync_path} | " \
                   f"grep {self.get_mongosync_conf_path()} | " \
                   f"awk '{{print $2}}' | xargs kill -9"
        self.resource.execute_bash(kill_cmd)

    def status_mongosync(self, fetch_error=True):
        running_mongosync_pids = self.os_lib_obj.find_running_processes(
            process_name=self.repository.mongosync_path,
            grep_params=[self.get_mongosync_conf_path()],
            awk_param="$2"
        )
        if running_mongosync_pids == "":
            if fetch_error:
                # TODO: fetch error from logs
                pass
            return False, ""
        else:
            return True, ""

    def start_sync(self, wait_cancommit=False):
        res = self.rest_obj.request_post(
            api_path="api/v1/start",
            params={"source": "cluster0", "destination": "cluster1"}
        )
        if wait_cancommit:
            max_timeout = 5*60
            start_time = time.time()
            while True:
                http_code, _, response_json = self.rest_obj.request_get(
                    api_path="api/v1/progress"
                )
                if int(http_code) == 200:
                    if response_json["progress"]["canCommit"]:
                        return True
                    else:
                        time.sleep(30)

    def pause_sync(self):
        res = self.rest_obj.request_post(
            api_path="api/v1/pause",
            params={}
        )
        return res

    def progress_sync(self):
        res = self.rest_obj.request_get(
                    api_path="api/v1/progress"
                )
        return res

    def resume_sync(self):
        res = self.rest_obj.request_post(
            api_path="api/v1/resume",
            params={}
        )
        return res

    def commit_sync(self):
        res = self.rest_obj.request_post(
            api_path="api/v1/commit",
            params={}
        )
        return res



