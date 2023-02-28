import json

from mongodb_lib.constants import MongoDBLibConstants
from ce_lib import helpers


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
        :param ssl_params: SSL params in the format [{'<property_name>':'<value>'}]
        :type ssl_params: ``list``

        :return: Standard connection string
        :rtype: ``str``
        """
        percent_encoding_dict = MongoDBLibConstants.STANDARD_CONN_STRING_ENCODING
        encoded_username = "".join([percent_encoding_dict[s] if s in percent_encoding_dict else s for s in username])
        encoded_password = "".join([percent_encoding_dict[s] if s in percent_encoding_dict else s for s in password])

        host_param_dict = helpers.parse_shell_params(host_conn_string)

        host_conn = host_param_dict["primary_key"]
        del host_param_dict["primary_key"]

        host_params = [f"{k}={host_param_dict[k]}" for k in host_param_dict.keys()]

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
            host_details=self.__class__.get_standard_conn_string(host_conn_string, username, password, database),
            cmd=cmd
        )
        result = self.resource.execute_bash(command)
        return json.loads(result.stdout)


if __name__ == "__main__":
    s = "ayesha-mongo603-src.dcol1.delphix.com:28501 --tls --tlsCertificateKeyFile=/home/delphix/nonsharded_src/ssl_certs/s0m0.pem --tlsCAFile=/home/delphix/nonsharded_src/ssl_certs/mongoCA.crt"
    print(MongoDB.get_standard_conn_string(s, "dlpx@admin", "delphix", "admin"))
