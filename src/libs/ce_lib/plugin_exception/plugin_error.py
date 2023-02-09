# !/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (c) 2022 by Delphix. All rights reserved.
#

from dlpx.virtualization.platform.exceptions import UserError

COMMON_ACTION = (
    "Please try again and if the problem persists please"
    " contact Delphix Support."
)


class PluginError(UserError):
    """Initialise and raise PluginError error."""

    def __init__(self, msg=""):
        """Initialise and raise PluginError error."""
        msg = "Observed issue in plugin: " + msg
        super().__init__(msg, COMMON_ACTION)


class VersionError(UserError):
    """Initialise and raise VersionError error."""

    def __init__(self, msg=""):
        """Initialise and raise VersionError error."""
        msg = "Failed to find Cassandra version."
        super().__init__(msg, COMMON_ACTION)


class CommandExecutionError(UserError):
    """Initialise and raise CommandExecutionError error."""

    def __init__(self, msg=""):
        """Initialise and raise CommandExecutionError error."""
        super().__init__(msg, COMMON_ACTION)


class CassandraLocationNotDefinedError(UserError):
    """Initialise and raise CassandraLocationNotDefinedError error."""

    def __init__(self):
        """Initialise and raise CassandraLocationNotDefinedError error."""
        super().__init__(
            "CassandraDB repositories could not be discovered on the host "
        )


class FailedToCreateDirectory(UserError):
    """Initialise and raise FailedToCreateDirectory error."""

    def __init__(self, directory):
        """Initialise and raise FailedToCreateDirectory error."""
        msg = "Failed to create the directory : [{directory}] on host".format(
            directory=directory
        )
        action = (
            "Please check if the user has proper permissions"
            " to create the directory"
        )
        super().__init__(msg, action)


class FailedToProvidePermission(UserError):
    """Initialise and raise FailedToProvidePermission error."""

    def __init__(self, directory):
        """Initialise and raise FailedToProvidePermission error."""
        msg = (
            "Failed to provide permission to the directory : [{directory}]"
            " on host".format(directory=directory)
        )
        action = (
            "Please check if the user can provide the permission to the"
            " directory"
        )
        super().__init__(msg, action)


class LocationNotValid(UserError):
    """Initialise and raise LocationNotValid error."""

    def __init__(self, dir_location):
        """Initialise and raise LocationNotValid error."""
        msg = "Provided Backup Location {dir_path} is not valid".format(
            dir_path=dir_location
        )
        action = (
            "Please check the location exists and has the correct permissions"
        )
        super().__init__(msg, action)


class InvalidInputError(UserError):
    """Initialise and raise InvalidInputError error."""

    def __init__(self, msg=""):
        """Initialise and raise InvalidInputError error."""
        super().__init__(msg)


class CommandFailed(UserError):
    """Initialise and raise CommandFailed error."""

    def __init__(self, cmd, err):
        """Initialise and raise CommandFailed error."""
        msg = 'Failed running command: "{}" with error "{}"'.format(cmd, err)
        super().__init__(msg)


class DsourceFailureError(UserError):
    """Initialise and raise DsourceFailureError error."""

    def __init__(self, msg=""):
        """Initialise and raise DsourceFailureError error."""
        super().__init__(msg)


class VdbFailureError(UserError):
    """Initialise and raise VdbFailureError error."""

    def __init__(self, msg=""):
        """Initialise and raise VdbFailureError error."""
        super().__init__(msg)


class CreateFileFailed(UserError):
    """Initialise and raise CreateFileFailed error."""

    def __init__(self, filename):
        """Initialise and raise CreateFileFailed error."""
        msg = "Failed to the create the file {file}".format(file=filename)
        action = (
            "Please check if Valid permissions are present to create the"
            " file. If the problem persists please contact Delphix"
            " Support."
        )
        super().__init__(msg, action)


class WriteIntoFileFailed(UserError):
    """Initialise and raise WriteIntoFileFailed error."""

    def __init__(self, filename):
        """Initialise and raise WriteIntoFileFailed error."""
        msg = "Failed to write into file: {file}".format(file=filename)
        action = (
            "Please check if valid permissions are present to write into file."
            "If the problem persists, then please contact Delphix Support."
        )
        super().__init__(msg, action)


class MoveFileFailed(UserError):
    """Initialise and raise MoveFileFailed error."""

    def __init__(self, old_file, new_file):
        """Initialise and raise MoveFileFailed error."""
        msg = (
            "Move Command Failed. File to be moved: {old_file}"
            " New File: {new_file}"
        ).format(old_file=old_file, new_file=new_file)
        super().__init__(msg, COMMON_ACTION)


class DeleteFileFailed(UserError):
    """Initialise and raise DeleteFileFailed error."""

    def __init__(self, file_name):
        """Initialise and raise DeleteFileFailed error."""
        msg = (
            "Delete Command Failed. File to be deleted: {file_name}"
        ).format(file_name=file_name)
        super().__init__(msg, COMMON_ACTION)


class MountLocationNotPresent(UserError):
    """Initialise and raise MountLocationNotPresent error."""

    def __init__(self):
        """Initialise and raise MountLocationNotPresent error."""
        msg = "Can't proceed, Mount Location is not present for the dataset."
        action = (
            "If you wish to use this dataset, take a snapshot and try again."
            " Otherwise, force delete the dataset."
        )
        super().__init__(msg, action)


class FileNotAccessible(UserError):
    """Initialise and raise FileNotAccessible error."""

    def __init__(self, err_msg):
        """Initialise and raise FileNotAccessible error."""
        self.msg = err_msg
        self.action = (
            "Please correct the read/execute permission and try again"
        )
        super().__init__(self.msg, self.action)


class InvalidParametersProvided(UserError):
    """Initialise and raise InvalidParametersProvided error."""

    def __init__(self, err_msg):
        """Initialise and raise InvalidParametersProvided error."""
        msg = err_msg
        action = "Please provide the correct parameters and try again."
        super().__init__(msg, action)


class RepositoryNotValid(UserError):
    """Initialise and raise InvalidParametersProvided error."""

    def __init__(self, err_msg):
        """Initialise and raise InvalidParametersProvided error."""
        msg = f"Repository not valid. Please correct and refresh the environment. {err_msg}"
        action = "Please provide the correct parameters and try again."
        super().__init__(msg, action)
