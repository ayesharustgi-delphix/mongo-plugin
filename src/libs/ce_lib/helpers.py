import shlex
import json

from dlpx.virtualization import libs


def parse_shell_params(shell_string: str) -> dict:
    """
    Parses parameters from shell string and creates a dictionary.

    It assumes that parameter name will start with '--' and values will not
    contain spaces.
    If the first parameter found is not parameter_name format,
    it is returned as "primary_key" in the dictionary.

    eg:
    shell string = "ayesha-mongo603-src.dcol1.delphix.com:28501 --tls --tlsCertificateKeyFile=/home/delphix/nonsharded_src/ssl_certs/s0m0.pem"
    Parsed = {"primary_key": "ayesha-mongo603-src.dcol1.delphix.com:28501",
                "tls": "true",
                "tlsCertificateKeyFile": "/home/delphix/nonsharded_src/ssl_certs/s0m0.pem"
                }


    :param shell_string: Shell string to be parsed
    :type shell_string: ``str``

    :return: Dictionary containing parameter name and value pairs.
    """
    param_list = shlex.split(shell_string)
    print(param_list)

    output_param_dict = {}
    i = 0
    while i < len(param_list):
        if i == 0 and not param_list[i].startswith("--"):
            k = "primary_key"
            value = param_list[i]
            increment = 1
        else:
            if param_list[i].startswith("--"):
                k = param_list[i][2:]
                if "=" in k:
                    k, value = k.split("=")
                    increment = 1
                elif i < len(param_list) - 1 and not param_list[
                    i + 1
                ].startswith("--"):
                    value = param_list[i + 1]
                    increment = 2
                else:
                    value = "true"
                    increment = 1
            else:
                raise RuntimeError(f"Cannot parse string {shell_string}")
        output_param_dict[k] = value
        i += increment

    return output_param_dict


def compare_version(v1: str, v2: str, version_checking: str) -> bool:
    """
    Compares v1 and v2 according to version checking which might be '>', '>=',
     '<', '<=', '=='

    :param v1: version to be compared
    :type v1: ``str``
    :param v2: version 2 to be compared
    :type v2: ``str``
    :param version_checking: Type of checking to be done. '>' means evaluation
                                for v1>v2
    :type version_checking: ``str``

    :return: Boolean result of evaluation
    :rtype: ``bool``
    """
    arr1 = v1.split(".")
    arr2 = v2.split(".")
    n = len(arr1)
    m = len(arr2)

    # converts to integer from string
    arr1 = [int(i) for i in arr1]
    arr2 = [int(i) for i in arr2]

    # compares which list is bigger and fills
    # smaller list with zero (for unequal delimiters)
    if n > m:
        for i in range(m, n):
            arr2.append(0)
    elif m > n:
        for i in range(n, m):
            arr1.append(0)

    # returns 1 if version 1 is bigger and -1 if
    # version 2 is bigger and 0 if equal
    comp = "="
    for i in range(len(arr1)):
        if arr1[i] > arr2[i]:
            comp = ">"
            break
        elif arr2[i] > arr1[i]:
            comp = "<"
            break

    return comp in version_checking


def _get_mongod_logpath_from_commandline(mongod_cmd: str) -> str:
    """
    Gets the log path from the command line.

    :param mongod_cmd: Command line string
    :type mongod_cmd: ``str``
    """
    # check if cmd contains logpath
    # e.g. /u01/mongo509/bin/mongod --dbpath /mnt/provision/seed_vdb_test/s0m0 \
    # --logpath /mnt/provision/seed_vdb_test/logs/dlpx.s0m0.28101.mongod.log \
    # --bind_ip 0.0.0.0 --port 28101 --auth \
    # --keyFile /home/delphix/keyfile/keyfile --clusterAuthMode keyFile \
    # --replSet dlpx-repl --fork
    log_path = ""
    try:
        log_path = mongod_cmd.split("--logpath")[1].split()[0]
    except IndexError:
        log_path = ""
    return log_path


def _get_mongod_logpath_from_conf(
    connection, mongod_cmd: str, env: dict
) -> str:
    """
    Gets the log path from the conf file.

    :param connection: Connection object
    :type connection: ``Connection``
    :param mongod_cmd: Command line string
    :type mongod_cmd: ``str``
    :param env: Environment variables
    :type env: ``dict``
    """
    # check if cmd contains any name of the conf file
    # e.g. /u01/mongo509/bin/mongod -f \
    #   /mnt/provision/seed_vdb_test/cfg/dlpx.s0m0.28101.conf
    log_path = ""
    try:
        mongod_conf_file: str = mongod_cmd.split("-f")[-1].split()[0]
    except IndexError:
        return log_path

    cmd = f"grep 'path:' {mongod_conf_file}"
    res = libs.run_bash(connection, cmd, env)
    exit_code = res.exit_code
    if exit_code:
        log_path = ""
    else:
        log_path = str(res.stdout).replace("\n", "").strip().split()[-1]
    return log_path


def _get_mongosync_logpath_from_conf(
    connection, conf_path: str, env: dict
) -> str:
    """
    Retrieves log path from given Mongosync Conf file.
    """

    cmd = f"grep 'logPath:' {conf_path}"
    res = libs.run_bash(connection, cmd, env)
    exit_code = res.exit_code
    if exit_code:
        log_path = ""
    else:
        log_path = str(res.stdout).replace("\n", "").strip().split()[-1]
    return log_path


def _get_logpath(
    connection, env: dict, command: str = "", mongosync_conf_path: str = ""
) -> str:
    """
    Retrieves the log path for the given command or conf path.
    """
    if "mongosync" in command or mongosync_conf_path:
        return _get_mongosync_logpath_from_conf(
            connection, mongosync_conf_path, env
        )

    if "mongod" in command:
        if "--logpath" in command:
            return _get_mongod_logpath_from_commandline(command)
        if " -f " in command:
            return _get_mongod_logpath_from_conf(connection, command, env)


def _parse_error_from_logpath(connection, logpath: str, env: dict) -> str:
    """
    Checks for errors in the file and parses out the last error message.
    """
    cmd = f"grep 'error\":' {logpath}"
    res = libs.run_bash(connection, cmd, env)
    exit_code = res.exit_code

    if exit_code:
        error_message = f"No possible errors were found in {logpath}."
    else:
        # We need pick the last most error message. However,
        # keep -2 index because the last element in the split list is ''
        mongo_full_errmsg_raw = res.stdout.split("\n")[-2].strip()
        # logger.debug("mongo_full_errmsg_raw\n{}".format(mongo_full_errmsg_raw))

        mongo_errmsg_raw_json = json.loads(mongo_full_errmsg_raw)
        error_message = mongo_errmsg_raw_json.get("error")
        if not error_message and mongo_errmsg_raw_json.get("attr"):
            error_message = mongo_errmsg_raw_json["attr"].get("error", "")

    return error_message


def get_error_from_logfile(
    connection, env: dict, command: str = "", conf_path: str = ""
) -> str:
    """Returns the error from the mongod logpath for the specified mongod
    command.
    :param connection: connection object
    :type: dlpx.virtualization.common._common_classes.RemoteConnection
    :param mongod_cmd: mongod command line
    :type: str
    :param env: Environment variables
    :type: dict
    :return: logpath.
    :rtype: str
    :raises Exception: In case of failure.
    """
    # Check if logpath is found in the mongod command line or in conf.
    log_error = ""
    if "/mongosync " in command or conf_path:
        logpath = _get_logpath(
            connection=connection,
            env=env,
            command=command,
            mongosync_conf_path=conf_path,
        )
        if not logpath:
            log_error = "Log path not found in Conf file."
        else:
            logpath = f"{logpath}/mongosync.log"
    elif "/mongod " in command:
        logpath = _get_logpath(connection=connection, env=env, command=command)
        if not logpath:
            log_error = "Log path not found in Conf file."

    if not log_error:
        log_error = _parse_error_from_logpath(connection, logpath, env)
    return log_error
