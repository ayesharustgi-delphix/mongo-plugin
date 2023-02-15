from utils import plugin_logger

from dlpx.virtualization.platform import Mount

# Global logger object for this file
logger = plugin_logger.PluginLogger("MONGODB")

from dlpx.virtualization.common import RemoteConnection
from dlpx.virtualization.common import RemoteEnvironment
from dlpx.virtualization.common import RemoteUser
from dlpx.virtualization.platform.exceptions import UserError

from dlpx.virtualization import libs

import json
import time
import re
import os

from operations import linked
from operations import constants

def adjust_mount_env(imounts, inodes, itotalnodes):
    i = 0
    itotalnodes = itotalnodes - 1
    omounts = []
    for mount in imounts:
        if i > itotalnodes:
            i = 0
        # logger.debug("i = {},env = {}".format(i, inodes[i]))
        tmpmount = Mount(inodes[i], mount.mount_path, mount.shared_path)
        omounts.append(tmpmount)
        i = i + 1
    return omounts


def cr_dir_structure(cend, send, mount_path, replicaset, connection):
    if replicaset:
        mend = 3
    else:
        mend = 1

    for c in range(cend):
        for m in range(mend):
            cmd = "mkdir -p {}/c{}m{}".format(mount_path, c, m)
            res = execute_bash_cmd(connection, cmd, {})

    for s in range(send):
        for m in range(mend):
            cmd = "mkdir -p {}/s{}m{}".format(mount_path, s, m)
            res = execute_bash_cmd(connection, cmd, {})

    cmd = "mkdir -p {}/{}".format(mount_path, "cfg")
    res = execute_bash_cmd(connection, cmd, {})

    cmd = "mkdir -p {}/{}".format(mount_path, "logs")
    res = execute_bash_cmd(connection, cmd, {})

    cmd = "mkdir -p {}/{}".format(mount_path, "mgs0")
    res = execute_bash_cmd(connection, cmd, {})


def cr_dir_structure_replicaset(mount_path, replicaset, rx_connection):
    if replicaset:
        mend = 3
    else:
        mend = 1

    for s in range(1):
        for m in range(mend):
            cmd = "mkdir -p {}/s{}m{}".format(mount_path, s, m)
            res = execute_bash_cmd(rx_connection, cmd, {})

    cmd = "mkdir -p {}/{}".format(mount_path, "cfg")
    res = execute_bash_cmd(rx_connection, cmd, {})

    cmd = "mkdir -p {}/{}".format(mount_path, "logs")
    res = execute_bash_cmd(rx_connection, cmd, {})


def extract_shard_config_backup(backupfile, mount_path, confignum, connection):
    cmd = "tar -{}xf {} -C {}/c{}m0 --strip-components 1".format(
        "z" if backupfile.endswith(".tar.gz") else "",
        backupfile,
        mount_path, confignum)
    res = execute_bash_cmd_silent(connection, cmd, {})


def extract_shard_backup(backupfile, mount_path, shardnum, connection):
    cmd = "tar -{}xf {} -C {}/s{}m0 --strip-components 1".format(
        "z" if backupfile.endswith(".tar.gz") else "",
        backupfile,
        mount_path, shardnum)
    res = execute_bash_cmd_silent(connection, cmd, {})


def extract_replicaset_backup(backupfile, mount_path, connection):
    cmd = "tar -{}xf {} -C {}/s0m0 --strip-components 1".format(
        "z" if backupfile.endswith(".tar.gz") else "",
        backupfile,
        mount_path)
    res = execute_bash_cmd_silent(connection, cmd, {})


def gen_shard_config_list(nodes, start_portpool, cmax, smax, mmax, mount_path, mongos_port, replicaset):
    if replicaset:
        mmax = 3
    else:
        mmax = 1
    mongoport = int(start_portpool)
    totalnodes = len(nodes)
    n = 0
    shard_cfg_list = []
    if totalnodes == 1:
        for i in range(cmax):
            for j in range(mmax):
                shard_cfg_dict = {}
                shard_cfg_dict = {"node": nodes[n], "type": "config", "mount_path": "{}".format(
                    mount_path), "dirname": "c{}m{}".format(i, j), "port": mongoport}
                # logger.debug(shard_cfg_dict)
                if replicaset:
                    shard_cfg_list.append(shard_cfg_dict)
                    logger.debug(shard_cfg_dict)
                else:
                    if j == 0:
                        shard_cfg_list.append(shard_cfg_dict)
                        logger.debug(shard_cfg_dict)
                n += 1
                mongoport = mongoport + 1
                n = 0 if n == totalnodes else n
    elif totalnodes == 2:
        for i in range(cmax):
            for j in range(mmax):
                shard_cfg_dict = {}
                shard_cfg_dict = {"node": nodes[n], "type": "config", "mount_path": "{}".format(
                    mount_path), "dirname": "c{}m{}".format(i, j), "port": mongoport}
                # logger.debug(shard_cfg_dict)
                if replicaset:
                    shard_cfg_list.append(shard_cfg_dict)
                    logger.debug(shard_cfg_dict)
                else:
                    if j == 0:
                        shard_cfg_list.append(shard_cfg_dict)
                        logger.debug(shard_cfg_dict)
                n += 1
                if n == totalnodes:
                    mongoport = mongoport + 1
                n = 0 if n == totalnodes else n
    elif totalnodes == 3:
        for i in range(cmax):
            n = 0 if n == totalnodes else n
            for j in range(mmax):
                shard_cfg_dict = {}
                shard_cfg_dict = {"node": nodes[n], "type": "config", "mount_path": "{}".format(
                    mount_path), "dirname": "c{}m{}".format(i, j), "port": mongoport}
                # logger.debug(shard_cfg_dict)
                if replicaset:
                    shard_cfg_list.append(shard_cfg_dict)
                    logger.debug(shard_cfg_dict)
                else:
                    if j == 0:
                        shard_cfg_list.append(shard_cfg_dict)
                        logger.debug(shard_cfg_dict)
                n += 1
            mongoport = mongoport + 1
    elif totalnodes > 3:
        for i in range(cmax):
            n = 0 if n == totalnodes else n
            for j in range(mmax):
                shard_cfg_dict = {}
                shard_cfg_dict = {"node": nodes[n], "type": "config", "mount_path": "{}".format(
                    mount_path), "dirname": "c{}m{}".format(i, j), "port": mongoport}
                # logger.debug(shard_cfg_dict)
                if replicaset:
                    shard_cfg_list.append(shard_cfg_dict)
                    logger.debug(shard_cfg_dict)
                else:
                    if j == 0:
                        shard_cfg_list.append(shard_cfg_dict)
                        logger.debug(shard_cfg_dict)
                n += 1
                n = 0 if n == totalnodes else n
            mongoport = mongoport + 1

    logger.debug(" ")

    n = 0
    if totalnodes == 1:
        for i in range(smax):
            for j in range(mmax):
                shard_cfg_dict = {}
                shard_cfg_dict = {"node": nodes[n], "type": "shard", "mount_path": "{}".format(
                    mount_path), "dirname": "s{}m{}".format(i, j), "port": mongoport}
                # logger.debug(shard_cfg_dict)
                if replicaset:
                    shard_cfg_list.append(shard_cfg_dict)
                    logger.debug(shard_cfg_dict)
                else:
                    if j == 0:
                        shard_cfg_list.append(shard_cfg_dict)
                        logger.debug(shard_cfg_dict)
                n += 1
                mongoport = mongoport + 1
                n = 0 if n == totalnodes else n
            logger.debug(" ")
    elif totalnodes == 2:
        mongoport = mongoport + 1
        for i in range(smax):
            for j in range(mmax):
                shard_cfg_dict = {}
                shard_cfg_dict = {"node": nodes[n], "type": "shard", "mount_path": "{}".format(
                    mount_path), "dirname": "s{}m{}".format(i, j), "port": mongoport}
                # logger.debug(shard_cfg_dict)
                if replicaset:
                    shard_cfg_list.append(shard_cfg_dict)
                    logger.debug(shard_cfg_dict)
                else:
                    if j == 0:
                        shard_cfg_list.append(shard_cfg_dict)
                        logger.debug(shard_cfg_dict)
                n += 1
                if n == totalnodes and j < 2:
                    mongoport = mongoport + 1
                n = 0 if n == totalnodes else n
            mongoport = mongoport + 1
            logger.debug(" ")
    elif totalnodes == 3:
        for i in range(smax):
            n = 0 if n == totalnodes else n
            for j in range(mmax):
                shard_cfg_dict = {}
                shard_cfg_dict = {"node": nodes[n], "type": "shard", "mount_path": "{}".format(
                    mount_path), "dirname": "s{}m{}".format(i, j), "port": mongoport}
                # logger.debug(shard_cfg_dict)
                if replicaset:
                    shard_cfg_list.append(shard_cfg_dict)
                    logger.debug(shard_cfg_dict)
                else:
                    if j == 0:
                        shard_cfg_list.append(shard_cfg_dict)
                        logger.debug(shard_cfg_dict)
                n += 1
            mongoport = mongoport + 1
            logger.debug(" ")
    elif totalnodes > 3:
        for i in range(smax):
            n = 0 if n == totalnodes else n
            for j in range(mmax):
                shard_cfg_dict = {}
                shard_cfg_dict = {"node": nodes[n], "type": "shard", "mount_path": "{}".format(
                    mount_path), "dirname": "s{}m{}".format(i, j), "port": mongoport}
                # logger.debug(shard_cfg_dict)
                if replicaset:
                    shard_cfg_list.append(shard_cfg_dict)
                    logger.debug(shard_cfg_dict)
                else:
                    if j == 0:
                        shard_cfg_list.append(shard_cfg_dict)
                        logger.debug(shard_cfg_dict)
                n += 1
                n = 0 if n == totalnodes else n
            mongoport = int(mongoport) + 1
            logger.debug(" ")
    n = 0
    shard_cfg_dict = {"node": nodes[n], "type": "mongos", "mount_path": "{}".format(
        mount_path), "dirname": "mgs{}".format(0), "port": mongos_port}
    logger.debug(shard_cfg_dict)
    logger.debug(" ")
    shard_cfg_list.append(shard_cfg_dict)

    add_debug_space()
    logger.info("Sharded cluster config :")
    for shard_config in shard_cfg_list:
        logger.info(shard_config)

    return shard_cfg_list


def gen_replicaset_config_list(nodes, start_portpool, mount_path, replicaset):
    if replicaset:
        mmax = 3
    else:
        mmax = 1
    mongoport = int(start_portpool)
    totalnodes = len(nodes)
    n = 0
    replicaset_cfg_list = []
    if totalnodes == 1:
        for i in range(1):
            for j in range(mmax):
                replicaset_cfg_dict = {}
                replicaset_cfg_dict = {"node": nodes[n], "type": "repset", "mount_path": "{}".format(
                    mount_path), "dirname": "s{}m{}".format(i, j), "port": mongoport}
                # logger.debug(replicaset_cfg_dict)
                if replicaset:
                    replicaset_cfg_list.append(replicaset_cfg_dict)
                    logger.debug(replicaset_cfg_dict)
                else:
                    if j == 0:
                        replicaset_cfg_list.append(replicaset_cfg_dict)
                        logger.debug(replicaset_cfg_dict)
                n += 1
                mongoport = mongoport + 1
                n = 0 if n == totalnodes else n
            logger.debug(" ")
    elif totalnodes == 2:
        for i in range(1):
            for j in range(mmax):
                replicaset_cfg_dict = {}
                replicaset_cfg_dict = {"node": nodes[n], "type": "repset", "mount_path": "{}".format(
                    mount_path), "dirname": "s{}m{}".format(i, j), "port": mongoport}
                # logger.debug(replicaset_cfg_dict)
                if replicaset:
                    replicaset_cfg_list.append(replicaset_cfg_dict)
                    logger.debug(replicaset_cfg_dict)
                else:
                    if j == 0:
                        replicaset_cfg_list.append(replicaset_cfg_dict)
                        logger.debug(replicaset_cfg_dict)
                n += 1
                if n == totalnodes and j < 2:
                    mongoport = mongoport + 1
                n = 0 if n == totalnodes else n
            mongoport = mongoport + 1
            logger.debug(" ")
    elif totalnodes == 3:
        for i in range(1):
            n = 0 if n == totalnodes else n
            for j in range(mmax):
                replicaset_cfg_dict = {}
                replicaset_cfg_dict = {"node": nodes[n], "type": "repset", "mount_path": "{}".format(
                    mount_path), "dirname": "s{}m{}".format(i, j), "port": mongoport}
                # logger.debug(replicaset_cfg_dict)
                if replicaset:
                    replicaset_cfg_list.append(replicaset_cfg_dict)
                    logger.debug(replicaset_cfg_dict)
                else:
                    if j == 0:
                        replicaset_cfg_list.append(replicaset_cfg_dict)
                        logger.debug(replicaset_cfg_dict)
                n += 1
            mongoport = mongoport + 1
            logger.debug(" ")
    elif totalnodes > 3:
        for i in range(1):
            n = 0 if n == totalnodes else n
            for j in range(mmax):
                replicaset_cfg_dict = {}
                replicaset_cfg_dict = {"node": nodes[n], "type": "repset", "mount_path": "{}".format(
                    mount_path), "dirname": "s{}m{}".format(i, j), "port": mongoport}
                # logger.debug(replicaset_cfg_dict)
                if replicaset:
                    replicaset_cfg_list.append(replicaset_cfg_dict)
                    logger.debug(replicaset_cfg_dict)
                else:
                    if j == 0:
                        replicaset_cfg_list.append(replicaset_cfg_dict)
                        logger.debug(replicaset_cfg_dict)
                n += 1
                n = 0 if n == totalnodes else n
            mongoport = int(mongoport) + 1
            logger.debug(" ")

    add_debug_space()
    logger.info("Replicaset config :")
    for replicaset_cfg in replicaset_cfg_list:
        logger.info(replicaset_cfg)

    return replicaset_cfg_list


def get_kmip_key_id(db_path, rx_connection):
    cmd = "cat {}/restoreInfo.txt|grep 'Master Key UUID'".format(db_path)
    res = execute_bash_cmd(rx_connection, cmd, {})
    kmip_key_id = res.split(':')[1].strip()
    logger.debug("kmip_key_id = {}".format(kmip_key_id))
    return kmip_key_id


def get_shard_port(shard_config_list, dirname):
    for shard_config in shard_config_list:
        if shard_config['dirname'] == dirname:
            return shard_config['port']


def get_shard_host(shard_config_list, dirname):
    for shard_config in shard_config_list:
        if shard_config['dirname'] == dirname:
            return shard_config['node']


def get_node_conn(sourceobj, host, dataset_type='Virtual'):
    node_reference = host.split(':')[0]
    user_reference = host.split(':')[1]

    if dataset_type == "Virtual":
        node_host = sourceobj.connection.environment.host
    elif dataset_type == "Staging":
        node_host = sourceobj.staged_connection.environment.host

    try:
        # node_host:
        # This is the remote host associated with the PRIMARY environment. Used as Dummy
        # This will represent the SECONDARY environment. We are putting in the "wrong" host here
        # but that's okay since it is totally ignored.
        node_environment = RemoteEnvironment(
            name="unused", reference=node_reference, host=node_host)
        node_user = RemoteUser(name="unused", reference=user_reference)
        node_connection = RemoteConnection(
            environment=node_environment, user=node_user)
        return node_connection
    except Exception as e:
        logger.debug(
            "ERROR : Unable to generate connection object for {}".format(host))
        logger.debug(e)
        return None


def _handle_exit_code(exit_code, std_err=None, std_output=None, callback_func=None, silent_status='N'):
    if exit_code == 0:
        if silent_status == "N":
            logger.debug("Code : {}, Response : {}".format(exit_code, std_output))
        elif silent_status == "Y":
            logger.debug("Code : {}".format(exit_code))
        return 0

    else:
        if silent_status == "I":
            return 1
        # Call back function which contains logic to skip the error and continue to throw
        if callback_func:
            logger.debug("Executing call back. Seems some exception is observed. Validating last error...")
            try:
                result_of_match = callback_func(std_output)
                logger.debug("Call back result is : {}".format(result_of_match))
                if result_of_match:
                    return True
            except Exception as err:
                logger.debug("Failed to execute call back function with error: {}".format(err.message))

    error_details = std_err
    if error_details is None or error_details == "":
        error_details = std_output
    logger.debug("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  ERRROR  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    logger.debug("cmd Exit Code: {}, Error Msg : {}, Output Msg : {}".format(exit_code, std_err, std_output))
    add_debug_space()
    raise Exception(error_details)


def execute_bash_cmd(connection, cmd, env):
    logger.debug("")
    logger.debug("")
    logger.debug(
        "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    logger.debug("cmd : {}".format(cmd))
    logger.debug(
        "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    logger.debug("")
    logger.debug("")
    callback_func = None

    res = libs.run_bash(connection, cmd, env)

    # strip the each part of result to remove spaces from beginning and last of output
    outputmsg = res.stdout.replace("\n", "").strip()
    errmsg = res.stderr.replace("\n", "").strip()
    exit_code = res.exit_code

    # Verify the exit code of each executed command. 0 means command ran successfully and for other code it is failed.
    # For failed cases we need to find the scenario in which programs will die and otherwise execution will continue.
    _handle_exit_code(exit_code, errmsg, outputmsg, callback_func, 'N')

    return outputmsg


def execute_bash_cmd_nofail(connection, cmd, env):
    logger.debug("")
    logger.debug("")
    logger.debug(
        "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    logger.debug("cmd : {}".format(cmd))
    logger.debug(
        "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    logger.debug("")
    logger.debug("")
    callback_func = None

    res = libs.run_bash(connection, cmd, env)

    # strip the each part of result to remove spaces from beginning and last of output
    outputmsg = res.stdout.replace("\n", "").strip()
    errmsg = res.stderr.replace("\n", "").strip()
    exit_code = res.exit_code

    return exit_code


def execute_bash_cmd_silent(connection, cmd, env):
    logger.debug("")
    logger.debug("")
    logger.debug(
        "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    logger.debug("cmd : {}".format(cmd))
    logger.debug(
        "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    # logger.debug("")
    # logger.debug("")
    callback_func = None

    res = libs.run_bash(connection, cmd, env)

    # strip the each part of result to remove spaces from beginning and last of output
    outputmsg = res.stdout.replace("\n", "").strip()
    errmsg = res.stderr.replace("\n", "").strip()
    exit_code = res.exit_code

    # Verify the exit code of each executed command. 0 means command ran successfully and for other code it is failed.
    # For failed cases we need to find the scenario in which programs will die and otherwise execution will continue.
    _handle_exit_code(exit_code, errmsg, outputmsg, callback_func, 'Y')
    logger.debug("")
    logger.debug("")
    return outputmsg


def execute_bash_cmd_silent_status(connection, cmd, env):
    callback_func = None

    res = libs.run_bash(connection, cmd, env)

    # strip the each part of result to remove spaces from beginning and last of output
    outputmsg = res.stdout.replace("\n", "").strip()
    errmsg = res.stderr.replace("\n", "").strip()
    exit_code = res.exit_code
    logger.debug("Value for result: cmd: {} ---- outputmsg: {} ---- errmsg: {} ---- exit_code: {} ".format(cmd, outputmsg,
                                                               errmsg, exit_code ))

    # Verify the exit code of each executed command. 0 means command ran successfully and for other code it is failed.
    # For failed cases we need to find the scenario in which programs will die and otherwise execution will continue.
    # I = Ignore Error
    ret = _handle_exit_code(exit_code, errmsg, outputmsg, callback_func, 'I')
    if ret == 1:
        return 1
    return outputmsg


def execute_bash_cmd_nocmdlog(connection, cmd, env):
    # logger.debug("cmd : {}".format(cmd))
    try:
        res = libs.run_bash(connection, cmd, env)
        if res.exit_code != 0:
            logger.debug(
                "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  ERRROR  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            errmsg = res.stderr.replace("\n", "").strip()
            logger.debug("cmd res   : {}".format(res))
            logger.debug("cmd Error : {}".format(errmsg))
            return 1

        logger.debug("Response : {}".format(res.exit_code))
        outputmsg = res.stdout.replace("\n", "").strip()
        logger.debug("Success outputmsg : {}".format(outputmsg))
        return outputmsg

    except Exception as e:
        logger.debug(
            "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  EXCEPTION ERRROR  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        logger.debug("ERROR : Unable to run cmd {}".format(cmd))
        logger.debug(e)
        return 1


def gen_shardserver_setting_list(shard_config_list, sourceobj, shard_count, mount_path, dataset_type='Virtual'):
    shard_setting_list = []
    if dataset_type == 'Staging':
        make_shards_replicaset = False
    else:
        make_shards_replicaset = sourceobj.parameters.make_shards_replicaset
    for shardnum in range(shard_count):
        shard_setting_dict = {}
        snm0 = "s{}m0".format(shardnum)
        snm0_port = get_shard_port(shard_config_list, snm0)
        snm0_host = get_shard_host(shard_config_list, snm0)
        snm0_conn = get_node_conn(sourceobj, snm0_host, dataset_type)
        snm0_host_name = execute_bash_cmd(snm0_conn, "hostname", {})

        cmd = "cat {}/{}/restoreInfo.txt|grep 'Replica Set:'".format(
            mount_path, snm0)
        snm0_replica_name = execute_bash_cmd(snm0_conn, cmd, {})
        snm0_replica_name = "{}".format(
            snm0_replica_name.replace("\n", "").split(':')[1].strip())
        logger.debug("snm0_replica_name={}".format(snm0_replica_name))
        shardservercfg = "{}/{}:{}".format(snm0_replica_name,
                                           snm0_host_name.replace("\n", ""), snm0_port)

        if make_shards_replicaset:
            for member in range(1, 3):
                snm0 = "s{}m{}".format(shardnum, member)
                snmn_port = get_shard_port(shard_config_list, snm0)
                snmn_host = get_shard_host(shard_config_list, snm0)
                snmn_conn = get_node_conn(sourceobj, snmn_host, dataset_type)
                snmn_host_name = execute_bash_cmd(snmn_conn, "hostname", {})
                shardservercfg = shardservercfg + "," + \
                                 "{}:{}".format(snmn_host_name, snmn_port)

        shard_setting_dict[snm0_replica_name] = shardservercfg
        shard_setting_list.append(shard_setting_dict)
    return shard_setting_list


def gen_configsvrstring(dataset_type, sourceobj, shard_config_list):
    mount_path = sourceobj.parameters.mount_path
    # Generate configsvrstring
    c0m0_port = get_shard_port(shard_config_list, 'c0m0')
    c0m0_host = get_shard_host(shard_config_list, 'c0m0')
    c0m0_conn = get_node_conn(sourceobj, c0m0_host, dataset_type)
    c0m0_host_name = execute_bash_cmd(c0m0_conn, "hostname", {})

    cmd = "cat {}/{}/restoreInfo.txt|grep 'Replica Set:'".format(
        mount_path, "c0m0")
    c0m0_replica_name = execute_bash_cmd(c0m0_conn, cmd, {})
    c0m0_replica_name = "{}".format(c0m0_replica_name.split(':')[1].strip())
    logger.debug("c0m0_replica_name={}".format(c0m0_replica_name))
    configsvrstring = "{}/{}:{}".format(c0m0_replica_name,
                                        c0m0_host_name, c0m0_port)

    if dataset_type == "Virtual":
        replicaset = sourceobj.parameters.make_shards_replicaset
    else:
        replicaset = False

    # if sourceobj.parameters.make_shards_replicaset:
    if replicaset:
        c0m1_port = get_shard_port(shard_config_list, 'c0m1')
        c0m1_host = get_shard_host(shard_config_list, 'c0m1')
        c0m1_conn = get_node_conn(sourceobj, c0m1_host, dataset_type)
        c0m1_host_name = execute_bash_cmd(c0m1_conn, "hostname", {})
        configsvrstring = configsvrstring + "," + \
                          "{}:{}".format(c0m1_host_name, c0m1_port)

        c0m2_port = get_shard_port(shard_config_list, 'c0m2')
        c0m2_host = get_shard_host(shard_config_list, 'c0m2')
        c0m2_conn = get_node_conn(sourceobj, c0m2_host, dataset_type)
        c0m2_host_name = execute_bash_cmd(c0m2_conn, "hostname", {})
        configsvrstring = configsvrstring + "," + \
                          "{}:{}".format(c0m2_host_name, c0m2_port)

    logger.debug("configsvrstring hostname={}".format(configsvrstring))
    return configsvrstring


def gen_mongo_conf_files(dataset_type, sourceobj, shard_config_list, snapshot):
    mount_path = sourceobj.parameters.mount_path

    logger.info("Read mongo structure config file")
    if dataset_type == "Virtual":
        cfgfile = "{}/.delphix/.tgt_vdbcfg.txt".format(mount_path)
        connection = sourceobj.connection
        d_source_type = snapshot.d_source_type

        source_encrypted = snapshot.source_encrypted
        encryption_method = snapshot.encryption_method

    elif dataset_type == "Staging":
        cfgfile = "{}/.delphix/.stg_dsourcecfg.txt".format(mount_path)
        connection = sourceobj.staged_connection
        source_encrypted = sourceobj.parameters.source_encrypted
        encryption_method = sourceobj.parameters.encryption_method

        d_source_type = sourceobj.parameters.d_source_type

    logger.debug("source_encrypted={}".format(source_encrypted))
    logger.debug("encryption_method={}".format(encryption_method))

    # Read config of mongo structure
    cmd = "cat {}".format(cfgfile)
    res = execute_bash_cmd(connection, cmd, {})

    json_result = res
    json_result = json_result.replace("[", "")
    json_result = json_result.replace("]", "")
    record_length = len(json_result.split("},"))
    i = 1
    for rec in json_result.split("},"):
        if i != record_length:
            rec = rec + "}"
        rec = rec.replace("'", '"')

        logger.debug("rec = {}".format(rec))
        jsonobj = json.loads(rec)
        logger.debug("Record = {}".format(rec))

        mongod_port = jsonobj['port']
        mongod_dirname = jsonobj['dirname']
        mongod_conn = get_node_conn(sourceobj, jsonobj['node'], dataset_type)
        mongo_process_type = jsonobj['type']
        mongo_host_name = execute_bash_cmd(mongod_conn, "hostname", {})

        bind_ip = sourceobj.parameters.bind_ip
        enable_user_auth = sourceobj.parameters.enable_authentication
        enable_ssl_tls = sourceobj.parameters.enable_ssl_tls
        ssl_tls_params = sourceobj.parameters.ssl_tls_params

        keyfile_path = sourceobj.parameters.keyfile_path

        cluster_auth_mode = sourceobj.parameters.cluster_auth_mode

        enable_ldap = sourceobj.parameters.enable_ldap
        ldap_params = sourceobj.parameters.ldap_params

        enable_setparams = sourceobj.parameters.enable_setparams
        setparam_params = sourceobj.parameters.setparam_params

        kmip_params = sourceobj.parameters.kmip_params

        encryption_keyfile = sourceobj.parameters.encryption_keyfile

        enable_auditlog = sourceobj.parameters.enable_auditlog
        auditlog_params = sourceobj.parameters.auditlog_params

        if mongo_process_type == "mongos":
            # mongo_cmd = "mongos"
            mongo_cmd = "{}/mongos".format(os.path.dirname(sourceobj.mongo_install_path))
        else:
            # mongo_process_type == "shard" or mongo_process_type == "config" or mongo_process_type == "repset":
            # mongo_cmd = "mongod"
            mongo_cmd = sourceobj.mongo_install_path
        logger.info("After mongo_process_type - mongo_cmd = {}".format(mongo_cmd))

        dbpath = "{}/{}".format(mount_path, mongod_dirname)
        cfgdir = "{}/cfg".format(mount_path)
        logdir = "{}/logs".format(mount_path)
        cfgfile = "{}/dlpx.{}.{}.conf".format(cfgdir, mongod_dirname, mongod_port)
        logfile = "{}/dlpx.{}.{}.mongod.log".format(logdir, mongod_dirname, mongod_port)

        if mongo_process_type == "mongos":
            # This (dbpath) parameter is not applicable
            mongo_cmd = mongo_cmd
        else:
            # mongo_process_type == "shard" or mongo_process_type == "config" or mongo_process_type == "repset":
            mongo_cmd = "{} --dbpath {}".format(mongo_cmd, dbpath)
            logger.info("After dbpath - mongo_cmd = {}".format(mongo_cmd))

        mongo_cmd = "{} --logpath {}".format(mongo_cmd, logfile)
        logger.info("After logpath - mongo_cmd = {}".format(mongo_cmd))

        mongo_cmd = add_net(mongo_cmd, bind_ip, mongod_port, enable_ssl_tls, ssl_tls_params)
        logger.info("After add_net - mongo_cmd = {}".format(mongo_cmd))
        add_debug_space()

        logger.info("mongo_process_type: {}".format(mongo_process_type))
        # if mongo_process_type == "mongos":
        #     logger.info("user_auth_mode: {}".format(user_auth_mode))
        #     if user_auth_mode == "None" or user_auth_mode == "SCRAM":
        #         logger.info("keyfile_path: {}".format(keyfile_path))
        #         if keyfile_path is not None and keyfile_path != "":
        #             mongo_cmd = "{} --keyFile {}".format(mongo_cmd, keyfile_path)
        #             logger.info("After add_keyfile_auth - mongo_cmd = {}".format(mongo_cmd))
        #         else:
        #             logger.info("Keyfile is empty")
        #             logger.info("After add_keyfile_auth - mongo_cmd = {}".format(mongo_cmd))
        #     else:
        #         logger.info("After add_keyfile_auth - mongo_cmd = {}".format(mongo_cmd))
        # else:
        mongo_cmd = add_keyfile_auth(mongo_cmd, enable_user_auth, keyfile_path)
        logger.info("After add_keyfile_auth - mongo_cmd = {}".format(mongo_cmd))
        add_debug_space()

        mongo_cmd = add_cluster_auth(mongo_cmd, cluster_auth_mode, keyfile_path)
        logger.info("After add_cluster_auth - mongo_cmd = {}".format(mongo_cmd))
        add_debug_space()

        mongo_cmd = add_ldap(mongo_cmd, enable_ldap, ldap_params)
        logger.info("After add_ldap - mongo_cmd = {}".format(mongo_cmd))
        add_debug_space()

        mongo_cmd = add_set_parameters(mongo_cmd, enable_setparams, setparam_params)
        logger.info("After add_set_parameters - mongo_cmd = {}".format(mongo_cmd))
        add_debug_space()

        if mongo_process_type == "mongos":
            # This (add_encryption_kmip) parameter is not applicable
            mongo_cmd = mongo_cmd
        else:
            # mongo_process_type == "shard" or mongo_process_type == "config" or mongo_process_type == "repset":
            logger.info("mongo_process_type:{}".format(mongo_process_type))
            logger.info("source_encrypted:{}".format(source_encrypted))
            if source_encrypted:
                logger.info("encryption_method:{}".format(encryption_method))
                if encryption_method == "KMIP":
                    logger.info("kmip_params:{}".format(kmip_params))
                    mongo_cmd = add_encryption_kmip(mongo_cmd, kmip_params)
                    logger.info("After add_encryption_kmip - mongo_cmd = {}".format(mongo_cmd))

                    if d_source_type not in ["offlinemongodump", "onlinemongodump", "extendedcluster"]:
                        cmd = "cat {}/{}/restoreInfo.txt|grep 'Master Key UUID'".format(mount_path, mongod_dirname)
                        res = execute_bash_cmd(mongod_conn, cmd, {})
                        kmip_key_id = res.split(':')[1].strip()
                        logger.debug("kmip_key_id = {}".format(kmip_key_id))

                        mongo_cmd = mongo_cmd + " --kmipKeyIdentifier {}".format(kmip_key_id)
                        logger.info("After add_encryption_kmip kmip_key_id - mongo_cmd = {}".format(mongo_cmd))

                elif encryption_method == "KeyFile":

                    mongo_cmd = add_encryption_keyfile(mongo_cmd, encryption_keyfile)
                    logger.info("After add_encryption_keyfile - mongo_cmd = {}".format(mongo_cmd))
            add_debug_space()

        mongo_cmd = add_auditlog(mongo_cmd, enable_auditlog, auditlog_params)
        logger.info("After add_auditlog - mongo_cmd = {}".format(mongo_cmd))
        add_debug_space()

        if mongo_process_type == "shard" or mongo_process_type == "repset":
            cmd = "cat {}/s{}m0/restoreInfo.txt|grep 'Replica Set:'".format(mount_path, mongod_dirname[1:2])
            res = execute_bash_cmd(mongod_conn, cmd, {})
            repset_name = res.split(':')[1].strip()
        elif mongo_process_type == "config":
            cmd = "cat {}/c{}m0/restoreInfo.txt|grep 'Replica Set:'".format(mount_path, mongod_dirname[1:2])
            res = execute_bash_cmd(mongod_conn, cmd, {})
            repset_name = res.split(':')[1].strip()

        if mongo_process_type == "shard":
            mongo_cmd = "{} --replSet {} --shardsvr".format(mongo_cmd, repset_name)
        elif mongo_process_type == "config":
            mongo_cmd = "{} --replSet {} --configsvr".format(mongo_cmd, repset_name)
        elif mongo_process_type == "repset":
            mongo_cmd = "{} --replSet {}".format(mongo_cmd, repset_name)
        logger.info("After replSet - mongo_cmd = {}".format(mongo_cmd))
        add_debug_space()

        if mongo_process_type == "mongos":
            logger.debug("shard_config_list = {}".format(shard_config_list))
            logger.debug("dataset_type = {}".format(dataset_type))
            cfgdblist = gen_configsvrstring(dataset_type, sourceobj, shard_config_list)
            mongo_cmd = "{} --configdb {}".format(mongo_cmd, cfgdblist)
            logger.info("After configsvrstring - mongo_cmd = {}".format(mongo_cmd))

        mongo_cmd = "{} --fork".format(mongo_cmd)
        logger.info("After fork - mongo_cmd = {}".format(mongo_cmd))
        add_debug_space()

        mongo_cmd = "{} --outputConfig |grep -v outputConfig > {}".format(mongo_cmd, cfgfile)
        logger.debug("mongo_cmd = {}".format(mongo_cmd))
        add_debug_space()
        res = execute_bash_cmd(mongod_conn, mongo_cmd, {})

        # This may be bug so added to fix proactively
        fix_mongod_cmd = "sed -i 's/replSet: {}/replSetName: {}/g' {}".format(repset_name, repset_name, cfgfile)
        logger.debug("fix_mongod_cmd: {}".format(fix_mongod_cmd))
        res = execute_bash_cmd(mongod_conn, fix_mongod_cmd, {})

        i += 1


def start_sharded_mongo(dataset_type, sourceobj):
    mount_path = sourceobj.parameters.mount_path
    if dataset_type == "Virtual":
        cfgfile = "{}/.delphix/.tgt_vdbcfg.txt".format(mount_path)
        connection = sourceobj.connection
        cmd = "cat {}/.delphix/.tgt_config.txt|grep DSOURCE_TYPE".format(mount_path)
        res = execute_bash_cmd(connection, cmd, {})
        d_source_type = res.split(':')[1].strip()

    elif dataset_type == "Staging":
        cfgfile = "{}/.delphix/.stg_dsourcecfg.txt".format(mount_path)
        connection = sourceobj.staged_connection
        d_source_type = sourceobj.parameters.d_source_type

    # Start mongod instances of shards
    cmd = "cat {}".format(cfgfile)
    res = execute_bash_cmd(connection, cmd, {})

    cmd = "hostname"
    hostname = execute_bash_cmd(connection, cmd, {})

    json_result = res
    json_result = json_result.replace("[", "")
    json_result = json_result.replace("]", "")
    record_length = len(json_result.split("},"))
    i = 1
    for rec in json_result.split("},"):
        if i != record_length:
            rec = rec + "}"
        rec = rec.replace("'", '"')
        # rec = rec.replace("}}", '}')
        logger.debug("rec = {}".format(rec))
        jsonobj = json.loads(rec)
        logger.debug("Record = {}".format(rec))

        mongod_port = jsonobj['port']
        mongod_dirname = jsonobj['dirname']
        mongod_conn = get_node_conn(sourceobj, jsonobj['node'], dataset_type)

        start_string = "{}/cfg/dlpx.{}.{}.conf".format(
            mount_path, mongod_dirname, mongod_port)
        if jsonobj['type'] == 'mongos':
            # cmd = "mongos -f {}".format(start_string)
            cmd = "{}/mongos -f {}".format(os.path.dirname(sourceobj.mongo_install_path), start_string)
        else:
            # cmd = "mongod -f {}".format(start_string)
            cmd = "{} -f {}".format(sourceobj.mongo_install_path, start_string)

        res = execute_bash_cmd(mongod_conn, cmd, {})
        i += 1

    if d_source_type == "shardedsource":
        # Start Balancer ( only for sharded )
        mongos_port = sourceobj.parameters.mongos_port
        start_portpool = sourceobj.parameters.start_portpool
        if mongos_port != start_portpool:
            # if both are same, it means nonsharded as we adjusted in mongopy.py
            mongo_shell_cmd = gen_mongo_cmd(dataset_type, sourceobj, hostname)
            cmd = "{} --port {} --eval 'sh.startBalancer()'".format(mongo_shell_cmd, mongos_port)
            logger.info("cmd = {}".format(cmd))
            res = execute_bash_cmd(connection, cmd, {})


def stop_sharded_mongo(dataset_type, sourceobj):
    mount_path = sourceobj.parameters.mount_path
    mongos_port = sourceobj.parameters.mongos_port

    if dataset_type == "Virtual":
        cfgfile = "{}/.delphix/.tgt_vdbcfg.txt".format(mount_path)
        connection = sourceobj.connection
        cmd = "cat {}/.delphix/.tgt_config.txt|grep DSOURCE_TYPE".format(mount_path)
        res = execute_bash_cmd(connection, cmd, {})
        d_source_type = res.split(':')[1].strip()

    elif dataset_type == "Staging":
        cfgfile = "{}/.delphix/.stg_dsourcecfg.txt".format(mount_path)
        connection = sourceobj.staged_connection
        d_source_type = sourceobj.parameters.d_source_type

    # cmd = "ps -ef|grep mongo|grep {}|grep {}|grep {}|grep dlpx|grep -v grep|wc -l".format(
    #    mount_path, "mgs0", mongos_port)
    # res = execute_bash_cmd(connection, cmd, {})

    cmd = "hostname"
    hostname = execute_bash_cmd(connection, cmd, {})

    mongo_shell_cmd = gen_mongo_cmd(dataset_type, sourceobj, hostname)
    mongos_port = sourceobj.parameters.mongos_port

    if d_source_type == "shardedsource":
        try:
            # Stop Balancer
            cmd = "{} --port {} --eval 'sh.stopBalancer()'".format(mongo_shell_cmd, mongos_port)
            res = execute_bash_cmd_nofail(connection, cmd, {})
        except Exception as e:
            pass

    if d_source_type == "stagingpush" and dataset_type == "Staging":
        logger.debug("Not Applicable for Staging-Stagingpush")
    else:
        # Stop mongod instances of shards
        cmd = "cat {}".format(cfgfile)
        res = execute_bash_cmd(connection, cmd, {})

        json_result = res
        json_result = json_result.replace("[", "")
        json_result = json_result.replace("]", "")
        record_length = len(json_result.split("},"))
        i = 1
        for rec in json_result.split("},"):
            if i != record_length:
                rec = rec + "}"
            rec = rec.replace("'", '"')
            jsonobj = json.loads(rec)
            logger.debug("Record = {}".format(rec))
            mongod_port = jsonobj['port']
            mongod_conn = get_node_conn(sourceobj, jsonobj['node'], dataset_type)
            mongod_dirname = jsonobj['dirname']

            cmd = "ps -ef|grep mongo|grep {}|grep {}|grep {}|grep dlpx|grep -v grep|wc -l".format(
                mount_path, mongod_dirname, mongod_port)
            res = execute_bash_cmd(mongod_conn, cmd, {})
            if int(res) == 1:
                cmd = "ps -ef|grep mongo|grep {}|grep {}|grep {}|grep -v grep|awk '{{ print \"kill \"$2 }}'|sh".format(
                    mount_path, mongod_dirname, mongod_port)
                res = execute_bash_cmd(mongod_conn, cmd, {})
            i += 1
        # Sleep for 10 sec to cleanly get out of all killed processes.
        time.sleep(7)


def get_status_sharded_mongo(dataset_type, sourceobj):
    active_status_flag = 0
    mount_path = sourceobj.parameters.mount_path
    dsource_type = ''

    if dataset_type == "Virtual":
        cfgfile = "{}/.delphix/.tgt_vdbcfg.txt".format(mount_path)
        connection = sourceobj.connection
    elif dataset_type == "Staging":
        cfgfile = "{}/.delphix/.stg_dsourcecfg.txt".format(mount_path)
        connection = sourceobj.staged_connection

        cmd = "cat {}/.delphix/.stg_config.txt | grep DSOURCE_TYPE".format(mount_path)
        res = execute_bash_cmd_silent_status(connection, cmd, {})
        if str(res) == "1":
            return active_status_flag
        dsource_type = res.split(':')[1]
    # logger.debug("cfgfile : {}".format(cfgfile))

    try:
        # Check if mongod/mongos process is running
        try:
            cmd = "cat {}".format(cfgfile)
            res = execute_bash_cmd_silent_status(connection, cmd, {})
            if res == 1:
                active_status_flag = 1
                return active_status_flag
        except Exception as e:
            logger.debug("File {} not found".format(cfgfile))
            active_status_flag = 1
            return active_status_flag

        json_result = res
        json_result = json_result.replace("[", "")
        json_result = json_result.replace("]", "")
        record_length = len(json_result.split("},"))
        i = 1
        for rec in json_result.split("},"):
            if i != record_length:
                rec = rec + "}"
            rec = rec.replace("'", '"')
            jsonobj = json.loads(rec)
            # logger.debug("Record = {}".format(rec))
            mongod_port = jsonobj['port']
            mongod_conn = get_node_conn(sourceobj, jsonobj['node'], dataset_type)
            mongod_dirname = jsonobj['dirname']
            if dsource_type == "stagingpush":
                cmd = "netstat -an|grep {}|wc -l".format(mongod_port)
            else:
                cmd = "ps -ef|grep mongo|grep {}|grep {}|grep {}|grep dlpx|grep -v grep|wc -l".format(
                    mount_path, mongod_dirname, mongod_port)
            res = execute_bash_cmd(mongod_conn, cmd, {})

            if int(res) == 0:
                logger.debug(
                    "Process for {}/cfg/dlpx.{}.{}.conf not running".format(mount_path, mongod_dirname, mongod_port))
                active_status_flag = 1
                return active_status_flag
                break

            i += 1

    except Exception as e:
        logger.debug(
            "ERROR : Checking status of sharded mongo - Mongos {} at {}".format(sourceobj.parameters.mongos_port,
                                                                                mount_path))
        logger.debug(e)
        active_status_flag = 1
        return active_status_flag

    return active_status_flag


def create_mongoadmin_user(sourceobj, connection, shard_count, shard_config_list, resync=False, dsource_type=None):
    logger.info("Creating Mongo Admin User")
    mongo_db_user = sourceobj.parameters.mongo_db_user
    mongo_db_password = sourceobj.parameters.mongo_db_password
    # In case of nonsharded source, start_portpool is copied to mongos_port in mongopy.py
    mongos_port = sourceobj.parameters.mongos_port
    # mongo_shell_cmd = "mongo"

    mongo_shell_cmd = sourceobj.mongo_shell_path
    if not resync and dsource_type and dsource_type == "onlinemongodump":
        cmd = "hostname"
        hostname = execute_bash_cmd(connection, cmd, {})
        mongo_shell_cmd = gen_mongo_cmd("Staging",sourceobj,hostname)

    # cmd = "{} --port {} --quiet --eval \"db.createRole({{ role: \"delphixadminrole\", privileges: [ {{ resource: {{ anyResource: true }}, actions: [ \"anyAction\" ] }}], roles: [{{ role: 'root', db: 'admin'}},{{ role: 'userAdminAnyDatabase', db: 'admin'}},{{ role: 'dbAdminAnyDatabase', db: 'admin'}},{{ role: 'readWriteAnyDatabase', db: 'admin'}},{{ role: 'clusterAdmin', db: 'admin'}}]}})\"".format(mongo_shell_cmd,mongos_port,mongo_db_user,mongo_db_password)
    cmd = "{} admin --port {} --quiet --eval \"db.createRole({{ role: \\\"delphixadminrole\\\", privileges: [{{ resource: {{ anyResource: true }}, actions: [ \\\"anyAction\\\" ] }}], roles: []}})\"".format(
        mongo_shell_cmd, mongos_port, mongo_db_user, mongo_db_password)
    res = execute_bash_cmd(connection, cmd, {})

    cmd = "{} --port {} --quiet --eval \"db.getSiblingDB('admin').createUser({{ user : '{}', pwd :  '{}', roles : ['__system', 'delphixadminrole',{{ role: 'root', db: 'admin'}},{{ role: 'userAdminAnyDatabase', db: 'admin'}},{{ role: 'dbAdminAnyDatabase', db: 'admin'}},{{ role: 'readWriteAnyDatabase', db: 'admin'}},{{ role: 'clusterAdmin', db: 'admin'}}]}})\"".format(
        mongo_shell_cmd, mongos_port, mongo_db_user, mongo_db_password)
    res = execute_bash_cmd(connection, cmd, {})

    # In case of nonsharded source, below will not be executed as shard_count = 0 passed as parameter
    for shardnum in range(shard_count):
        logger.info("Create {} user in Shard s{}".format(mongo_db_user, shardnum))
        snm0_port = get_shard_port(shard_config_list, 's{}m0'.format(shardnum))
        snm0_host = get_shard_host(shard_config_list, 's{}m0'.format(shardnum))
        snm0_conn = get_node_conn(sourceobj, snm0_host, 'Staging')

        cmd = "{} --port {} --quiet --eval \"db.getSiblingDB('admin').createUser({{ user : '{}', pwd :  '{}', roles : [{{ role: 'userAdminAnyDatabase', db: 'admin'}},{{ role: 'dbAdminAnyDatabase', db: 'admin'}},{{ role: 'readWriteAnyDatabase', db: 'admin'}},{{ role: 'clusterAdmin', db: 'admin'}}]}});\"".format(
            mongo_shell_cmd, snm0_port, mongo_db_user, mongo_db_password)
        res = execute_bash_cmd(snm0_conn, cmd, {})

    logger.info("Creating Mongo Admin User - Done")
    return res


def update_mongoadmin_pwd(sourceobj, connection, shard_count, shard_config_list, mongo_db_user, mongo_db_password,
                          mongos_port):
    logger.info("Updating password of Mongo Admin User")
    # mongo_shell_cmd = "mongo"

    # mongo_shell_cmd = "{}/mongo".format(os.path.dirname(sourceobj.mongo_install_path))
    mongo_shell_cmd = sourceobj.mongo_shell_path

    logger.info("Update {} password".format(mongo_db_user))
    cmd = "{} --port {} --eval \"db.getSiblingDB('admin').updateUser('{}', {{pwd :  '{}'}});\"".format(mongo_shell_cmd,
                                                                                                       mongos_port,
                                                                                                       mongo_db_user,
                                                                                                       mongo_db_password)
    res = execute_bash_cmd(connection, cmd, {})

    for shardnum in range(shard_count):
        logger.info("Update {} password in Shard s{}".format(mongo_db_user, shardnum))
        snm0_port = get_shard_port(shard_config_list, 's{}m0'.format(shardnum))
        snm0_host = get_shard_host(shard_config_list, 's{}m0'.format(shardnum))
        snm0_conn = get_node_conn(sourceobj, snm0_host, 'Virtual')

        cmd = "{} --port {} --eval \"db.getSiblingDB('admin').updateUser('{}', {{pwd :  '{}'}});\"".format(
            mongo_shell_cmd, snm0_port, mongo_db_user, mongo_db_password)
        res = execute_bash_cmd(snm0_conn, cmd, {})
        time.sleep(1)

    logger.info("Updated Mongo Admin User password - Done")
    return res


def gen_mongo_cmd(dataset_type, sourceobj, hostname, use_source=False):
    client_tls_cert = sourceobj.parameters.client_tls_cert
    client_tls_cacert = sourceobj.parameters.client_tls_cacert
    mount_path = sourceobj.parameters.mount_path

    if use_source:
        mongo_db_user = sourceobj.parameters.src_db_user
        mongo_db_password = sourceobj.parameters.src_db_password
    else:
        if dataset_type == "Staging":
            mongo_db_user = sourceobj.parameters.mongo_db_user
            mongo_db_password = sourceobj.parameters.mongo_db_password
        elif dataset_type == "Virtual":
            rx_connection = sourceobj.connection
            cmd = "cat {}/.delphix/.stg_config.txt|grep 'MONGO_DB_USER:'|cut -d':' -f2".format(mount_path)
            mongo_db_user = execute_bash_cmd(rx_connection, cmd, {})
            mongo_db_password = sourceobj.parameters.mongo_db_password

    # mongo_shell_cmd = "mongo"
    mongo_shell_cmd = "{} ".format(sourceobj.mongo_shell_path)

    logger.debug("enable_ssl_tls: {}".format(sourceobj.parameters.enable_ssl_tls))
    if sourceobj.parameters.enable_ssl_tls:
        mongo_shell_cmd = "{} --tls --host {} --tlsCertificateKeyFile {} --tlsCAFile {}".format(mongo_shell_cmd,
                                                                                                hostname,
                                                                                                client_tls_cert,
                                                                                                client_tls_cacert)

    if sourceobj.parameters.keyfile_path:
        mongo_shell_cmd = "{} --username {} --password {} --authenticationDatabase admin".format(mongo_shell_cmd,
                                                                                                 mongo_db_user,
                                                                                                 mongo_db_password)

    return mongo_shell_cmd


def fsync_lock_sharded_mongo(sourceobj, dataset_type='Virtual'):
    mount_path = sourceobj.parameters.mount_path
    mongos_port = sourceobj.parameters.mongos_port
    if dataset_type == "Virtual":
        cfgfile = "{}/.delphix/.tgt_vdbcfg.txt".format(mount_path)
        connection = sourceobj.connection
    elif dataset_type == "Staging":
        cfgfile = "{}/.delphix/.stg_dsourcecfg.txt".format(mount_path)
        connection = sourceobj.staged_connection

    cmd = "hostname"
    hostname = execute_bash_cmd(connection, cmd, {})

    mongo_shell_cmd = gen_mongo_cmd(dataset_type, sourceobj, hostname)

    # Stop Balancer
    cmd = "{} --port {} --eval 'sh.stopBalancer()'".format(mongo_shell_cmd, mongos_port)
    logger.info("cmd = {}".format(cmd))
    res = execute_bash_cmd(connection, cmd, {})

    # Freeze mongod instances of shards
    cmd = "cat {}".format(cfgfile)
    res = execute_bash_cmd(connection, cmd, {})

    json_result = res
    json_result = json_result.replace("[", "")
    json_result = json_result.replace("]", "")
    record_length = len(json_result.split("},"))
    i = 1
    for rec in json_result.split("},"):
        if i != record_length:
            rec = rec + "}"
        rec = rec.replace("'", '"')
        # rec = rec.replace("}}", '}')
        logger.debug("rec = {}".format(rec))
        jsonobj = json.loads(rec)
        logger.debug("Record = {}".format(rec))

        mongod_port = jsonobj['port']
        mongod_dirname = jsonobj['dirname']
        mongod_conn = get_node_conn(sourceobj, jsonobj['node'], dataset_type)

        if jsonobj['type'] != 'mongos':
            cmd = "{} --port {} --eval 'db.fsyncLock()'".format(mongo_shell_cmd, mongod_port)

        res = execute_bash_cmd(mongod_conn, cmd, {})
        i += 1


def fsync_unlock_sharded_mongo(sourceobj, dataset_type='Virtual'):
    mount_path = sourceobj.parameters.mount_path
    if dataset_type == "Virtual":
        cfgfile = "{}/.delphix/.tgt_vdbcfg.txt".format(mount_path)
        connection = sourceobj.connection
    elif dataset_type == "Staging":
        cfgfile = "{}/.delphix/.stg_dsourcecfg.txt".format(mount_path)
        connection = sourceobj.staged_connection

    cmd = "hostname"
    hostname = execute_bash_cmd(connection, cmd, {})

    mongo_shell_cmd = gen_mongo_cmd(dataset_type, sourceobj, hostname)

    # Freeze mongod instances of shards
    cmd = "cat {}".format(cfgfile)
    res = execute_bash_cmd(connection, cmd, {})

    json_result = res
    json_result = json_result.replace("[", "")
    json_result = json_result.replace("]", "")
    record_length = len(json_result.split("},"))
    i = 1
    for rec in json_result.split("},"):
        if i != record_length:
            rec = rec + "}"
        rec = rec.replace("'", '"')
        # rec = rec.replace("}}", '}')
        logger.debug("rec = {}".format(rec))
        jsonobj = json.loads(rec)
        logger.debug("Record = {}".format(rec))

        mongod_port = jsonobj['port']
        mongod_dirname = jsonobj['dirname']
        mongod_conn = get_node_conn(sourceobj, jsonobj['node'], dataset_type)

        if jsonobj['type'] != 'mongos':
            cmd = "{} --port {} --eval 'db.fsyncUnlock()'".format(mongo_shell_cmd, mongod_port)

        res = execute_bash_cmd(mongod_conn, cmd, {})
        i += 1

    # Start Balancer
    mongos_port = sourceobj.parameters.mongos_port
    cmd = "{} --port {} --eval 'sh.startBalancer()'".format(mongo_shell_cmd, mongos_port)
    logger.info("cmd = {}".format(cmd))
    res = execute_bash_cmd(connection, cmd, {})


def fsync_lock_mongo(sourceobj, dataset_type):
    mount_path = sourceobj.parameters.mount_path
    mongos_port = sourceobj.parameters.mongos_port
    if dataset_type == "Virtual":
        cfgfile = "{}/.delphix/.tgt_vdbcfg.txt".format(mount_path)
        connection = sourceobj.connection
    elif dataset_type == "Staging":
        cfgfile = "{}/.delphix/.stg_dsourcecfg.txt".format(mount_path)
        connection = sourceobj.staged_connection

    cmd = "hostname"
    hostname = execute_bash_cmd(connection, cmd, {})

    mongo_shell_cmd = gen_mongo_cmd(dataset_type, sourceobj, hostname)

    cmd = "cat {}".format(cfgfile)
    res = execute_bash_cmd(connection, cmd, {})

    json_result = res
    json_result = json_result.replace("[", "")
    json_result = json_result.replace("]", "")
    record_length = len(json_result.split("},"))
    i = 1
    for rec in json_result.split("},"):
        if i != record_length:
            rec = rec + "}"
        rec = rec.replace("'", '"')
        # rec = rec.replace("}}", '}')
        logger.debug("rec = {}".format(rec))
        jsonobj = json.loads(rec)
        logger.debug("Record = {}".format(rec))

        mongod_port = jsonobj['port']
        mongod_dirname = jsonobj['dirname']
        mongod_conn = get_node_conn(sourceobj, jsonobj['node'], dataset_type)

        if jsonobj['type'] != 'mongos':
            cmd = "{} --port {} --eval 'db.fsyncLock()'".format(mongo_shell_cmd, mongod_port)

        res = execute_bash_cmd(mongod_conn, cmd, {})
        i += 1


def fsync_unlock_mongo(sourceobj, dataset_type):
    mount_path = sourceobj.parameters.mount_path
    if dataset_type == "Virtual":
        cfgfile = "{}/.delphix/.tgt_vdbcfg.txt".format(mount_path)
        connection = sourceobj.connection
    elif dataset_type == "Staging":
        cfgfile = "{}/.delphix/.stg_dsourcecfg.txt".format(mount_path)
        connection = sourceobj.staged_connection

    cmd = "hostname"
    hostname = execute_bash_cmd(connection, cmd, {})

    mongo_shell_cmd = gen_mongo_cmd(dataset_type, sourceobj, hostname)

    cmd = "cat {}".format(cfgfile)
    res = execute_bash_cmd(connection, cmd, {})

    json_result = res
    json_result = json_result.replace("[", "")
    json_result = json_result.replace("]", "")
    record_length = len(json_result.split("},"))
    i = 1
    for rec in json_result.split("},"):
        if i != record_length:
            rec = rec + "}"
        rec = rec.replace("'", '"')
        # rec = rec.replace("}}", '}')
        logger.debug("rec = {}".format(rec))
        jsonobj = json.loads(rec)
        logger.debug("Record = {}".format(rec))

        mongod_port = jsonobj['port']
        mongod_dirname = jsonobj['dirname']
        mongod_conn = get_node_conn(sourceobj, jsonobj['node'], dataset_type)

        if jsonobj['type'] != 'mongos':
            cmd = "{} --port {} --eval 'db.fsyncUnlock()'".format(mongo_shell_cmd, mongod_port)

        res = execute_bash_cmd(mongod_conn, cmd, {})
        i += 1


def setup_mongos(sourceobj, rx_connection, mount_path, membernum, mongos_port, configsvrstring, shard_config_list):
    logger.debug("Setup Mongos Servers")

    dbpath = "{}/mgs{}".format(mount_path, membernum)
    cfgdir = "{}/cfg".format(mount_path)
    logdir = "{}/logs".format(mount_path)
    cfgfile = "{}/dlpx.mgs{}.{}.conf".format(cfgdir, membernum, mongos_port)
    logfile = "{}/dlpx.mgs{}.{}.mongod.log".format(logdir, membernum, mongos_port)

    cmd = "hostname"
    hostname = execute_bash_cmd(rx_connection, cmd, {})
    logger.debug("{},{},{},{}".format(dbpath, mongos_port, cfgfile, hostname))

    # cmd = "mongos --bind_ip 0.0.0.0 --port {} --configdb {} --logpath {} --fork".format(mongos_port, configsvrstring,
    #                                                                                        logfile)
    cmd = "{}/mongos --bind_ip 0.0.0.0 --port {} --configdb {} --logpath {} --fork".format(
        os.path.dirname(sourceobj.mongo_install_path), mongos_port, configsvrstring,
        logfile)
    # restart_mongos_cmd = "mongos --bind_ip 0.0.0.0 --port {} --configdb {} --logpath {} --fork".format(mongos_port,
    #                                                                                                   configsvrstring,
    #                                                                                                   logfile)
    restart_mongos_cmd = "{}/mongos --bind_ip 0.0.0.0 --port {} --configdb {} --logpath {} --fork".format(
        os.path.dirname(sourceobj.mongo_install_path), mongos_port,
        configsvrstring,
        logfile)
    res = execute_bash_cmd(rx_connection, cmd, {})
    time.sleep(3)

    mgs0_port = get_shard_port(shard_config_list, "mgs0")
    c0m0_port = get_shard_port(shard_config_list, "c0m0")
    logger.debug("mgs0_port: {}, c0m0_port: {}".format(mgs0_port, c0m0_port))

    # cmd = "mongo --port {} --quiet --eval 'sh.status()'".format(mgs0_port)
    cmd = "{} --port {} --quiet --eval 'sh.status()'".format(sourceobj.mongo_shell_path, mgs0_port)
    res = execute_bash_cmd(rx_connection, cmd, {})

    # cmd = "mongo --port {} --quiet --eval 'sh.startBalancer()'".format(mgs0_port)
    cmd = "{} --port {} --quiet --eval 'sh.startBalancer()'".format(sourceobj.mongo_shell_path, mgs0_port)
    res = execute_bash_cmd(rx_connection, cmd, {})

    # cmd = "mongo admin --port {} --quiet --eval 'db.runCommand(\"getShardMap\")'".format(c0m0_port)
    cmd = "{} admin --port {} --quiet --eval 'db.runCommand(\"getShardMap\")'".format(sourceobj.mongo_shell_path,
                                                                                      c0m0_port)
    res = execute_bash_cmd(rx_connection, cmd, {})


def setup_config_member(sourceobj, rx_connection, mount_path, confignum, membernum, cfg_port, shardcount,
                        shard_config_list,
                        encryption_method, enc_params_list_string, shardserver_setting_list):
    dbpath = "{}/c{}m{}".format(mount_path, confignum, membernum)
    cfgdir = "{}/cfg".format(mount_path)
    logdir = "{}/logs".format(mount_path)
    cfgfile = "{}/dlpx.c{}m{}.{}.conf".format(cfgdir, confignum, membernum, cfg_port)
    logfile = "{}/dlpx.c{}m{}.{}.mongod.log".format(logdir, confignum, membernum, cfg_port)

    cmd = "hostname"
    hostname = execute_bash_cmd(rx_connection, cmd, {})
    logger.debug("{},{},{},{},{}".format(dbpath, cfg_port, shardcount, cfgfile, hostname))

    cmd = "cat {}/c{}m{}/restoreInfo.txt|grep 'Replica Set:'".format(mount_path, confignum, membernum)
    res = execute_bash_cmd(rx_connection, cmd, {})
    config_repset_name = res.split(':')[1].strip()
    logger.debug("config_repset_name = {}".format(config_repset_name))

    if encryption_method is None:
        cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} --fork".format(sourceobj.mongo_install_path,
                                                                                      cfg_port, dbpath, logfile)
        restart_mongod_cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} --fork --replSet {} --configsvr".format(
            sourceobj.mongo_install_path,
            cfg_port, dbpath, logfile, config_repset_name)
    else:
        cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} {} --fork".format(sourceobj.mongo_install_path,
                                                                                         cfg_port, dbpath, logfile,
                                                                                         enc_params_list_string)
        restart_mongod_cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} {} --fork --replSet {} --configsvr".format(
            sourceobj.mongo_install_path,
            cfg_port, dbpath, logfile, enc_params_list_string, config_repset_name)

    res = execute_bash_cmd(rx_connection, cmd, {})
    time.sleep(7)

    cmd = "{} local --port {} --quiet --eval 'db.dropDatabase()'".format(sourceobj.mongo_shell_path, cfg_port)
    res = execute_bash_cmd(rx_connection, cmd, {})

    for i in range(shardcount):
        shardmember = "s{}m0".format(i)
        snm0_port = get_shard_port(shard_config_list, shardmember)
        shard_dbpath = "{}/s{}m0".format(mount_path, i)
        logger.debug("{},{},{}".format(shardmember, snm0_port, shard_dbpath))
        logger.debug("adjust_config_shardinfo - Start")
        adjust_config_shardinfo(sourceobj, rx_connection, shard_dbpath, cfg_port, hostname, snm0_port,
                                shardserver_setting_list)
        logger.debug("adjust_config_shardinfo - End")

    # cmd = "ps -ef|grep mongo|grep {}|grep {}|grep -v grep|awk '{ print \"kill \"$2}'|sh".format(dbpath, cfg_port)
    shutdown_server(rx_connection, sourceobj.mongo_shell_path, cfg_port)

    # start_mongod_cmd = "mongod -f {}".format(cfgfile)
    res = execute_bash_cmd(rx_connection, restart_mongod_cmd, {})

    return restart_mongod_cmd


def setup_config_replset_members(shard_config_list, sourceobj, mount_path, encryption_method,
                                 enc_params_list_string, dataset_type):
    confignum = 0
    c0m0_port = get_shard_port(shard_config_list, 'c0m0')
    c0m0_host = get_shard_host(shard_config_list, 'c0m0')
    c0m0_conn = get_node_conn(sourceobj, c0m0_host, dataset_type)

    for i in range(1, 3):
        membernum = i
        add_debug_heading_block("Member: c{}m{}".format(confignum, membernum))
        cnmn_port = get_shard_port(shard_config_list, 'c{}m{}'.format(confignum, membernum))
        cnmn_host = get_shard_host(shard_config_list, 'c{}m{}'.format(confignum, membernum))
        cnmn_conn = get_node_conn(sourceobj, cnmn_host, dataset_type)
        cnmn_host_name = execute_bash_cmd(cnmn_conn, "hostname", {})

        dbpath = "{}/c{}m{}".format(mount_path, confignum, membernum)
        cfgdir = "{}/cfg".format(mount_path)
        logdir = "{}/logs".format(mount_path)
        cfgfile = "{}/dlpx.c{}m{}.{}.conf".format(cfgdir, confignum, membernum, cnmn_port)
        logfile = "{}/dlpx.c{}m{}.{}.mongod.log".format(logdir, confignum, membernum, cnmn_port)

        logger.debug("{},{},{},{}".format(dbpath, cnmn_port, cfgfile, cnmn_host_name))

        cmd = "cp -p {}/c0m0/restoreInfo.txt {}/c{}m{}/restoreInfo.txt".format(mount_path, mount_path, confignum,
                                                                               membernum)
        res = execute_bash_cmd(c0m0_conn, cmd, {})

        cmd = "cat {}/c{}m{}/restoreInfo.txt|grep 'Replica Set:'".format(mount_path, "0", "0")
        res = execute_bash_cmd(c0m0_conn, cmd, {})

        config_repset_name = res.split(':')[1].strip()
        logger.debug("config_repset_name = {}".format(config_repset_name))

        if encryption_method is None:
            cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} --fork".format(sourceobj.mongo_install_path,
                                                                                          cnmn_port, dbpath,
                                                                                          logfile)
            restart_mongod_cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} --fork --replSet {} --configsvr".format(
                sourceobj.mongo_install_path,
                cnmn_port, dbpath, logfile, config_repset_name)
        else:
            cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} {} --fork".format(
                sourceobj.mongo_install_path, cnmn_port, dbpath,
                logfile,
                enc_params_list_string)
            restart_mongod_cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} {} --fork --replSet {} --configsvr".format(
                sourceobj.mongo_install_path,
                cnmn_port, dbpath, logfile, enc_params_list_string, config_repset_name)

        res = execute_bash_cmd(cnmn_conn, cmd, {})
        time.sleep(7)

        # cmd = "ps -ef|grep mongo|grep {}|grep {}|grep -v grep|awk '{ print \"kill \"$2}'|sh".format(dbpath, cnmn_port)

        shutdown_server(cnmn_conn, sourceobj.mongo_shell_path, cnmn_port)

        res = execute_bash_cmd(cnmn_conn, restart_mongod_cmd, {})
        time.sleep(5)

        # Add Member to replicaset
        logger.info("Add replicaset Member c{}m{} to replicaset {}".format(confignum, membernum, config_repset_name))
        cmd = '{} --port {} --eval \'rs.add("{}:{}")\''.format(sourceobj.mongo_shell_path, c0m0_port, cnmn_host_name,
                                                               cnmn_port)
        cmd_response = execute_bash_cmd(c0m0_conn, cmd, {})
        logger.info(
            "Add replicaset Member c{}m{} to replicaset {} - done".format(confignum, membernum, config_repset_name))

        add_debug_space()


def setup_shard_replset_members(shard_config_list, virtual_source, mount_path, encryption_method,
                                base_enc_params_list_string, shard_count, dataset_type):
    logger.debug("shard_count :{}".format(shard_count))
    logger.debug("mount_path  :{}".format(mount_path))
    for shardnum in range(shard_count):
        snm0_port = get_shard_port(shard_config_list, 's{}m0'.format(shardnum))
        snm0_host = get_shard_host(shard_config_list, 's{}m0'.format(shardnum))
        snm0_conn = get_node_conn(virtual_source, snm0_host, dataset_type)

        if encryption_method == "KMIP":
            kmip_key_id = get_kmip_key_id("{}/s{}m0".format(mount_path, shardnum), snm0_conn)
            enc_params_list_string = base_enc_params_list_string
            enc_params_list_string = enc_params_list_string + " --kmipKeyIdentifier {}".format(kmip_key_id)
        else:
            kmip_key_id = None

        for i in range(1, 3):
            membernum = i
            add_debug_heading_block("Member: s{}m{}".format(shardnum, membernum))
            snmn_port = get_shard_port(shard_config_list, 's{}m{}'.format(shardnum, membernum))
            snmn_host = get_shard_host(shard_config_list, 's{}m{}'.format(shardnum, membernum))
            snmn_conn = get_node_conn(virtual_source, snmn_host, dataset_type)
            snmn_host_name = execute_bash_cmd(snmn_conn, "hostname", {})

            dbpath = "{}/s{}m{}".format(mount_path, shardnum, membernum)
            cfgdir = "{}/cfg".format(mount_path)
            logdir = "{}/logs".format(mount_path)
            cfgfile = "{}/dlpx.s{}m{}.{}.conf".format(cfgdir, shardnum, membernum, snmn_port)
            logfile = "{}/dlpx.s{}m{}.{}.mongod.log".format(logdir, shardnum, membernum, snmn_port)

            logger.debug("{},{},{}".format(dbpath, cfgfile, snmn_host_name))

            # Create restoreInfo.txt file and add correct encryption keyid for KMIP
            cmd = "cp -p {}/s{}m0/restoreInfo.txt {}/s{}m{}/restoreInfo.txt".format(mount_path, shardnum, mount_path,
                                                                                    shardnum,
                                                                                    membernum)
            res = execute_bash_cmd(snmn_conn, cmd, {})
            cmd = "sed -i '/Master Key UUID/d' {}/s{}m{}/restoreInfo.txt".format(mount_path, shardnum, membernum)
            res = execute_bash_cmd(snmn_conn, cmd, {})
            if encryption_method:
                cmd = "echo 'Master Key UUID: {}' >> {}/s{}m{}/restoreInfo.txt".format(kmip_key_id, mount_path, shardnum,
                                                                                   membernum)
                res = execute_bash_cmd(snmn_conn, cmd, {})
            logger.info("Copied and Adjusted restoreInfo.txt")

            cmd = "cat {}/s{}m{}/restoreInfo.txt|grep 'Replica Set:'".format(mount_path, shardnum, "0")
            res = execute_bash_cmd(snm0_conn, cmd, {})
            shard_repset_name = res.split(':')[1].strip()
            logger.debug("shard_repset_name = {}".format(shard_repset_name))

            if encryption_method is None:
                cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} --fork".format(
                    virtual_source.mongo_install_path, snmn_port, dbpath,
                    logfile)
                restart_mongod_cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} --fork --replSet {} --shardsvr".format(
                    virtual_source.mongo_install_path,

                    snmn_port, dbpath, logfile, shard_repset_name)
            else:
                cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} {} --fork".format(
                    virtual_source.mongo_install_path, snmn_port, dbpath,
                    logfile,
                    enc_params_list_string)
                restart_mongod_cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} {} --fork --replSet {} --shardsvr".format(
                    virtual_source.mongo_install_path,
                    snmn_port, dbpath, logfile, enc_params_list_string, shard_repset_name)

            res = execute_bash_cmd(snmn_conn, cmd, {})
            time.sleep(7)

            add_debug_space()

            # cmd = "ps -ef|grep mongo|grep {}|grep {}|grep -v grep|awk '{ print \"kill \"$2}'|sh".format(dbpath, snmn_conn)
            shutdown_server(snmn_conn, virtual_source.mongo_shell_path, snmn_port)

            add_debug_space()

            res = execute_bash_cmd(snmn_conn, restart_mongod_cmd, {})
            time.sleep(5)

            # Add Member to replicaset
            logger.info("Add replicaset Member s{}m{} to replicaset {}".format(shardnum, membernum, shard_repset_name))
            cmd = '{} --port {} --eval \'rs.add("{}:{}")\''.format(virtual_source.mongo_shell_path, snm0_port,
                                                                   snmn_host_name, snmn_port)
            cmd_response = execute_bash_cmd(snm0_conn, cmd, {})
            logger.info(
                "Add replicaset Member s{}m{} to replicaset {} - done".format(shardnum, membernum, shard_repset_name))

            add_debug_space()


def add_replset_members(sourceobj, dataset_type, start_portpool, replicaset_config_list, mount_path, encryption_method,
                        enc_params_list_string):
    if dataset_type == "Virtual":
        cfgfile = "{}/.delphix/.tgt_vdbcfg.txt".format(mount_path)
        rx_connection = sourceobj.connection
    elif dataset_type == "Staging":
        cfgfile = "{}/.delphix/.stg_dsourcecfg.txt".format(mount_path)
        rx_connection = sourceobj.staged_connection

    s0m0_port = start_portpool
    s0m0_host = get_shard_host(replicaset_config_list, 's0m0')
    s0m0_conn = get_node_conn(sourceobj, s0m0_host)

    for i in range(1, 3):
        membernum = i
        add_debug_heading_block("Member: s0m{}".format(membernum))
        snmn_port = get_shard_port(replicaset_config_list, 's0m{}'.format(membernum))
        snmn_host = get_shard_host(replicaset_config_list, 's0m{}'.format(membernum))
        snmn_conn = get_node_conn(sourceobj, snmn_host)
        snmn_host_name = execute_bash_cmd(snmn_conn, "hostname", {})

        dbpath = "{}/s0m{}".format(mount_path, membernum)
        cfgdir = "{}/cfg".format(mount_path)
        logdir = "{}/logs".format(mount_path)
        cfgfile = "{}/dlpx.s0m{}.{}.conf".format(cfgdir, membernum, snmn_port)
        logfile = "{}/dlpx.s0m{}.{}.mongod.log".format(logdir, membernum, snmn_port)

        logger.debug("{},{},{},{}".format(dbpath, snmn_port, cfgfile, snmn_host_name))

        cmd = "cp -p {}/s0m0/restoreInfo.txt {}/s0m{}/restoreInfo.txt".format(mount_path, mount_path, membernum)
        res = execute_bash_cmd(s0m0_conn, cmd, {})

        cmd = "cat {}/s0m0/restoreInfo.txt|grep 'Replica Set:'".format(mount_path)
        res = execute_bash_cmd(s0m0_conn, cmd, {})

        repset_name = res.split(':')[1].strip()
        logger.debug("repset_name = {}".format(repset_name))

        if encryption_method is None:
            # cmd = "mongod --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} --fork".format(snmn_port, dbpath, logfile)
            restart_mongod_cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} --fork --replSet {}".format(
                sourceobj.mongo_install_path,
                snmn_port, dbpath, logfile, repset_name)
        else:
            # cmd = "mongod --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} {} --fork".format(snmn_port, dbpath, logfile, enc_params_list_string)
            restart_mongod_cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} {} --fork --replSet {}".format(
                sourceobj.mongo_install_path,
                snmn_port, dbpath, logfile, enc_params_list_string, repset_name)

        res = execute_bash_cmd(snmn_conn, restart_mongod_cmd, {})
        time.sleep(7)

        # Add Member to replicaset
        logger.info("Add replicaset Member s0m{} to replicaset {}".format(membernum, repset_name))
        cmd = '{} --port {} --eval \'rs.add("{}:{}")\''.format(sourceobj.mongo_shell_path, s0m0_port, snmn_host_name,
                                                               snmn_port)
        cmd_response = execute_bash_cmd(s0m0_conn, cmd, {})
        logger.info(
            "Add replicaset Member s0m{} to replicaset {} - done".format(membernum, repset_name))

        add_debug_space()


def adjust_config_shardinfo(sourceobj, rx_connection, shard_dbpath, cfg_port, hostname, shard_port,
                            shardserver_setting_list):
    cmd = "cat {}/restoreInfo.txt|grep 'Replica Set:'".format(shard_dbpath)
    res = execute_bash_cmd(rx_connection, cmd, {})
    shard_repset_name = res.split(':')[1]
    shard_repset_name = shard_repset_name.strip()
    logger.debug("shard_repset_name = {}".format(shard_repset_name))

    # shard_host_cfg = "{}/{}:{}".format(shard_repset_name, hostname, shard_port)
    # shard_host_cfg = shard_host_cfg.strip()
    # logger.debug("shard_host_cfg: {}".format(shard_host_cfg))
    logger.debug("shardserver_setting_list:{}".format(shardserver_setting_list))
    for shardserver_setting in shardserver_setting_list:
        if shard_repset_name in shardserver_setting.keys():
            shard_host_cfg = shardserver_setting[shard_repset_name]
    logger.debug("shard_host_cfg: {}".format(shard_host_cfg))

    cmd = "{} config --port {} --quiet --eval 'db.shards.updateOne({{ _id : \"{}\" }},{{ $set : {{ host : \"{}\", state : 1 }} }})'".format(
        sourceobj.mongo_shell_path,
        cfg_port, shard_repset_name, shard_host_cfg)
    res = execute_bash_cmd(rx_connection, cmd, {})


def setup_shard_member(sourceobj, rx_connection, mount_path, shardnum, membernum, snm0_port, shardcount,
                       shard_config_list,
                       encryption_method, enc_params_list_string, configsvrstring):
    dbpath = "{}/s{}m{}".format(mount_path, shardnum, membernum)
    cfgdir = "{}/cfg".format(mount_path)
    logdir = "{}/logs".format(mount_path)
    cfgfile = "{}/dlpx.s{}m{}.{}.conf".format(cfgdir, shardnum, membernum, snm0_port)
    logfile = "{}/dlpx.s{}m{}.{}.mongod.log".format(logdir, shardnum, membernum, snm0_port)

    cmd = "hostname"
    hostname = execute_bash_cmd(rx_connection, cmd, {})
    logger.debug("{},{},{},{},{}".format(dbpath, snm0_port, shardcount, cfgfile, hostname))

    cmd = "cat {}/s{}m{}/restoreInfo.txt|grep 'Replica Set:'".format(mount_path, shardnum, membernum)
    res = execute_bash_cmd(rx_connection, cmd, {})
    shard_repset_name = res.split(':')[1].strip()
    logger.debug("shard_repset_name = {}".format(shard_repset_name))

    if encryption_method is None:
        cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} --fork".format(sourceobj.mongo_install_path,
                                                                                      snm0_port, dbpath, logfile)
        restart_mongod_cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} --fork --replSet {} --shardsvr".format(
            sourceobj.mongo_install_path,
            snm0_port, dbpath, logfile, shard_repset_name)

    else:
        cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} {} --fork".format(sourceobj.mongo_install_path,
                                                                                         snm0_port, dbpath, logfile,
                                                                                         enc_params_list_string)
        restart_mongod_cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} {} --fork --replSet {} --shardsvr".format(
            sourceobj.mongo_install_path,
            snm0_port, dbpath, logfile, enc_params_list_string, shard_repset_name)

    res = execute_bash_cmd(rx_connection, cmd, {})
    time.sleep(7)

    cmd = "{} local --port {} --quiet --eval 'db.dropDatabase()'".format(sourceobj.mongo_shell_path, snm0_port)
    res = execute_bash_cmd(rx_connection, cmd, {})

    cmd = "{} admin --port {} --quiet --eval 'db.system.version.deleteOne( {{ _id: \"minOpTimeRecovery\" }} )'".format(
        sourceobj.mongo_shell_path,
        snm0_port)
    res = execute_bash_cmd(rx_connection, cmd, {})

    cmd = "{} admin --port {} --quiet --eval 'db.system.version.updateOne({{ \"_id\" : \"shardIdentity\" }},{{ $set :{{ \"configsvrConnectionString\" : \"{}\" }} }})'".format(
        sourceobj.mongo_shell_path,
        snm0_port, configsvrstring)
    res = execute_bash_cmd(rx_connection, cmd, {})

    cmd = "{} admin --port {} --quiet --eval 'db.system.version.find( {{ \"_id\" : \"shardIdentity\" }} ).pretty()'".format(
        sourceobj.mongo_shell_path,
        snm0_port)
    res = execute_bash_cmd(rx_connection, cmd, {})

    # cmd = "ps -ef|grep mongo|grep {}|grep {}|grep -v grep|awk '{ print \"kill \"$2}'|sh".format(dbpath, snm0_port)
    shutdown_server(rx_connection, sourceobj.mongo_shell_path, snm0_port)

    # Create YAML file
    cmd = "{} --outputConfig |grep -v outputConfig > {}".format(restart_mongod_cmd, cfgfile)
    res = execute_bash_cmd(rx_connection, cmd, {})

    # This may be bug so added to fix proactively
    fix_mongod_cmd = "sed -i 's/replSet: {}/replSetName: {}/g' {}".format(shard_repset_name, shard_repset_name, cfgfile)
    logger.debug("fix_mongod_cmd: {}".format(fix_mongod_cmd))
    res = execute_bash_cmd(rx_connection, fix_mongod_cmd, {})

    # start_mongod_cmd = "mongod -f {}".format(cfgfile)
    res = execute_bash_cmd(rx_connection, restart_mongod_cmd, {})
    time.sleep(7)


def setup_replicaset_member(sourceobj, rx_connection, mount_path, cfg_port, encryption_method, enc_params_list_string,
                            dsource_type):
    dbpath = "{}/s0m0".format(mount_path)
    cfgdir = "{}/cfg".format(mount_path)
    logdir = "{}/logs".format(mount_path)
    cfgfile = "{}/dlpx.s0m0.{}.conf".format(cfgdir, cfg_port)
    logfile = "{}/dlpx.s0m0.{}.mongod.log".format(logdir, cfg_port)

    cmd = "hostname"
    hostname = execute_bash_cmd(rx_connection, cmd, {})
    logger.debug("{},{},{},{}".format(dbpath, cfg_port, cfgfile, hostname))

    cmd = "cat {}/s0m0/restoreInfo.txt|grep 'Replica Set:'".format(mount_path)
    res = execute_bash_cmd(rx_connection, cmd, {})
    repset_name = res.split(':')[1].strip()
    logger.debug("repset_name = {}".format(repset_name))

    if encryption_method is None:
        cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} --fork".format(sourceobj.mongo_install_path,
                                                                                      cfg_port, dbpath, logfile)
        restart_mongod_cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} --fork --replSet {}".format(
            sourceobj.mongo_install_path,
            cfg_port, dbpath, logfile, repset_name)
        restart_mongod_cmd_stdalone = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} --fork ".format(
            sourceobj.mongo_install_path,
            cfg_port, dbpath, logfile)
    else:
        cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} {} --fork".format(sourceobj.mongo_install_path,
                                                                                         cfg_port, dbpath, logfile,
                                                                                         enc_params_list_string)
        restart_mongod_cmd = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} {} --fork --replSet {} ".format(
            sourceobj.mongo_install_path,
            cfg_port, dbpath, logfile, enc_params_list_string, repset_name)
        restart_mongod_cmd_stdalone = "{} --bind_ip 0.0.0.0 --port {} --dbpath {} --logpath {} {} --fork  ".format(
            sourceobj.mongo_install_path,
            cfg_port, dbpath, logfile, enc_params_list_string, repset_name)

    if dsource_type == "extendedcluster":
        res = execute_bash_cmd(rx_connection, restart_mongod_cmd_stdalone, {})
        time.sleep(5)

        cmd = "{} admin --port {} --quiet --eval 'db.getUsers()'".format(
            sourceobj.mongo_shell_path, cfg_port)
        res = execute_bash_cmd(rx_connection, cmd, {})

        cmd = "{} local --port {} --quiet --eval 'db.dropDatabase()'".format(
            sourceobj.mongo_shell_path, cfg_port)
        res = execute_bash_cmd(rx_connection, cmd, {})

        cmd = "{} admin --port {} --quiet --eval 'db.getUsers()'".format(
            sourceobj.mongo_shell_path, cfg_port)
        res = execute_bash_cmd(rx_connection, cmd, {})

        cmd = "{} --dbpath {} --port {} --shutdown".format(sourceobj.mongo_install_path, dbpath, cfg_port)
        res = execute_bash_cmd(rx_connection, cmd, {})
        time.sleep(3)

    else:

        res = execute_bash_cmd(rx_connection, cmd, {})
        time.sleep(7)

        cmd = "{} local --port {} --quiet --eval 'db.getSiblingDB(\"local\").replset.minvalid.drop()'".format(
            sourceobj.mongo_shell_path, cfg_port)
        res = execute_bash_cmd(rx_connection, cmd, {})

        cmd = "{} local --port {} --quiet --eval 'db.getSiblingDB(\"local\").replset.oplogTruncateAfterPoint.drop()'".format(
            sourceobj.mongo_shell_path, cfg_port)
        res = execute_bash_cmd(rx_connection, cmd, {})

        cmd = "{} local --port {} --quiet --eval 'db.getSiblingDB(\"local\").replset.election.drop()'".format(
            sourceobj.mongo_shell_path, cfg_port)
        res = execute_bash_cmd(rx_connection, cmd, {})

        cmd = "{} local --port {} --quiet --eval 'db.getSiblingDB(\"local\").system.replset.remove({{ }})'".format(
            sourceobj.mongo_shell_path, cfg_port)
        res = execute_bash_cmd(rx_connection, cmd, {})

        cmd = "{} local --port {} --quiet --eval 'db.getSiblingDB(\"local\").system.replset.insert({{\"_id\" : \"{}\", \"version\" : NumberInt(1), \"protocolVersion\" : NumberInt(1), \"members\" : [{{ \"_id\" : NumberInt(0), \"host\" : \"{}:{}\"}}], \"settings\" : {{ }} }})'".format(
            sourceobj.mongo_shell_path, cfg_port, repset_name, hostname, cfg_port)
        res = execute_bash_cmd(rx_connection, cmd, {})

        cmd = "{} local --port {} --quiet --eval 'db.getSiblingDB(\"local\").replset.minvalid.insert({{\"_id\" : ObjectId(), \"t\" : NumberLong(-1), \"ts\" : Timestamp(0,1) }})'".format(
            sourceobj.mongo_shell_path, cfg_port)
        res = execute_bash_cmd(rx_connection, cmd, {})

        try:
            cmd = "cat {}/s0m0/restoreInfo.txt|grep 'Last Oplog Applied:'".format(mount_path)
            res = execute_bash_cmd_nofail(rx_connection, cmd, {})
            extractTS = re.search(r'\(\d+,\s\d+\)', res)
            restoreTS = extractTS.group()
            truncateAfterPoint = "Timestamp{}".format(restoreTS)

            # AJAY This is imporatnt but temporary commented
            # cmd = "mongo local --port {} --quiet --eval 'db.getSiblingDB(\"local\").replset.oplogTruncateAfterPoint.insert({{\"_id\" : \"oplogTruncateAfterPoint\", \"oplogTruncateAfterPoint\" : {} }})'".format(cfg_port,truncateAfterPoint)
            # res = execute_bash_cmd(rx_connection, cmd, {})
        except:
            # This is valid in case of dsource type as "offlinemongodump" or "onlinemongodump". Gracefully proceed
            pass

        # cmd = "ps -ef|grep mongo|grep {}|grep {}|grep -v grep|awk '{ print \"kill \"$2}'|sh".format(dbpath, cfg_port)
        # cmd = "mongo admin --port {} --quiet --eval 'db.shutdownServer()'".format(cfg_port)
        cmd = "{} --dbpath {} --port {} --shutdown".format(sourceobj.mongo_install_path, dbpath, cfg_port)
        res = execute_bash_cmd(rx_connection, cmd, {})
        time.sleep(3)

    res = execute_bash_cmd(rx_connection, restart_mongod_cmd, {})
    time.sleep(5)

    logger.info("setup_replicaset_member function is complete")
    return restart_mongod_cmd


def add_net(mongo_cmd, bind_ip, mongod_port, enable_ssl_tls, ssl_tls_params):
    mongo_cmd = "{} --bind_ip {}".format(mongo_cmd, bind_ip)
    mongo_cmd = "{} --port {}".format(mongo_cmd, mongod_port)

    if enable_ssl_tls:
        ssl_tls_params_list_string = ""
        for ssl_tls_params_rec in ssl_tls_params:
            if ssl_tls_params_rec['value'].upper() == "TRUE":
                ssl_tls_params_list_string = ssl_tls_params_list_string + " --{}".format(
                    ssl_tls_params_rec['property_name'])
            else:
                ssl_tls_params_list_string = ssl_tls_params_list_string + " --{} {}".format(
                    ssl_tls_params_rec['property_name'], ssl_tls_params_rec['value'])
        mongo_cmd = "{} {}".format(mongo_cmd, ssl_tls_params_list_string)
    return mongo_cmd


def add_keyfile_auth(mongo_cmd, enable_user_auth, keyfile_path):
    # user_auth_mode = None,SCRAM,x509,ldap
    # if user_auth_mode == "None":
    #     # mongo_cmd = "{} --noauth".format(mongo_cmd)
    #     mongo_cmd = mongo_cmd
    # elif user_auth_mode == "SCRAM" or user_auth_mode == "x509" or user_auth_mode == "ldap":
    if not mongo_cmd.split(" ")[0].endswith("mongos"):
        if enable_user_auth:
            mongo_cmd = "{} --auth".format(mongo_cmd)

    if keyfile_path is not None and keyfile_path != "":
        mongo_cmd = "{} --keyFile {}".format(mongo_cmd, keyfile_path)
    else:
        logger.info("Keyfile is empty")

    return mongo_cmd


def add_cluster_auth(mongo_cmd, cluster_auth_mode, keyfile_path):
    # cluster_auth_mode = None,keyFile,x509,sendKeyFile,sendX509
    if cluster_auth_mode == "None":
        pass
    else:
        mongo_cmd = "{} --clusterAuthMode {}".format(mongo_cmd, cluster_auth_mode)
    return mongo_cmd


def add_ldap(mongo_cmd, enable_ldap, ldap_params):
    # simple / sasl
    if enable_ldap:
        ldap_params_list_string = ""
        for ldap_params_rec in ldap_params:
            if ldap_params_rec['value'].upper() == "TRUE":
                ldap_params_list_string = ldap_params_list_string + " --{}".format(ldap_params_rec['property_name'])
            else:
                if ldap_params_rec['property_name'] == "ldapAuthzQueryTemplate":
                    # Find if the start of command mongo_cmd is mongod or mongos
                    utilitynamefullpath = mongo_cmd.split(" ")[0]
                    utilityname = utilitynamefullpath.split("/")[-1]
                    if utilityname == "mongos":
                        print("Skip ldapAuthzQueryTemplate")
                    else:
                        ldap_params_list_string = ldap_params_list_string + " --{} {}".format(ldap_params_rec['property_name'], ldap_params_rec['value'])
                else:
                    ldap_params_list_string = ldap_params_list_string + " --{} {}".format(ldap_params_rec['property_name'],
                                                                                      ldap_params_rec['value'])
        mongo_cmd = "{} {}".format(mongo_cmd, ldap_params_list_string)
    return mongo_cmd

def add_set_parameters(mongo_cmd, enable_setparams, setparam_params):
    if enable_setparams:
        set_params_list_string = ""
        for set_params_rec in setparam_params:
            if set_params_rec['value'].upper() == "TRUE":
                set_params_list_string = set_params_list_string + " --{}".format(set_params_rec['property_name'])
            else:
                set_params_list_string = set_params_list_string + " --setParameter {}={}".format(set_params_rec['property_name'],
                                                                                    set_params_rec['value'])
        mongo_cmd = "{} {}".format(mongo_cmd, set_params_list_string)
    return mongo_cmd


def add_encryption_kmip(mongo_cmd, kmip_params):
    if kmip_params:
        mongo_cmd = "{} --enableEncryption".format(mongo_cmd)
        kmip_params_list_string = ""
        for kmip_params_rec in kmip_params:
            if kmip_params_rec['value'].upper() == "TRUE":
                kmip_params_list_string = kmip_params_list_string + " --{}".format(kmip_params_rec['property_name'])
            else:
                kmip_params_list_string = kmip_params_list_string + " --{} {}".format(kmip_params_rec['property_name'],
                                                                                      kmip_params_rec['value'])
        mongo_cmd = "{} {}".format(mongo_cmd, kmip_params_list_string)
    return mongo_cmd


def add_encryption_keyfile(mongo_cmd, enc_key_file_name):
    if enc_key_file_name:
        mongo_cmd = "{} --enableEncryption".format(mongo_cmd)
        mongo_cmd = "{} --encryptionKeyFile {}".format(mongo_cmd, enc_key_file_name)
    return mongo_cmd


def add_auditlog(mongo_cmd, enable_auditlog, auditlog_params):
    if enable_auditlog:
        auditlog_params_list_string = ""
        for auditlog_params_rec in auditlog_params:
            if auditlog_params_rec['value'].upper() == "TRUE":
                auditlog_params_list_string = auditlog_params_list_string + " --{}".format(
                    auditlog_params_rec['property_name'])
            else:
                auditlog_params_list_string = auditlog_params_list_string + " --{} {}".format(
                    auditlog_params_rec['property_name'], auditlog_params_rec['value'])
        mongo_cmd = "{} {}".format(mongo_cmd, auditlog_params_list_string)
    return mongo_cmd


def gen_config_files(dataset_type, sourceobj, shard_config_list, snapshot=None):
    if dataset_type == "Virtual":
        connection = sourceobj.connection
        cmd = "cat {}/.delphix/.tgt_config.txt|grep DSOURCE_TYPE".format(sourceobj.parameters.mount_path)
        res = execute_bash_cmd(connection, cmd, {})
        d_source_type = res.split(':')[1].strip()
    elif dataset_type == "Staging":
        connection = sourceobj.staged_connection
        cfgfile = "{}/.delphix/.stg_dsourcecfg.txt".format(sourceobj.parameters.mount_path)
        d_source_type = sourceobj.parameters.d_source_type

    add_debug_space()
    # logger.info("Generating Config Files")
    # logger.info(snapshot)
    if dataset_type == "Virtual":
        gen_mongo_conf_files(dataset_type, sourceobj, shard_config_list, snapshot)
    else:
        gen_mongo_conf_files(dataset_type, sourceobj, shard_config_list, None)
    logger.info("Completed generating Config Files")
    add_debug_space()

    if d_source_type == "stagingpush" and dataset_type == "Staging":
        logger.info("++++++++++ Not Applicable for Staging-Stagingpush ++++++++++")
    else:
        logger.info("++++++++++ Stop Mongo ++++++++++")
        stop_sharded_mongo(dataset_type, sourceobj)
        logger.info("Sleeping for 60 seconds.......")
        time.sleep(60)
        add_debug_space()
        logger.info("++++++++++ Start Mongo +++++++++")
        start_sharded_mongo(dataset_type, sourceobj)


def create_node_array(dataset_type, sourceobj):
    if dataset_type == "Virtual":
        connection = sourceobj.connection
    elif dataset_type == "Staging":
        connection = sourceobj.staged_connection

    nodes = []
    nodes.append("{}:{}".format(connection.environment.reference,
                                connection.user.reference))
    if dataset_type == "Virtual":
        if sourceobj.parameters.make_shards_replicaset:
            for node in sourceobj.parameters.additional_nodes:
                nodes.append("{}:{}".format(
                    node['environment'], node['environment_user']))

    totalnodes = len(nodes)
    logger.debug("Total Nodes : {}".format(totalnodes))
    logger.info(" ")
    return nodes


def setup_dataset(sourceobj, dataset_type, snapshot, dsource_type):
    if dataset_type == 'Staging':
        rx_connection = sourceobj.staged_connection
        dataset_cfgfile = ".stg_config.txt"
    elif dataset_type == 'Virtual':
        rx_connection = sourceobj.connection
        dataset_cfgfile = ".tgt_config.txt"

    if dataset_type == 'Staging':
        # Validate backup config file exists
        linked.validate_backup_configfile(sourceobj)

        # Create delphix internal directory
        cmd = "mkdir -p {}/.delphix".format(sourceobj.parameters.mount_path)
        res = execute_bash_cmd(sourceobj.staged_connection, cmd, {})

        # Write backup information
        linked.write_first_backup_timestamp(sourceobj)

    # Generate and write config file
    nodes = create_node_array(dataset_type, sourceobj)
    add_debug_space()

    # Define variables
    mount_path = sourceobj.parameters.mount_path
    start_portpool = sourceobj.parameters.start_portpool
    mongos_port = sourceobj.parameters.mongos_port
    #replicaset = sourceobj.parameters.make_shards_replicaset
    if dataset_type == "Virtual":
        replicaset = sourceobj.parameters.make_shards_replicaset
    else:
        replicaset = False

    if dsource_type == "shardedsource":
        cmax = 1
        if dataset_type == 'Staging':
            smax = len(sourceobj.parameters.shard_backupfiles)
        elif dataset_type == 'Virtual':
            smax = snapshot.shard_count
        mmax = 3

    if dataset_type == 'Staging':
        config_backupfile = sourceobj.parameters.config_backupfile
        rx_connection = sourceobj.staged_connection
        source_encrypted = sourceobj.parameters.source_encrypted
        encryption_method = sourceobj.parameters.encryption_method
    elif dataset_type == 'Virtual':
        rx_connection = sourceobj.connection
        source_encrypted = snapshot.source_encrypted
        encryption_method = snapshot.encryption_method

    logger.info("nodes = {}".format(nodes))
    logger.info("start_portpool = {}".format(start_portpool))
    logger.info("mount_path     = {}".format(mount_path))
    logger.info("replicaset     = {}".format(replicaset))

    if dsource_type == "shardedsource":
        logger.info("mongos_port    = {}".format(mongos_port))
        logger.info("cmax           = {}".format(cmax))
        logger.info("smax           = {}".format(smax))
        logger.info("mmax           = {}".format(mmax))

    # Create directory structure
    add_debug_heading_block("Create directory structure")
    if dsource_type == "shardedsource":
        cr_dir_structure(cmax, smax, mount_path, replicaset, rx_connection)
    elif dsource_type == "nonshardedsource" or dsource_type == "offlinemongodump" or dsource_type == "onlinemongodump" or dsource_type == "extendedcluster" or dsource_type == "stagingpush":
        cr_dir_structure_replicaset(mount_path, replicaset, rx_connection)

    if dataset_type == 'Virtual':
        # Cleanup log and cfg location
        cmd = "rm -f {}/cfg/*.conf".format(mount_path)
        res = execute_bash_cmd(sourceobj.connection, cmd, {})

        cmd = "rm -Rf {}/logs/*.*".format(mount_path)
        res = execute_bash_cmd(sourceobj.connection, cmd, {})

    if dsource_type == "shardedsource":
        # Generate shard config mappings
        add_debug_heading_block("Generate shard config mappings")
        shard_config_list = []
        shard_config_list = gen_shard_config_list(
            nodes, start_portpool, cmax, smax, mmax, mount_path, mongos_port, replicaset)
        for shard_config in shard_config_list:
            logger.info("shard config :{}".format(shard_config))
    elif dsource_type in [ "nonshardedsource", "offlinemongodump", "onlinemongodump", "extendedcluster", "stagingpush", "seed" ]:
        # Generate replicaset mappings
        add_debug_heading_block("Generate replicaset mappings")
        replicaset_config_list = []
        replicaset_config_list = gen_replicaset_config_list(
            nodes, start_portpool, mount_path, replicaset)
        for replicaset_config in replicaset_config_list:
            logger.info("replicaset_config :{}".format(replicaset_config))

    add_debug_space()

    if dsource_type == "shardedsource":
        if dataset_type == 'Staging':
            cmd = "echo \"{}\" > {}/.delphix/.stg_dsourcecfg.txt".format(shard_config_list, mount_path)
        elif dataset_type == 'Virtual':
            cmd = "echo \"{}\" > {}/.delphix/.tgt_vdbcfg.txt".format(shard_config_list, mount_path)
        res = execute_bash_cmd(rx_connection, cmd, {})
    elif dsource_type in [ "nonshardedsource", "offlinemongodump", "onlinemongodump", "extendedcluster", "stagingpush", "seed" ]:
        if dataset_type == 'Staging':
            cmd = "echo \"{}\" > {}/.delphix/.stg_dsourcecfg.txt".format(replicaset_config_list, mount_path)
        elif dataset_type == 'Virtual':
            cmd = "echo \"{}\" > {}/.delphix/.tgt_vdbcfg.txt".format(replicaset_config_list, mount_path)
        res = execute_bash_cmd(rx_connection, cmd, {})

    if dataset_type == 'Staging':
        if dsource_type == "shardedsource":
            # restore backups
            extract_shard_config_backup(config_backupfile, mount_path, 0, rx_connection)
            shardnum = 0
            for shardfile in sourceobj.parameters.shard_backupfiles:
                extract_shard_backup(shardfile['backupfile'], mount_path, shardnum, rx_connection)
                shardnum = shardnum + 1
            shardnum = shardnum - 1
            logger.debug("Extracted Configserver / Shard backups successfully")
        elif dsource_type == "nonshardedsource":
            # restore backups
            extract_replicaset_backup(config_backupfile, mount_path, rx_connection)
            logger.debug("Extracted Replicaset backup successfully")

        add_debug_space()

    if dsource_type == "shardedsource":
        # Generate configsvrstring
        add_debug_heading_block("Generate configsvrstring")
        c0m0_port = get_shard_port(shard_config_list, 'c0m0')
        c0m0_host = get_shard_host(shard_config_list, 'c0m0')
        c0m0_conn = get_node_conn(sourceobj, c0m0_host, dataset_type)
        c0m0_host_name = execute_bash_cmd(c0m0_conn, "hostname", {})

        cmd = "cat {}/{}/restoreInfo.txt|grep 'Replica Set:'".format(
            mount_path, "c0m0")
        c0m0_replica_name = execute_bash_cmd(c0m0_conn, cmd, {})
        c0m0_replica_name = "{}".format(c0m0_replica_name.split(':')[1].strip())
        logger.debug("c0m0_replica_name={}".format(c0m0_replica_name))
        configsvrstring = "{}/{}:{}".format(c0m0_replica_name,
                                            c0m0_host_name, c0m0_port)

        #if sourceobj.parameters.make_shards_replicaset:
        if replicaset:
            c0m1_port = get_shard_port(shard_config_list, 'c0m1')
            c0m1_host = get_shard_host(shard_config_list, 'c0m1')
            c0m1_conn = get_node_conn(sourceobj, c0m1_host, dataset_type)
            c0m1_host_name = execute_bash_cmd(c0m1_conn, "hostname", {})
            configsvrstring = configsvrstring + "," + \
                              "{}:{}".format(c0m1_host_name, c0m1_port)

            c0m2_port = get_shard_port(shard_config_list, 'c0m2')
            c0m2_host = get_shard_host(shard_config_list, 'c0m2')
            c0m2_conn = get_node_conn(sourceobj, c0m2_host, dataset_type)
            c0m2_host_name = execute_bash_cmd(c0m2_conn, "hostname", {})
            configsvrstring = configsvrstring + "," + \
                              "{}:{}".format(c0m2_host_name, c0m2_port)

        logger.debug("configsvrstring hostname={}".format(configsvrstring))
        add_debug_space()

        # Generate shardservercfg/shardserver_setting_list
        shardserver_setting_list = []
        shardserver_setting_list = gen_shardserver_setting_list(
            shard_config_list, sourceobj, smax, mount_path, dataset_type)
        logger.debug("shardserver_setting_list:")
        for shardserver_setting in shardserver_setting_list:
            logger.debug("shardserver_setting:  {}".format(shardserver_setting))
        add_debug_space()

    if dataset_type == 'Staging':
        if dsource_type == "shardedsource":
            cmd = "echo \"SHARD_COUNT:{}\" > {}/.delphix/{}".format(smax, mount_path, dataset_cfgfile)
            res = execute_bash_cmd(rx_connection, cmd, {})
        elif dsource_type == "nonshardedsource":
            cmd = "cat /dev/null > {}/.delphix/{}".format(mount_path, dataset_cfgfile)
            res = execute_bash_cmd(rx_connection, cmd, {})

        cmd = "echo \"DSOURCE_TYPE:{}\" >> {}/.delphix/{}".format(sourceobj.parameters.d_source_type, mount_path,
                                                                  dataset_cfgfile)
        res = execute_bash_cmd(rx_connection, cmd, {})

        cmd = "echo \"MONGO_DB_USER:{}\" >> {}/.delphix/{}".format(sourceobj.parameters.mongo_db_user, mount_path,
                                                                   dataset_cfgfile)
        res = execute_bash_cmd(rx_connection, cmd, {})

    elif dataset_type == 'Virtual':
        if dsource_type == "shardedsource":
            cmd = "echo \"SHARD_COUNT:{}\" > {}/.delphix/{}".format(smax, mount_path, dataset_cfgfile)
            res = execute_bash_cmd(rx_connection, cmd, {})
        elif dsource_type in [ "nonshardedsource", "offlinemongodump", "onlinemongodump", "extendedcluster", "stagingpush", "seed" ]:
            cmd = "cat /dev/null > {}/.delphix/{}".format(mount_path, dataset_cfgfile)
            res = execute_bash_cmd(rx_connection, cmd, {})
        cmd = "echo \"DSOURCE_TYPE:{}\" >> {}/.delphix/{}".format(snapshot.d_source_type, mount_path, dataset_cfgfile)
        res = execute_bash_cmd(rx_connection, cmd, {})
        cmd = "echo \"MONGO_DB_USER:{}\" >> {}/.delphix/{}".format(snapshot.mongo_db_user, mount_path,
                                                                      dataset_cfgfile)
        res = execute_bash_cmd(rx_connection, cmd, {})

    if source_encrypted:
        cmd = "echo \"SOURCE_ENCRYPTED:{}\" >> {}/.delphix/{}".format("True", mount_path, dataset_cfgfile)
        res = execute_bash_cmd(rx_connection, cmd, {})

        cmd = "echo \"ENCRYPTION_METHOD:{}\" >> {}/.delphix/{}".format(encryption_method, mount_path, dataset_cfgfile)
        res = execute_bash_cmd(rx_connection, cmd, {})
    else:
        cmd = "echo \"SOURCE_ENCRYPTED:{}\" >> {}/.delphix/{}".format("False", mount_path, dataset_cfgfile)
        res = execute_bash_cmd(rx_connection, cmd, {})
    add_debug_space()

    if source_encrypted:
        if encryption_method == "KMIP":

            enc_params_list_string = "--enableEncryption"
            for kmip_params in sourceobj.parameters.kmip_params:
                enc_params_list_string = enc_params_list_string + " --{} {}".format(kmip_params['property_name'],
                                                                                    kmip_params['value'])

            base_enc_params_list_string = enc_params_list_string

            if dsource_type == "shardedsource":
                kmip_key_id = get_kmip_key_id("{}/c{}m{}".format(mount_path, 0, 0), rx_connection)
                enc_params_list_string = enc_params_list_string + " --kmipKeyIdentifier {}".format(kmip_key_id)

            logger.debug("enc_params_list_string = {}".format(enc_params_list_string))
        else:

            if dataset_type == 'Staging':
                enc_params_list_string = " --enableEncryption --encryptionKeyFile {}".format(
                    sourceobj.parameters.encryption_keyfile)
            elif dataset_type == 'Virtual':
                enc_params_list_string = " --enableEncryption --encryptionKeyFile {}/.delphix/.dlpx_enckeyfile".format(
                    mount_path)
            base_enc_params_list_string = enc_params_list_string

            # Save encryption file. Assuming same file used for all config servers and all shards
            cmd = "cp -p {} {}/.delphix/.dlpx_enckeyfile".format(sourceobj.parameters.encryption_keyfile,
                                                                 mount_path)
            res = execute_bash_cmd(rx_connection, cmd, {})
    else:
        enc_params_list_string = None
        base_enc_params_list_string = enc_params_list_string
        encryption_method = None

    if dsource_type == "shardedsource":
        # setup configserver
        confignum = 0
        membernum = 0

        if source_encrypted:
            add_debug_heading_block("Encrypted - setup_config_member")
            res = setup_config_member(sourceobj, rx_connection, mount_path, confignum, membernum, start_portpool, smax,
                                      shard_config_list, encryption_method, enc_params_list_string,
                                      shardserver_setting_list)

        else:
            add_debug_heading_block("Unencrypted - setup_config_member")
            res = setup_config_member(sourceobj, rx_connection, mount_path, confignum, membernum, start_portpool, smax,
                                      shard_config_list, None, None, shardserver_setting_list)

    elif dsource_type in [ "nonshardedsource", "offlinemongodump", "onlinemongodump", "extendedcluster", "stagingpush", "seed" ]:

        # setup Replicaset
        if source_encrypted:
            add_debug_heading_block("Encrypted - setup_replicaset_member")
            res = setup_replicaset_member(sourceobj, rx_connection, mount_path, start_portpool, encryption_method,
                                          enc_params_list_string, dsource_type)

        else:
            add_debug_heading_block("Unencrypted - setup_replicaset_member")
            res = setup_replicaset_member(sourceobj, rx_connection, mount_path, start_portpool, None, None,
                                          dsource_type)

    rs_initiate(rx_connection, sourceobj.mongo_shell_path, start_portpool)

    cmd = "{} --port {} --quiet --eval 'rs.conf()'".format(sourceobj.mongo_shell_path, start_portpool)
    res = execute_bash_cmd(rx_connection, cmd, {})

    cmd = "{} --port {} --quiet --eval 'rs.status()'".format(sourceobj.mongo_shell_path, start_portpool)
    res = execute_bash_cmd(rx_connection, cmd, {})
    # OUTPUT=$(mongo --port $DBPORT --eval "rs.status()"|egrep "name|stateStr")
    add_debug_space()

    if dsource_type == "shardedsource":

        if replicaset:
            add_debug_heading_block("Replicaset - setup_config_replset_members")
            setup_config_replset_members(shard_config_list, sourceobj, mount_path, encryption_method,
                                         enc_params_list_string, dataset_type)

            add_debug_space()

    elif dsource_type in [ "nonshardedsource", "offlinemongodump", "onlinemongodump", "extendedcluster", "stagingpush", "seed" ]:

        if replicaset:
            add_debug_heading_block("Replicaset - setup_replset_members")
            logger.info("{},{},{},{},{},{} ".format(dataset_type, start_portpool, replicaset_config_list, mount_path,
                                                    encryption_method, enc_params_list_string))
            add_replset_members(sourceobj, dataset_type, start_portpool, replicaset_config_list, mount_path,
                                encryption_method, enc_params_list_string)
            add_debug_space()

    if dsource_type == "shardedsource":
        # setup shardserver
        cmd = "hostname"
        hostname = execute_bash_cmd(rx_connection, cmd, {})

        cmd = "cat {}/c0m0/restoreInfo.txt|grep 'Replica Set:'".format(mount_path)
        res = execute_bash_cmd(rx_connection, cmd, {})
        config_repset_name = res.split(':')[1].strip()
        logger.debug("config_repset_name = {}".format(config_repset_name))
        configsvrstring = "{}/{}:{}".format(config_repset_name, hostname, start_portpool)

        if source_encrypted:
            for i in range(smax):
                shardnum = i
                membernum = 0
                shardmember = "s{}m0".format(i)
                snm0_port = get_shard_port(shard_config_list, shardmember)
                logger.debug("{},{}".format(shardmember, snm0_port))

                if encryption_method == "KMIP":
                    kmip_key_id = get_kmip_key_id("{}/s{}m{}".format(mount_path, i, 0), rx_connection)
                    enc_params_list_string = base_enc_params_list_string
                    enc_params_list_string = enc_params_list_string + " --kmipKeyIdentifier {}".format(kmip_key_id)

                setup_shard_member(sourceobj, rx_connection, mount_path, shardnum, membernum, snm0_port, smax,
                                   shard_config_list, encryption_method, enc_params_list_string, configsvrstring)

                rs_initiate(rx_connection, sourceobj.mongo_shell_path, snm0_port)

                cmd = "{} --port {} --quiet --eval 'rs.status()'".format(sourceobj.mongo_shell_path, snm0_port)
                res = execute_bash_cmd(rx_connection, cmd, {})
        else:
            base_enc_params_list_string = None
            for i in range(smax):
                shardnum = i
                membernum = 0
                shardmember = "s{}m0".format(i)
                snm0_port = get_shard_port(shard_config_list, shardmember)
                logger.debug("{},{}".format(shardmember, snm0_port))
                setup_shard_member(sourceobj, rx_connection, mount_path, shardnum, membernum, snm0_port, smax,
                                   shard_config_list, None, None, configsvrstring)

                rs_initiate(rx_connection, sourceobj.mongo_shell_path, snm0_port)

                cmd = "{} --port {} --quiet --eval 'rs.status()'".format(sourceobj.mongo_shell_path, snm0_port)
                res = execute_bash_cmd(rx_connection, cmd, {})

                add_debug_space()

        if replicaset:
            add_debug_heading_block("Replicaset - setup_shard_replset_members")
            logger.debug("setup_shard_replset_members() - Start")
            setup_shard_replset_members(shard_config_list, sourceobj, mount_path, encryption_method,
                                        base_enc_params_list_string, smax, dataset_type)
            logger.debug("setup_shard_replset_members() - End")
            add_debug_space()

        # setup mongos
        add_debug_heading_block("setup mongos")
        setup_mongos(sourceobj, rx_connection, mount_path, membernum, mongos_port, configsvrstring, shard_config_list)

    if dsource_type == "shardedsource":
        if dataset_type == 'Staging':
            # Create mongo admin user
            create_mongoadmin_user(sourceobj, rx_connection, smax, shard_config_list)
        elif dataset_type == 'Virtual':
            # Update mongo admin password
            update_mongoadmin_pwd(sourceobj, rx_connection, smax, shard_config_list, snapshot.mongo_db_user,
                                  sourceobj.parameters.mongo_db_password, mongos_port)

        # Generate Config files
        add_debug_heading_block("Generate Config files")
        gen_config_files(dataset_type, sourceobj, shard_config_list, snapshot)

    elif dsource_type in [ "nonshardedsource", "offlinemongodump", "onlinemongodump", "extendedcluster", "stagingpush", "seed" ]:
        if dataset_type == 'Staging':
            if dsource_type != "extendedcluster":
                # Create mongo admin user
                create_mongoadmin_user(sourceobj, rx_connection, 0, replicaset_config_list)
        elif dataset_type == 'Virtual':
            # Update mongo admin password
            update_mongoadmin_pwd(sourceobj, rx_connection, 0, replicaset_config_list, snapshot.mongo_db_user, sourceobj.parameters.mongo_db_password,
                                  mongos_port)

        # Generate Config files
        add_debug_heading_block("Generate Config files")
        gen_config_files(dataset_type, sourceobj, replicaset_config_list, snapshot)


def setup_sharded_mongo_dataset(sourceobj, dataset_type, snapshot):
    if dataset_type == 'Staging':
        rx_connection = sourceobj.staged_connection
        dataset_cfgfile = ".stg_config.txt"
    elif dataset_type == 'Virtual':
        rx_connection = sourceobj.connection
        dataset_cfgfile = ".tgt_config.txt"

    if dataset_type == 'Staging':
        # Validate backup config file exists
        linked.validate_backup_configfile(sourceobj)

        # Create delphix internal directory
        cmd = "mkdir -p {}/.delphix".format(sourceobj.parameters.mount_path)
        res = execute_bash_cmd(sourceobj.staged_connection, cmd, {})

        # Write backup information
        linked.write_first_backup_timestamp(sourceobj)

    # Generate and write config file
    nodes = create_node_array(dataset_type, sourceobj)
    add_debug_space()

    # Define variables
    mount_path = sourceobj.parameters.mount_path
    start_portpool = sourceobj.parameters.start_portpool
    mongos_port = sourceobj.parameters.mongos_port
    #replicaset = sourceobj.parameters.make_shards_replicaset
    if dataset_type == "Virtual":
        replicaset = sourceobj.parameters.make_shards_replicaset
    else:
        replicaset = False

    cmax = 1
    if dataset_type == 'Staging':
        smax = len(sourceobj.parameters.shard_backupfiles)
    elif dataset_type == 'Virtual':
        smax = snapshot.shard_count
    mmax = 3

    if dataset_type == 'Staging':
        config_backupfile = sourceobj.parameters.config_backupfile
        rx_connection = sourceobj.staged_connection
        source_encrypted = sourceobj.parameters.source_encrypted
        encryption_method = sourceobj.parameters.encryption_method
    elif dataset_type == 'Virtual':
        rx_connection = sourceobj.connection
        source_encrypted = snapshot.source_encrypted
        encryption_method = snapshot.encryption_method

    logger.info("nodes = {}".format(nodes))
    logger.info("mongos_port    = {}".format(mongos_port))
    logger.info("start_portpool = {}".format(start_portpool))
    logger.info("cmax           = {}".format(cmax))
    logger.info("smax           = {}".format(smax))
    logger.info("mmax           = {}".format(mmax))
    logger.info("mount_path     = {}".format(mount_path))
    logger.info("replicaset     = {}".format(replicaset))

    # Create directory structure
    add_debug_heading_block("Create directory structure")
    cr_dir_structure(cmax, smax, mount_path, replicaset, rx_connection)

    if dataset_type == 'Virtual':
        # Cleanup log and cfg location
        cmd = "rm -f {}/cfg/*.conf".format(mount_path)
        res = execute_bash_cmd(sourceobj.connection, cmd, {})

        cmd = "rm -Rf {}/logs/*.*".format(mount_path)
        res = execute_bash_cmd(sourceobj.connection, cmd, {})

    # Generate shard config mappings
    add_debug_heading_block("Generate shard config mappings")
    shard_config_list = []
    shard_config_list = gen_shard_config_list(
        nodes, start_portpool, cmax, smax, mmax, mount_path, mongos_port, replicaset)
    for shard_config in shard_config_list:
        logger.info("shard config :{}".format(shard_config))
    add_debug_space()

    if dataset_type == 'Staging':
        cmd = "echo \"{}\" > {}/.delphix/.stg_dsourcecfg.txt".format(shard_config_list, mount_path)
    elif dataset_type == 'Virtual':
        cmd = "echo \"{}\" > {}/.delphix/.tgt_vdbcfg.txt".format(shard_config_list, mount_path)
    res = execute_bash_cmd(rx_connection, cmd, {})

    if dataset_type == 'Staging':
        # restore backups
        extract_shard_config_backup(config_backupfile, mount_path, 0, rx_connection)
        shardnum = 0
        for shardfile in sourceobj.parameters.shard_backupfiles:
            extract_shard_backup(shardfile['backupfile'], mount_path, shardnum, rx_connection)
            shardnum = shardnum + 1
        shardnum = shardnum - 1
        logger.debug("Extracted Configserver / Shard backups successfully")

    # Generate configsvrstring
    add_debug_heading_block("Generate configsvrstring")
    c0m0_port = get_shard_port(shard_config_list, 'c0m0')
    c0m0_host = get_shard_host(shard_config_list, 'c0m0')
    c0m0_conn = get_node_conn(sourceobj, c0m0_host, dataset_type)
    c0m0_host_name = execute_bash_cmd(c0m0_conn, "hostname", {})

    cmd = "cat {}/{}/restoreInfo.txt|grep 'Replica Set:'".format(
        mount_path, "c0m0")
    c0m0_replica_name = execute_bash_cmd(c0m0_conn, cmd, {})
    c0m0_replica_name = "{}".format(c0m0_replica_name.split(':')[1].strip())
    logger.debug("c0m0_replica_name={}".format(c0m0_replica_name))
    configsvrstring = "{}/{}:{}".format(c0m0_replica_name,
                                        c0m0_host_name, c0m0_port)

    #if sourceobj.parameters.make_shards_replicaset:
    if replicaset:
        c0m1_port = get_shard_port(shard_config_list, 'c0m1')
        c0m1_host = get_shard_host(shard_config_list, 'c0m1')
        c0m1_conn = get_node_conn(sourceobj, c0m1_host, dataset_type)
        c0m1_host_name = execute_bash_cmd(c0m1_conn, "hostname", {})
        configsvrstring = configsvrstring + "," + \
                          "{}:{}".format(c0m1_host_name, c0m1_port)

        c0m2_port = get_shard_port(shard_config_list, 'c0m2')
        c0m2_host = get_shard_host(shard_config_list, 'c0m2')
        c0m2_conn = get_node_conn(sourceobj, c0m2_host, dataset_type)
        c0m2_host_name = execute_bash_cmd(c0m2_conn, "hostname", {})
        configsvrstring = configsvrstring + "," + \
                          "{}:{}".format(c0m2_host_name, c0m2_port)

    logger.debug("configsvrstring hostname={}".format(configsvrstring))
    add_debug_space()

    # Generate shardservercfg/shardserver_setting_list
    shardserver_setting_list = []
    shardserver_setting_list = gen_shardserver_setting_list(
        shard_config_list, sourceobj, smax, mount_path, dataset_type)
    logger.debug("shardserver_setting_list:")
    for shardserver_setting in shardserver_setting_list:
        logger.debug("shardserver_setting:  {}".format(shardserver_setting))
    add_debug_space()

    cmd = "echo \"SHARD_COUNT:{}\" > {}/.delphix/{}".format(smax, mount_path, dataset_cfgfile)
    res = execute_bash_cmd(rx_connection, cmd, {})

    if dataset_type == 'Staging':
        cmd = "echo \"DSOURCE_TYPE:{}\" >> {}/.delphix/{}".format(sourceobj.parameters.d_source_type, mount_path,
                                                                  dataset_cfgfile)
        res = execute_bash_cmd(rx_connection, cmd, {})

        cmd = "echo \"MONGO_DB_USER:{}\" >> {}/.delphix/{}".format(sourceobj.parameters.mongo_db_user, mount_path,
                                                                   dataset_cfgfile)
        res = execute_bash_cmd(rx_connection, cmd, {})

    elif dataset_type == 'Virtual':
        cmd = "echo \"DSOURCE_TYPE:{}\" >> {}/.delphix/{}".format(snapshot.d_source_type, mount_path, dataset_cfgfile)
        res = execute_bash_cmd(rx_connection, cmd, {})



    if source_encrypted:
        cmd = "echo \"SOURCE_ENCRYPTED:{}\" >> {}/.delphix/{}".format("True", mount_path, dataset_cfgfile)
        res = execute_bash_cmd(rx_connection, cmd, {})

        cmd = "echo \"ENCRYPTION_METHOD:{}\" >> {}/.delphix/{}".format(encryption_method, mount_path, dataset_cfgfile)
        res = execute_bash_cmd(rx_connection, cmd, {})
    else:
        cmd = "echo \"SOURCE_ENCRYPTED:{}\" >> {}/.delphix/{}".format("False", mount_path, dataset_cfgfile)
        res = execute_bash_cmd(rx_connection, cmd, {})
    add_debug_space()

    if source_encrypted:
        if encryption_method == "KMIP":

            enc_params_list_string = "--enableEncryption"
            for kmip_params in sourceobj.parameters.kmip_params:
                enc_params_list_string = enc_params_list_string + " --{} {}".format(kmip_params['property_name'],
                                                                                    kmip_params['value'])

            base_enc_params_list_string = enc_params_list_string

            kmip_key_id = get_kmip_key_id("{}/c{}m{}".format(mount_path, 0, 0), rx_connection)
            enc_params_list_string = enc_params_list_string + " --kmipKeyIdentifier {}".format(kmip_key_id)

            logger.debug("enc_params_list_string = {}".format(enc_params_list_string))
        else:

            if dataset_type == 'Staging':
                enc_params_list_string = " --enableEncryption --encryptionKeyFile {}".format(
                    sourceobj.parameters.encryption_keyfile)
            elif dataset_type == 'Virtual':
                enc_params_list_string = " --enableEncryption --encryptionKeyFile {}/.delphix/.dlpx_enckeyfile".format(
                    mount_path)
            base_enc_params_list_string = enc_params_list_string

            # Save encryption file. Assuming same file used for all config servers and all shards
            cmd = "cp -p {} {}/.delphix/.dlpx_enckeyfile".format(sourceobj.parameters.encryption_keyfile,
                                                                 mount_path)
            res = execute_bash_cmd(rx_connection, cmd, {})

    # setup configserver
    confignum = 0
    membernum = 0

    if source_encrypted:
        add_debug_heading_block("Encrypted - setup_config_member")
        res = setup_config_member(rx_connection, mount_path, confignum, membernum, start_portpool, smax,
                                  shard_config_list, encryption_method, enc_params_list_string,
                                  shardserver_setting_list)

    else:
        add_debug_heading_block("Unencrypted - setup_config_member")
        res = setup_config_member(rx_connection, mount_path, confignum, membernum, start_portpool, smax,
                                  shard_config_list, None, None, shardserver_setting_list)

    rs_initiate(rx_connection, sourceobj.mongo_shell_path, start_portpool)

    cmd = "{} --port {} --quiet --eval 'rs.status()'".format(sourceobj.mongo_shell_path, start_portpool)
    res = execute_bash_cmd(rx_connection, cmd, {})
    # OUTPUT=$(mongo --port $DBPORT --eval "rs.status()"|egrep "name|stateStr")
    add_debug_space()

    if replicaset:
        add_debug_heading_block("Replicaset - setup_config_replset_members")
        setup_config_replset_members(shard_config_list, sourceobj, mount_path, encryption_method,
                                     enc_params_list_string, dataset_type)

    add_debug_space()

    # setup shardserver
    cmd = "hostname"
    hostname = execute_bash_cmd(rx_connection, cmd, {})

    cmd = "cat {}/c0m0/restoreInfo.txt|grep 'Replica Set:'".format(mount_path)
    res = execute_bash_cmd(rx_connection, cmd, {})
    config_repset_name = res.split(':')[1].strip()
    logger.debug("config_repset_name = {}".format(config_repset_name))
    configsvrstring = "{}/{}:{}".format(config_repset_name, hostname, start_portpool)

    if source_encrypted:
        for i in range(smax):
            shardnum = i
            membernum = 0
            shardmember = "s{}m0".format(i)
            snm0_port = get_shard_port(shard_config_list, shardmember)
            logger.debug("{},{}".format(shardmember, snm0_port))

            if encryption_method == "KMIP":
                kmip_key_id = get_kmip_key_id("{}/s{}m{}".format(mount_path, i, 0), rx_connection)
                enc_params_list_string = base_enc_params_list_string
                enc_params_list_string = enc_params_list_string + " --kmipKeyIdentifier {}".format(kmip_key_id)

            setup_shard_member(sourceobj, rx_connection, mount_path, shardnum, membernum, snm0_port, smax,
                               shard_config_list, encryption_method, enc_params_list_string, configsvrstring)

            rs_initiate(rx_connection, sourceobj.mongo_shell_path, snm0_port)

            cmd = "{} --port {} --quiet --eval 'rs.status()'".format(sourceobj.mongo_shell_path, snm0_port)
            res = execute_bash_cmd(rx_connection, cmd, {})
    else:
        for i in range(smax):
            shardnum = i
            membernum = 0
            shardmember = "s{}m0".format(i)
            snm0_port = get_shard_port(shard_config_list, shardmember)
            logger.debug("{},{}".format(shardmember, snm0_port))
            setup_shard_member(sourceobj, rx_connection, mount_path, shardnum, membernum, snm0_port, smax,
                               shard_config_list, None, None, configsvrstring)

            rs_initiate(rx_connection, sourceobj.mongo_shell_path, snm0_port)

            cmd = "{} --port {} --quiet --eval 'rs.status()'".format(sourceobj.mongo_shell_path, snm0_port)
            res = execute_bash_cmd(rx_connection, cmd, {})

            add_debug_space()

    if replicaset:
        add_debug_heading_block("Replicaset - setup_shard_replset_members")
        logger.debug("setup_shard_replset_members() - Start")
        setup_shard_replset_members(shard_config_list, sourceobj, mount_path, encryption_method,
                                    base_enc_params_list_string, smax, dataset_type)
        logger.debug("setup_shard_replset_members() - End")
        add_debug_space()

    # setup mongos
    add_debug_heading_block("setup mongos")
    setup_mongos(sourceobj, rx_connection, mount_path, membernum, mongos_port, configsvrstring, shard_config_list)

    if dataset_type == 'Staging':
        # Create mongo admin user
        create_mongoadmin_user(sourceobj, rx_connection, smax, shard_config_list)
    elif dataset_type == 'Virtual':
        # Update mongo admin password
        update_mongoadmin_pwd(sourceobj, rx_connection, smax, shard_config_list, snapshot.mongo_db_user,
                              snapshot.mongo_db_password, mongos_port)

    # Generate Config files
    add_debug_heading_block("Generate Config files")
    gen_config_files(dataset_type, sourceobj, shard_config_list, snapshot)


def add_debug_space():
    logger.debug("\n\n\n\n")


def add_debug_heading_block(heading):
    logger.debug("\n\n\n\n")
    logger.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    logger.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    logger.info("\t\t{}".format(heading))
    logger.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    logger.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    logger.debug("\n\n\n\n")


def _is_port_empty(port: int) -> bool:
    assert str(port) != '', "Port number must not be empty."
    assert port != 0, "Port number must not be 0."


def _validate_clustersync_user_inputs(source_obj) -> None:
    # clustersync and backupfiles must not coexist.
    try:
        assert str(source_obj.parameters.config_backupfile) == '', \
            "Cluster sync and backup file parameters can't coexist."
    except AssertionError as ae:
        raise UserError(f"{str(ae)}")

    # Check if Mongosync port is not empty/0
    try:
        _is_port_empty(source_obj.parameters.mongosync_port)
    except AssertionError as ae:
        raise UserError(
            f"{str(ae)}. Please provide a valid unused Mongosync port number."
        )


def check_input_parameters(source_obj):
    if source_obj.parameters.enable_authentication:
        if (source_obj.parameters.cluster_auth_mode in ["keyFile","sendKeyFile"] and
                not source_obj.parameters.keyfile_path):
            raise UserError(
                "Incorrect authentication configuration provided. "
                "Please provide keyFile path when cluster authentication "
                "mode is keyFile.")
        elif source_obj.parameters.cluster_auth_mode in ["x509","sendX509"]:
            if source_obj.parameters.enable_ssl_tls:
                tls_param_name_list =[p["property_name"] for p in
                                      source_obj.parameters.ssl_tls_params]
                tls_expected_param = ["tlsMode", "tlsCAFile", "tlsPEMKeyFile",
                                      "sslAllowConnectionsWithoutCertificates"]
                list_diff = set(tls_expected_param) - set(tls_param_name_list)
                if list_diff:
                    raise UserError(
                        f"Incorrect authentication configuration provided. "
                        f"Please provide all necessary SSL/TLS parameters when "
                        f"cluster authentication mode is x509. "
                        f"Params provided : {tls_param_name_list} "
                        f"Expected parameters: {tls_expected_param} ")
            else:
                raise UserError(
                    "Incorrect authentication configuration provided. "
                    "Please provide SSL/TLS parameters when cluster "
                    "authentication mode is x509.")

    # cluster sync specific validation
    if hasattr(source_obj.parameters,
               'enable_clustersync') \
     and source_obj.parameters.enable_clustersync:
        _validate_clustersync_user_inputs(source_obj)


def _mongosh_marked_failed_shutdown(shutdown_error: str) -> bool:
    # REFERENCE:
    # $ /u01/mongo603/bin/mongosh admin --port 28500 --quiet
    #   --eval ‘db.shutdownServer()’
    # MongoNetworkError: connection 3 to 127.0.0.1:28500 closed
    # [delphix@mongo509-src-13sep22 ~]$ echo $?
    # 1
    return shutdown_error.split()[0] == \
           constants.Globals.EXPECTED_SERVER_SHUTDOWN_ERROR.split()[0] \
             and shutdown_error.split()[-1] == \
                constants.Globals.EXPECTED_SERVER_SHUTDOWN_ERROR.split()[-1]


def _mongosh_marked_failed_rs_initiate(rs_initiate_error: str) -> bool:
    # REFERENCE:
    # $ /u01/mongo603/bin/mongosh --port 28801 --quiet --eval 'rs.initiate()' -u dlpxadmin -p delphix --verbose
    # MongoServerError: already initialized
    # [delphix@mongo509-src-13sep22 ~]$ echo $?
    # 1
    return rs_initiate_error == constants.Globals.EXPECTED_RS_INITIATE_ERROR


def shutdown_server(
        rx_connection,
        mongo_shell_path: str,
        port: int
        ) -> None:

    cmd = constants.Globals.SERVER_SHUTDOWN.format(
            mongo_shell_path=mongo_shell_path,
            port=port
        )
    try:
        execute_bash_cmd(rx_connection, cmd, {})
        time.sleep(5)
    except Exception as e:
        if not mongo_shell_path.split('/')[-1] == 'mongosh' \
         and not _mongosh_marked_failed_shutdown(str(e)):
            err = constants.Globals.ERR_SERVER_SHUTDOWN.format(port=port)
            err += str(e)
            raise Exception(err)


def rs_initiate(
        rx_connection,
        mongo_shell_path: str,
        port: int
) -> None:
    cmd = constants.Globals.RS_INITIATE.format(
        mongo_shell_path=mongo_shell_path,
        port=port
    )
    try:
        execute_bash_cmd(rx_connection, cmd, {})
        time.sleep(5)
    except Exception as e:
        if not mongo_shell_path.split('/')[-1] == 'mongosh' \
         and not _mongosh_marked_failed_rs_initiate(str(e)):
            err = constants.Globals.ERR_RS_INITIATE
            err += str(e)
            raise Exception(err)
