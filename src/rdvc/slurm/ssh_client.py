import logging
import os
from types import TracebackType
from typing import IO, List, Optional, Tuple, Type, Union, overload

import click
import paramiko

log = logging.getLogger("rdvc")


class SSHClient:
    def __init__(self, host: str, username: Optional[str] = None):
        self.host = host
        self.username = username
        self._client = paramiko.SSHClient()
        self._sftp_client: Optional[paramiko.SFTPClient] = None

        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def __enter__(self) -> "SSHClient":
        log.info(f"Establishing SSH connection to {self.host}...")
        self._client.connect(self.host, username=self.username)
        log.info("Connected.")
        return self

    @overload
    def __exit__(self, exc_type: None, exc_val: None, exc_tb: None) -> None:
        ...

    @overload
    def __exit__(
        self,
        exc_type: Type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
    ) -> None:
        ...

    def __exit__(
        self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]
    ) -> None:
        del exc_type, exc_val, exc_tb

        if self._sftp_client:
            self._sftp_client.close()
        self._client.close()

    def _exec_command(
        self, command: str, print_stdout: bool = True, print_stderr: bool = True, assert_exit_code: Optional[int] = 0
    ) -> Tuple[int, str, str]:
        _, stdout, stderr = self._client.exec_command(command)

        stdout_str = stdout.read().decode().rstrip()
        if print_stdout and stdout_str:
            click.echo(stdout_str)

        stderr_str = stderr.read().decode().rstrip()
        if print_stderr and stderr_str:
            click.echo(stderr_str, err=True)

        exit_code = stdout.channel.recv_exit_status()
        if assert_exit_code is not None:
            assert exit_code == 0, f"Exit code not equal to {assert_exit_code} ({command})."

        return exit_code, stdout_str, stderr_str

    def upload(self, file_obj: IO, remote_file_path: Union[str, os.PathLike], chmod: Optional[int] = None) -> None:
        if not self._sftp_client:
            log.info("Establishing SFTP connection...")
            self._sftp_client = self._client.open_sftp()
            log.info("Connected.")

        self._sftp_client.putfo(file_obj, str(remote_file_path))

        if chmod is not None:
            self._sftp_client.chmod(str(remote_file_path), chmod)

    def listdir(self, path: str) -> List[str]:
        if not self._sftp_client:
            log.info("Establishing SFTP connection...")
            self._sftp_client = self._client.open_sftp()
            log.info("Connected.")

        return self._sftp_client.listdir(path)

    def file_exists(self, path: str) -> bool:
        if not self._sftp_client:
            log.info("Establishing SFTP connection...")
            self._sftp_client = self._client.open_sftp()
            log.info("Connected.")

        try:
            self._sftp_client.stat(path)
            return True
        except FileNotFoundError:
            return False

    def mkdir(self, path: str) -> Tuple[int, str, str]:
        return self._exec_command(f"mkdir -p {path}")

    def make_tmpdir(self, template: str) -> str:
        _, tmpdir, _ = self._exec_command(f"mktemp {template}", print_stdout=False)
        return tmpdir

    def move(self, old_path: str, new_path: str) -> Tuple[int, str, str]:
        return self._exec_command(f"mv {old_path} {new_path}")

    def submit_sbatch(self, sbatch_file_path: str) -> str:
        _, job_id, _ = self._exec_command("sbatch --parsable " + sbatch_file_path, print_stdout=False)
        return job_id
