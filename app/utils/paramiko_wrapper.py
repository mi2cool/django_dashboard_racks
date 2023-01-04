from __future__ import annotations

import os
import re
import sys
from stat import S_ISDIR, S_ISREG
from typing import Iterable

import paramiko

import logging

sftp_instances = {}  # {'hostname' : SftpApiInstance}

logger = logging.getLogger('paramiko_wrapper')

DEFAULT_PATH_SEP = "/"

NOT_CONNECTED_ERROR = "Not connected to the SFTP server. Try initialising the SftpApi again."
COPY_FROM_REMOTE_ERROR = "Could not copy remote file '{0}' to local path '{1}'."
COPY_FROM_LOCAL_ERROR = "Could not copy local file '{0}' to remote path '{1}'."
MKDIR_REMOTE_ERROR = "Could not create directory '{0}' on remote system."
MKDIR_LOCAL_ERROR = "Could not create directory '{0}' on local system."
DELETE_FROM_REMOTE_ERROR = "Could not delete remote file '{0}'."
NO_FILE_MATCHING_ERROR = "No file matching pattern '{0}' in remote directory '{1}'."
FUNCTION_ABORTED = "{0} aborted."
CONTINUING = "Continuing with other directory entries."
IO_ERROR = "IO Error: {0}"
OS_ERROR = "OS Error: {0}"
IO_OS_ERROR = "IO/OS Error: {0}"
SSH_EXCEPTION = "SSHException: {0}"


def get_sftp_instance_by_hostname(hostname, username, password, private_key=None, port=22):
    global sftp_instances
    return (
        SftpApi(
            remote_ip=hostname,
            username=username,
            password=password,
            private_key=private_key or '',
            port=port,
        )
        if hostname not in sftp_instances.keys()
        else sftp_instances.get(hostname)
    )


def _create_local_dir(local_dir: str, calling_function: str) -> bool:
    """
    Creates the given local directory if it does not exist.
    :param local_dir:        Local directory.
    :param calling_function: Name of the function calling this function for error logging.
    :return: True, if the operation was successful. False, if at least one Error has occurred.
    """
    if not os.path.exists(local_dir):
        try:
            os.makedirs(local_dir)
        except OSError as err:
            logger.warning(MKDIR_LOCAL_ERROR.format(local_dir))
            logger.warning(OS_ERROR.format(err))
            logger.warning(FUNCTION_ABORTED.format(calling_function))
            return False
    return True


class SftpApi:
    _ssh: paramiko.SSHClient | None
    _sftp: paramiko.SFTPClient | None

    def __init__(self, remote_ip: str, username: str = "", password: (str | None) = None,
                 private_key: (str | None) = None, port: int = 22):
        """
        Initialises the SftpApi, tries to establish a connection with the SSH/SFTP server.
        :param remote_ip:   Host IP.
        :param username:    SSH username.
        :param password:    SSH password (leave None if you use a private key file).
        :param private_key: SSH private key file (leave None if you use a password).
        :param port:        SSH port.
        """
        self._ssh = None
        self._sftp = None
        self.private_key = private_key
        self.remote_ip = remote_ip
        self.username = username
        self.password = password
        self.port = port

    def connect(self):
        try:
            self._ssh = paramiko.SSHClient()
            self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
            if not self.private_key:  # use password
                self._ssh.connect(hostname=self.remote_ip, username=self.username, password=self.password, port=self.port,
                                  disabled_algorithms=dict(pubkeys=["rsa-sha2-512", "rsa-sha2-256"]))
            else:  # use private key file
                key = paramiko.RSAKey.from_private_key_file(self.private_key)
                self._ssh.connect(hostname=self.remote_ip, username=self.username, pkey=key, port=self.port,
                                  disabled_algorithms=dict(pubkeys=["rsa-sha2-512", "rsa-sha2-256"]))
            self._sftp = self._ssh.open_sftp()
        except paramiko.SSHException as e:
            logger.warning(SSH_EXCEPTION.format(e))

    @property
    def is_connected(self):
        if self._ssh and self._ssh.get_transport() is not None:
            return self._ssh.get_transport().is_active()
        else:
            return False

    def __del__(self):
        """
        Closes the SFTP and SSH connections.
        """
        if self._sftp is not None:
            self._sftp.close()
        if self._ssh is not None:
            self._ssh.close()

    def copy_file_to_remote(self, remote_path: str, local_path: str) -> bool:
        """
        Copies a local file to the remote system.
        :param remote_path: Destination path on the remote system (including file name and file ending!).
        :param local_path:  Path to the file on the local system.
        :return True, if the operation was successful. False, if at least one Error has occurred.
        """
        sftp = self._check_sftp(self.copy_file_to_remote.__name__)
        if sftp is None:
            return False

        try:
            sftp.put(localpath=local_path, remotepath=remote_path)
            return True
        except (IOError, OSError) as err:
            logger.warning(COPY_FROM_LOCAL_ERROR.format(local_path, remote_path))
            logger.warning(IO_OS_ERROR.format(err))
            return False

    def copy_file_from_remote(self, remote_path: str, local_path: str) -> bool:
        """
        Copies a remote file to the local system.
        :param remote_path: Path to the file on the remote system.
        :param local_path:  Destination path on the local system (including file name and file ending!).
        :return True, if the operation was successful. False, if at least one Error has occurred.
        """
        sftp = self._check_sftp(self.copy_file_from_remote.__name__)
        if sftp is None:
            return False

        if not _create_local_dir(os.path.dirname(local_path), self.copy_file_from_remote.__name__):
            return False

        try:
            local_file_path = os.path.abspath(os.path.join(local_path, os.path.basename(remote_path)))
            sftp.get(remotepath=remote_path, localpath=local_file_path)
        except IOError as err:
            logger.warning(COPY_FROM_REMOTE_ERROR.format(remote_path, local_path))
            logger.warning(IO_ERROR.format(err))
            return False
        return True

    def copy_dir_to_remote(self, remote_dir: str, local_dir: str, remote_path_sep: str = DEFAULT_PATH_SEP,
                           ignore_regex: (Iterable[re.Pattern] | Iterable[str] | None) = None) -> bool:
        """
        Recursively copies a local directory to the remote system.
        :param remote_dir:      Remote destination path for the copy operation.
        :param local_dir:       Path to the local directory to be copied.
        :param remote_path_sep: Path separator symbol ('/' for Linux/Unix/Mac, '\\' for Windows).
        :param ignore_regex:    Local files/directories whose base name matches any of the regular expressions in
                                ignore_regex are ignored.
        :return True, if the operation was successful. False, if at least one Error has occurred.
        """
        sftp = self._check_sftp(self.copy_dir_to_remote.__name__)
        if sftp is None:
            return False

        if ignore_regex is None:
            ignore_regex = []

        if not self.exists(remote_dir):
            try:
                sftp.mkdir(remote_dir)
            except OSError as err:
                logger.warning(MKDIR_REMOTE_ERROR.format(remote_dir))
                logger.warning(OS_ERROR.format(err))
                logger.warning(FUNCTION_ABORTED.format(self.copy_dir_to_remote.__name__))
                return False

        if any(re.match(regex, os.path.basename(local_dir)) for regex in ignore_regex):
            return True

        success = True
        for entry in os.listdir(local_dir):
            remote_path = remote_dir + remote_path_sep + entry
            local_path = os.path.join(local_dir, entry)

            if any(re.match(regex, os.path.basename(local_path)) for regex in ignore_regex):
                continue

            if not os.path.isfile(local_path):
                if not self.exists(remote_path):
                    try:
                        sftp.mkdir(remote_path)
                    except OSError as err:
                        logger.warning(MKDIR_REMOTE_ERROR.format(remote_path))
                        logger.warning(OS_ERROR.format(err))
                        logger.warning(CONTINUING)
                        success = False
                        continue
                self.copy_dir_to_remote(remote_path, local_path, remote_path_sep, ignore_regex)
            else:
                success = self.copy_file_to_remote(remote_path, local_path) and success

        return success

    def copy_dir_from_remote(self, remote_dir: str, local_dir: str, remote_path_sep: str = DEFAULT_PATH_SEP,
                             ignore_regex: (Iterable[re.Pattern] | Iterable[str] | None) = None) -> bool:
        """
        Recursively copies a remote directory to the local system.
        :param remote_dir:      Remote destination path for the copy operation.
        :param local_dir:       Path to the local directory to be copied.
        :param remote_path_sep: Path separator symbol ('/' for Linux/Unix/Mac, '\\' for Windows).
        :param ignore_regex:    Remote files/directories whose base name matches any of the regular expressions in
                                ignore_regex are ignored.
        :return True, if the operation was successful. False, if at least one Error has occurred.
        """
        sftp = self._check_sftp(self.copy_dir_from_remote.__name__)
        if sftp is None:
            return False

        if ignore_regex is None:
            ignore_regex = []

        if not _create_local_dir(local_dir, self.copy_dir_from_remote.__name__):
            return False

        if any(re.match(regex, remote_dir.rsplit(remote_path_sep)[0]) for regex in ignore_regex):
            return True

        success = True
        for entry in sftp.listdir_attr(remote_dir):
            remote_path = remote_dir + remote_path_sep + entry.filename
            local_path = os.path.join(local_dir, entry.filename)

            if any(re.match(regex, entry.filename) for regex in ignore_regex):
                continue

            if self.is_dir(remote_path):
                try:
                    os.mkdir(local_path)
                except OSError as err:
                    logger.warning(MKDIR_LOCAL_ERROR.format(local_path))
                    logger.warning(OS_ERROR.format(err))
                    logger.warning(CONTINUING)
                    success = False
                    continue
                self.copy_dir_from_remote(remote_path, local_path, remote_path_sep, ignore_regex)
            elif self.is_file(remote_path):
                success = self.copy_file_from_remote(remote_path, local_path) and success

        return success

    def copy_pattern_from_remote(self, remote_dir: str, local_dir: str, remote_regex: re.Pattern | str,
                                 remote_path_sep: str = DEFAULT_PATH_SEP) -> bool:
        """
        Copies all files in a given directory on the remote system that match the given regular expression to the given
        local directory, preserving file names.
        Note: Only considers the files in the specific directory, not in any subdirectories.
        :param remote_dir:      Path to the remote directory with the files to be copied.
        :param local_dir:       Local destination path for the copy operation.
        :param remote_regex:    Regular expression for the files to be copied.
        :param remote_path_sep: Path separator symbol ('/' for Linux/Unix/Mac, '\\' for Windows).
        :return: True, if the operation was successful. False, if at least one Error has occurred.
        """
        sftp = self._check_sftp(self.copy_pattern_from_remote.__name__)
        if sftp is None:
            return False

        if not _create_local_dir(local_dir, self.copy_pattern_from_remote.__name__):
            return False

        files = filter(lambda entry: re.match(remote_regex, entry.filename), sftp.listdir_attr(remote_dir))
        remote_names_paths = map(lambda entry: (entry.filename, remote_dir + remote_path_sep + entry.filename), files)
        remote_names_paths = filter(lambda name, path: self.is_file(path), remote_names_paths)

        success = True
        for file_name, remote_path in remote_names_paths:
            success = self.copy_file_from_remote(remote_path, os.path.join(local_dir, file_name)) and success
        return success

    def copy_latest_pattern_from_remote(self, remote_dir: str, local_path: str, remote_regex: re.Pattern | str,
                                        remote_path_sep: str = DEFAULT_PATH_SEP) -> bool:
        """
        Copies the latest file on the remote system that matches the given regular expression to the local system.
        Logs a warning and returns False if no such file exists.
        :param remote_dir:      Path to the remote directory with the file to be copied.
        :param local_path:      Destination path on the local system (including file name and ending!).
        :param remote_regex:    Regular expression for the file to be copied.
        :param remote_path_sep: Path separator symbol ('/' for Linux/Unix/Mac, '\\' for Windows).
        :return: True, if the operation was successful. False, if at least one Error has occurred.
        """
        sftp = self._check_sftp(self.copy_latest_pattern_from_remote.__name__)
        if sftp is None:
            return False

        files = list(filter(lambda entry: re.match(remote_regex, entry.filename), sftp.listdir_attr(remote_dir)))
        files.sort(key=lambda entry: entry.st_mtime)

        if len(files) == 0:
            logger.warning(NO_FILE_MATCHING_ERROR.format(remote_regex, remote_dir))
            return False

        remote_path = remote_dir + remote_path_sep + files[-1].filename
        return self.copy_file_from_remote(remote_path, local_path)

    def move_from_remote_by_pattern(self, remote_dir: str, local_path: str, remote_regex: re.Pattern | str,
                                        remote_path_sep: str = DEFAULT_PATH_SEP) -> int:
        """
        Copies the latest file on the remote system that matches the given regular expression to the local system.
        Logs a warning and returns False if no such file exists.
        :rtype: int:            Number of files moved from remote to local.
        :param remote_dir:      Path to the remote directory with the file to be copied.
        :param local_path:      Destination path on the local system (including file name and ending!).
        :param remote_regex:    Regular expression for the file to be copied.
        :param remote_path_sep: Path separator symbol ('/' for Linux/Unix/Mac, '\\' for Windows).
        """
        sftp = self._check_sftp(self.move_from_remote_by_pattern.__name__)
        if sftp is None:
            return False

        files = list(filter(lambda entry: re.match(remote_regex, entry.filename), sftp.listdir_attr(remote_dir)))
        files.sort(key=lambda entry: entry.st_mtime)

        if not files:
            logger.warning(NO_FILE_MATCHING_ERROR.format(remote_regex, remote_dir))
            return False

        for f in files:
            path = remote_dir + remote_path_sep + f.filename

            self.copy_file_from_remote(path, local_path)
            self.delete_file_on_remote(path)

        return len(files)

    def delete_file_on_remote(self, remote_path: str) -> bool:
        """
        Deletes a file on the remote system.
        :param remote_path: Path to the file on the remote system.
        :return: True, if the operation was successful. False, if at least one Error has occurred.
        """
        sftp = self._check_sftp(self.delete_file_on_remote.__name__)
        if sftp is None:
            return False

        if not self.exists(remote_path):
            return True

        try:
            sftp.remove(path=remote_path)
        except IOError as err:
            logger.warning(DELETE_FROM_REMOTE_ERROR.format(remote_path))
            logger.warning(IO_ERROR.format(err))
            return False
        return True

    def delete_dir_on_remote(self, remote_dir: str, remote_path_sep: str = DEFAULT_PATH_SEP) -> bool:
        """
        Recursively deletes a directory on the remote system.
        :param remote_dir:      Directory to be deleted.
        :param remote_path_sep: Path separator symbol ('/' for Linux/Unix/Mac, '\\' for Windows).
        :return: True, if the operation was successful. False, if at least one Error has occurred.
        """
        sftp = self._check_sftp(self.delete_dir_on_remote.__name__)
        if sftp is None:
            return False

        if not self.exists(remote_dir):
            return True

        success = True
        for entry in sftp.listdir_attr(remote_dir):
            remote_path = remote_dir + remote_path_sep + entry.filename
            if self.is_dir(remote_path):
                success = self.delete_dir_on_remote(remote_path, remote_path_sep) and success
            elif self.is_file(remote_path):
                success = self.delete_file_on_remote(remote_path) and success
        sftp.rmdir(remote_dir)
        return success

    def delete_pattern_on_remote(self, remote_dir: str, remote_regex: re.Pattern | str,
                                 remote_path_sep: str = DEFAULT_PATH_SEP) -> bool:
        """
        Deletes all files in a given directory on the remote system that match the given regular expression.
        Note: Only considers the files in the given directory, not in any subdirectories.
        :param remote_dir:      Directory of the files to be deleted.
        :param remote_regex:    Regular expression for the files to be deleted.
        :param remote_path_sep: Path separator symbol ('/' for Linux/Unix/Mac, '\\' for Windows).
        :return: True, if the operation was successful. False, if at least one Error has occurred.
        """
        sftp = self._check_sftp(self.delete_pattern_on_remote.__name__)
        if sftp is None:
            return False

        files = filter(lambda entry: re.match(remote_regex, entry.filename), sftp.listdir_attr(remote_dir))
        file_paths = map(lambda entry: remote_dir + remote_path_sep + entry.filename, files)
        file_paths = filter(lambda path: self.is_file(path), file_paths)

        success = True
        for file_path in file_paths:
            success = self.delete_file_on_remote(file_path) and success
        return success

    def exists(self, remote_path: str) -> bool:
        """
        Checks whether the given remote path exists.
        :param remote_path: Remote path.
        :return: True, if the path exists. False, otherwise.
        """
        sftp = self._check_sftp(self.exists.__name__)
        if sftp is None:
            return False

        try:
            sftp.stat(remote_path)
        except IOError:
            return False
        return True

    def is_file(self, remote_path: str) -> bool:
        """
        Checks whether the given remote path points to a file.
        :param remote_path: Remote path.
        :return: True, if the path points to a file. False, otherwise.
        """
        sftp = self._check_sftp(self.is_file.__name__)
        if sftp is None:
            return False

        try:
            result = S_ISREG(sftp.stat(remote_path).st_mode)
        except IOError:
            result = False
        return result

    def is_dir(self, remote_path: str) -> bool:
        """
        Checks whether the given remote path points to a directory.
        :param remote_path: Remote path.
        :return: True, if the path points to a directory. False, otherwise.
        """
        sftp = self._check_sftp(self.is_dir.__name__)
        if sftp is None:
            return False

        try:
            result = S_ISDIR(sftp.stat(remote_path).st_mode)
        except IOError:
            result = False
        return result

    def get_ssh(self) -> paramiko.SSHClient | None:
        """
        Allows access to the paramiko SSHClient for actions that are not implemented in this library.
        :return: paramiko SSHClient, if connection is established. None, otherwise.
        """
        return self._ssh

    def get_sftp(self) -> paramiko.SFTPClient | None:
        """
        Allows access to the paramiko SFTPClient for actions that are not implemented in this library.
        :return: paramiko SFTP Client, if connection is established. None, otherwise.
        """
        sftp = self._check_sftp(self.get_sftp.__name__)
        return sftp

    def _check_sftp(self, calling_function: str) -> paramiko.SFTPClient | None:
        """
        Simple check to ensure connection to SFTP server has been properly established in __init__.
        Returns the connection but logs warnings if the SFTP Client is None.
        :param calling_function: Name of the function calling _check_sftp for log warning.
        :return: paramiko SFTP Client, if connection is established. None, otherwise.
        """
        sftp = self._sftp
        if sftp is None:
            logger.warning(NOT_CONNECTED_ERROR)
            logger.warning(FUNCTION_ABORTED.format(calling_function))
        return sftp
