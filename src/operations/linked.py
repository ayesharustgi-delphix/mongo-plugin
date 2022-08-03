from dlpx.virtualization.platform.exceptions import UserError
import logging
from operations import common
import datetime
import os
import json
import time

# Global logger object for this file
logger = logging.getLogger(__name__)


def validate_backup_configfile(staged_source):
    if not staged_source.parameters.backup_metadata_file:
        if staged_source.parameters.d_source_type != "extendedcluster":
            raise UserError(
                "Backup DateConfig File Name cannot be empty",
                'Make sure file exists with last backup time in format MMDDYYYY_HH24MISS',
                '{}\n{}'.format("ls -l filename", " "))


def write_first_backup_timestamp(staged_source):
    cmd = "(ls {} >> /dev/null 2>&1 && echo yes) || echo no".format(staged_source.parameters.backup_metadata_file)
    res = common.execute_bash_cmd(staged_source.staged_connection, cmd, {})
    if res == "yes":
        logger.info("Backup File {} exists.".format(staged_source.parameters.backup_metadata_file))
        cmd = "cat {}".format(staged_source.parameters.backup_metadata_file)
        src_lastbackup_datetime = common.execute_bash_cmd(staged_source.staged_connection, cmd, {})
        logger.info("src_lastbackup_datetime: {}".format(src_lastbackup_datetime))
        cmd = "echo {} > {}/.delphix/.stg_lastbackup_datetime.txt".format(src_lastbackup_datetime,
                                                                          staged_source.parameters.mount_path)
        res = common.execute_bash_cmd(staged_source.staged_connection, cmd, {})

    else:
        logger.error("File {} does not exist".format(staged_source.parameters.backup_metadata_file))
        raise UserError(
            "File {} does not exist".format(staged_source.parameters.backup_metadata_file),
            'Make sure file {} exists with last backup time in format MMDDYYYY_HH24MISS',
            '{}\n{}'.format(res, "Error:"))


def stg_pre_snapsync(staged_source):
    cmd = "(ls {} >> /dev/null 2>&1 && echo yes) || echo no".format(staged_source.parameters.backup_metadata_file)
    res = common.execute_bash_cmd(staged_source.staged_connection, cmd, {})
    if res == "yes":
        logger.info("Backup File {} exists.".format(staged_source.parameters.backup_metadata_file))
        cmd = "cat {}".format(staged_source.parameters.backup_metadata_file)
        src_lastbackup_datetime = common.execute_bash_cmd(staged_source.staged_connection, cmd, {})
        logger.info("src_lastbackup_datetime: {}".format(src_lastbackup_datetime))

        cmd = "cat {}/.delphix/.stg_lastbackup_datetime.txt".format(staged_source.parameters.mount_path)
        stg_lastbackup_datetime = common.execute_bash_cmd(staged_source.staged_connection, cmd, {})
        if src_lastbackup_datetime == stg_lastbackup_datetime:
            logger.info("No new backups found.")
            return 1
        else:
            logger.info("New backups found.")
            common.stop_sharded_mongo('Staging', staged_source)

            if staged_source.parameters.d_source_type == "shardedsource":
                cmd = "rm -Rf {}/c*".format(staged_source.parameters.mount_path)
                res = common.execute_bash_cmd(staged_source.staged_connection, cmd, {})

                cmd = "rm -Rf {}/s*".format(staged_source.parameters.mount_path)
                res = common.execute_bash_cmd(staged_source.staged_connection, cmd, {})

            elif staged_source.parameters.d_source_type in ["nonshardedsource", "offlinemongodump"]:
                cmd = "rm -Rf {}/s*".format(staged_source.parameters.mount_path)
                res = common.execute_bash_cmd(staged_source.staged_connection, cmd, {})

            return 0
    else:
        logger.info("Backup File {} does not exists. Cannot determine new backups. Skipping step".format(
            staged_source.parameters.backup_metadata_file))
        return 1


def stg_cleanup_pre_snapsync(staged_source, repository=None, source_config=None):

    if staged_source.parameters.d_source_type == "shardedsource":
        common.stop_sharded_mongo('Staging', staged_source)
        cmd = "rm -Rf {}/c*".format(staged_source.parameters.mount_path)
        res = common.execute_bash_cmd(staged_source.staged_connection, cmd, {})

        cmd = "rm -Rf {}/s*".format(staged_source.parameters.mount_path)
        res = common.execute_bash_cmd(staged_source.staged_connection, cmd, {})

    else:
        if staged_source.parameters.d_source_type == "extendedcluster":
            # stop_staging(repository, source_config, staged_source)
            common.add_debug_heading_block("Resync - Stop Existing Staging")

            staged_source.mongo_install_path = repository.mongo_install_path
            staged_source.mongo_shell_path = repository.mongo_shell_path

            if staged_source.parameters.d_source_type == "extendedcluster":
                staged_source.parameters.mongos_port = staged_source.parameters.start_portpool
                staged_source.parameters.mongo_db_user = staged_source.parameters.src_db_user
                staged_source.parameters.mongo_db_password = staged_source.parameters.src_db_password
                drop_staging_from_primary(staged_source, 'Staging', "extendedcluster")
            logger.debug(" ")
        else:
            common.stop_sharded_mongo('Staging', staged_source)

        cmd = "rm -Rf {}/s*".format(staged_source.parameters.mount_path)
        res = common.execute_bash_cmd(staged_source.staged_connection, cmd, {})


def restore_mongodump_online(sourceobj, dataset_type, mongo_backup_dir):
    if dataset_type == "Staging":
        rx_connection = sourceobj.staged_connection

    start_portpool = sourceobj.parameters.start_portpool
    # -u {} -p {} --host {} --authenticationDatabase=admin
    cmd = "{}/mongorestore --port {} --drop --quiet --gzip --dir={}".format(
        os.path.dirname(sourceobj.mongo_restore_path), start_portpool, mongo_backup_dir)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    common.add_debug_space()

def restore_mongodump_online_presync(sourceobj, dataset_type, mongo_backup_dir):
    if dataset_type == "Staging":
        rx_connection = sourceobj.staged_connection

    cmd = "hostname"
    hostname = common.execute_bash_cmd(rx_connection, cmd, {})
    mongo_shell_cmd = common.gen_mongo_cmd(dataset_type, sourceobj, hostname)

    cmd = "echo \"{}\"|cut -f2- -d' '".format(mongo_shell_cmd)
    mongorestore_connparams = common.execute_bash_cmd_silent_status(rx_connection, cmd, {})
    resarr = mongorestore_connparams.split()
    if sourceobj.parameters.mongo_db_password:
        if sourceobj.parameters.mongo_db_password in resarr:
            i_pwd = resarr.index(sourceobj.parameters.mongo_db_password)
            resarr[i_pwd] =  'xxxxxxxxx'
    logger.info("mongorestore_connparams: {}".format(' '.join(resarr)))

    mongorestore_cmd = "{} {}".format(sourceobj.mongo_restore_path, mongorestore_connparams)

    start_portpool = sourceobj.parameters.start_portpool
    cmd = "{} --port {} --drop --quiet --gzip --dir={}".format(
        mongorestore_cmd, start_portpool, mongo_backup_dir)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    common.add_debug_space()


def create_seed_database(sourceobj, dataset_type):
    if dataset_type == "Staging":
        rx_connection = sourceobj.staged_connection

    mount_path = sourceobj.parameters.mount_path
    start_portpool = sourceobj.parameters.start_portpool
    source_encrypted = sourceobj.parameters.source_encrypted
    encryption_method = sourceobj.parameters.encryption_method
    replicaset_name = sourceobj.parameters.src_replicaset_name
    if replicaset_name == "" or replicaset_name is None:
        replicaset_name = "dlpx_rs0"

    if source_encrypted:
        if encryption_method == "KMIP":

            enc_params_list_string = "--enableEncryption"
            for kmip_params in sourceobj.parameters.kmip_params:
                enc_params_list_string = enc_params_list_string + " --{} {}".format(kmip_params['property_name'],
                                                                                    kmip_params['value'])

            base_enc_params_list_string = enc_params_list_string

            logger.debug("enc_params_list_string = {}".format(enc_params_list_string))
        else:

            if dataset_type == 'Staging':
                enc_params_list_string = " --enableEncryption --encryptionKeyFile {}".format(
                    sourceobj.parameters.encryption_keyfile)

            base_enc_params_list_string = enc_params_list_string

            # Save encryption file. Assuming same file used for all config servers and all shards
            cmd = "cp -p {} {}/.delphix/.dlpx_enckeyfile".format(sourceobj.parameters.encryption_keyfile, mount_path)
            res = common.execute_bash_cmd(rx_connection, cmd, {})

        start_mongo_cmd = "{} --dbpath {}/s0m0 --logpath {}/logs/dlpx.s0m0.{}.mongod.log --bind_ip 0.0.0.0 --port {} {} --replSet {} --fork".format(
            sourceobj.mongo_install_path,
            mount_path, mount_path, start_portpool, start_portpool, base_enc_params_list_string, replicaset_name)

    else:
        start_mongo_cmd = "{} --dbpath {}/s0m0 --logpath {}/logs/dlpx.s0m0.{}.mongod.log --bind_ip 0.0.0.0 --port {} --replSet {} --fork".format(
            sourceobj.mongo_install_path,
            mount_path, mount_path, start_portpool, start_portpool, replicaset_name)

    res = common.execute_bash_cmd(rx_connection, start_mongo_cmd, {})

    cmd = "{} --port {} --quiet --eval 'rs.initiate()'".format(sourceobj.mongo_shell_path, start_portpool)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    cmd = "{} --port {} --quiet --eval 'rs.status()'".format(sourceobj.mongo_shell_path, start_portpool)
    res = common.execute_bash_cmd(rx_connection, cmd, {})
    # OUTPUT=$(mongo --port $DBPORT --eval "rs.status()"|egrep "name|stateStr")

    cmd = "echo \"Replica Set: {}\" > {}/s0m0/restoreInfo.txt".format(replicaset_name, mount_path)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    common.add_debug_space()


def restore_mongodump(sourceobj, dataset_type):
    if dataset_type == "Staging":
        rx_connection = sourceobj.staged_connection

    start_portpool = sourceobj.parameters.start_portpool
    config_backupfile = sourceobj.parameters.config_backupfile

    cmd = "{}/mongorestore --port {} --drop --quiet --gzip --dir={}".format(
        os.path.dirname(sourceobj.mongo_restore_path), start_portpool, config_backupfile)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    common.add_debug_space()


def setup_dataset_mongodump_offline(sourceobj, dataset_type, snapshot, dsource_type):
    rx_connection = sourceobj.staged_connection
    dataset_cfgfile = ".stg_config.txt"

    # Validate backup config file exists
    validate_backup_configfile(sourceobj)

    # Create delphix internal directory
    cmd = "mkdir -p {}/.delphix".format(sourceobj.parameters.mount_path)
    res = common.execute_bash_cmd(sourceobj.staged_connection, cmd, {})

    # Generate and write config file
    nodes = common.create_node_array(dataset_type, sourceobj)
    common.add_debug_space()

    # Define variables
    mount_path = sourceobj.parameters.mount_path
    start_portpool = sourceobj.parameters.start_portpool
    mongos_port = sourceobj.parameters.mongos_port
    replicaset = sourceobj.parameters.make_shards_replicaset

    config_backupfile = sourceobj.parameters.config_backupfile
    rx_connection = sourceobj.staged_connection
    source_encrypted = sourceobj.parameters.source_encrypted
    encryption_method = sourceobj.parameters.encryption_method

    logger.info("nodes = {}".format(nodes))
    logger.info("start_portpool = {}".format(start_portpool))
    logger.info("mount_path     = {}".format(mount_path))
    logger.info("replicaset     = {}".format(replicaset))

    # Create directory structure
    common.add_debug_heading_block("Create directory structure")
    common.cr_dir_structure_replicaset(mount_path, replicaset, rx_connection)

    # Generate replicaset mappings
    common.add_debug_heading_block("Generate replicaset mappings")
    replicaset_config_list = []
    replicaset_config_list = common.gen_replicaset_config_list(
        nodes, start_portpool, mount_path, replicaset)

    for replicaset_config in replicaset_config_list:
        logger.info("replicaset_config :{}".format(replicaset_config))

    common.add_debug_space()

    cmd = "echo \"{}\" > {}/.delphix/.stg_dsourcecfg.txt".format(replicaset_config_list, mount_path)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    # create seed database
    common.add_debug_heading_block("create seed database")
    create_seed_database(sourceobj, dataset_type)

    # restore mongodump backup
    common.add_debug_heading_block("restore mongodump backup")
    restore_mongodump(sourceobj, dataset_type)

    cmd = "echo \"DSOURCE_TYPE:{}\" > {}/.delphix/{}".format(dsource_type, mount_path,
                                                             dataset_cfgfile)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    cmd = "echo \"MONGO_DB_USER:{}\" >> {}/.delphix/{}".format(sourceobj.parameters.mongo_db_user, mount_path,
                                                               dataset_cfgfile)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    if source_encrypted:
        cmd = "echo \"SOURCE_ENCRYPTED:{}\" >> {}/.delphix/{}".format("True", mount_path, dataset_cfgfile)
        res = common.execute_bash_cmd(rx_connection, cmd, {})

        cmd = "echo \"ENCRYPTION_METHOD:{}\" >> {}/.delphix/{}".format(encryption_method, mount_path, dataset_cfgfile)
        res = common.execute_bash_cmd(rx_connection, cmd, {})
    else:
        cmd = "echo \"SOURCE_ENCRYPTED:{}\" >> {}/.delphix/{}".format("False", mount_path, dataset_cfgfile)
        res = common.execute_bash_cmd(rx_connection, cmd, {})
    common.add_debug_space()

    # Create mongo admin user
    common.create_mongoadmin_user(sourceobj, rx_connection, 0, replicaset_config_list)

    # Generate Config files
    common.add_debug_heading_block("Generate Config files")
    common.gen_config_files(dataset_type, sourceobj, replicaset_config_list, snapshot)


def setup_dataset_seed(sourceobj, dataset_type, snapshot, dsource_type):
    rx_connection = sourceobj.staged_connection
    dataset_cfgfile = ".stg_config.txt"

    # Create delphix internal directory
    cmd = "mkdir -p {}/.delphix".format(sourceobj.parameters.mount_path)
    res = common.execute_bash_cmd(sourceobj.staged_connection, cmd, {})

    # Generate and write config file
    nodes = common.create_node_array(dataset_type, sourceobj)
    common.add_debug_space()

    # Define variables
    mount_path = sourceobj.parameters.mount_path
    start_portpool = sourceobj.parameters.start_portpool
    mongos_port = sourceobj.parameters.mongos_port
    replicaset = sourceobj.parameters.make_shards_replicaset

    config_backupfile = sourceobj.parameters.config_backupfile
    rx_connection = sourceobj.staged_connection
    source_encrypted = sourceobj.parameters.source_encrypted
    encryption_method = sourceobj.parameters.encryption_method

    logger.info("nodes = {}".format(nodes))
    logger.info("start_portpool = {}".format(start_portpool))
    logger.info("mount_path     = {}".format(mount_path))
    logger.info("replicaset     = {}".format(replicaset))

    # Create directory structure
    common.add_debug_heading_block("Create directory structure")
    common.cr_dir_structure_replicaset(mount_path, replicaset, rx_connection)

    # Generate replicaset mappings
    common.add_debug_heading_block("Generate replicaset mappings")
    replicaset_config_list = []
    replicaset_config_list = common.gen_replicaset_config_list(
        nodes, start_portpool, mount_path, replicaset)

    for replicaset_config in replicaset_config_list:
        logger.info("replicaset_config :{}".format(replicaset_config))

    common.add_debug_space()

    cmd = "echo \"{}\" > {}/.delphix/.stg_dsourcecfg.txt".format(replicaset_config_list, mount_path)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    # create seed database
    common.add_debug_heading_block("create seed database")
    create_seed_database(sourceobj, dataset_type)

    cmd = "echo \"DSOURCE_TYPE:{}\" > {}/.delphix/{}".format(dsource_type, mount_path,
                                                             dataset_cfgfile)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    cmd = "echo \"MONGO_DB_USER:{}\" >> {}/.delphix/{}".format(sourceobj.parameters.mongo_db_user, mount_path,
                                                               dataset_cfgfile)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    if source_encrypted:
        cmd = "echo \"SOURCE_ENCRYPTED:{}\" >> {}/.delphix/{}".format("True", mount_path, dataset_cfgfile)
        res = common.execute_bash_cmd(rx_connection, cmd, {})

        cmd = "echo \"ENCRYPTION_METHOD:{}\" >> {}/.delphix/{}".format(encryption_method, mount_path, dataset_cfgfile)
        res = common.execute_bash_cmd(rx_connection, cmd, {})
    else:
        cmd = "echo \"SOURCE_ENCRYPTED:{}\" >> {}/.delphix/{}".format("False", mount_path, dataset_cfgfile)
        res = common.execute_bash_cmd(rx_connection, cmd, {})
    common.add_debug_space()

    # Create mongo admin user
    common.create_mongoadmin_user(sourceobj, rx_connection, 0, replicaset_config_list)

    # Generate Config files
    common.add_debug_heading_block("Generate Config files")
    common.gen_config_files(dataset_type, sourceobj, replicaset_config_list, snapshot)


def setup_dataset_mongodump_online(sourceobj, dataset_type, snapshot, dsource_type):
    dataset_cfgfile = ".stg_config.txt"

    # Create delphix internal directory
    cmd = "mkdir -p {}/.delphix".format(sourceobj.parameters.mount_path)
    res = common.execute_bash_cmd(sourceobj.staged_connection, cmd, {})

    # Generate and write config file
    nodes = common.create_node_array(dataset_type, sourceobj)
    common.add_debug_space()

    # Define variables
    mount_path = sourceobj.parameters.mount_path
    start_portpool = sourceobj.parameters.start_portpool
    mongos_port = sourceobj.parameters.mongos_port
    replicaset = sourceobj.parameters.make_shards_replicaset
    # logsync = True
    logsync = sourceobj.parameters.enable_logsync

    rx_connection = sourceobj.staged_connection
    source_encrypted = sourceobj.parameters.source_encrypted
    encryption_method = sourceobj.parameters.encryption_method

    logger.info("nodes          = {}".format(nodes))
    logger.info("start_portpool = {}".format(start_portpool))
    logger.info("mount_path     = {}".format(mount_path))
    logger.info("replicaset     = {}".format(replicaset))

    mongo_db_user = sourceobj.parameters.mongo_db_user
    mongo_db_password = sourceobj.parameters.mongo_db_password
    src_mongo_host_conn = sourceobj.parameters.src_mongo_host_conn
    src_db_user = sourceobj.parameters.src_db_user
    src_db_password = sourceobj.parameters.src_db_password

    # Create directory structure
    common.add_debug_heading_block("Create directory structure")
    common.cr_dir_structure_replicaset(mount_path, replicaset, rx_connection)

    # Generate replicaset mappings
    common.add_debug_heading_block("Generate replicaset mappings")
    replicaset_config_list = common.gen_replicaset_config_list(nodes, start_portpool, mount_path, replicaset)

    for replicaset_config in replicaset_config_list:
        logger.info("replicaset_config :{}".format(replicaset_config))
    common.add_debug_space()

    cmd = "echo \"{}\" > {}/.delphix/.stg_dsourcecfg.txt".format(replicaset_config_list, mount_path)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    # create seed database
    common.add_debug_heading_block("create seed database")
    create_seed_database(sourceobj, dataset_type)

    # create oplog backup dir
    x = datetime.datetime.now()
    x_dateformat = x.strftime("%m%d%Y_%H%M%S")
    mongo_backup_dir = "{}/mongo_bkps/{}".format(mount_path, x_dateformat)

    cmd = "mkdir -p {}".format(mongo_backup_dir)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    # logsync is not reliable. Cannot guarantee presence of oplogs as it is circular and may get overwritten
    # So disabling/removing this functionality
    # Modified to use same variable to capture or not capture oplogs. TRue = capture oplogs
    if logsync:
        # common.add_debug_heading_block("Get oplog position")
        # cmd = "mkdir -p {}/s0m0/oplogs/local".format(mount_path)
        # res = common.execute_bash_cmd(rx_connection, cmd, {})
        #
        # # common.fsync_lock_mongo(sourceobj, dataset_type)
        #
        # curroplogpos = get_current_oplog_position(sourceobj, dataset_type)
        # logger.info("Write oplog position to file")
        # cmd = "echo \"{}\" > {}/.delphix/oplog.pos".format(curroplogpos, mount_path)
        # res = common.execute_bash_cmd(rx_connection, cmd, {})
        # cmd = "echo \"{}\" > {}/.delphix/oplog.pos.incr".format(curroplogpos, mount_path)
        # res = common.execute_bash_cmd(rx_connection, cmd, {})
        # logger.info("Write oplog position to file done.")

        # generate mongodump backup
        common.add_debug_heading_block("Generate mongodump backup")
        cmd = "{}/mongodump -u {} -p {} --host {} --authenticationDatabase=admin --oplog --gzip -o {}".format(
            os.path.dirname(sourceobj.mongo_dump_path), src_db_user, src_db_password, src_mongo_host_conn,
            mongo_backup_dir)
        res = common.execute_bash_cmd(rx_connection, cmd, {})

    else:
        # generate mongodump backup
        common.add_debug_heading_block("Generate mongodump backup")
        cmd = "{}/mongodump -u {} -p {} --host {} --authenticationDatabase=admin --gzip -o {}".format(
            os.path.dirname(sourceobj.mongo_dump_path), src_db_user, src_db_password, src_mongo_host_conn,
            mongo_backup_dir)
        res = common.execute_bash_cmd(rx_connection, cmd, {})

    cmd = "du -sh {}".format(mongo_backup_dir)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    if logsync:
        # common.fsync_unlock_mongo(sourceobj, dataset_type)
        pass

    restore_mongodump_online(sourceobj, dataset_type, mongo_backup_dir)

    cmd = "echo \"DSOURCE_TYPE:{}\" > {}/.delphix/{}".format(dsource_type, mount_path,
                                                             dataset_cfgfile)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    cmd = "echo \"MONGO_DB_USER:{}\" >> {}/.delphix/{}".format(sourceobj.parameters.mongo_db_user, mount_path,
                                                               dataset_cfgfile)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    if source_encrypted:
        cmd = "echo \"SOURCE_ENCRYPTED:{}\" >> {}/.delphix/{}".format("True", mount_path, dataset_cfgfile)
        res = common.execute_bash_cmd(rx_connection, cmd, {})

        cmd = "echo \"ENCRYPTION_METHOD:{}\" >> {}/.delphix/{}".format(encryption_method, mount_path, dataset_cfgfile)
        res = common.execute_bash_cmd(rx_connection, cmd, {})
    else:
        cmd = "echo \"SOURCE_ENCRYPTED:{}\" >> {}/.delphix/{}".format("False", mount_path, dataset_cfgfile)
        res = common.execute_bash_cmd(rx_connection, cmd, {})

    cmd = "echo \"LAST_DUMP_DIR:{}\" >> {}/.delphix/{}".format(x_dateformat, mount_path, dataset_cfgfile)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    common.add_debug_space()

    # Create mongo admin user
    common.create_mongoadmin_user(sourceobj, rx_connection, 0, replicaset_config_list)

    # Generate Config files
    common.add_debug_heading_block("Generate Config files")
    common.gen_config_files(dataset_type, sourceobj, replicaset_config_list, snapshot)


def setup_dataset(sourceobj, dataset_type, snapshot, dsource_type):
    rx_connection = sourceobj.staged_connection
    dataset_cfgfile = ".stg_config.txt"

    # Create delphix internal directory
    cmd = "mkdir -p {}/.delphix".format(sourceobj.parameters.mount_path)
    res = common.execute_bash_cmd(sourceobj.staged_connection, cmd, {})

    # Generate and write config file
    nodes = common.create_node_array(dataset_type, sourceobj)
    common.add_debug_space()

    # Define variables
    mount_path = sourceobj.parameters.mount_path
    start_portpool = sourceobj.parameters.start_portpool
    mongos_port = sourceobj.parameters.mongos_port
    replicaset = sourceobj.parameters.make_shards_replicaset

    config_backupfile = sourceobj.parameters.config_backupfile
    rx_connection = sourceobj.staged_connection
    source_encrypted = sourceobj.parameters.source_encrypted
    encryption_method = sourceobj.parameters.encryption_method

    logger.info("nodes = {}".format(nodes))
    logger.info("start_portpool = {}".format(start_portpool))
    logger.info("mount_path     = {}".format(mount_path))
    logger.info("replicaset     = {}".format(replicaset))

    # Create directory structure
    common.add_debug_heading_block("Create directory structure")
    common.cr_dir_structure_replicaset(mount_path, replicaset, rx_connection)

    # Generate replicaset mappings
    common.add_debug_heading_block("Generate replicaset mappings")
    replicaset_config_list = []
    replicaset_config_list = common.gen_replicaset_config_list(
        nodes, start_portpool, mount_path, replicaset)

    for replicaset_config in replicaset_config_list:
        logger.info("replicaset_config :{}".format(replicaset_config))

    common.add_debug_space()

    cmd = "echo \"{}\" > {}/.delphix/.stg_dsourcecfg.txt".format(replicaset_config_list, mount_path)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    # create seed database
    common.add_debug_heading_block("create seed database")
    create_seed_database(sourceobj, dataset_type)

    cmd = "echo \"DSOURCE_TYPE:{}\" > {}/.delphix/{}".format(dsource_type, mount_path,
                                                             dataset_cfgfile)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    cmd = "echo \"MONGO_DB_USER:{}\" >> {}/.delphix/{}".format(sourceobj.parameters.mongo_db_user, mount_path,
                                                               dataset_cfgfile)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    if source_encrypted:
        cmd = "echo \"SOURCE_ENCRYPTED:{}\" >> {}/.delphix/{}".format("True", mount_path, dataset_cfgfile)
        res = common.execute_bash_cmd(rx_connection, cmd, {})

        cmd = "echo \"ENCRYPTION_METHOD:{}\" >> {}/.delphix/{}".format(encryption_method, mount_path, dataset_cfgfile)
        res = common.execute_bash_cmd(rx_connection, cmd, {})
    else:
        cmd = "echo \"SOURCE_ENCRYPTED:{}\" >> {}/.delphix/{}".format("False", mount_path, dataset_cfgfile)
        res = common.execute_bash_cmd(rx_connection, cmd, {})
    common.add_debug_space()

    # Create mongo admin user
    common.create_mongoadmin_user(sourceobj, rx_connection, 0, replicaset_config_list)

    # Generate Config files
    common.add_debug_heading_block("Generate Config files")
    common.gen_config_files(dataset_type, sourceobj, replicaset_config_list, snapshot)

    cmd = "echo \"IGNORE dsPreSnapshot scripts\" > {}/.delphix/NEWDSOURCEFILE.cfg".format(mount_path)
    res = common.execute_bash_cmd(rx_connection, cmd, {})
    common.add_debug_space()


# def presync_mongodump_online(sourceobj, dataset_type, snapshot, dsource_type):
#     dataset_cfgfile = ".stg_config.txt"
#
#     # Generate and write config file
#     nodes = common.create_node_array(dataset_type, sourceobj)
#     common.add_debug_space()
#
#     # Define variables
#     mount_path = sourceobj.parameters.mount_path
#     start_portpool = sourceobj.parameters.start_portpool
#     mongos_port = sourceobj.parameters.mongos_port
#     replicaset = sourceobj.parameters.make_shards_replicaset
#     logsync = True
#
#     rx_connection = sourceobj.staged_connection
#     source_encrypted = sourceobj.parameters.source_encrypted
#     encryption_method = sourceobj.parameters.encryption_method
#
#     logger.info("nodes          = {}".format(nodes))
#     logger.info("start_portpool = {}".format(start_portpool))
#     logger.info("mount_path     = {}".format(mount_path))
#     logger.info("replicaset     = {}".format(replicaset))
#
#     mongo_db_user = sourceobj.parameters.mongo_db_user
#     mongo_db_password = sourceobj.parameters.mongo_db_password
#     src_mongo_host_conn = sourceobj.parameters.src_mongo_host_conn
#     src_db_user = sourceobj.parameters.src_db_user
#     src_db_password = sourceobj.parameters.src_db_password
#
#     # Generate replicaset mappings
#     common.add_debug_heading_block("Generate replicaset mappings")
#     replicaset_config_list = common.gen_replicaset_config_list(nodes, start_portpool, mount_path, replicaset)
#
#     for replicaset_config in replicaset_config_list:
#         logger.info("replicaset_config :{}".format(replicaset_config))
#     common.add_debug_space()
#
#     # Cleanup last run oplogs from staging
#     logger.info("Cleanup last run oplogs from staging ...")
#     cmd = "rm -f {}/s0m0/oplogs/local/*.bson".format(mount_path)
#     res = common.execute_bash_cmd_nofail(rx_connection, cmd, {})
#
#     # create oplog backup dir
#     x = datetime.datetime.now()
#     x_dateformat = x.strftime("%m%d%Y_%H%M%S")
#     mongo_backup_dir = "{}/mongo_bkps/{}".format(mount_path, x_dateformat)
#
#     cmd = "mkdir -p {}".format(mongo_backup_dir)
#     res = common.execute_bash_cmd(rx_connection, cmd, {})
#
#     if logsync:
#         cmd = "mkdir -p {}/s0m0/oplogs/local".format(mount_path)
#         res = common.execute_bash_cmd(rx_connection, cmd, {})
#
#         # common.fsync_lock_mongo(sourceobj, dataset_type)
#
#         curroplogpos = get_current_oplog_position(sourceobj, dataset_type)
#
#         cmd = "cat {}/.delphix/oplog.pos.incr".format(mount_path)
#         lastoplogpos = common.execute_bash_cmd(rx_connection, cmd, {})
#         lastoplogposarr = re.findall(r'\d+', lastoplogpos)
#         timestampval = int(lastoplogposarr[0])
#         incrval = int(lastoplogposarr[1])
#         logger.info("timestampval:{}, incrval:{}".format(timestampval, incrval))
#
#         cmd = "{}/mongodump -u {} -p {} --host {} --authenticationDatabase=admin --quiet -d local -c oplog.rs -o {}/s0m0/oplogs --query \"{{ \\\"ts\\\" : {{ \\\"\\$gt\\\" : {{ \\\"\$timestamp\\\": {{ \\\"t\\\": {} ,\\\"i\\\": {} }}}}}}}}\"".format(
#             os.path.dirname(sourceobj.mongo_install_path), src_db_user, src_db_password, src_mongo_host_conn,
#             mount_path, timestampval, incrval)
#         res = common.execute_bash_cmd(rx_connection, cmd, {})
#
#         logger.info("Write current oplog position to file")
#         cmd = "echo \"{}\" > {}/.delphix/oplog.pos.incr".format(curroplogpos, mount_path)
#         res = common.execute_bash_cmd(rx_connection, cmd, {})
#         logger.info("Write current oplog position to file done.")
#
#         cmd = "du -sh {}/s0m0/oplogs".format(mount_path)
#         res = common.execute_bash_cmd(rx_connection, cmd, {})
#
#         common.fsync_unlock_mongo(sourceobj, dataset_type)
#
#         logger.info("Cleanup and prepare for oplog restore on staging")
#         cmd = "rm -f {}/s0m0/oplogs/local/*.json".format(mount_path)
#         res = common.execute_bash_cmd(rx_connection, cmd, {})
#
#         cmd = "mv {}/s0m0/oplogs/local/oplog.rs.bson {}/s0m0/oplogs/local/oplog.bson".format(mount_path, mount_path)
#         res = common.execute_bash_cmd(rx_connection, cmd, {})
#
#         cmd = "{}/mongorestore -u {} -p {} --host 127.0.0.1:{} --authenticationDatabase=admin --oplogReplay {}/s0m0/oplogs/local".format(
#             os.path.dirname(sourceobj.mongo_install_path), mongo_db_user, mongo_db_password, mongos_port, mount_path)
#         res = common.execute_bash_cmd(rx_connection, cmd, {})
#
#         cmd = "echo \"DSOURCE_TYPE:{}\" > {}/.delphix/{}".format(dsource_type, mount_path, dataset_cfgfile)
#         res = common.execute_bash_cmd(rx_connection, cmd, {})
#
#         cmd = "echo \"MONGO_DB_USER:{}\" >> {}/.delphix/{}".format(sourceobj.parameters.mongo_db_user, mount_path,
#                                                                    dataset_cfgfile)
#         res = common.execute_bash_cmd(rx_connection, cmd, {})
#
#         if source_encrypted:
#             cmd = "echo \"SOURCE_ENCRYPTED:{}\" >> {}/.delphix/{}".format("True", mount_path, dataset_cfgfile)
#             res = common.execute_bash_cmd(rx_connection, cmd, {})
#
#             cmd = "echo \"ENCRYPTION_METHOD:{}\" >> {}/.delphix/{}".format(encryption_method, mount_path,
#                                                                            dataset_cfgfile)
#             res = common.execute_bash_cmd(rx_connection, cmd, {})
#         else:
#             cmd = "echo \"SOURCE_ENCRYPTED:{}\" >> {}/.delphix/{}".format("False", mount_path, dataset_cfgfile)
#             res = common.execute_bash_cmd(rx_connection, cmd, {})
#
#         cmd = "echo \"LAST_DUMP_DIR:{}\" >> {}/.delphix/{}".format(x_dateformat, mount_path, dataset_cfgfile)
#         res = common.execute_bash_cmd(rx_connection, cmd, {})
#
#         common.add_debug_space()

def presync_mongodump_online(sourceobj, dataset_type, snapshot, dsource_type):
    dataset_cfgfile = ".stg_config.txt"

    # Define variables
    mount_path = sourceobj.parameters.mount_path
    start_portpool = sourceobj.parameters.start_portpool
    mongos_port = sourceobj.parameters.mongos_port
    logsync = sourceobj.parameters.enable_logsync

    source_encrypted = sourceobj.parameters.source_encrypted
    encryption_method = sourceobj.parameters.encryption_method

    rx_connection = sourceobj.staged_connection

    cmd = "cat {}/.delphix/.stg_dsourcecfg.txt".format(mount_path)
    res = common.execute_bash_cmd(rx_connection, cmd, {})
    replicaset_config_list = res

    logger.info("start_portpool         = {}".format(start_portpool))
    logger.info("mount_path             = {}".format(mount_path))
    logger.info("replicaset_config_list = {}".format(replicaset_config_list))

    src_mongo_host_conn = sourceobj.parameters.src_mongo_host_conn
    src_db_user = sourceobj.parameters.src_db_user
    src_db_password = sourceobj.parameters.src_db_password

    # create backup dir
    x = datetime.datetime.now()
    x_dateformat = x.strftime("%m%d%Y_%H%M%S")
    mongo_backup_dir = "{}/mongo_bkps/{}".format(mount_path, x_dateformat)
    cmd = "mkdir -p {}".format(mongo_backup_dir)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    if logsync:
        # generate mongodump backup
        common.add_debug_heading_block("Generate mongodump backup")
        cmd = "{}/mongodump -u {} -p {} --host {} --authenticationDatabase=admin --oplog --gzip -o {}".format(
            os.path.dirname(sourceobj.mongo_dump_path), src_db_user, src_db_password, src_mongo_host_conn,
            mongo_backup_dir)
        res = common.execute_bash_cmd(rx_connection, cmd, {})

    else:
        # generate mongodump backup
        common.add_debug_heading_block("Generate mongodump backup")
        cmd = "{}/mongodump -u {} -p {} --host {} --authenticationDatabase=admin --gzip -o {}".format(
            os.path.dirname(sourceobj.mongo_dump_path), src_db_user, src_db_password, src_mongo_host_conn,
            mongo_backup_dir)
        res = common.execute_bash_cmd(rx_connection, cmd, {})

    cmd = "du -sh {}".format(mongo_backup_dir)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    restore_mongodump_online_presync(sourceobj, dataset_type, mongo_backup_dir)

    cmd = "echo \"DSOURCE_TYPE:{}\" > {}/.delphix/{}".format(dsource_type, mount_path,
                                                             dataset_cfgfile)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    cmd = "echo \"MONGO_DB_USER:{}\" >> {}/.delphix/{}".format(sourceobj.parameters.mongo_db_user, mount_path,
                                                               dataset_cfgfile)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    if source_encrypted:
        cmd = "echo \"SOURCE_ENCRYPTED:{}\" >> {}/.delphix/{}".format("True", mount_path, dataset_cfgfile)
        res = common.execute_bash_cmd(rx_connection, cmd, {})

        cmd = "echo \"ENCRYPTION_METHOD:{}\" >> {}/.delphix/{}".format(encryption_method, mount_path, dataset_cfgfile)
        res = common.execute_bash_cmd(rx_connection, cmd, {})
    else:
        cmd = "echo \"SOURCE_ENCRYPTED:{}\" >> {}/.delphix/{}".format("False", mount_path, dataset_cfgfile)
        res = common.execute_bash_cmd(rx_connection, cmd, {})

    cmd = "echo \"LAST_DUMP_DIR:{}\" >> {}/.delphix/{}".format(x_dateformat, mount_path, dataset_cfgfile)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    common.add_debug_space()

    # Create mongo admin user
    # common.create_mongoadmin_user(sourceobj, rx_connection, 0, replicaset_config_list)

def get_current_oplog_position(sourceobj, dataset_type):
    rx_connection = sourceobj.staged_connection
    src_db_user = sourceobj.parameters.src_db_user
    src_db_password = sourceobj.parameters.src_db_password
    src_mongo_host_conn = sourceobj.parameters.src_mongo_host_conn

    logger.info("Find current oplog position")
    cmd = "{} -u {} -p {} --host {} --authenticationDatabase=admin --quiet local --eval \"printjson(db.oplog.rs.find().sort({{\$natural:-1}}).limit(1).next().ts)\"|tail -1".format(
        sourceobj.mongo_shell_path, src_db_user, src_db_password, src_mongo_host_conn)
    cmdlog = "{} -u {} -p {} --host {} --authenticationDatabase=admin --quiet local --eval \"printjson(db.oplog.rs.find().sort({{\$natural:-1}}).limit(1).next().ts)\"|tail -1".format(
        sourceobj.mongo_shell_path,
        src_db_user, "xxxxxx", src_mongo_host_conn)
    curroplogpos = common.execute_bash_cmd(rx_connection, cmd, {})

    if curroplogpos.find("Timestamp") == -1:
        # print("src_unfreeze_io")
        raise UserError(
            "Unable to find current oplog position",
            "Make sure file credentials to source are correct",
            cmdlog)
        logger.error("Unable to find current oplog position")

    return curroplogpos


def check_pre_snapshot_possible(staged_source, optional_snapshot_parameters):
    logger.debug("starting check_pre_snapshot_possible!!!!!!!!")
    src_db_user = staged_source.parameters.src_db_user
    src_db_password = staged_source.parameters.src_db_password
    src_mongo_host_conn = staged_source.parameters.src_mongo_host_conn
    mongo_host = staged_source.parameters.mongo_host
    mongod_port = staged_source.parameters.start_portpool
    staging_host_port = "{}:{}".format(mongo_host, mongod_port)
    rx_connection = staged_source.staged_connection
    mount_path = staged_source.parameters.mount_path

    cmd = "{} --host {} --username {} --password {} --authenticationDatabase admin --quiet --eval \"rs.status()\" | grep \"name\|stateStr\" | awk '!(NR%2){{s = p; for (i = 3; i <= NF; i++) s = s $i \" \"; print s}}{{p=$3}}'| grep \"{}\"".format(staged_source.mongo_shell_path,src_mongo_host_conn, src_db_user, src_db_password,staging_host_port)
    res = common.execute_bash_cmd(rx_connection, cmd, {})
    logger.debug("check_pre_snapshot_possible output::" + str(res))
    if len(res.split(",")) >= 3:
        state_string = res.split(",")[-2][1:-1]
    else:
        state_string = "replicaset member not found!"
    if state_string == "SECONDARY":
        logger.debug("SNAPSHOT POSSIBLE")
    else:
        logger.debug("SNAPSHOT NOT POSSIBLE")
        if optional_snapshot_parameters is not None and optional_snapshot_parameters.resync:
            logger.info("Replica set member {} in state {}! Waiting for the replica set member to come into SECONDARY state.......".format(staging_host_port,state_string))
            while True:
                res = common.execute_bash_cmd(rx_connection, cmd, {})
                state_string = res.split(",")[-2][1:-1]
                logger.info("host : '{}' , state : '{}'".format(staging_host_port, state_string))
                if state_string == "SECONDARY":
                    logger.info("Replica set member now in SECONDARY state. Continuing with snapshot!")
                    break
                time.sleep(60)
        else:
            cmd_possible = "echo \"SNAPSHOT NOT POSSIBLE \n HOST : '{}' \n STATE : '{}'\" > {}/.delphix/snapshot_not_possible.txt".format(staging_host_port, state_string, mount_path)
            res = common.execute_bash_cmd(rx_connection, cmd_possible, {})


def setup_replicaset_dsource(sourceobj, dataset_type, dsource_type):
    dataset_cfgfile = ".stg_config.txt"

    # Validate backup config file exists
    validate_backup_configfile(sourceobj)

    # Create delphix internal directory
    cmd = "mkdir -p {}/.delphix".format(sourceobj.parameters.mount_path)
    res = common.execute_bash_cmd(sourceobj.staged_connection, cmd, {})

    # Generate and write config file
    nodes = common.create_node_array(dataset_type, sourceobj)
    common.add_debug_space()

    rx_connection = sourceobj.staged_connection
    src_db_user = sourceobj.parameters.src_db_user
    src_db_password = sourceobj.parameters.src_db_password
    src_mongo_host_conn = sourceobj.parameters.src_mongo_host_conn
    source_encrypted = sourceobj.parameters.source_encrypted
    encryption_method = sourceobj.parameters.encryption_method
    mount_path = sourceobj.parameters.mount_path
    mongo_host = sourceobj.parameters.mongo_host
    mongod_port = sourceobj.parameters.mongos_port
    staging_host_port = "{}:{}".format(mongo_host, mongod_port)
    start_portpool = sourceobj.parameters.start_portpool

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

    # kmip_params = sourceobj.parameters.kmip_params
    # encryption_keyfile = sourceobj.parameters.encryption_keyfile

    enable_auditlog = sourceobj.parameters.enable_auditlog
    auditlog_params = sourceobj.parameters.auditlog_params

    dbpath = "{}/s0m0".format(mount_path)
    cfgdir = "{}/cfg".format(mount_path)
    logdir = "{}/logs".format(mount_path)
    cfgfile = "{}/dlpx.s0m0.{}.conf".format(cfgdir, mongod_port)
    logfile = "{}/dlpx.s0m0.{}.mongod.log".format(logdir, mongod_port)

    common.cr_dir_structure_replicaset(mount_path, False, rx_connection)

    cmd = "hostname"
    hostname = common.execute_bash_cmd(rx_connection, cmd, {})
    logger.debug("{},{},{},{}".format(dbpath, mongod_port, cfgfile, hostname))

    cmd = "{} --host {} --username {} --password {} --authenticationDatabase admin --quiet --eval \"db.isMaster().setName\"".format(
        sourceobj.mongo_shell_path, src_mongo_host_conn, src_db_user, src_db_password)
    res = common.execute_bash_cmd(rx_connection, cmd, {})
    repset_name = res.strip()
    logger.debug("repset_name = {}".format(repset_name))

    enc_params_list_string = ""
    if source_encrypted:
        if encryption_method == "KMIP":

            enc_params_list_string = "--enableEncryption"
            for kmip_params in sourceobj.parameters.kmip_params:
                enc_params_list_string = enc_params_list_string + " --{} {}".format(kmip_params['property_name'],
                                                                                    kmip_params['value'])
            base_enc_params_list_string = enc_params_list_string
            logger.debug("enc_params_list_string = {}".format(enc_params_list_string))
        else:
            if dataset_type == 'Staging':
                enc_params_list_string = " --enableEncryption --encryptionKeyFile {}".format(
                    sourceobj.parameters.encryption_keyfile)
            base_enc_params_list_string = enc_params_list_string

            # Save encryption file. Assuming same file used for all config servers and all shards
            cmd = "cp -p {} {}/.delphix/.dlpx_enckeyfile".format(sourceobj.parameters.encryption_keyfile,
                                                                 mount_path)
            res = common.execute_bash_cmd(rx_connection, cmd, {})

    if encryption_method is None:
        mongo_cmd = "{} --dbpath {} --logpath {} --fork".format(sourceobj.mongo_install_path, dbpath, logfile)
    else:
        mongo_cmd = "{} --dbpath {} --logpath {} {} --fork".format(sourceobj.mongo_install_path, dbpath, logfile,
                                                                   enc_params_list_string)

    mongo_cmd = common.add_net(mongo_cmd, bind_ip, mongod_port, enable_ssl_tls, ssl_tls_params)
    logger.info("After add_net - mongo_cmd = {}".format(mongo_cmd))
    common.add_debug_space()

    mongo_cmd = common.add_keyfile_auth(mongo_cmd, enable_user_auth, keyfile_path)
    logger.info("After add_keyfile_auth - mongo_cmd = {}".format(mongo_cmd))
    common.add_debug_space()

    mongo_cmd = common.add_cluster_auth(mongo_cmd, cluster_auth_mode, keyfile_path)
    logger.info("After add_cluster_auth - mongo_cmd = {}".format(mongo_cmd))
    common.add_debug_space()

    mongo_cmd = common.add_ldap(mongo_cmd, enable_ldap, ldap_params)
    logger.info("After add_ldap - mongo_cmd = {}".format(mongo_cmd))
    common.add_debug_space()

    mongo_cmd = common.add_set_parameters(mongo_cmd, enable_setparams, setparam_params)
    logger.info("After add_set_parameters - mongo_cmd = {}".format(mongo_cmd))
    common.add_debug_space()

    mongo_cmd = common.add_auditlog(mongo_cmd, enable_auditlog, auditlog_params)
    logger.info("After add_auditlog - mongo_cmd = {}".format(mongo_cmd))
    common.add_debug_space()

    mongo_cmd = "{} --replSet {}".format(mongo_cmd, repset_name)
    logger.info("After replicaset - mongo_cmd = {}".format(mongo_cmd))
    common.add_debug_space()

    mongo_cmd = "{} --outputConfig |grep -v outputConfig > {}".format(mongo_cmd, cfgfile)
    logger.debug("mongo_cmd = {}".format(mongo_cmd))
    common.add_debug_space()
    res = common.execute_bash_cmd(rx_connection, mongo_cmd, {})

    # This may be bug so added to fix proactively
    fix_mongod_cmd = "sed -i 's/replSet: {}/replSetName: {}/g' {}".format(repset_name, repset_name, cfgfile)
    logger.debug("fix_mongod_cmd: {}".format(fix_mongod_cmd))
    res = common.execute_bash_cmd(rx_connection, fix_mongod_cmd, {})

    cmd = "{} -f {}".format(sourceobj.mongo_install_path, cfgfile)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    time.sleep(7)

    cmd = "{} --host {} --username {} --password {} --authenticationDatabase admin --quiet --eval \"rs.isMaster().primary\"".format(
        sourceobj.mongo_shell_path, src_mongo_host_conn, src_db_user, src_db_password)
    res = common.execute_bash_cmd(rx_connection, cmd, {})
    logger.info("Primary Node: {}".format(res))
    primaryNode = res

    cmd = "{} --host {} --username {} --password {} --authenticationDatabase admin --quiet --eval \"JSON.stringify(rs.conf())\"".format(
        sourceobj.mongo_shell_path, src_mongo_host_conn, src_db_user, src_db_password)
    res = common.execute_bash_cmd(rx_connection, cmd, {})
    conf_data = json.loads(res)
    member_info = conf_data['members']
    logger.info("member_info:{}".format(member_info))
    logger.info(" ")
    logger.info("Current Member info:")
    last_member_id = 0
    for member_info in member_info:
        logger.info("Id: {} , host: {}".format(member_info['_id'], member_info['host']))
        last_member_id = member_info['_id'] if member_info['_id'] > last_member_id else last_member_id
        logger.info("staging_host_port: {} , current_host_in_cfg: {}".format(staging_host_port, member_info['host']))
        if staging_host_port == member_info['host']:
            logger.error(
                "Configuration already exists for {} on source cluster. Please remove/cleanup before proceeding.".format(
                    staging_host_port))
            raise UserError(
                "Configuration already exists for {} on source cluster.".format(staging_host_port),
                'Please remove/cleanup before proceeding.',
                '{}\n{}'.format("rs.conf()", " "))

    new_member_id = last_member_id + 1
    cmd = "{} --host {} --username {} --password {} --authenticationDatabase admin --quiet --eval \"JSON.stringify(rs.add({{ host:'{}:{}', priority: 0, votes: 0, hidden: true, _id: {} }}))\"".format(
        sourceobj.mongo_shell_path, primaryNode, src_db_user, src_db_password, mongo_host, mongod_port, new_member_id)
    res = common.execute_bash_cmd(rx_connection, cmd, {})
    logger.info(res)

    common.add_debug_space()
    # Generate replicaset mappings
    common.add_debug_heading_block("Generate replicaset mappings")
    replicaset_config_list = []
    replicaset = False
    replicaset_config_list = common.gen_replicaset_config_list(
        nodes, start_portpool, mount_path, replicaset)

    for replicaset_config in replicaset_config_list:
        logger.info("replicaset_config :{}".format(replicaset_config))

    common.add_debug_space()

    cmd = "echo \"{}\" > {}/.delphix/.stg_dsourcecfg.txt".format(replicaset_config_list, mount_path)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    cmd = "echo \"DSOURCE_TYPE:{}\" > {}/.delphix/{}".format(dsource_type, mount_path,
                                                             dataset_cfgfile)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    cmd = "echo \"MONGO_DB_USER:{}\" >> {}/.delphix/{}".format(sourceobj.parameters.mongo_db_user, mount_path,
                                                               dataset_cfgfile)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    if source_encrypted:
        cmd = "echo \"SOURCE_ENCRYPTED:{}\" >> {}/.delphix/{}".format("True", mount_path, dataset_cfgfile)
        res = common.execute_bash_cmd(rx_connection, cmd, {})

        cmd = "echo \"ENCRYPTION_METHOD:{}\" >> {}/.delphix/{}".format(encryption_method, mount_path, dataset_cfgfile)
        res = common.execute_bash_cmd(rx_connection, cmd, {})
    else:
        cmd = "echo \"SOURCE_ENCRYPTED:{}\" >> {}/.delphix/{}".format("False", mount_path, dataset_cfgfile)
        res = common.execute_bash_cmd(rx_connection, cmd, {})
    common.add_debug_space()

    cmd = "echo \"Replica Set: {}\" > {}/s0m0/restoreInfo.txt".format(repset_name, mount_path)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    return 0


def add_staging_to_primary(sourceobj, dataset_type, dsource_type):
    rx_connection = sourceobj.staged_connection
    src_db_user = sourceobj.parameters.src_db_user
    src_db_password = sourceobj.parameters.src_db_password
    src_mongo_host_conn = sourceobj.parameters.src_mongo_host_conn
    mongo_host = sourceobj.parameters.mongo_host
    mongod_port = sourceobj.parameters.mongos_port
    staging_host_port = "{}:{}".format(mongo_host, mongod_port)

    mount_path = sourceobj.parameters.mount_path
    cfgdir = "{}/cfg".format(mount_path)
    cfgfile = "{}/dlpx.s0m0.{}.conf".format(cfgdir, mongod_port)

    cmd = "{} --host {} --username {} --password {} --authenticationDatabase admin --quiet --eval \"rs.isMaster().primary\"".format(
        sourceobj.mongo_shell_path, src_mongo_host_conn, src_db_user, src_db_password)
    res = common.execute_bash_cmd(rx_connection, cmd, {})
    logger.info("Primary Node: {}".format(res))
    primaryNode = res

    cmd = "{} --host {} --username {} --password {} --authenticationDatabase admin --quiet --eval \"JSON.stringify(rs.conf())\"".format(
        sourceobj.mongo_shell_path, src_mongo_host_conn, src_db_user, src_db_password)
    res = common.execute_bash_cmd(rx_connection, cmd, {})
    conf_data = json.loads(res)
    member_info = conf_data['members']
    logger.info("member_info:{}".format(member_info))
    logger.info(" ")
    logger.info("Current Member info:")
    last_member_id = 0
    for member_info in member_info:
        logger.info("Id: {} , host: {}".format(member_info['_id'], member_info['host']))
        last_member_id = member_info['_id'] if member_info['_id'] > last_member_id else last_member_id
        logger.info("staging_host_port: {} , current_host_in_cfg: {}".format(staging_host_port, member_info['host']))
        if staging_host_port == member_info['host']:
            logger.error(
                "Configuration already exists for {} on source cluster. Please remove/cleanup before proceeding.".format(
                    staging_host_port))
            raise UserError(
                "Configuration already exists for {} on source cluster.".format(staging_host_port),
                'Please remove/cleanup before proceeding.',
                '{}\n{}'.format("rs.conf()", " "))

    new_member_id = last_member_id + 1
    cmd = "{} --host {} --username {} --password {} --authenticationDatabase admin --quiet --eval \"JSON.stringify(rs.add({{ host:'{}:{}', priority: 0, votes: 0, hidden: true, _id: {} }}))\"".format(
        sourceobj.mongo_shell_path, primaryNode, src_db_user, src_db_password, mongo_host, mongod_port, new_member_id)
    res = common.execute_bash_cmd(rx_connection, cmd, {})
    logger.info(res)

    cmd = "{} -f {}".format(sourceobj.mongo_install_path, cfgfile)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    return 0


def drop_staging_from_primary(sourceobj, dataset_type, dsource_type):
    rx_connection = sourceobj.staged_connection
    src_db_user = sourceobj.parameters.src_db_user
    src_db_password = sourceobj.parameters.src_db_password
    src_mongo_host_conn = sourceobj.parameters.src_mongo_host_conn

    mongo_host = sourceobj.parameters.mongo_host
    mongod_port = sourceobj.parameters.mongos_port
    staging_host_port = "{}:{}".format(mongo_host, mongod_port)

    cmd = "{} --host {} --username {} --password {} --authenticationDatabase admin --quiet --eval \"rs.isMaster().primary\"".format(
        sourceobj.mongo_shell_path, src_mongo_host_conn, src_db_user, src_db_password)
    res = common.execute_bash_cmd(rx_connection, cmd, {})
    logger.info("Primary Node: {}".format(res))
    primaryNode = res

    cmd = "{} --host {} --username {} --password {} --authenticationDatabase admin --quiet --eval \"rs.remove('{}:{}')\"".format(
        sourceobj.mongo_shell_path, primaryNode, src_db_user, src_db_password, mongo_host, mongod_port)
    res = common.execute_bash_cmd(rx_connection, cmd, {})
    logger.info(res)

    cmd = "{} --host {} --username {} --password {} --authenticationDatabase admin --quiet --eval \"db.getSiblingDB('admin').shutdownServer({{force: true}})\"".format(
        sourceobj.mongo_shell_path, staging_host_port, src_db_user, src_db_password)
    res = common.execute_bash_cmd(rx_connection, cmd, {})
    logger.info(res)
    logger.info("Sleeping for 7 secs")
    time.sleep(7)


def initiate_emptyfs_for_dsource(sourceobj, dataset_type, dsource_type):
    logger.info("dSource_Type:{}, dataset_type: {}".format(dsource_type, dataset_type))
    dataset_cfgfile = ".stg_config.txt"

    # Validate backup config file exists
    # validate_backup_configfile(sourceobj)

    # Create delphix internal directory
    cmd = "mkdir -p {}/.delphix".format(sourceobj.parameters.mount_path)
    res = common.execute_bash_cmd(sourceobj.staged_connection, cmd, {})

    # Generate and write config file
    nodes = common.create_node_array(dataset_type, sourceobj)
    common.add_debug_space()

    rx_connection = sourceobj.staged_connection
    src_db_user = sourceobj.parameters.src_db_user
    src_db_password = sourceobj.parameters.src_db_password
    src_mongo_host_conn = sourceobj.parameters.src_mongo_host_conn
    source_encrypted = sourceobj.parameters.source_encrypted
    encryption_method = sourceobj.parameters.encryption_method
    mount_path = sourceobj.parameters.mount_path
    mongo_host = sourceobj.parameters.mongo_host
    mongod_port = sourceobj.parameters.mongos_port
    staging_host_port = "{}:{}".format(mongo_host, mongod_port)
    start_portpool = sourceobj.parameters.start_portpool

    bind_ip = sourceobj.parameters.bind_ip
    enable_ssl_tls = sourceobj.parameters.enable_ssl_tls
    ssl_tls_params = sourceobj.parameters.ssl_tls_params

    keyfile_path = sourceobj.parameters.keyfile_path

    cluster_auth_mode = sourceobj.parameters.cluster_auth_mode

    enable_ldap = sourceobj.parameters.enable_ldap
    ldap_params = sourceobj.parameters.ldap_params

    enable_setparams = sourceobj.parameters.enable_setparams
    setparam_params = sourceobj.parameters.setparam_params

    # kmip_params = sourceobj.parameters.kmip_params
    # encryption_keyfile = sourceobj.parameters.encryption_keyfile

    enable_auditlog = sourceobj.parameters.enable_auditlog
    auditlog_params = sourceobj.parameters.auditlog_params

    dbpath = "{}/s0m0".format(mount_path)
    cfgdir = "{}/cfg".format(mount_path)
    logdir = "{}/logs".format(mount_path)
    cfgfile = "{}/dlpx.s0m0.{}.conf".format(cfgdir, mongod_port)
    logfile = "{}/dlpx.s0m0.{}.mongod.log".format(logdir, mongod_port)

    common.cr_dir_structure_replicaset(mount_path, False, rx_connection)

    cmd = "hostname"
    hostname = common.execute_bash_cmd(rx_connection, cmd, {})
    logger.debug("{},{},{},{}".format(dbpath, mongod_port, cfgfile, hostname))

    # cmd = "{} --host {} --username {} --password {} --authenticationDatabase admin --quiet --eval \"db.isMaster().setName\"".format(
    #     sourceobj.mongo_shell_path, src_mongo_host_conn, src_db_user, src_db_password)
    # res = common.execute_bash_cmd(rx_connection, cmd, {})
    # repset_name = res.strip()
    repset_name = sourceobj.parameters.src_replicaset_name
    # logger.debug("repset_name = {}".format(repset_name))

    # Generate replicaset mappings
    common.add_debug_heading_block("Generate replicaset mappings")
    replicaset_config_list = []
    replicaset = False
    replicaset_config_list = common.gen_replicaset_config_list(
        nodes, start_portpool, mount_path, replicaset)

    for replicaset_config in replicaset_config_list:
        logger.info("replicaset_config :{}".format(replicaset_config))

    cmd = "echo \"{}\" > {}/.delphix/.stg_dsourcecfg.txt".format(replicaset_config_list, mount_path)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    cmd = "echo \"DSOURCE_TYPE:{}\" > {}/.delphix/{}".format(dsource_type, mount_path,
                                                             dataset_cfgfile)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    cmd = "echo \"MONGO_DB_USER:{}\" >> {}/.delphix/{}".format(sourceobj.parameters.mongo_db_user, mount_path,
                                                               dataset_cfgfile)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    if source_encrypted:
        cmd = "echo \"SOURCE_ENCRYPTED:{}\" >> {}/.delphix/{}".format("True", mount_path, dataset_cfgfile)
        res = common.execute_bash_cmd(rx_connection, cmd, {})

        cmd = "echo \"ENCRYPTION_METHOD:{}\" >> {}/.delphix/{}".format(encryption_method, mount_path, dataset_cfgfile)
        res = common.execute_bash_cmd(rx_connection, cmd, {})
    else:
        cmd = "echo \"SOURCE_ENCRYPTED:{}\" >> {}/.delphix/{}".format("False", mount_path, dataset_cfgfile)
        res = common.execute_bash_cmd(rx_connection, cmd, {})
    common.add_debug_space()

    cmd = "echo \"Replica Set: {}\" > {}/s0m0/restoreInfo.txt".format(repset_name, mount_path)
    res = common.execute_bash_cmd(rx_connection, cmd, {})

    cmd = "echo \"IGNORE dsPreSnapshot scripts\" > {}/.delphix/NEWDSOURCEFILE.cfg".format(mount_path)
    res = common.execute_bash_cmd(rx_connection, cmd, {})
    common.add_debug_space()
