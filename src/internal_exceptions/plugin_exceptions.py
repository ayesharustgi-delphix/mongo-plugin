#
# Copyright (c) 2020 by Delphix. All rights reserved.
#

#######################################################################################################################
"""
Adding exceptions related to plugin.
"""
#######################################################################################################################

from internal_exceptions.base_exceptions import PluginException


class RepositoryDiscoveryError(PluginException):
    def __init__(self, message=""):
        message = "Not able to search repository information, " + message
        super(RepositoryDiscoveryError, self).__init__(message,
                                                       "Check the MONGO_PATH & MongoDB installation",
                                                       "Failed to search repository information")


# This exception will be raised when failed to find source config
class SourceConfigDiscoveryError(PluginException):
    def __init__(self, message=""):
        message = "Failed to find source config, " + message
        super(SourceConfigDiscoveryError, self).__init__(message,
                                                         "Stop the MongoDB service if it is running",
                                                         "Not able to find source")


class MultipleSyncError(PluginException):
    def __init__(self, message=""):
        message = "Resynchronization is in progress for other dSource, " + message
        super(MultipleSyncError, self).__init__(message,
                                                "Please wait while the other resync operation completes and try again ",
                                                "Staging host already in use. Only Serial operations supported for MongoDB")


class MultipleSnapSyncError(PluginException):
    def __init__(self, message=""):
        message = "SnapSync is running for any other dSource " + message
        super(MultipleSnapSyncError, self).__init__(message,
                                                    "Please wait while the other operation completes and try again ",
                                                    "Staging host already in use for SNAP-SYNC. Only Serial operations supported for MongoDB")


class FileIOError(PluginException):
    def __init__(self, message=""):
        message = "Failed to read/write operation from a file " + message
        super(FileIOError, self).__init__(message,
                                          "Verify the permission",
                                          "Please check the logs for more details")


class MountPathError(PluginException):
    def __init__(self, message=""):
        message = "Failed to create mount path because another file system is already mounted " + message
        super(MountPathError, self).__init__(message,
                                             "Please re-try after the previous operation is completed",
                                             "Please check the logs for more details")


class UnmountFileSystemError(PluginException):
    def __init__(self, message=""):
        message = "Failed to unmount the file system from host in resync operation " + message
        super(UnmountFileSystemError, self).__init__(message,
                                                     "Please try again",
                                                     "Please check the logs for more details")