#
# Copyright (c) 2019 by Delphix. All rights reserved.
#

from __future__ import print_function

from dlpx.virtualization.platform import (
    Mount,
    MountSpecification,
    Plugin,
    Status
)

from operations import discovery, linked, virtual, constants, common
import _version

from utils import setup_logger

import json
import logging
import pkgutil
import re, copy
import time
# import pickle
from datetime import datetime

from dlpx.virtualization.platform.exceptions import UserError
# raise UserError(
#     "Stopped for debugging.",
#     'Stopped for debugging. check logs',
#     '{}\n{}'.format(" ", " "))

from dlpx.virtualization import libs
from dlpx.virtualization.common import RemoteConnection
from dlpx.virtualization.common import RemoteEnvironment
from dlpx.virtualization.common import RemoteUser



# stg_dsource_type
# "enum": [
#             "Seed",
#             "emptyStagingFS",
#             "Staging",
#             "osdatacopyStagingFS",
#             "mongoAtlas",
#             "advmongodump",
#             "stdmongodump",
#             "shardedsource"
#         ],


from generated.definitions import RepositoryDefinition
from generated.definitions import SourceConfigDefinition
from generated.definitions import SnapshotDefinition
from helpers import helpers

setup_logger._setup_logger()
logger = logging.getLogger(__name__)
# logger = logging.getLogger()
# logger.addHandler(libs.PlatformHandler())
# logger.setLevel(logging.DEBUG)

plugin = Plugin()

@plugin.upgrade.snapshot("2021.09.20.009")
def add_new_flag_to_snapshot(old_snapshot):
    return old_snapshot

@plugin.discovery.repository()
def repository_discovery(source_connection):
    common.add_debug_heading_block("Start Repository Discovery")
    helpers._record_hook("repository_discovery", source_connection)

    env = {
        "DELPHIX_DIR": source_connection.environment.host.binary_path,
        "DLPX_PLUGIN_WORKFLOW": 'repoDiscovery',
        "DLPX_TOOLKIT_WORKFLOW": 'repoDiscovery'
    }
    logger.debug("env: {}".format(env))
    repositories = []
    script_content = pkgutil.get_data('resources', 'discover_repos.sh')
    #logger.debug("discover_repos_repository_script: {}".format(script_content))
    res = libs.run_bash(source_connection, script_content, env)
    logger.debug("res = {}".format(res))
    logger.debug("res.stdout = {}".format(res.stdout))
    repodiscovery = json.loads(res.stdout)
    logger.debug(repodiscovery)
    for item in repodiscovery:
        logger.debug("item:{}".format(item))
        repository = RepositoryDefinition(version=item['version'], mongo_install_path=item['mongo_install_path'],
                                          mongo_shell_path=item['mongo_shell_path'], pretty_name=item['pretty_name'])
        repositories.append(repository)

    # # Write library file for future use
    # env = {
    #     "DELPHIX_DIR": source_connection.environment.host.binary_path,
    #     "DLPX_PLUGIN_WORKFLOW": 'sourceConfigDiscovery',
    #     "MONGO_LIBRARY_SOURCE": pkgutil.get_data('resources', 'library.sh')
    # }
    # script_content = pkgutil.get_data('resources', 'write_library.sh')
    # res = libs.run_bash(source_connection, script_content, env)
    # data = json.loads(res.stdout)
    # logger.debug(data)
    common.add_debug_heading_block("End Repository Discovery")
    return repositories


@plugin.discovery.source_config()
def source_config_discovery(source_connection, repository):
    common.add_debug_heading_block("Start SourceConfig Discovery")
    helpers._record_hook("source_config_discovery", source_connection)
    # return [SourceConfigDefinition("Test"), SourceConfigDefinition("Test2")]
    common.add_debug_heading_block("End SourceConfig Discovery")
    return []


@plugin.linked.mount_specification()
def staged_mount_specification(staged_source, repository):
    common.add_debug_heading_block("Start Staged Mount Specification")
    helpers._record_hook("staging mount specification",
                         staged_source.staged_connection)
    logger.debug("mount_path={}".format(staged_source.parameters.mount_path))
    mount = Mount(staged_source.staged_connection.environment,
                  staged_source.parameters.mount_path)
    common.add_debug_heading_block("End Staged Mount Specification")
    return MountSpecification([mount])


@plugin.linked.pre_snapshot()
def staged_pre_snapshot(repository, source_config, staged_source, optional_snapshot_parameters):
    common.add_debug_heading_block("Start Staged Pre Snapshot")
    helpers._record_hook("staging pre snapshot",
                         staged_source.staged_connection)
    staged_source.mongo_install_path = repository.mongo_install_path
    staged_source.mongo_shell_path = repository.mongo_shell_path
    logger.info("optional_snapshot_parameters={}".format(optional_snapshot_parameters))
    if optional_snapshot_parameters is not None and optional_snapshot_parameters.resync:
        common.add_debug_heading_block("Start Staged Pre Snapshot Resync")

        if staged_source.parameters.d_source_type == "stagingpush":
            cmd = "(ls {}/.delphix/MongoOps_Automation_DSOURCE_RESYNC.cfg >> /dev/null 2>&1 && echo yes) || echo no".format(
                staged_source.parameters.mount_path)
            result = common.execute_bash_cmd(staged_source.staged_connection, cmd, {})

            if result == "yes":
                logger.error(
                    "dSource Re-Syncronization is not a valid option for {} ingestion type on host: {}".format(
                        staged_source.parameters.d_source_type,staged_source.parameters.mongo_host))
                raise UserError(
                    "dSource Re-Syncronization is not a valid option for {} ingestion type on host: {}".format(staged_source.parameters.d_source_type,staged_source.parameters.mongo_host), '\nPlease remove / cleanup the dSource manually in case of re-syncronizing dSource')

        cmd = "(ls {}/.delphix/DSOURCE_RESYNC.cfg >> /dev/null 2>&1 && echo yes) || echo no".format(staged_source.parameters.mount_path)
        res = common.execute_bash_cmd(staged_source.staged_connection, cmd, {})

        if res == "yes":
            logger.info("Its resync operation on dSource as File {}/.delphix/DSOURCE_RESYNC.cfg exists.".format(staged_source.parameters.mount_path))
            linked.stg_cleanup_pre_snapsync(staged_source, repository, None)
        else:
            logger.info("Its new dSource as File {}/.delphix/DSOURCE_RESYNC.cfg does not exists.".format(
                staged_source.parameters.mount_path))

        if staged_source.parameters.d_source_type == "shardedsource":
            common.setup_dataset(staged_source, 'Staging', None, "shardedsource")

        elif staged_source.parameters.d_source_type == "nonshardedsource":
            staged_source.parameters.mongos_port = staged_source.parameters.start_portpool
            common.setup_dataset(staged_source, 'Staging', None, "nonshardedsource")

        elif staged_source.parameters.d_source_type == "offlinemongodump":
            staged_source.parameters.mongos_port = staged_source.parameters.start_portpool
            linked.setup_dataset_mongodump_offline(staged_source, 'Staging', None, "offlinemongodump")

            # Write backup information
            linked.write_first_backup_timestamp(staged_source)

        elif staged_source.parameters.d_source_type == "onlinemongodump":
            staged_source.parameters.mongos_port = staged_source.parameters.start_portpool
            linked.setup_dataset_mongodump_online(staged_source, 'Staging', None, "onlinemongodump")

        elif staged_source.parameters.d_source_type == "seed":
            staged_source.parameters.mongos_port = staged_source.parameters.start_portpool
            linked.setup_dataset_seed(staged_source, 'Staging', None, "seed")

        elif staged_source.parameters.d_source_type == "extendedcluster":
            staged_source.parameters.mongo_db_user = staged_source.parameters.src_db_user
            staged_source.parameters.mongo_db_password = staged_source.parameters.src_db_password
            staged_source.parameters.mongos_port = staged_source.parameters.start_portpool
            linked.setup_replicaset_dsource(staged_source, 'Staging', "extendedcluster")

        elif staged_source.parameters.d_source_type == "stagingpush":
            staged_source.parameters.mongo_db_user = staged_source.parameters.src_db_user
            staged_source.parameters.mongo_db_password = staged_source.parameters.src_db_password
            staged_source.parameters.mongos_port = staged_source.parameters.start_portpool
            linked.initiate_emptyfs_for_dsource(staged_source, 'Staging', "stagingpush")
            cmd = "echo \"DO NOT DELETE THIS FILE. It is used to check if its resync or new dsource\" >> {}/.delphix/MongoOps_Automation_DSOURCE_RESYNC.cfg".format(staged_source.parameters.mount_path)
            status = common.execute_bash_cmd(staged_source.staged_connection, cmd, {})

        cmd = "echo \"DO NOT DELETE THIS FILE. It is used to check if its resync or new dsource\" >> {}/.delphix/DSOURCE_RESYNC.cfg".format(staged_source.parameters.mount_path)
        res = common.execute_bash_cmd(staged_source.staged_connection, cmd, {})

        common.add_debug_heading_block("End Staged Pre Snapshot Resync")
    # Pre-Snapshot
    common.add_debug_space()
    common.add_debug_heading_block("Pre-Snapshot")
    if staged_source.parameters.d_source_type == "extendedcluster":
        linked.check_pre_snapshot_possible(staged_source, optional_snapshot_parameters)
        staged_source.parameters.mongo_db_user = staged_source.parameters.src_db_user
        staged_source.parameters.mongo_db_password = staged_source.parameters.src_db_password

    if staged_source.parameters.d_source_type not in ["onlinemongodump","extendedcluster","stagingpush","seed"]:
        ret = linked.stg_pre_snapsync(staged_source)
    else:
        ret = 0

    if ret == 0:
        if staged_source.parameters.d_source_type == "shardedsource":
            common.setup_dataset(staged_source, 'Staging', None, "shardedsource")
        elif staged_source.parameters.d_source_type == "nonshardedsource":
            staged_source.parameters.mongos_port = staged_source.parameters.start_portpool
            common.setup_dataset(staged_source, 'Staging', None, "nonshardedsource")
        elif staged_source.parameters.d_source_type == "offlinemongodump":
            staged_source.parameters.mongos_port = staged_source.parameters.start_portpool
            linked.setup_dataset_mongodump_offline(staged_source, 'Staging', None, "offlinemongodump")
        elif staged_source.parameters.d_source_type == "onlinemongodump":
            staged_source.parameters.mongos_port = staged_source.parameters.start_portpool
            linked.presync_mongodump_online(staged_source, 'Staging', None, "onlinemongodump")
        elif staged_source.parameters.d_source_type in ["seed","stagingpush"]:
            staged_source.parameters.mongos_port = staged_source.parameters.start_portpool

        if staged_source.parameters.d_source_type not in ["onlinemongodump", "extendedcluster", "stagingpush", "seed"]:
            # Write backup information
            cmd = "cat {}".format(staged_source.parameters.backup_metadata_file)
            src_lastbackup_datetime = common.execute_bash_cmd(staged_source.staged_connection, cmd, {})
            cmd = "echo {} > {}/.delphix/.stg_lastbackup_datetime.txt".format(src_lastbackup_datetime,
                                                                              staged_source.parameters.mount_path)
            res = common.execute_bash_cmd(staged_source.staged_connection, cmd, {})

    #logger.debug("Staging Pre Snapshot - Freeze IO")
    #common.fsync_lock_sharded_mongo(staged_source, 'Staging')
    #logger.debug("Staging Pre Snapshot - Freeze IO - done")

    logger.debug("End of pre snapshot")
    common.add_debug_heading_block("End Staged Pre Snapshot")
    logger.debug(" ")

@plugin.linked.post_snapshot()
def staged_post_snapshot(repository, source_config, staged_source, optional_snapshot_parameters):
    common.add_debug_heading_block("Start Staged Post Snapshot")
    helpers._record_hook("staging post snapshot",
                         staged_source.staged_connection)
    helpers._set_running(staged_source.staged_connection, staged_source.guid)
    staged_source.mongo_install_path = repository.mongo_install_path
    staged_source.mongo_shell_path = repository.mongo_shell_path

    if staged_source.parameters.d_source_type == "extendedcluster":
        staged_source.parameters.mongo_db_user = staged_source.parameters.src_db_user
        staged_source.parameters.mongo_db_password = staged_source.parameters.src_db_password

        snapshot_possible_file_path = "{}/{}".format(staged_source.parameters.mount_path,
                                                     ".delphix/snapshot_not_possible.txt")
        cmd = "test -f {} && cat {} || echo 'file does not exist.'".format(snapshot_possible_file_path,
                                                                           snapshot_possible_file_path)
        res = common.execute_bash_cmd(staged_source.staged_connection, cmd, {})
        if res != "file does not exist.":
            cmd = "rm {}".format(snapshot_possible_file_path)
            res_rm = common.execute_bash_cmd(staged_source.staged_connection, cmd, {})
            errorMsg = "Cannot perform Snapshot as the host {} is in state {}".format(
                res.split("  ")[1].split(" : ")[1], res.split("  ")[2].split(" : ")[1])
            logger.info(errorMsg)
            raise UserError(errorMsg)

    elif staged_source.parameters.d_source_type == "stagingpush":
        staged_source.parameters.mongo_db_user = staged_source.parameters.src_db_user
        staged_source.parameters.mongo_db_password = staged_source.parameters.src_db_password

    if staged_source.parameters.d_source_type == "nonshardedsource":
        staged_source.parameters.mongos_port = staged_source.parameters.start_portpool

    logger.info("In Post snapshot...")
    logger.debug("len shard_backupfiles: {}".format(len(staged_source.parameters.shard_backupfiles)))
    script_content = 'echo "$(uname):$(uname -p):$(cat /etc/*-release)"'
    res = common.execute_bash_cmd(staged_source.staged_connection, script_content, {})
    output = res.strip().split(":")
    logger.debug("output = {}".format(output))

    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("%m%d%Y-%H%M%S.%f")
    snapshot = SnapshotDefinition(validate=False)

    snapshot.toolkit_version = _version.Version
    snapshot.timestamp = timestampStr
    snapshot.architecture = output[1]
    snapshot.os_type = output[0]
    snapshot.os_version = re.search('.*"VERSION="([\d\.]+).*', output[2]).group(1)
    snapshot.mongo_version = repository.version
    snapshot.delphix_mount = staged_source.parameters.mount_path
    snapshot.storage_engine = staged_source.parameters.storage_engine
    snapshot.user_auth_mode = staged_source.parameters.user_auth_mode
    snapshot.keyfile_path = staged_source.parameters.keyfile_path
    snapshot.replica_set = "N/A"
    snapshot.journal_interval = staged_source.parameters.journal_interval
    snapshot.oplog_size = staged_source.parameters.oplog_size
    snapshot.d_source_type = staged_source.parameters.d_source_type
    snapshot.append_db_path = "N/A"
    snapshot.mongo_db_user = staged_source.parameters.mongo_db_user
    snapshot.mongo_db_password = staged_source.parameters.mongo_db_password
    snapshot.source_sharded = staged_source.parameters.source_sharded
    snapshot.shard_count = (len(staged_source.parameters.shard_backupfiles))
    snapshot.source_encrypted = staged_source.parameters.source_encrypted
    snapshot.cluster_auth_mode = staged_source.parameters.cluster_auth_mode
    snapshot.encryption_method = staged_source.parameters.encryption_method
    snapshot.encryption_keyfile = ".delphix/.dlpx_enckeyfile"
    snapshot.kmip_params = staged_source.parameters.kmip_params

    #logger.debug("Staging Post Snapshot - Unfreeze IO")
    #common.fsync_unlock_sharded_mongo(staged_source, 'Staging')
    #logger.debug("Staging Post Snapshot - Unfreeze IO - done")

    mask_snap = copy.deepcopy(snapshot)
    mask_snap.mongo_db_password = 'xxxxxxxxxx'
    logger.debug("snapshot schema: {}".format(mask_snap))
    common.add_debug_heading_block("End Staged Post Snapshot")
    # ADD start Balancer
    return snapshot


@plugin.linked.start_staging()
def start_staging(repository, source_config, staged_source):
    common.add_debug_heading_block("Start Staged  - Start Staging")
    helpers._record_hook("staging start", staged_source.staged_connection)
    helpers._set_running(staged_source.staged_connection, staged_source.guid)

    staged_source.mongo_install_path = repository.mongo_install_path
    staged_source.mongo_shell_path = repository.mongo_shell_path

    if staged_source.parameters.d_source_type == "extendedcluster":
        staged_source.parameters.mongos_port = staged_source.parameters.start_portpool
        staged_source.parameters.mongo_db_user = staged_source.parameters.src_db_user
        staged_source.parameters.mongo_db_password = staged_source.parameters.src_db_password
        linked.add_staging_to_primary(staged_source, 'Staging', "extendedcluster")
    elif staged_source.parameters.d_source_type == "stagingpush":
        logger.info("No action needed for stagingpsuh")
    else:

        if staged_source.parameters.d_source_type == "nonshardedsource":
            staged_source.parameters.mongos_port = staged_source.parameters.start_portpool

        common.start_sharded_mongo('Staging', staged_source)

    logger.debug("End of start staging")
    common.add_debug_heading_block("End Staged - Start Staging")
    logger.debug(" ")


@plugin.linked.stop_staging()
def stop_staging(repository, source_config, staged_source):
    common.add_debug_heading_block("Start Staged  - Stop Staging")
    helpers._record_hook("staging stop", staged_source.staged_connection)
    helpers._set_stopped(staged_source.staged_connection, staged_source.guid)

    staged_source.mongo_install_path = repository.mongo_install_path
    staged_source.mongo_shell_path = repository.mongo_shell_path

    if staged_source.parameters.d_source_type == "extendedcluster":
        staged_source.parameters.mongos_port = staged_source.parameters.start_portpool
        staged_source.parameters.mongo_db_user = staged_source.parameters.src_db_user
        staged_source.parameters.mongo_db_password = staged_source.parameters.src_db_password
        linked.drop_staging_from_primary(staged_source, 'Staging', "extendedcluster")
    elif staged_source.parameters.d_source_type == "stagingpush":
        logger.info("No action needed for stagingpsuh")
    else:

        if staged_source.parameters.d_source_type == "nonshardedsource":
            staged_source.parameters.mongos_port = staged_source.parameters.start_portpool

        common.stop_sharded_mongo('Staging', staged_source)

    logger.debug("End of stop staging")
    common.add_debug_heading_block("End Staged  - Stop Staging")
    logger.debug(" ")


@plugin.linked.status()
def staged_status(staged_source, repository, source_config):
    helpers._record_hook("staging status", staged_source.staged_connection)
    # mount_status = libs.run_bash(staged_source.staged_connection, "mount")
    # file_status = libs.run_bash(staged_source.staged_connection,
    #    "test -f /var/tmp/running-{}".format(staged_source.guid))
    # if file_status.exit_code==0 and staged_source.parameters.path in mount_status.stdout:
    #    return Status.ACTIVE
    # else:
    #    return Status.INACTIVE

    staged_source.mongo_install_path = repository.mongo_install_path
    staged_source.mongo_shell_path = repository.mongo_shell_path

    if staged_source.parameters.d_source_type in ["extendedcluster","stagingpush"] :
        staged_source.parameters.mongo_db_user = staged_source.parameters.src_db_user
        staged_source.parameters.mongo_db_password = staged_source.parameters.src_db_password

    if staged_source.parameters.d_source_type in ["nonshardedsource","extendedcluster","stagingpush"] :
        staged_source.parameters.mongos_port = staged_source.parameters.start_portpool

    get_status = common.get_status_sharded_mongo("Staging",staged_source)
    logger.debug("Staging : get_status : {}".format(get_status))
    if get_status == 0:
        return Status.ACTIVE
    else:
        return Status.INACTIVE


@plugin.linked.worker()
def staged_worker(repository, source_config, staged_source):
    helpers._record_hook("staging worker", staged_source.staged_connection)


@plugin.virtual.mount_specification()
def mount_specification(repository, virtual_source):
    helpers._record_hook("virtual mount spec", virtual_source.connection)
    virtual_source.mongo_install_path = repository.mongo_install_path
    virtual_source.mongo_shell_path = repository.mongo_shell_path

    nodes = []
    nodes.append(virtual_source.connection.environment.reference)
    for node in virtual_source.parameters.additional_nodes:
        nodes.append(node['environment'])
    totalnodes = len(nodes)
    logger.info("Total Nodes : {}".format(totalnodes))
    logger.info("Nodes = {}".format(nodes))
    logger.info("Mount Path = {}".format(virtual_source.parameters.mount_path))

    nodemount_list = []
    for node in nodes:
        nodemount = Mount(node, virtual_source.parameters.mount_path)
        nodemount_list.append(nodemount)
    return MountSpecification(nodemount_list)

    # script_content = pkgutil.get_data('resources', 'fetchIDs.sh')
    # res = libs.run_bash(virtual_source.connection, "whoami")
    # env_vars = {"USER_NAME" : res.stdout.strip()}
    # res = libs.run_bash(virtual_source.connection, script_content, env_vars)
    # json_dict = json.loads(res.stdout)
    # spec = OwnershipSpecification(int(json_dict["uid"]),int(json_dict["gid"]))
    # return MountSpecification([mount], ownership_specification=spec)


@plugin.virtual.configure()
def configure(virtual_source, repository, snapshot):
    helpers._record_hook("virtual configure", virtual_source.connection)
    helpers._set_running(virtual_source.connection, virtual_source.guid)

    virtual_source.mongo_install_path = repository.mongo_install_path
    virtual_source.mongo_shell_path = repository.mongo_shell_path

    logger.info("snapshot:{}".format(snapshot))
    logger.info("d_source_type:{}".format(snapshot.d_source_type))
    d_source_type = snapshot.d_source_type
    if d_source_type in  ["nonshardedsource","offlinemongodump","onlinemongodump","seed","stagingpush","extendedcluster"]:
        virtual_source.parameters.mongos_port = virtual_source.parameters.start_portpool
    common.setup_dataset(virtual_source, 'Virtual', snapshot, d_source_type)

    logger.debug("End of virtual configure")
    logger.debug(" ")

    discovery_type = "Auto"
    pretty_name = "{}-{}-{}".format(d_source_type, virtual_source.parameters.mount_path, virtual_source.parameters.start_portpool)

    return SourceConfigDefinition(
        discovery_type=discovery_type,
        pretty_name=pretty_name
    )

@plugin.virtual.pre_snapshot()
def pre_snapshot(repository, source_config, virtual_source):
    helpers._record_hook("virtual pre snapshot", virtual_source.connection)

    ## Run bash checks
    # res = libs.run_bash(virtual_source.connection, "exit 1")
    # assert res.exit_code == 1, "exit_code ({}) != 1".format(res.exit_code)
    # res = libs.run_bash(virtual_source.connection, "echo 'text'")
    # assert "text" in res.stdout, "string 'text' not in stdout. Got {}".format(
    #    res.stdout)
    # assert res.exit_code == 0, "exit_code ({}) != 0".format(res.exit_code)
    # res = libs.run_bash(virtual_source.connection, "ls nothing123")
    # assert "nothing123" in res.stderr, "string 'nothing123' not in stderr. Got {}".format(
    #    res.stderr)
    # assert res.exit_code == 2, "exit_code ({}) != 2".format(res.exit_code)

    # Get all nodes information

    # Freeze IO
    #logger.debug("Virtual Pre Snapshot - Freeze IO")
    #common.fsync_lock_sharded_mongo(virtual_source, 'Virtual')
    #logger.debug("Virtual Pre Snapshot - Freeze IO - done")

    virtual_source.mongo_install_path = repository.mongo_install_path
    virtual_source.mongo_shell_path = repository.mongo_shell_path

    logger.debug("End of virtual pre_snapshot")
    logger.debug(" ")


@plugin.virtual.post_snapshot()
def post_snapshot(repository, source_config, virtual_source):
    helpers._record_hook("virtual post snapshot", virtual_source.connection)
    logger.info("In Post snapshot...")

    virtual_source.mongo_install_path = repository.mongo_install_path
    virtual_source.mongo_shell_path = repository.mongo_shell_path

    # Define variables
    mount_path = virtual_source.parameters.mount_path
    start_portpool = virtual_source.parameters.start_portpool
    cfgfile = "{}/.delphix/.tgt_config.txt".format(mount_path)

    cmd = "cat {}|grep DSOURCE_TYPE|awk -F: '{{ print $2 }}'".format(cfgfile)
    d_source_type = common.execute_bash_cmd(virtual_source.connection, cmd, {})

    if d_source_type == "nonshardedsource":
        virtual_source.parameters.mongos_port = start_portpool

    mongos_port = virtual_source.parameters.mongos_port

    shard_count = 0

    if d_source_type == "shardedsource":
        cmd = "cat {}|grep SHARD_COUNT|awk -F: '{{ print $2 }}'".format(cfgfile)
        shard_count = common.execute_bash_cmd(virtual_source.connection, cmd, {})
        if not isinstance(shard_count, int):
            shard_count = int(shard_count)

    cmd = "cat {}|grep DSOURCE_TYPE|awk -F: '{{ print $2 }}'".format(cfgfile)
    d_source_type = common.execute_bash_cmd(virtual_source.connection, cmd, {})

    if d_source_type == "shardedsource":
        source_sharded = True
    else:
        source_sharded = False

    cmd = "cat {}|grep SOURCE_ENCRYPTED|awk -F: '{{ print $2 }}'".format(cfgfile)
    source_encrypted = common.execute_bash_cmd(virtual_source.connection, cmd, {})

    cmd = "cat {}|grep ENCRYPTION_METHOD|awk -F: '{{ print $2 }}'".format(cfgfile)
    encryption_method = common.execute_bash_cmd(virtual_source.connection, cmd, {})

    if encryption_method == "KeyFile":
        encryption_keyfile = ".delphix/.dlpx_enckeyfile"
    else:
        encryption_keyfile = ""
    logger.debug("encryption_keyfile = {}".format(encryption_keyfile))

    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("%m%d%Y-%H%M%S.%f")

    script_content = 'echo "$(uname):$(uname -p):$(cat /etc/redhat-release)"'
    res = libs.run_bash(virtual_source.connection, script_content)
    logger.debug("res = {}".format(res))
    output = res.stdout.strip().split(":")
    logger.debug("output = {}".format(output))

    snapshot = SnapshotDefinition(validate=False)

    snapshot.toolkit_version = _version.Version
    snapshot.timestamp = timestampStr
    snapshot.architecture = output[1]
    snapshot.os_type = output[0]
    snapshot.os_version = re.sub(r".*\s(\d)", r'\1', output[2]).split(" ")[0]

    snapshot.mongo_version = repository.version
    snapshot.delphix_mount = virtual_source.parameters.mount_path
    snapshot.storage_engine = "WiredTiger"
    snapshot.user_auth_mode = virtual_source.parameters.user_auth_mode
    snapshot.keyfile_path = virtual_source.parameters.keyfile_path
    snapshot.replica_set = "N/A"

    snapshot.journal_interval = virtual_source.parameters.journal_interval
    snapshot.oplog_size = virtual_source.parameters.oplog_size
    snapshot.d_source_type = d_source_type

    snapshot.append_db_path = "N/A"
    if d_source_type == "extendedcluster":
        cmd = "cat {}|grep MONGO_DB_USER|awk -F: '{{ print $2 }}'".format(cfgfile)
        mongo_db_user = common.execute_bash_cmd(virtual_source.connection, cmd, {})
        snapshot.mongo_db_user = mongo_db_user
    else:
        snapshot.mongo_db_user = "delphixadmin"
    snapshot.mongo_db_password = virtual_source.parameters.mongo_db_password

    logger.debug("source_sharded = {}".format(source_sharded))
    # logger.debug("source_sharded = {}".format(ast.literal_eval(source_sharded)))
    if source_sharded == 1 or source_sharded == True or source_sharded == "True":
        snapshot.source_sharded = True
    else:
        snapshot.source_sharded = False

    snapshot.shard_count = shard_count

    logger.debug("source_encrypted = {}".format(source_encrypted))
    # logger.debug("source_encrypted = {}".format(ast.literal_eval(source_encrypted)))
    if source_encrypted == 1 or source_encrypted == True or source_encrypted == "True":
        snapshot.source_encrypted = True
    else:
        snapshot.source_encrypted = False

    snapshot.cluster_auth_mode = virtual_source.parameters.cluster_auth_mode
    snapshot.encryption_method = encryption_method
    snapshot.encryption_keyfile = encryption_keyfile
    snapshot.kmip_params = []

    # Unlock Freeze
    #logger.debug("Virtual Post Snapshot - Unfreeze IO")
    #common.fsync_unlock_sharded_mongo(virtual_source, 'Virtual')
    #logger.debug("Virtual Post Snapshot - Unfreeze IO - done")

    mask_snap = copy.deepcopy(snapshot)
    mask_snap.mongo_db_password = 'xxxxxxxxxx'
    logger.debug("snapshot schema: {}".format(mask_snap))
    common.add_debug_heading_block("End Virtual Post Snapshot")
    return snapshot


@plugin.virtual.reconfigure()
def reconfigure(snapshot, repository, source_config, virtual_source):
    helpers._record_hook("virtual reconfigure", virtual_source.connection)
    helpers._set_running(virtual_source.connection, virtual_source.guid)

    virtual_source.mongo_install_path = repository.mongo_install_path
    virtual_source.mongo_shell_path = repository.mongo_shell_path

    common.start_sharded_mongo('Virtual', virtual_source)

    return source_config


@plugin.virtual.start()
def start(repository, source_config, virtual_source):
    helpers._record_hook("virtual start", virtual_source.connection)
    helpers._set_running(virtual_source.connection, virtual_source.guid)

    virtual_source.mongo_install_path = repository.mongo_install_path
    virtual_source.mongo_shell_path = repository.mongo_shell_path

    common.start_sharded_mongo('Virtual', virtual_source)

    logger.debug("End of start virtual")
    logger.debug(" ")


@plugin.virtual.stop()
def stop(repository, source_config, virtual_source):
    helpers._record_hook("virtual stop", virtual_source.connection)
    helpers._set_stopped(virtual_source.connection, virtual_source.guid)

    virtual_source.mongo_install_path = repository.mongo_install_path
    virtual_source.mongo_shell_path = repository.mongo_shell_path

    common.stop_sharded_mongo('Virtual', virtual_source)

    logger.debug("End of stop virtual")
    logger.debug(" ")


@plugin.virtual.status()
def status(repository, source_config, virtual_source):
    helpers._record_hook("virtual status", virtual_source.connection)
    # mount_status = libs.run_bash(virtual_source.connection, "mount")

    # file_status = libs.run_bash(virtual_source.connection,
    #     "test -f /var/tmp/running-{}".format(virtual_source.guid))
    # if file_status.exit_code==0 and virtual_source.parameters.path in mount_status.stdout:
    #     return Status.ACTIVE
    # else:
    #     return Status.INACTIVE

    virtual_source.mongo_install_path = repository.mongo_install_path
    virtual_source.mongo_shell_path = repository.mongo_shell_path

    get_status = common.get_status_sharded_mongo("Virtual", virtual_source)
    logger.debug("Virtual : get_status : {}".format(get_status))
    if get_status == 0:
        return Status.ACTIVE
    else:
        return Status.INACTIVE

@plugin.virtual.unconfigure()
def unconfigure(repository, source_config, virtual_source):
    helpers._record_hook("virtual unconfigure", virtual_source.connection)
    helpers._set_stopped(virtual_source.connection, virtual_source.guid)

    virtual_source.mongo_install_path = repository.mongo_install_path
    virtual_source.mongo_shell_path = repository.mongo_shell_path
    
    common.stop_sharded_mongo('Virtual', virtual_source)


