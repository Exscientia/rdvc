# rDVC

rDVC executes DVC pipelines on SLURM clusters.

It expects an `init_python_venv.sh` script at the root of the DVC repository which will set up the full environment for execution.

## Remote execution

Install rDVC and navigate into a local copy of your DVC repository. Make sure it's synchronised with the remote (i.e. stage, commit and `git push`). If correctly set up, you can kick off a remote job with

```sh
$ rdvc -S my_param=a
...  # wait for the job to finish
$ dvc exp pull origin
```

## Setup

### Local machine

The following steps take place on your local machine.

1. copy your SSH key to the cluster:

```sh
ssh-copy-id <SLURM_CLUSTER_SSH>
```

2. run `rdvc init` subcommands:
    1. (one-off) `rdvc init global`
    2. (one-off) `rdvc init remote`
    3. (once for every project) `rdvc init project` in your project directory

### Remote machine

It is the user's responsibility to guarantee the remote job's access to any relevant secrets such as GitHub credentials. If in doubt, speak to your infrastructure team.

A (non-exhaustive) list of things to set up for your remote user account:

- Git credentials
  - likely as an SSH key
- private PyPI repository keys
- Experiment tracking credentials, e.g. for Iterative Studio
  - these go in `~/.config/dvc/config`

For the [demo project](https://github.com/exs-dmiketa/rdvc-demo-project), ensure that Python 3.11 is available on the SLURM cluster.

## rDVC configuration options

All options are loaded, in the order of increasing priority, from

1. `~/.config/rdvc/config.toml`
2. `PROJECT_ROOT/.rdvc/config.toml`
3. `rdvc` CLI options (read `rdvc --help` for details)

## Folder structure and organisation of SLURM jobs

Remote runs generate a number of files. You can find them, by type, in your (remote) home directory:

-   submitted jobs: `$HOME/.rdvc/submissions/%Y-%m-%d-%H-%M-%S-%f-git_hash-sbatch_script_hash`
-   logs: `$HOME/.rdvc/logs/slurm-$SLURM_JOB_ID.out`
-   job working directories: `$HOME/.rdvc/workspaces/$SLURM_JOB_ID`
-   default DVC cache: `$HOME/.dvc/cache`

## Customising rDVC for your SLURM cluster

rDVC works by composing and submitting a `sbatch` script. It needs to allocate the job to a partition existing in the cluster. The list (and properties) of available partitions is defined in `src/rdvc/slurm/instance.py` as the `Enum` class `InstanceTypes`. Modify its entries to match your SLURM cluster's configuration. The current version of rDVC does not support setting up instance types via config, so you have to fork and modify rDVC source code.

You can find which partitions and node types are available by consulting `sinfo` while logged into the SLURM cluster.
