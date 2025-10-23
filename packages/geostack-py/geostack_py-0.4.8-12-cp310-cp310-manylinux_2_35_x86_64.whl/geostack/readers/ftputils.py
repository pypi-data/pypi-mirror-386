# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os.path as pth
from ftplib import FTP, error_perm
from typing import List, Union, Optional
from functools import partial


class Ftp:
    def __init__(self, ftp_server: str, user: Optional[str] = None,
                 passwd: Optional[str] = None, timeout: int = 30) -> None:
        try:
            self.connection = FTP(ftp_server, timeout=timeout)
        except Exception as e:
            raise RuntimeError(f"Unable to instantiate ftp {str(e)}")

        try:
            if user is None:
                user = "anonymous"
            if passwd is None:
                passwd = ''
            rc = self.connection.login(user=user, passwd=passwd)
        except Exception as e:
            raise RuntimeError(f"Unable to login to ftp {str(e)}")

        if not rc.startswith("230"):
            raise RuntimeError(f"Unable to login to {ftp_server} server")

    def chdir(self, dirpath: str) -> None:
        try:
            rc = self.connection.cwd(dirpath)
        except error_perm:
            raise ValueError(
                f"{dirpath} is not a valid file directory")

    def getcwd(self) -> str:
        try:
            rc = self.connection.pwd()
        except error_perm:
            raise ValueError("Unable to get path")
        return rc

    def listdir(self, directory: str = None) -> List:
        file_list = []
        pwd = self.getcwd()

        if directory is None:
            method_map = self.connection.nlst
        else:
            method_map = partial(self.connection.nlst, directory)
            self.chdir(directory)

        file_list = method_map()
        self.chdir(pwd)
        return file_list

    def listfiles(self, directory: str = None) -> List:
        file_list = []
        pwd = self.getcwd()

        if directory is None:
            method_map = self.connection.nlst
        else:
            method_map = partial(self.connection.nlst, directory)
            self.chdir(directory)

        file_list = map(lambda s: pth.basename(s),
                        filter(lambda s: not self.isdir(s),
                               method_map()))
        self.chdir(pwd)
        return list(file_list)

    def isdir(self, path: str) -> bool:
        return self._directory_exists(path)

    def isfile(self, path: str) -> bool:
        return not self.isdir(path)

    def mkdir(self, path: str):
        try:
            self.connection.mkd(path)
        except error_perm:
            raise RuntimeError("Unable to make directory")

    def makedirs(self, path: str, exists_ok: bool = False):
        if not exists_ok:
            if self._directory_exist(path):
                raise RuntimeError(f"{path} exists")

        if not self._directory_exist(path):
            self.mkdir(path)

    def rmfile(self, path: str):
        self.connection.delete(path)

    def rmdir(self, path: str):
        self.connection.rmd(path)

    def rmtree(self, path: str):
        for fname in self.listdir(path):
            self.rmfile(fname)
        self.rmdir(path)

    def upload_files(self, files: Union[str, List],
                     source: str, destination: str) -> None:
        if isinstance(files, str):
            files = [files]

        for filename in files:
            self.upload_file(pth.join(source, pth.basename(filename)),
                             pth.join(destination, pth.basename(filename)))

    def download_tree(self, remote_dir: str,
                      local_dir: str) -> None:

        files = self.listfiles(remote_dir)
        for filename in files:
            self.download_file(pth.join(remote_dir, pth.basename(filename)),
                               pth.join(local_dir, pth.basename(filename)))

    def download_file(self, remote_path: str, local_path: str) -> None:
        with open(local_path, 'wb') as outp:
            self.connection.retrbinary(f'RETR {remote_path}', outp.write)

    def upload_file(self, local_path: str, remote_path: str) -> None:
        with open(local_path, 'rb') as inp:
            self.connection.storbinary(f'STOR {remote_path}', inp)

    def _directory_exists(self, path: str) -> bool:
        current_path = self.getcwd()
        exists = True
        try:
            self.chdir(path)
        except Exception as e:
            exists = False
        finally:
            self.chdir(current_path)
            return exists

    @property
    def is_alive(self) -> bool:
        try:
            self.connection.retrlines('LIST')
        except Exception:
            return False
        return True

    def close(self) -> None:
        self.connection.quit()

    def __enter__(self):
        return self

    def __exit__(self, kind, value, tb):
        self.close()
