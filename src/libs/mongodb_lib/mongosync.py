import json
import os
import time
from typing import Tuple, Dict, Union, List

from ce_lib.rest_lib.RestAPI import RestAPI
from ce_lib.os_lib.os_lib import OSLib
from ce_lib.resource import Resource
from ce_lib.plugin_exception import plugin_error
from mongodb_lib.MongoDB import MongoDB
from mongodb_lib.constants import MongoSyncConstants
from ce_lib import helpers
from generated.definitions import LinkedSourceDefinition
from generated.definitions import RepositoryDefinition


class MongoSync:
    """
    Implements methods for operating MongoSync.
    """
    def __init__(self,
                 staged_source: LinkedSourceDefinition,
                 repository: RepositoryDefinition,
                 mongosync_host: str = "127.0.0.1",
                 mongosync_port: int = None,
                 check_params: bool = True,
                 mongosync_id: str = None
                 ) -> None:
        """
        Initialise MongoSync object.
        
        :param staged_source: Staged source for the dSource
        :type staged_source: ``generated.definitions.LinkedSourceDefinition``
        :param repository: Repository corresponding to dSource
        :type repository: ``generated.definitions.RepositoryDefinition``
        :param mongosync_host: Host address for contacting mongosync API server
        :type mongosync_host: ``str``
        :param mongosync_port: Host port for contacting mongosync API server
        :type mongosync_port: ``int``
        :param check_params: boolean specifying whether to perform input
                                parameters check
        :type check_params: ``bool``
        :param mongosync_id: ID specifying shard_id or replicaset id in
                                case of multiple mongosync instances.
        :type mongosync_id: ``str``

        :return: None
        :rtype: ``NoneType``
        """
        self.staged_source = staged_source
        self.repository = repository
        self.mongosync_host = mongosync_host
        self.mongosync_id = mongosync_id
        self.mongosync_port = mongosync_port if mongosync_port else self.staged_source.parameters.mongosync_port

        self.resource = Resource(
            connection=self.staged_source.staged_connection,
            hidden_directory=""
        )

        self.rest_obj = RestAPI.get_rest_api_lib(
            connection=self.staged_source.staged_connection,
            host=self.mongosync_host,
            port=self.mongosync_port,
            api_type=MongoSyncConstants.api_method,
            resource=self.resource
        )

        self.os_lib_obj = OSLib(resource=self.resource)
        self.mongodb_obj = MongoDB(
            repository=self.repository,
            resource=self.resource
        )
        self.logger = self.resource.logger

        if not self.os_lib_obj.check_file_dir_exists(
                path=self.get_mongosync_data_dir(), is_directory=True):
            self.os_lib_obj.make_directory(self.get_mongosync_data_dir())

        if check_params:
            self.check_input_parameters()

    def check_input_parameters(self) -> None:
        """
        Checks staging and source input parameters for mongosync utility.

        :return: None
        :rtype: ``NoneType``
        """
        self.check_staging_parameters()
        self.check_source_parameters()

    def check_staging_parameters(self) -> None:
        """
        Checks staging input parameters for Mongosync.
        1. Mongosync path in repository should not be empty
        2. Check if mongosync path in repository exists
        3. Mongosync version==1.0.0
        4. Staging MongoDB version >=6.0.0
        5. Staging MongoDB should be enterprise version
        6. Storage Engine selected should be wiredTiger
        7. Mongosync port number should be available
        
        :return: None
        :rtype: ``NoneType``
        """
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
        if not helpers.compare_version(
                mongosync_version,
                MongoSyncConstants.mongosync_supported_version,
                MongoSyncConstants.mongosync_supported_version_checking
        ):
            error_msg = f"Mongosync version: {mongosync_version} not " \
                        f"supported. Only " \
                        f"{MongoSyncConstants.mongosync_supported_version_checking}" \
                        f"{MongoSyncConstants.mongosync_supported_version} " \
                        f"supported."
            raise plugin_error.RepositoryNotValid(error_msg)

        # mongodb version >= 6.0.x
        mongod_version = self.repository.version[1:]
        self.logger.debug(f"mongod_version: {mongod_version}")
        if not helpers.compare_version(
                mongod_version,
                MongoSyncConstants.mongodb_supported_version,
                MongoSyncConstants.mongodb_supported_version_checking
        ):
            error_msg = f"MongoDB version: {mongod_version} not supported " \
                        f"with ClusterSync. Only " \
                        f"{MongoSyncConstants.mongodb_supported_version_checking}" \
                        f"{MongoSyncConstants.mongodb_supported_version} " \
                        f"supported."
            raise plugin_error.RepositoryNotValid(error_msg)

        # mongodb should be enterprise edition
        mongod_build_info = json.loads(self.os_lib_obj.get_binary_version(
            binary_path=self.repository.mongo_install_path
        ).split("Build Info:")[1].strip())
        mongod_type = mongod_build_info["modules"]
        self.logger.debug(f"modules= {mongod_type}")
        if MongoSyncConstants.mongodb_supported_type not in mongod_type:
            error_msg = "Selected MongoDB repository does not seem to be " \
                        "enterprise version. MongoDB enterprise version " \
                        "required for Cluster to Cluster Sync."
            raise plugin_error.RepositoryNotValid(error_msg)

        # storage engine should be wiredTiger
        if self.staged_source.parameters.storage_engine != MongoSyncConstants.supported_engine:
            error_msg = f"Storage Engine : " \
                        f"{self.staged_source.parameters.storage_engine} " \
                        f"not supported for Cluster to Cluster Sync. " \
                       f"It should be wiredTiger."
            raise plugin_error.InvalidParametersProvided(error_msg)

        # mongosync port number is available
        if not self.os_lib_obj.check_port_available(
                self.mongosync_port
        ):
            error_msg = f"Port number: " \
                        f"{self.mongosync_port} " \
                        f"not available on staging host for Mongosync utility."
            raise plugin_error.InvalidParametersProvided(error_msg)

    def check_source_parameters(self) -> None:
        """
        Check source MongoDB parameters.
        1. Source MongoDB version >= 6.0.0
        2. Source MongoDB version == staging MongoDB version
        3. Source MongoD should be Enterprise Edition
        4. Verify source database user RBAC

        :return: None
        :rtype: ``NoneType``
        """
        # mongodb version >= 6.0.x
        mongodb_version = self.mongodb_obj.get_version(
            host_conn_string=self.staged_source.parameters.src_mongo_host_conn,
            username=self.staged_source.parameters.src_db_user,
            password=self.staged_source.parameters.src_db_password
        )
        if not helpers.compare_version(mongodb_version, self.repository.version[1:], "="):
            error_msg = f"Source database version {mongodb_version} does " \
                        f"not match Staging Repository version selected " \
                        f"{self.repository.version[1:]}."
            raise plugin_error.InvalidParametersProvided(error_msg)

        # mongodb should be enterprise edition
        if MongoSyncConstants.mongodb_supported_type not in self.mongodb_obj.get_type(
            host_conn_string=self.staged_source.parameters.src_mongo_host_conn,
            username=self.staged_source.parameters.src_db_user,
            password=self.staged_source.parameters.src_db_password
        ):
            error_msg = " Source database provided is not Enterprise." \
                        "Cluster to cluster Sync is only supported in " \
                        "Enterprise version."
            raise plugin_error.InvalidParametersProvided(error_msg)

        # TODO: storage engine wiredTiger

        # verify source database user RBAC
        user_roles = self.mongodb_obj.get_user_roles(
            host_conn_string=self.staged_source.parameters.src_mongo_host_conn,
            username=self.staged_source.parameters.src_db_user,
            password=self.staged_source.parameters.src_db_password,
            user_check=self.staged_source.parameters.src_db_user
        )
        present_roles = {x["role"] for x in user_roles["roles"]}
        mandatory_roles = MongoSyncConstants.source_user_mandatory_roles
        if len(mandatory_roles-present_roles) > 0:
            error_string = f"User privilege invalid. " \
                           f"Required roles are {mandatory_roles} while " \
                           f"roles present are {present_roles}"
            raise plugin_error.InvalidParametersProvided(error_string)

        self.logger.debug(f"user rbac : {present_roles}")

        # TODO: verify if source is sharded and not replicaset.

    def get_mongosync_data_dir(self) -> str:
        """
        Returns mongosync reserved directory inside .delphix.

        :return: Path to .delphix/mongosync
        :rtype: ``str``
        """
        mongosync_dir = os.path.join(self.staged_source.parameters.mount_path,
                                 ".delphix", "mongosync")
        if self.mongosync_id:
            mongosync_dir = f"{mongosync_dir}_{self.mongosync_id}"

        return mongosync_dir

    def get_mongosync_conf_path(self) -> str:
        """
        Generates and returns path of mongosync.conf

        :return: Path for mongosync.conf
        :rtype: ``str``
        """
        conf_path = os.path.join(self.get_mongosync_data_dir(),
                                 "mongosync.conf")
        if self.mongosync_id:
            conf_path = conf_path.replace(".conf",
                                          f"_{self.mongosync_id}.conf")
        return conf_path

    def create_mongosync_conf(self) -> None:
        """
        Creates mongosync.conf

        :return: None
        :rtype: ``NoneType``
        """
        conf_path = self.get_mongosync_conf_path()
        src_conn_string = MongoDB.get_standard_conn_string(
            host_conn_string=self.staged_source.parameters.src_mongo_host_conn,
            username=self.staged_source.parameters.src_db_user,
            password=self.staged_source.parameters.src_db_password
        )
        dst_conn_string = MongoDB.get_standard_conn_string(
            host_conn_string=f"{self.staged_source.parameters.mongo_host}:"
                             f"{self.staged_source.parameters.mongos_port}",
            username=self.staged_source.parameters.mongo_db_user,
            password=self.staged_source.parameters.mongo_db_password,
            ssl_params=self.staged_source.parameters.ssl_tls_params
            if self.staged_source.parameters.enable_ssl_tls else None
        )
        conf_data = MongoSyncConstants.mongosync_conf_data.format(
            src_conn_string=src_conn_string,
            dst_conn_string=dst_conn_string,
            mongosync_log_path=os.path.dirname(conf_path),
            mongosync_port=self.staged_source.parameters.mongosync_port
        )
        if self.mongosync_id:
            conf_data += MongoSyncConstants.mongosync_conf_id_data.format(
                shard_id=self.mongosync_id
            )

        self.os_lib_obj.dump_to_file(content=conf_data, file_path=conf_path)

    def start_mongosync(self, create_conf: bool = True) -> None:
        """
        Start Mongosync utility and creates mongosync.conf if create_conf=True.
        
        :return: None
        :rtype: ``NoneType``
        """
        if create_conf:
            self.create_mongosync_conf()
        conf_path = self.get_mongosync_conf_path()
        start_cmd = MongoSyncConstants.mongosync_start_cmd.format(
            mongosync_path=self.repository.mongosync_path,
            conf_path=conf_path
        )
        res = self.resource.execute_bash(start_cmd, raise_exception=False)
        time.sleep(10)

        # NOTE: We are deliberatly removing the conf file to avoid any
        # further vulnerability exploitation. Wait of N seconds is to make sure
        # the file contents are loaded in the memory safely and the file on
        # disk is no more required. However, displaying file contents in the
        # log file could raise some concerns but be assured as logging masks
        # the sensitive data.
        try:
            self.os_lib_obj.cat_file(file_path=conf_path)
        except Exception as e:
            raise plugin_error.PluginError(f"Unable to log the contents "
                                           f"of {conf_path} : {str(e)}")
        finally:
            self.os_lib_obj.delete_file(file_path=conf_path, force=True)

        if res.exit_code != 0:
            # TODO: fetch logs from error
            raise plugin_error.PluginError(f"Mongosync start failed with "
                                           f"error : {res.stderr}")

        self.logger.debug("waiting for 60 seconds for Mongosync to start.....")
        time.sleep(60)

    def stop_mongosync(self, force_stop: bool = False) -> None:
        """
        Kills Mongosync utility. Also, pauses the utility first if
        force_stop=False.

        :return: None
        :rtype: ``NoneType``
        """
        if not force_stop:
            self.pause_sync()
        pids = self.os_lib_obj.find_running_processes(
            process_name=self.repository.mongosync_path,
            grep_params=[self.get_mongosync_conf_path()],
            awk_param="$2"
        )
        if pids.strip() != "":
            self.os_lib_obj.process_kill(process_id=pids, option="-9")

    def status_mongosync(self, fetch_error: bool = True) -> Tuple[bool, str]:
        """
        Checks status of Mongosync Status. Also, fetches from logs if not
        running and fetch_error=True.

        :param fetch_error: Boolean to specify if errors have to be fetched
                            from logs
        :type fetch_error: ``bool``

        :return: Tuple containing boolean and error message
        :rtype: ``Tuple[bool, str]``
        """
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

    def start_sync(self, wait_cancommit: bool = False) -> bool:
        """
        Starts Sync between source and staging. Also, waits for canCommit=True
        if wait_cancommit=True.

        :param wait_cancommit: Boolean specifying whether to wait for
                                canCommit=True
        :type wait_cancommit: ``bool``

        :return: Boolean specifying if sync started successfully
        :rtype: ``bool``
        """
        http_code, _, response_json = self.progress_sync()
        if int(http_code) == 200 and response_json["progress"]["state"] != "RUNNING":
            http_code, response, json_response = self.rest_obj.request_post(
                api_path=MongoSyncConstants.start_api,
                params=MongoSyncConstants.start_api_params
            )
        sync_started = int(http_code) == 200
        if wait_cancommit:
            # TODO: timeout when timelagSeconds is same for one hour.
            max_timeout = 5*60
            start_time = time.time()
            while True:
                http_code, _, response_json = self.progress_sync()
                if int(http_code) == 200:
                    if response_json["progress"]["canCommit"]:
                        return True
                    else:
                        time.sleep(30)
        else:
            return sync_started

    def pause_sync(self) -> Tuple[int, str, Dict[str, Union[List, str, int, dict]]]:
        """
        Pauses sync.

        :return: Tuple containing http_code, output string_response,
                    output json_response
        :rtype: ``Tuple[int, str, Dict[str, Union[List, str, int, dict]]]``
        """
        res = self.rest_obj.request_post(
            api_path=MongoSyncConstants.pause_api,
            params=MongoSyncConstants.pause_api_params
        )
        return res

    def progress_sync(self) -> Tuple[int, str, Dict[str, Union[List, str, int, dict]]]:
        """
        Returns sync progress.

        :return: Tuple containing http_code, output string_response,
                    output json_response
        :rtype: ``Tuple[int, str, Dict[str, Union[List, str, int, dict]]]``
        """
        res = self.rest_obj.request_get(
                    api_path=MongoSyncConstants.progress_api
                )
        return res

    def resume_sync(self) -> Tuple[int, str, Dict[str, Union[List, str, int, dict]]]:
        """
        Resumes sync.

        :return: Tuple containing http_code, output string_response,
                    output json_response
        :rtype: ``Tuple[int, str, Dict[str, Union[List, str, int, dict]]]``
        """
        res = self.rest_obj.request_post(
            api_path=MongoSyncConstants.resume_api,
            params=MongoSyncConstants.pause_api_params
        )
        return res

    def commit_sync(self) -> Tuple[int, str, Dict[str, Union[List, str, int, dict]]]:
        """
        Commits sync.

        :return: Tuple containing http_code, output string_response,
                    output json_response
        :rtype: ``Tuple[int, str, Dict[str, Union[List, str, int, dict]]]``
        """
        res = self.rest_obj.request_post(
            api_path=MongoSyncConstants.commit_api,
            params=MongoSyncConstants.commit_api_params
        )
        return res



