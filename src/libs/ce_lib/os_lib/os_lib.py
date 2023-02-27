# !/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (c) 2022 by Delphix. All rights reserved.
#
import os

from ce_lib.resource import Resource
from ce_lib.plugin_exception import plugin_error


class OSLib:
    """Declare methods to perform host related operations."""

    def __init__(self, resource: Resource):
        """
        Initialise OSLib object.

        :param resource: Resource object
        :type resource: :class:``src.core.core_lib.resource.Resource``
        """
        self.active_process_state = "active (running)"
        self._resource = resource
        self.logger = resource.logger

    def find_running_processes(
        self,
        process_name: str,
        return_count: bool = False,
        grep_params: list = None,
        grep_exclude_params: list = None,
        awk_param: str = None,
    ) -> str:
        """
        Return list of running processes with process_name running on a host.

        :param process_name: Process name to be found
        :type process_name: ``str``
        :param return_count: Boolean value which defines if to get process
                             name from count.
                             1. True if count of processes have to be returned
                             2. False if name of processes have to be returned
        :type return_count: ``boolean``
        :param grep_params: additional parameters for grep command
        :type grep_params: ``list``
        :param grep_exclude_params: exclude parameters in grep command
        :type grep_exclude_params: ``list``
        :param awk_param: awk param to print result in a particular format
        :type awk_param: ``str``

        :return: List/count of cassandra processes
        :rtype: ``str``
        """
        cmd_list = [
            "ps -eaf | grep {process_name}".format(process_name=process_name)
        ]
        if grep_params:
            for p in grep_params:
                cmd_list.append(f"| grep {p}")
        if grep_exclude_params:
            for p in grep_exclude_params:
                cmd_list.append(f"| grep -v {p}")
        if return_count:
            cmd_list.append("| grep -iv grep | wc -l")
        else:
            cmd_list.append("| { grep -iv grep || true; }")

        if awk_param:
            cmd_list.append(f"| awk '{{print {awk_param}}}'")

        command = " ".join(cmd_list)
        output = self._resource.execute_bash(
            cmd=command, raise_exception=False
        )
        self._resource.check_and_raise_exception(
            output, command, plugin_error.CommandFailed
        )
        return output.stdout

    def read_environment_variable(self, env_var: str) -> str:
        """
        Return the content of environment variable defined on the host.

        :param env_var: Environment variable to read
        :type env_var: ``str``

        :return: Value stored in this variable
        :rtype: ``str``
        """
        command = "echo ${variable}".format(variable=env_var)
        output = self._resource.execute_bash(
            cmd=command, raise_exception=False
        )
        self._resource.check_and_raise_exception(
            output, command, plugin_error.CommandFailed
        )
        return output.stdout

    def cat_file(self, file_path: str) -> str:
        """
        Return the content of given filename.

        :param file_path: Absolute file path
        :type file_path: ``str``

        :return: Contents of file
        :rtype: ``str``
        """
        command = "cat {file_path}".format(file_path=file_path)
        output = self._resource.execute_bash(
            cmd=command, raise_exception=False
        )
        self._resource.check_and_raise_exception(
            output, command, plugin_error.FileNotAccessible
        )
        return output.stdout.strip()

    def make_directory(self, folder_name: str) -> None:
        """
        Create folder.

        :param folder_name: Absolute folder path
        :type folder_name: ``str``

        :return: None
        :rtype: ``NoneType``
        """
        command = "mkdir -p {folder_name}".format(folder_name=folder_name)
        output = self._resource.execute_bash(
            cmd=command, raise_exception=False
        )
        self._resource.check_and_raise_exception(
            output, command, plugin_error.CommandFailed
        )

    def find_binary_location(self, bin_name: str) -> str:
        """
        Return the location of binary.

        :param bin_name: Name of binary of interest
        :type bin_name: ``str``

        :return: Location of binary
        :rtype: ``str``
        """
        command = "which {variable}".format(variable=bin_name)
        output = self._resource.execute_bash(
            cmd=command, raise_exception=False
        )
        self._resource.check_and_raise_exception(
            output, command, plugin_error.CommandFailed
        )
        return output.stdout

    def dump_to_file(
        self,
        content: str,
        file_path: str,
        append_to_file: bool = False,
        file_permissions: str = None,
    ):
        """
        Add given data into given filename.

        :param content: Data to add into file
        :type content: ``str``
        :param file_path: File location on host
        :type file_path: ``str``
        :param append_to_file: Boolean to specify if content has to be
                                appended to the file
        :type append_to_file: ``bool``
        :param file_permissions: Permissions of the file to write
        :type file_permissions: ``str``

        :return: execute_bash result object
        :rtype ``com.delphix.virtualization.libs.RunBashResponse``
        """
        cmd_template = ""
        if file_permissions:
            cmd_template = "umask {perm}; ".format(perm=file_permissions)

        if ("*" in file_path) or ("~" in file_path) or ("$" in file_path):
            cmd_template += "echo -e '{content}' {operator} {file_path}"
        else:
            cmd_template += "echo -e '{content}' {operator} '{file_path}'"

        dump_operator = ">"
        if append_to_file:
            dump_operator = ">>"
            content = "\n" + content

        cmd = cmd_template.format(
            content=content, operator=dump_operator, file_path=file_path
        )
        output = self._resource.execute_bash(cmd=cmd, raise_exception=False)
        if output.exit_code != 0:
            if append_to_file:
                self._resource.check_and_raise_exception(
                    output, cmd, plugin_error.WriteIntoFileFailed, file_path
                )
            else:
                self._resource.check_and_raise_exception(
                    output, cmd, plugin_error.CreateFileFailed, file_path
                )
        return output

    def check_file_dir_exists(
        self, path: str, is_directory: bool = False
    ) -> bool:
        """
        Check if the file exists.

        :param path: Comprises of the file name/directory name and path of
                     the file to be checked.
        :type path: ``str``
        :param is_directory: Contains the information whether the check needs
                             to be done for a file or directory.
        :type is_directory: ``boolean``

        :return: Return True if file is present else return False
        :rtype: ``boolean``
        """
        if is_directory:
            check_operator = "d"
        else:
            check_operator = "f"

        if ("*" in path) or ("~" in path) or ("$" in path):
            cmd_template = (
                "if [ -{check_operator} {path} ]; "
                "then echo 'True'; else echo 'False'; fi"
            )
        else:
            cmd_template = (
                "if [ -{check_operator} '{path}' ]; "
                "then echo 'True'; else echo 'False'; fi"
            )

        cmd = cmd_template.format(check_operator=check_operator, path=path)
        output = self._resource.execute_bash(cmd=cmd, raise_exception=False)
        self._resource.check_and_raise_exception(
            output, cmd, plugin_error.CommandFailed
        )
        return bool(output.stdout == "True")

    def check_permissions(
        self, path: str, option: str, is_sudo: bool = False
    ) -> None:
        """
        Check permissions of the file path provided.

        :param path: Path of directory/file to check
        :type path: ``str``
        :param option: type of permission to check. [w for write, r for read]
        :type option: ``str``
        :param is_sudo: The type of permission to check.
        :type is_sudo: ``bool``

        :return: None
        :rtype: ``NoneType``
        """
        cmd_list = ["test -{option} {path}".format(option=option, path=path)]
        if is_sudo:
            cmd_list = ["sudo"] + cmd_list

        cmd = " ".join(cmd_list)
        cmd_res = self._resource.execute_bash(cmd=cmd, raise_exception=False)
        self._resource.check_and_raise_exception(
            cmd_res, cmd, plugin_error.LocationNotValid, path
        )

    def get_disk_filesystem(self, dir_name: str):
        """
        Return disk filesystem structure of the host.

        :param dir_name: Directory Name for status
        :type dir_name: ``str``

        :return: Command output
        :rtype: ``com.delphix.virtualization.libs.RunBashResponse``
        """
        cmd = f"du -sh {dir_name}"
        cmd_res = self._resource.execute_bash(cmd=cmd, raise_exception=False)

        return cmd_res

    def unmount_filesystem(self, mount_location: str) -> None:
        """
        Unmounts filesystem mounted on mount_location provided.

        :param mount_location: absolute path of the mounted filesystem.
        :type mount_location: ``str``

        :return: None
        :rtype: ``NoneType``
        """
        cmd = "sudo umount {}".format(mount_location)
        cmd_res = self._resource.execute_bash(cmd=cmd, raise_exception=False)
        self._resource.check_and_raise_exception(
            cmd_res, cmd, plugin_error.CommandFailed
        )

    def get_ipaddr(self) -> str:
        """
        Fetch IP_address of the specified host.

        :return: ip_addr of host
        :rtype: ``str``
        """
        cmd = "hostname -I"
        ipaddr = self._resource.execute_bash(cmd=cmd, raise_exception=False)
        return ipaddr.stdout

    def os_info(self) -> str:
        """
        Fetch os_info of the specified host.

        :return: os info of host
        :rtype: ``str``
        """
        cmd = 'echo "$(uname):$(uname -p):$(cat /etc/redhat-release)"'
        cmd_res = self._resource.execute_bash(cmd=cmd, raise_exception=False)
        self._resource.check_and_raise_exception(
            cmd_res, cmd, plugin_error.CommandFailed
        )

        return cmd_res.stdout.strip()

    def systemctl_reload_service(self) -> None:
        """
        Reload systemd manager configuration.

        :return: None
        :rtype: ``NoneType``
        """
        cmd = "sudo systemctl daemon-reload"
        cmd_res = self._resource.execute_bash(cmd=cmd, raise_exception=False)
        self._resource.check_and_raise_exception(
            cmd_res, cmd, plugin_error.CommandFailed
        )

    def systemctl_list_unit_files(self, service: str) -> None:
        """
        List systemctl unit-files corresponding to service provided.

        :param service: The service name which is to be listed.
        :type service: ``str``

        :return: None
        :rtype: ``NoneType``
        """
        cmd = "sudo systemctl list-unit-files {service}".format(
            service=service
        )
        cmd_res = self._resource.execute_bash(cmd=cmd, raise_exception=False)
        self._resource.check_and_raise_exception(
            cmd_res, cmd, plugin_error.CommandFailed
        )

    def systemctl_start_service(self, service: str) -> None:
        """
        Start the systemctl service provided.

        :param service: The service name which is to be started.
        :type service: ``str``

        :return: None
        :rtype: ``NoneType``
        """
        cmd = "sudo systemctl restart {service_name}".format(
            service_name=service
        )
        cmd_res = self._resource.execute_bash(cmd=cmd, raise_exception=False)
        self._resource.check_and_raise_exception(
            cmd_res, cmd, plugin_error.CommandFailed
        )

    def systemctl_stop_service(self, service: str) -> None:
        """
        Stop the systemctl service provided.

        :param service: The service name which is to be stopped.
        :type service: ``str``

        :return: None
        :rtype: ``NoneType``
        """
        cmd = "sudo systemctl stop {service_name}".format(service_name=service)
        cmd_res = self._resource.execute_bash(cmd=cmd, raise_exception=False)
        self._resource.check_and_raise_exception(
            cmd_res, cmd, plugin_error.CommandFailed
        )

    def systemctl_status_service(self, service: str) -> bool:
        """
        Return status systemctl service provided.

        :param service: The service name whose status has to be found
        :type service: ``str``

        :return: True if status is ACTIVE and False if INACTIVE/DEAD
        :rtype: ``bool``
        """
        cmd = "sudo systemctl status {service_name}".format(
            service_name=service
        )
        cmd_res = self._resource.execute_bash(cmd=cmd, raise_exception=False)
        self.logger.debug("cmd_res of Cassandra status: {}".format(cmd_res))
        self._resource.check_and_raise_exception(
            cmd_res, cmd, plugin_error.CommandFailed
        )
        if self.active_process_state in cmd_res.stdout:
            return True
        else:
            return False

    def service_link(
        self, service_src_loc: str, service_dest_loc: str
    ) -> None:
        """
        Create a softlink between service_src_loc and service_dest_loc.

        :param service_src_loc: src service file location
        :type service_src_loc: ``str``
        :param service_dest_loc: dest service file location
        :type service_dest_loc: ``str``

        :return: None
        :rtype: ``NoneType``
        """
        cmd = "sudo ln -s {src_loc} {dest_loc}".format(
            src_loc=service_src_loc, dest_loc=service_dest_loc
        )
        cmd_res = self._resource.execute_bash(cmd=cmd, raise_exception=False)
        self._resource.check_and_raise_exception(
            cmd_res, cmd, plugin_error.CommandFailed
        )

    def service_unlink(self, service_loc: str) -> None:
        """
        Unlink the service provided.

        :param service_loc: service file location
        :type service_loc: ``str``

        :return: None
        :rtype: ``NoneType``
        """
        cmd = "sudo unlink {src_loc}".format(src_loc=service_loc)
        cmd_res = self._resource.execute_bash(cmd=cmd, raise_exception=False)
        self._resource.check_and_raise_exception(
            cmd_res, cmd, plugin_error.CommandFailed
        )

    def list_files(
        self,
        path: str,
        is_directory: bool = False,
        count_files: bool = False,
        postfix: str = None,
        list_all_files: bool = False,
    ) -> str:
        """
        List files corresponding to a directory or pattern.

        :param path: Path of file/directory.
        :type path: ``str``
        :param is_directory: Path specified is directory or not
                             [True if directory, False if not]
        :type is_directory: ``boolean``
        :param count_files: return list of files or count of files
                            [True if file count is needed,
                            False if list of names is needed]
        :type count_files: ``boolean``
        :param postfix: postfix pattern specified for matching. [default=None]
        :type postfix: ``str``
        :param list_all_files: True if all files have to be listed including
                                hidden files
        :type list_all_files: ``bool``

        :return: list/ count of matching files found
        :rtype: ``str``
        """
        if list_all_files:
            list_param = "-a"
        else:
            list_param = ""
        cmd_list = ["ls {p} {path}".format(p=list_param, path=path)]

        if not is_directory:
            cmd_list.append("*")
            if postfix:
                cmd_list.append(postfix)
        else:
            cmd_list.append("/")
            if postfix:
                cmd_list.append("*" + postfix)

        if count_files:
            cmd_list.append(" | wc -l")

        cmd = "".join(cmd_list)
        cmd_res = self._resource.execute_bash(cmd=cmd, raise_exception=False)
        self._resource.check_and_raise_exception(
            cmd_res, cmd, plugin_error.CommandFailed
        )
        return cmd_res.stdout

    def delete_file(
        self, file_path: str, is_directory: bool = False, force: bool = True
    ):
        """
        Delete file or directory.

        :param file_path: File location
        :type file_path: ``str``
        :param is_directory: Location is file or directory
        :type is_directory: ``bool``
        :param force: Forcefully perform delete operation
        :type force: ``bool``

        :return: execute_bash result object
        :rtype ``com.delphix.virtualization.libs.RunBashResponse``
        """
        command = "rm {directory}{force}{file_path}".format(
            directory=" -r " if is_directory else "",
            force=" -f " if force else "",
            file_path=file_path,
        )
        cmd_res = self._resource.execute_bash(
            cmd=command, raise_exception=False
        )
        self._resource.check_and_raise_exception(
            cmd_res, command, plugin_error.DeleteFileFailed, file_path
        )
        return cmd_res

    def get_hostname(self) -> str:
        """
        Run command to find hostname of specified host.

        :return: hostname
        :rtype: ``str``
        """
        cmd = "hostname"
        cmd_res = self._resource.execute_bash(cmd=cmd, raise_exception=False)
        self._resource.check_and_raise_exception(
            cmd_res, cmd, plugin_error.CommandFailed
        )
        return cmd_res.stdout.strip()

    def find_pid(self, directory: str) -> str:
        """
        Return the PID for active Cassandra Process.

        :param directory: Cassandra data directory
        :type directory: ``str``

        :return: process_id of active cassandra process
        :rtype ``str``
        """
        command = "pgrep -f {directory}".format(directory=directory)
        pid = self._resource.execute_bash(
            cmd=command, raise_exception=False
        ).stdout.strip()
        return pid

    def process_kill(self, process_id: str, option: str):
        """
        Kill the specified process_id with the options provided.

        kill <option> <process_id>

        :param process_id: Process id that needs to be killed
        :type process_id: str
        :param option: Option to kill command
        :type option: str

        :return: execute_bash result object
        :rtype ``com.delphix.virtualization.libs.RunBashResponse``
        """
        cmd = "kill {option} {process_id}".format(
            option=option, process_id=process_id
        )
        cmd_res = self._resource.execute_bash(cmd=cmd, raise_exception=False)
        self._resource.check_and_raise_exception(
            cmd_res, cmd, plugin_error.CommandFailed
        )
        return cmd_res

    def get_host_datetime(self) -> str:
        """
        Return system datetime for the host.

        :return: system datetime
        :rtype: ``str``
        """
        cmd = "date '+%Y-%m-%d %H:%M:%S'"
        cmd_res = self._resource.execute_bash(cmd=cmd, raise_exception=False)
        self._resource.check_and_raise_exception(
            cmd_res, cmd, plugin_error.CommandFailed
        )
        return cmd_res.stdout

    def get_file_create_time(self, file_path: str) -> str:
        """
        Return file creation time for the file_path mentioned.

        :param file_path: Absolute path of the file
        :type file_path: ``str``

        :return: datetime of file creation
        :rtype: ``str``
        """
        cmd = "stat -c %y {}".format(file_path)
        cmd_res = self._resource.execute_bash(cmd=cmd, raise_exception=False)
        self._resource.check_and_raise_exception(
            cmd_res, cmd, plugin_error.CommandFailed
        )
        return cmd_res.stdout

    def check_port_available(self, port: int) -> bool:
        """
        Check if the provided port is available at the host.

        :param port: port number
        :type port: ``int``

        :return: Boolean value signifying availability of port
        :rtype: ``bool``
        """
        # noinspection PyBroadException
        try:
            self.find_binary_location("netstat")
            binary_exist = True
        except:  # noqa: E722
            binary_exist = False

        if binary_exist:
            binary = "netstat"
        else:
            binary = "ss"
        command = (
            "{binary} -tulnp 2>/dev/null | grep -w "
            "'{port}' | wc -l".format(binary=binary, port=port)
        )

        cmd_res = self._resource.execute_bash(command, raise_exception=False)
        self._resource.check_and_raise_exception(
            cmd_res, command, plugin_error.CommandFailed
        )
        if int(cmd_res.stdout) > 0:
            self.logger.debug(
                "Port: {port} is not available to use".format(port=port)
            )
            return False
        else:
            self.logger.debug(
                "Port: {port} is available " "to use".format(port=port)
            )
            return True

    def move_file(self, old_file_path: str, new_file_path: str) -> None:
        """
        Move the files from one location to another.

        :param old_file_path: Source path
        :type old_file_path: ``str``
        :param new_file_path: Destination path
        :type new_file_path: ``str``

        :return: None
        :rtype: ``NoneType``
        """
        command = "mv {old} {new}".format(old=old_file_path, new=new_file_path)
        cmd_res = self._resource.execute_bash(
            cmd=command, raise_exception=False
        )
        self._resource.check_and_raise_exception(
            cmd_res, command, plugin_error.CommandFailed
        )

    def copy_binaries(self, old_bin_path: str, new_bin_path: str) -> None:
        """
        Copy the cassanda binaries from one location to another.

        :param old_bin_path: Source path
        :type old_bin_path: ``str``
        :param new_bin_path: Destination path
        :type new_bin_path: ``str``

        :return: None
        :rtype: ``NoneType``
        """
        command = "cp -r {old} {new}".format(
            old=old_bin_path, new=new_bin_path
        )
        cmd_res = self._resource.execute_bash(
            cmd=command, raise_exception=False
        )
        self._resource.check_and_raise_exception(
            cmd_res, command, plugin_error.CommandFailed
        )

    def add_ipaddr(self, ip_addr: str) -> None:
        """
        Add IP address in staging/target host.

        :param ip_addr: ip address to be added
        :type ip_addr: ``str``

        :return: None
        :rtype: ``NoneType``
        """
        # Verify the network interface attached.
        check1 = "{print $1}"
        check2 = "{print $2}"

        # find interface that has same subnet of IP address provided.
        # e.g. if ip=192.168.1.10 , find interface with 192.168.1.*
        command = (
            f"ip -o addr show | grep {ip_addr.rsplit('.', 1)[0]} "
            f"| awk '{check2}'"
        )
        output = self._resource.execute_bash(
            cmd=command, raise_exception=False
        )
        interface = output.stdout
        if interface:
            # select first interface from list of interfaces found.
            interface = interface.split("\n")[0]
        else:
            # if no interfaces are found with same subnet, select any one
            # interface out of the ones available except "lo"
            command = (
                f"ip link show | grep -v lo | awk -F': ' 'NF > 1 {check2}'"
            )
            output = self._resource.execute_bash(
                cmd=command, raise_exception=False
            )
            interface = output.stdout.split("\n")[0]

        # Find IP size block of the interface selected.
        command = (
            f"ip addr | grep {interface} | grep inet | awk -F'/' "
            f"'{check2}' | awk -F' ' '{check1}' | sort | uniq"
        )
        output = self._resource.execute_bash(
            cmd=command, raise_exception=False
        )
        ip_size_block = output.stdout.split("\n")[0]

        # Add new IP Addr
        command = f"sudo ip addr add {ip_addr}/{ip_size_block} dev {interface}"
        cmd_res = self._resource.execute_bash(
            cmd=command, raise_exception=False
        )
        self._resource.check_and_raise_exception(
            cmd_res, command, plugin_error.CommandFailed
        )

    def replace_string_in_file(
        self, old_string: str, new_string: str, file_path: str
    ) -> None:
        """
        Replace string patterns with new string.

        :param old_string: pattern to edit
        :type old_string: ``str``
        :param new_string: line to update
        :type new_string: ``str``
        :param file_path: path of file to be edited
        :type file_path: ``str``

        :return: None
        :rtype: ``NoneType``
        """
        if '"' in old_string or '"' in new_string:
            command = f"sed -i 's@{old_string}@{new_string}@'  {file_path}"
        else:
            command = f'sed -i "s@{old_string}@{new_string}@"  {file_path}'

        cmd_res = self._resource.execute_bash(
            cmd=command, raise_exception=False
        )
        self._resource.check_and_raise_exception(
            cmd_res, command, plugin_error.CommandFailed
        )

    def replace_string_in_file_with_newline(
        self, old_string: str, new_string: str, file_path: str
    ) -> None:
        """
        Replace string patterns containing newline with new string.

        :param old_string: pattern to edit
        :type old_string: ``str``
        :param new_string: line to update
        :type new_string: ``str``
        :param file_path: path of file to be edited
        :type file_path: ``str``

        :return: None
        :rtype: ``NoneType``
        """
        command = (
            f"sed -i '/{old_string}/{{n;s@.*@{new_string}@}}' {file_path}"
        )
        cmd_res = self._resource.execute_bash(
            cmd=command, raise_exception=False
        )
        self._resource.check_and_raise_exception(
            cmd_res, command, plugin_error.CommandFailed
        )

    def delete_string_with_pattern_in_file(
        self, pattern: str, file_path: str
    ) -> None:
        """
        Delete lines of a pattern and empty lines from a file.

        :param pattern: pattern to delete
        :type pattern: ``str``
        :param file_path: path of file to be edited
        :type file_path: ``str``

        :return: None
        :rtype: ``NoneType``
        """
        command = (
            f"sed '/^{pattern}/d' {file_path} | awk 'NF' > "
            f"{file_path}.tmp && mv {file_path}.tmp {file_path}"
        )
        cmd_res = self._resource.execute_bash(
            cmd=command, raise_exception=False
        )
        self._resource.check_and_raise_exception(
            cmd_res, command, plugin_error.CommandFailed
        )

    def extract_tar(self, tar_path: str, destination_path: str) -> None:
        """
        Extract tar file.

        :param tar_path: path of tar to be extracted
        :type tar_path: ``str``
        :param destination_path: destination folder path of extracted data
        :type destination_path: ``str``

        :return: None
        :rtype: ``NoneType``
        """
        command = (
            f"tar -{'z' if tar_path.endswith('.tar.gz') else ''}xf "
            f"{tar_path} -C {destination_path} --strip-components 1"
        )
        cmd_res = self._resource.execute_bash(
            cmd=command, raise_exception=False
        )
        self._resource.check_and_raise_exception(
            cmd_res, command, plugin_error.CommandFailed
        )

    def list_directories(self, folder_path: str) -> str:
        """
        List all directories in a folder.

        :param folder_path: Folder path
        :type folder_path: ``str``

        :return: String containing all directories in a folder
        :rtype: ``str``
        """
        command = (
            f"find {os.path.join(folder_path,'*')} -maxdepth 0 "
            f"-type d -printf '%f\n'"
        )
        cmd_res = self._resource.execute_bash(
            cmd=command, raise_exception=False
        )
        self._resource.check_and_raise_exception(
            cmd_res, command, plugin_error.CommandFailed
        )
        return cmd_res.stdout

    def get_ip_addr_list(self) -> str:
        """
        List all IP addresses in a host.

        :return: list of IP addresses
        :rtype: ``str``
        """
        cmd_grp = "(?<=inet ).*(?=/)"
        command = f"ip addr show  | grep -oP '{cmd_grp}'"
        cmd_res = self._resource.execute_bash(
            cmd=command, raise_exception=False
        )
        self._resource.check_and_raise_exception(
            cmd_res, command, plugin_error.CommandFailed
        )
        return cmd_res.stdout

    def readlink_file_name(self, pid: int) -> str:
        """
        Return canonical file or directory path associated with pid.

        :param pid: PID of process
        :type pid: ``int``

        :return: directory or file path
        :rtype: ``str``
        """
        command = f"readlink /proc/{pid}/cwd"
        cmd_res = self._resource.execute_bash(
            cmd=command, raise_exception=False
        )
        return cmd_res.stdout

    def get_binary_version(self, binary_path: str) -> str:
        """
        Return version of the binary provided.

        :param binary_path: Path of binary
        :type binary_path: ``str``

        :return: version of Binary
        :rtype: str
        """
        command = f"{binary_path} --version"
        cmd_res = self._resource.execute_bash(
            cmd=command, raise_exception=False
        )
        self._resource.check_and_raise_exception(
            cmd_res, command, plugin_error.CommandFailed
        )
        return cmd_res.stdout

