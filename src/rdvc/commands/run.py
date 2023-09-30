# Duplicating code helps make each command self-contained and explicit
# pylint: disable=duplicate-code
import logging
import os
from typing import Any, Tuple

import click
from click_option_group import optgroup
from dir import get_git_root
from dulwich.repo import Repo

from rdvc import cli_options
from rdvc.repo import check_local_repo_consistent_with_remote, get_job_repo
from rdvc.slurm.instance import InstanceTypes
from rdvc.slurm.remote_checks import check_rdvc_init
from rdvc.slurm.remote_command import submit_remote
from rdvc.slurm.sbatch_script import render_template
from rdvc.slurm.ssh_client import SSHClient

log = logging.getLogger("rdvc")


@click.command(context_settings={"ignore_unknown_options": True})
@cli_options.options("cluster")
@cli_options.options("instance")
@cli_options.options("sbatch")
@optgroup.group("DVC options")
@optgroup.option(
    "--pull/--no-pull",
    show_default=True,
    default=True,
    help="pull dependencies and attempt to pull outputs of previously run stages from DVC remote",
)
@click.option("-v", "--verbose", is_flag=True, help="verbose mode")
@click.argument(
    "args",
    nargs=-1,
    type=click.UNPROCESSED,
)
@click.pass_context
# pylint: disable-next=too-many-locals
def run(
    ctx: click.Context,
    pull: bool,
    args: Tuple[str, ...],
    verbose: bool,
    **kwargs: Any,
) -> None:
    """Execute `dvc exp run ARGS` on a remote cluster.

    All unlisted options and arguments are added to ARGS and passed to the remote
    process without modification."""

    # We capture these arguments through ctx.params and delete their references only to satisfy linters
    del kwargs

    if verbose:
        logging.basicConfig(level=logging.INFO)

    repo = Repo(str(get_git_root()))

    # Check repo consistency once all earlier issues have been ruled out.
    check_local_repo_consistent_with_remote(repo)

    job_repo = get_job_repo(os.getcwd())
    cluster_key_value_options, _ = cli_options.get_options_from_context(ctx, "cluster")
    sbatch_key_value_options, sbatch_flag_options = cli_options.get_options_from_context(ctx, "sbatch")
    instance_key_value_options, _ = cli_options.get_options_from_context(ctx, "instance")

    instance = InstanceTypes.from_name(instance_key_value_options["instance"])

    sbatch_script = render_template(
        "commands/run.sbatch.j2",
        job_repo=job_repo,
        sbatch_key_value_options=sbatch_key_value_options,
        sbatch_flag_options=sbatch_flag_options,
        instance_key_value_options=instance.to_key_value_options(),
        instance_flag_options=instance.to_flag_options(),
        dvc_exp_run_pull=pull,
    )

    host = cluster_key_value_options["host"]
    username = cluster_key_value_options.get("username", None)
    with SSHClient(host=host, username=username) as client:
        check_rdvc_init(client)
        submit_remote(client, sbatch_script)
