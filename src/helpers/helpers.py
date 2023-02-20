#
# Copyright (c) 2019 by Delphix. All rights reserved.
#
from utils import plugin_logger
import posixpath
import random
from datetime import datetime

from dlpx.virtualization import libs

logger = plugin_logger.PluginLogger("MONGODB")


def _record_hook(hook_name, connection):
    logger.info(f'Running {hook_name}')
    libs.run_bash(connection, "echo '{}:{}' >> {}".format(
        datetime.now(), "Running {}".format(hook_name),
        posixpath.join("/var/tmp", "pythonStaging.log")))


def _set_running(connection, guid):
    libs.run_bash(connection, "echo {} >> /var/tmp/running-{}".format(
        random.random(), guid))


def _set_stopped(connection, guid):
    libs.run_bash(connection, "rm -f /var/tmp/running-{}".format(guid))