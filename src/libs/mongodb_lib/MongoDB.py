
class MongoDB:
    def __init__(self, repository, resource):
        self.repository = repository
        self.resource = resource

    def get_version(self, host, port, username, password):
        res = self.run_mongo_shell_command(
            host=host,
            port=port,
            database="admin",
            username=username,
            password=password,
            cmd="db.version()"
        )
        version = res.stdout
        return version

    def get_type(self, host, port, username, password):
        res = self.run_mongo_shell_command(
            host=host,
            port=port,
            database="admin",
            username=username,
            password=password,
            cmd="db.serverBuildInfo().modules"
        )
        modules = res.stdout
        return modules

    def get_user_roles(self, host, port, username, password, user_check):
        res = self.run_mongo_shell_command(
            host=host,
            port=port,
            database="admin",
            username=username,
            password=password,
            cmd=f"EJSON.stringify(db.getUser('{user_check}'))"
        )
        roles = res.stdout
        return roles

    def get_jdbc_conn_string(self, host, port, username, password, database=None):
        jdbc = f"mongodb://{username}:{password}@{host}:{port}"
        if database:
            jdbc = f"{jdbc}/{database}"
        return jdbc

    def run_mongo_shell_command(self, host, port, database, username, password, cmd):
        command = f'{self.repository.mongo_shell_path} ' \
                  f'{self.get_jdbc_conn_string(host, port, username, password, database)}' \
                  f' --quiet --eval "{cmd}"'
        result = self.resource.execute_bash(command)
        return result