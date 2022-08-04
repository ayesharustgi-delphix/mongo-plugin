#
# Copyright (c) 2020 by Delphix. All rights reserved.
#

from utils import plugin_logger

from dlpx.virtualization import libs
from dlpx.virtualization.libs import exceptions

# logger object
logger = plugin_logger.PluginLogger("MONGODB")


def execute_bash(source_connection, command_name, callback_func=None, environment_vars=None):
    """
    :param callback_func:
    :param source_connection: Connection object for the source environment
    :param command_name: Command to be search from dictionary of bash command
    :param environment_vars: Expecting environment variables which are required to execute the command
    :return: list of output of command, error string, exit code
    """

    if source_connection is None:
        raise exceptions.PluginScriptError("Connection object cannot be empty")

    result = libs.run_bash(source_connection, command=command_name, variables=environment_vars, use_login_shell=True)

    # strip the each part of result to remove spaces from beginning and last of output
    output = result.stdout.strip()
    error = result.stderr.strip()
    exit_code = result.exit_code

    # Verify the exit code of each executed command. 0 means command ran successfully and for other code it is failed.
    # For failed cases we need to find the scenario in which programs will die and otherwise execution will continue.
    _handle_exit_code(exit_code, error, output, callback_func)
    return [output, error, exit_code]


def _handle_exit_code(exit_code, std_err=None, std_output=None, callback_func=None):
    if exit_code == 0:
        return

    else:
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

    error_details = std_output
    if error_details is None or error_details == "":
        error_details = std_err
    raise Exception(error_details)

