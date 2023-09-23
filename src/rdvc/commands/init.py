# Duplicating code helps make each command self-contained and explicit
# pylint: disable=duplicate-code
import logging
from pathlib import Path

import click
import tomli_w

from rdvc import cli_options
from rdvc.dir import get_git_root
from rdvc.slurm.instance import InstanceTypes
from rdvc.slurm.remote_checks import REMOTE_RDVC_DIRECTORIES
from rdvc.slurm.ssh_client import SSHClient

log = logging.getLogger("rdvc")


def make_global_rdvc_config(global_rdvc_config_path: Path) -> None:
    global_rdvc_config_path.parent.mkdir(parents=True, exist_ok=True)

    host = click.prompt("Enter SLURM host address")
    email = click.prompt("(Optional) Enter an e-mail address for SLURM notifications")

    mail_config = {"mail-user": email, "mail-type": "END,FAIL"} if len(email) > 0 else {}
    basic_config = {"cluster": {"host": host}, "run": mail_config}

    with open(global_rdvc_config_path, "wb") as f:
        tomli_w.dump(basic_config, f)


def _get_default_wckey() -> str:
    return get_git_root().name


def make_project_rdvc_config(project_rdvc_config_path: Path) -> None:
    instances = InstanceTypes.to_dict()
    instance_name: str = click.prompt(
        "Which instance type?", default="t3.xlarge", type=click.Choice(list(instances.keys()))
    )

    wckey = click.prompt("How to tag this project?", default=_get_default_wckey(), type=str)

    config = {"run": {"wckey": wckey, "instance": instance_name}}

    with open(project_rdvc_config_path, "wb") as f:
        tomli_w.dump(config, f)


def make_project_rdvc_gitignore(project_rdvc_gitignore_path: Path) -> None:
    with open(project_rdvc_gitignore_path, "w") as f:
        f.write("queue\n")


@click.group
def init() -> None:
    """Setup rDVC."""


@init.command(name="global")
@click.option("-f", "--force", is_flag=True, help="overwrite existing config")
@click.option("-v", "--verbose", is_flag=True, help="verbose mode")
def global_(
    force: bool,
    verbose: bool,
) -> None:
    """Setup global rDVC config."""

    if verbose:
        logging.basicConfig(level=logging.INFO)

    log.info("Checking global rDVC config.")
    global_rdvc_config_path = cli_options.get_global_rdvc_config_path()

    if force or not global_rdvc_config_path.exists():
        log.info("Generating global rDVC config.")
        make_global_rdvc_config(global_rdvc_config_path)


@init.command()
@click.option("-v", "--verbose", is_flag=True, help="verbose mode")
def remote(
    verbose: bool,
) -> None:
    """Setup remote rDVC config."""

    if verbose:
        logging.basicConfig(level=logging.INFO)

    init_options = cli_options.get_cli_defaults()["init"]
    host = init_options["host"]
    username = init_options.get("username", None)

    with SSHClient(host, username=username) as client:
        log.info("Generating remote directories if missing.")
        remote_directories_command = f"mkdir -p .rdvc/{{{','.join(REMOTE_RDVC_DIRECTORIES)}}}"
        client.mkdir(remote_directories_command)


@init.command()
@click.option("-f", "--force", is_flag=True, help="overwrite existing config")
@click.option("-v", "--verbose", is_flag=True, help="verbose mode")
def project(
    force: bool,
    verbose: bool,
) -> None:
    """Setup project-local rDVC config."""

    if verbose:
        logging.basicConfig(level=logging.INFO)

    log.info("Checking project rDVC config.")

    project_rdvc_config_path = cli_options.get_project_rdvc_config_path()
    project_rdvc_config_path.parent.mkdir(exist_ok=True)
    if force or not project_rdvc_config_path.exists():
        log.info("Generating project rDVC config.")
        make_project_rdvc_config(project_rdvc_config_path)

    project_rdvc_gitignore_path = project_rdvc_config_path.parent / ".gitignore"
    if force or not project_rdvc_gitignore_path.exists():
        log.info("Generating project rDVC gitignore.")
        make_project_rdvc_gitignore(project_rdvc_gitignore_path)
