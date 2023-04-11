import json
import os
from threading import Thread

from ce_lib.os_lib.os_lib import OSLib
from mongodb_lib.constants import MongoDBLibConstants
from ce_lib import helpers
import urllib.parse
from dlpx.virtualization.platform.exceptions import UserError


class MongoDB:
    def __init__(self, repository, resource):
        self.repository = repository
        self.resource = resource

    def get_version(self, host_conn_string: str, username: str, password: str
                    ) -> json:
        """
        Gets version og running MongoDB instance.

        :param host_conn_string: Connection string of database
        :type host_conn_string: ``str``
        :param username: Username of database
        :type username: ``str``
        :param password: Password of database
        :type password: ``str``

        :return: version of database
        :rtype: ``json``
        """
        version = self.run_mongo_shell_command(
            host_conn_string=host_conn_string,
            username=username,
            password=password,
            cmd=MongoDBLibConstants.DB_VERSION_CMD
        )
        # version = res.stdout
        return version

    def get_type(self, host_conn_string: str, username: str, password: str
                 ) -> json:
        """
        Fetches modules from build info of running MongoDB instance.
        Used for determining if MongoDB is enterprise or community.

        :param host_conn_string: Connection string of database
        :type host_conn_string: ``str``
        :param username: Username of database
        :type username: ``str``
        :param password: Password of database
        :type password: ``str``

        :return: List of modules in MongoDB
        :rtype: ``json``
        """
        modules = self.run_mongo_shell_command(
            host_conn_string=host_conn_string,
            username=username,
            password=password,
            cmd=MongoDBLibConstants.BUILD_INFO_CMD
        )["modules"]
        # modules = res.stdout
        return modules

    def get_user_roles(self, host_conn_string: str, username: str,
                       password: str, user_check: str) -> json:
        """
        Get roles associated with a user.

        :param host_conn_string: Connection string of database
        :type host_conn_string: ``str``
        :param username: Username of database
        :type username: ``str``
        :param password: Password of database
        :type password: ``str``
        :param user_check: Username for which RBAC has to be fetched.
        :type user_check: ``str``

        :return: Dictionary containing roles associated with user_check
        :rtype: ``json``
        """
        roles = self.run_mongo_shell_command(
            host_conn_string=host_conn_string,
            username=username,
            password=password,
            cmd=MongoDBLibConstants.USER_DETAILS_CMD.format(user=user_check)
        )
        # roles = res.stdout
        return roles

    def get_sh_status(
            self,
            host_conn_string: str,
            username: str,
            password: str
    ) -> json:
        """
        Fetch shard status of a cluster.

        :param host_conn_string: Connection string of database
        :type host_conn_string: ``str``
        :param username: Username of database
        :type username: ``str``
        :param password: Password of database
        :type password: ``str``

        :return: shard status of a cluster
        :rtype: ``json``
        """
        try:
            return self.run_mongo_shell_command(
                host_conn_string=host_conn_string,
                username=username,
                password=password,
                cmd=MongoDBLibConstants.SH_STATUS
            )
        except Exception as e:
            err = "Failed to execute sh.status().\n"
            err += str(e)
            raise Exception(err)

    def get_shards_details(
            self,
            host_conn_string: str,
            username: str,
            password: str
    ) -> json:
        """
        Fetches Shard Details of the cluster.

        :param host_conn_string: Connection string of database
        :type host_conn_string: ``str``
        :param username: Username of database
        :type username: ``str``
        :param password: Password of database
        :type password: ``str``

        :return: shard details of the cluster
        :rtype: ``json``
        """
        try:
            return self.get_sh_status(
                host_conn_string,
                username,
                password
            )['value']['shards']
        except Exception as e:
            err = "Failed to get shards details.\n"
            err += str(e)
            raise Exception(err)

    def sh_add_shard(
            self,
            host_conn_string: str,
            username: str,
            password: str,
            replicaset_str: str
    ) -> json:
        """
        Add Shard to cluster.

        :param host_conn_string: Connection string of database
        :type host_conn_string: ``str``
        :param username: Username of database
        :type username: ``str``
        :param password: Password of database
        :type password: ``str``
        :param replicaset_str: Shard address of the replicaset to be added
        :type replicaset_str: ``str``

        :return: output of sh.addShard command
        :rtype: ``json``
        """
        try:
            return self.run_mongo_shell_command(
                host_conn_string=host_conn_string,
                username=username,
                password=password,
                cmd=MongoDBLibConstants.SH_ADD_SHARD.format(
                    replicaset_str=replicaset_str
                )
            )
        except Exception as e:
            err = "Failed to execute sh.addShard().\n"
            err += str(e)
            raise Exception(err)

    def show_databases(
            self,
            host_conn_string: str,
            username: str,
            password: str,
    ) -> list:
        """
        Show databases.

        :param host_conn_string: Connection string of database
        :type host_conn_string: ``str``
        :param username: Username of database
        :type username: ``str``
        :param password: Password of database
        :type password: ``str``

        :return: list of databases
        :rtype: ``list``
        """
        res = self.run_mongo_shell_command(
            host_conn_string=host_conn_string,
            username=username,
            password=password,
            cmd=MongoDBLibConstants.SHOW_DBS,
        )
        # res = {"databases":[{"name":"admin"},{"name":"config"},
        # {"name":"sample_airbnb"},{"name":"sample_analytics"},
        # {"name":"sample_geospatial"},{"name":"sample_guides"},
        # {"name":"sample_mflix"},{"name":"sample_restaurants"},
        # {"name":"sample_supplies"},{"name":"sample_training"},
        # {"name":"sample_weatherdata"},{"name":"ycsb"}],
        # "ok":1,"$clusterTime":{"clusterTime":
        # {"$timestamp":"7208819696840212482"},"signature":
        # {"hash":"AAAAAAAAAAAAAAAAAAAAAAAAAAA=",
        # "keyId":{"low":0,"high":0,"unsigned":false}}},
        # "operationTime":{"$timestamp":"7208819696840212482"}}

        return list(database_dict["name"] for database_dict in res["databases"])

    def db_exists(
            self,
            host_conn_string: str,
            username: str,
            password: str,
            db_name: str,
    ) -> bool:
        """
        Check if database exists.

        :param host_conn_string: Connection string of database
        :type host_conn_string: ``str``
        :param username: Username of database
        :type username: ``str``
        :param password: Password of database
        :type password: ``str``
        :param db_name: Name of database
        :type db_name: ``str``

        :return: True or False
        :rtype: ``bool``
        """
        return db_name in self.show_databases(
            host_conn_string=host_conn_string,
            username=username,
            password=password,
        )

    def drop_database(
            self,
            host_conn_string: str,
            username: str,
            password: str,
            db_name: str,
    ) -> None:
        """
        Drops database.

        :param host_conn_string: Connection string of database
        :type host_conn_string: ``str``
        :param username: Username of database
        :type username: ``str``
        :param password: Password of database
        :type password: ``str``
        :param db_name: Name of database
        :type db_name: ``str``

        :return: None
        :rtype: ``None``
        :raises:
            Exception: stdout/stderr
        """
        self.run_mongo_shell_command(
            host_conn_string=host_conn_string,
            username=username,
            password=password,
            cmd=MongoDBLibConstants.DROP_DATABASE.format(
                db_name=db_name
            )
        )

    def fsync_dump(self,
                   host_conn_string: str,
                   username: str,
                   password: str,
                   ):
        """
        Runs fsync command on database and forces it to dump all in memory
        data to disk.

        :param host_conn_string: Connection string of database
        :type host_conn_string: ``str``
        :param username: Username of database
        :type username: ``str``
        :param password: Password of database
        :type password: ``str``

        :return: None
        :rtype: ``None``
        :raises:
            Exception: stdout/stderr
        """
        self.run_mongo_shell_command(
            host_conn_string=host_conn_string,
            username=username,
            password=password,
            cmd=MongoDBLibConstants.FSYNC_DUMP
        )

    def get_db_time(self, host_conn_string: str, username: str, password: str
                    ) -> str:
        """
        Fetch timestamp (ISO 8601 format) of database in UTC Timezone.

        :param host_conn_string: Connection string of database
        :type host_conn_string: ``str``
        :param username: Username of database
        :type username: ``str``
        :param password: Password of database
        :type password: ``str``

        :return: Timestamp string in ISO 8601 format
        :rtype: ``str``
        """
        res = self.run_mongo_shell_command(
            host_conn_string=host_conn_string,
            username=username,
            password=password,
            cmd=MongoDBLibConstants.GET_TIMESTAMP
        )
        return res["$date"]

    def run_mongodump(self,
                      host_conn_string: str,
                      username: str,
                      password: str,
                      authentication_db: str,
                      output_dir: str,
                      log_sync: bool,
                      os_lib_obj: OSLib,
                      mount_path: str
                      ):
        """
        Runs Mongodump to generate cluster backup.

        :param host_conn_string: Connection string of database
        :type host_conn_string: ``str``
        :param username: Username of database
        :type username: ``str``
        :param password: Password of database
        :type password: ``str``
        :param authentication_db: Database for connection
        :type authentication_db: ``str``
        :param output_dir: mongodump directory
        :type output_dir: ``str``
        :param log_sync: enable oplog sync boolean
        :type log_sync: ``bool``
        :param os_lib_obj: OSLib object
        :type os_lib_obj: ``ce_lib.os_lib.os_lib.OSLib``
        :param mount_path: Mount path of dataset
        :type mount_path: ``str``

        :return:
        """
        config_file_path = os.path.join(mount_path, ".delphix/config.yaml")
        std_conn_string = self.__class__.get_standard_conn_string(
            host_conn_string, username, password, authentication_db)
        os_lib_obj.dump_to_file(
            content=f'uri: {std_conn_string}',
            file_path=config_file_path
        )
        dump_cmd = MongoDBLibConstants.DUMP_CMD.format(
            mongo_dump_path=self.repository.mongo_dump_path,
            config_file_path=config_file_path,
            param='--oplog' if log_sync else '',
            output_dir=output_dir
        )
        run_cmd = MongoDBLibConstants.DELETE_SHELL.format(
            cmd=dump_cmd,
            config_file_path=config_file_path
        )
        res = self.resource.execute_bash(run_cmd, raise_exception=False)
        res.exit_code = int(res.stdout.split("DLPX_RET=")[1].split("__")[0])
        if res.exit_code != 0:
            raise UserError(f"Mongodump failed with error : {res.stderr}")
        return res

    @staticmethod
    def get_standard_conn_string(host_conn_string: str, username: str,
                                 password: str, database: str = "",
                                 ssl_params: list = None) -> str:
        """
        Generates standard connection string for a MongoDB instance.
        SSL params can be provided either as command line arguments in
        host_conn_string or in ssl_params list.
        Do not provide parameters in both.

        :param host_conn_string: Connection string of database
        :type host_conn_string: ``str``
        :param username: Username of database
        :type username: ``str``
        :param password: Password of database
        :type password: ``str``
        :param database: Database for connection
        :type database: ``str``
        :param ssl_params: SSL/TLS params in the following format
              [
               {"property_name": "<ssl param name1>", "value": "<value1>"},
               {"property_name": "<ssl param name2>", "value": "<value2>"},
              ]
        :type ssl_params: ``list``

        :return: Standard connection string
        :rtype: ``str``
        """
        encoded_username = urllib.parse.quote(username)
        encoded_password = urllib.parse.quote(password)

        host_param_dict = helpers.parse_shell_params(host_conn_string)

        host_conn = host_param_dict["primary_key"]
        del host_param_dict["primary_key"]

        host_params = [f"{k}={host_param_dict[k]}" for k in
                       host_param_dict.keys()]

        if ssl_params:
            host_params.append("tls=true")
            for p in ssl_params:
                param_data = f"{p['property_name']}={p['value']}"
                if param_data not in host_params:
                    host_params.append(param_data)

        jdbc = MongoDBLibConstants.STANDARD_CONN_STRING_FORMAT.format(
            username=encoded_username,
            password=encoded_password,
            host_conn_string=host_conn,
            database=database,
            additional_auth_params='&'.join(host_params)
        )
        return jdbc

    def run_mongo_shell_command(self, host_conn_string: str, username: str,
                                password: str, cmd: str,
                                database: str = "admin") -> json:
        """
        Runs MongoDB cmd on the running MongoDB instance.

        :param host_conn_string: Connection string of database
        :type host_conn_string: ``str``
        :param username: Username of database
        :type username: ``str``
        :param password: Password of database
        :type password: ``str``
        :param cmd: Command to run
        :type cmd: ``str``
        :param database: Database for connection
        :type database: ``str``

        :return: json output of command result
        :rtype: ``json``
        """
        command = MongoDBLibConstants.RUN_MONGODB_CMD.format(
            mongo_shell_path=self.repository.mongo_shell_path,
            host_details=self.__class__.get_standard_conn_string(
                host_conn_string=host_conn_string,
                username=username,
                password=password,
                database=database,
            ),
            cmd=cmd
        )
        result = self.resource.execute_bash(command)
        try:
            return json.loads(result.stdout)
        except json.decoder.JSONDecodeError:
            # Commands like "show dbs" doesn't return json
            return result.stdout


if __name__ == "__main__":
    s = "ayesha-mongo603-src.dcol1.delphix.com:28501 --tls --tlsCertificateKeyFile=/home/delphix/nonsharded_src/ssl_certs/s0m0.pem --tlsCAFile=/home/delphix/nonsharded_src/ssl_certs/mongoCA.crt"
    print(MongoDB.get_standard_conn_string(s, "dlpx@admin", "delphix", "admin"))
