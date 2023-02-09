# !/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by Delphix. All rights reserved.
#

import os

# from constants import PluginConstants
# from core.logger_lib.logger import LoggingLogger
from utils import plugin_logger
from dlpx.virtualization import libs
from dlpx.virtualization.common import RemoteConnection
from ce_lib.plugin_exception import plugin_error

resource_instances = {}


class Singleton(type):
    """Singleton class for maintaining objects for Resource."""

    def __call__(cls, *args, **kwargs):
        """Verify and create Resource object based on connection object."""
        global resource_instances
        id_var = kwargs.get("connection").environment.reference
        if id_var not in resource_instances:
            resource_instances[id_var] = super(Singleton, cls).__call__(
                *args, **kwargs
            )
        return resource_instances[id_var]


class Resource(metaclass=Singleton):
    """Hold a logger object and execute_bash functions."""

    def __init__(
        self, connection: RemoteConnection, hidden_directory: str
    ) -> None:
        """
        Initialise the Resource object.

        :param connection: Connection object of target host
        :type connection: ``dlpx.virtualization.common.RemoteConnection``
        :param hidden_directory: Hidden directory for a paramater
        :type hidden_directory: ``str``

        :return: None
        :rtype: ``NoneType``
        """
        self.connection = connection
        # pwd_mask_list = [
        #     ("--password ", " "),
        #     ("'cassandra_password':", ","),
        #     ("PASSWORD = '\\''", "'\\''")
        #     # ("AWS_ACCESS_KEY_ID=", "&"),
        #     # ("AWS_SECRET_ACCESS_KEY=", '"'),
        # ]
        # if hidden_directory:
        #     pwd_mask_list.append(
        #         (
        #             os.path.join(
        #                 hidden_directory, PluginConstants.CQL_script_filename
        #             ),
        #             None,
        #         )
        #     )
        self.__logger = plugin_logger.PluginLogger("MONGODB")
        self.cmd_run_block = "=" * 119

    @property
    def logger(self) -> plugin_logger.PluginLogger:
        """
        Return logger protected object.

        :return: A logging.Logger object.
        :rtype: ``core.logger_lib.logger.LoggingLogger``
        """
        return self.__logger

    def execute_bash(
        self,
        cmd: str,
        connection: RemoteConnection = None,
        variables: dict = None,
        raise_exception: bool = True,
    ):
        """
        Execute the cmd with corresponding connection and variables.

        Difference between run_bash and execute_bash is we
        can control the output of each command in a single place.
        Current use case:
        1. Removing extra characters from each command's output.
        2. Print the command if it is fails

        :param cmd: The command which is to be executed.
        :type cmd: ``str``
        :param connection: Target host's connection object
        :type connection: ``dlpx.virtualization.common.RemoteConnection``
        :param variables: Environment variables required for this command.
        :type variables: ``dict``
        :param raise_exception: Whether to raise an exception if command fails
        :type raise_exception: ``bool``

        :returns: Command output
        :rtype: ``com.delphix.virtualization.libs.RunBashResponse``
        """
        self.logger.debug(self.cmd_run_block)
        self.logger.debug("Running command : {}".format(cmd))

        if self.connection is None:
            if connection is None:
                error_string = "Connection object cannot be empty"
                self.logger.exception(error_string)
                raise plugin_error.PluginError(error_string)

        conn = connection or self.connection
        result = libs.run_bash(
            conn, command=cmd, variables=variables, use_login_shell=True
        )

        result.stderr = result.stderr.encode("utf-8")
        result.stdout = result.stdout.encode("utf-8")
        result.stdout = result.stdout.strip()

        self.logger.debug("stdout : {}".format(result.stdout))
        self.logger.debug("exit_code : {}".format(result.exit_code))
        self.logger.debug("stderr : {}".format(result.stderr))

        if result.exit_code != 0 and raise_exception:
            error_string = (
                result.stderr if result.stderr.strip() != "" else result.stdout
            )
            error_string = self.logger.exception(error_string)

            raise plugin_error.CommandExecutionError(msg=error_string)

        self.logger.debug(self.cmd_run_block)
        return result

    def check_and_raise_exception(
        self, cmd_output, cmd: str, error_obj, arg: str = None
    ) -> None:
        """
        Check and raise RunBashResponse error.

        It locates the occurrence of error in command
        execution and raises the error mentioned in error_obj.

        :param cmd_output: Output of the command executed on the host
        :type cmd_output: ``com.delphix.virtualization.libs.RunBashResponse``
        :param cmd: Command that was executed
        :type cmd: ``str``
        :param error_obj: Type of error to be raised
        :param arg: Specific argument required in plugin error.
        :type arg: ``str``

        :return: None
        :rtype: ``NoneType``
        """
        if cmd_output.exit_code != 0:
            err = (
                cmd_output.stderr
                if cmd_output.stderr.strip() != ""
                else cmd_output.stdout
            )

            log_msg = "Error occurred : {} in running command : {}".format(
                cmd_output.stderr, cmd_output.stdout
            )
            self.logger.exception(log_msg)

            if error_obj == plugin_error.FileNotAccessible:
                raise error_obj(err)
            elif (
                error_obj == plugin_error.WriteIntoFileFailed
                or error_obj == plugin_error.CreateFileFailed
                or error_obj == plugin_error.LocationNotValid
                or error_obj == plugin_error.DeleteFileFailed
            ):
                raise error_obj(arg)
            raise error_obj(cmd, err)
