import io
import logging
from pathlib import Path

import click
from rdvc.slurm.ssh_client import SSHClient

log = logging.getLogger("rdvc")


def submit_remote(client: SSHClient, sbatch_script: str) -> None:
    submissions_dir = Path(".rdvc/submissions")
    sbatch_script_fo = io.BytesIO(sbatch_script.encode("utf-8"))
    temp_sbatch_path = client.make_tmpdir("rdvc-sbatch-XXXXXXXXXX")

    log.info(f"Copying sbatch submission file to {temp_sbatch_path}.")
    client.upload(sbatch_script_fo, temp_sbatch_path, chmod=775)

    job_id = client.submit_sbatch(temp_sbatch_path)
    click.echo(f"Submitted batch job {job_id}.")

    final_remote_file_path = submissions_dir / f"{job_id}.sbatch.sh"
    client.move(temp_sbatch_path, str(final_remote_file_path))
