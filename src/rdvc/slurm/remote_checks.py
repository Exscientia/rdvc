import logging
from typing import List

from rdvc.slurm.ssh_client import SSHClient

log = logging.getLogger("rdvc")
REMOTE_RDVC_DIRECTORIES = ["logs", "submissions"]


class RDvcInitError(Exception):
    """Exception raised when the remote rDVC folder is missing or malformed.

    Attributes:
        remote_dirs (List[str]): list of directories in the remote .rdvc
        message (str): message displayed to the user
    """

    def __init__(
        self,
        remote_dirs: List[str],
        message: str = "The remote rDVC folder is missing or malformed, run `rdvc init`.",
    ):
        self.remote_dirs = remote_dirs
        self.message = message
        super().__init__(self.message)


def check_rdvc_init(client: SSHClient) -> None:
    """Check for existence of rDVC directories on the remote host."""
    log.info("Checking that rDVC directories exist on the remote host.")
    remote_dirs = client.listdir(".rdvc")

    if not set(REMOTE_RDVC_DIRECTORIES).issubset(remote_dirs):
        raise RDvcInitError(remote_dirs)
