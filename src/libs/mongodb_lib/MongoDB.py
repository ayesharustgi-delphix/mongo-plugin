import json

from mongodb_lib.constants import MongoDBLibConstants
from ce_lib import helpers

class MongoDB:
    def __init__(self, repository, resource):
        self.repository = repository
        self.resource = resource

    def get_version(self, host_conn_string, username, password):
        res = self.run_mongo_shell_command(
            host_conn_string=host_conn_string,
            username=username,
            password=password,
            cmd=MongoDBLibConstants.DB_VERSION_CMD
        )
        version = res.stdout
        return version

    def get_type(self, host_conn_string, username, password):
        res = self.run_mongo_shell_command(
            host_conn_string=host_conn_string,
            username=username,
            password=password,
            cmd=MongoDBLibConstants.MODULES_CMD
        )
        modules = res.stdout
        return modules

    def get_user_roles(self, host_conn_string, username, password, user_check):
        res = self.run_mongo_shell_command(
            host_conn_string=host_conn_string,
            username=username,
            password=password,
            cmd=MongoDBLibConstants.USER_DETAILS_CMD.format(user=user_check)
        )
        roles = res.stdout
        return roles


    def get_sh_status(
        self,
        host_conn_string: str,
        username: str,
        password: str
    ) -> json:
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
    def get_standard_conn_string(host_conn_string, username, password, database="", ssl_params=None):
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

    def run_mongo_shell_command(self, host_conn_string, username, password, cmd, database="admin"):
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
