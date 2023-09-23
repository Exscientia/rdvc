import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar, cast

import click
import tomli
from click_option_group import optgroup
from typing_extensions import ParamSpec

from rdvc.dir import get_git_root
from rdvc.repo import OutsideRepositoryError, get_job_repo

P = ParamSpec("P")
R = TypeVar("R")


@dataclass
class OptionGroup:
    help: str
    options: Dict[str, Dict[str, Any]]


CLUSTER_OPTIONS: Dict[str, Dict[str, Any]] = {
    "host": {"required": True, "show_default": True, "help": "SLURM cluster address"},
    "username": {"required": False, "show_default": True, "help": "SLURM cluster username"},
}

INSTANCE_OPTIONS: Dict[str, Dict[str, Any]] = {
    "instance": {
        "show_default": True,
        "help": "select instance type",
    },
}

SBATCH_OPTIONS: Dict[str, Dict[str, Any]] = {
    "begin": {"show_default": True, "help": "submit now but defer job until specified time"},
    "comment": {"show_default": True, "help": "arbitrary comment"},
    "deadline": {"show_default": True, "help": "remove job if no ending is possible before deadline"},
    "job-name": {"show_default": True, "help": "name for job allocation"},
    "mail-type": {"show_default": True, "help": "notify user by email when these event types occur"},
    "mail-user": {"show_default": True, "help": "user to receive email notification"},
    "time": {"show_default": True, "help": "set limit on total run time of job allocation"},
    "wckey": {"show_default": True, "help": "project tag"},
}

OPTION_GROUPS = {
    "cluster": OptionGroup(help="cluster configuration", options=CLUSTER_OPTIONS),
    "instance": OptionGroup(help="instance options", options=INSTANCE_OPTIONS),
    "sbatch": OptionGroup(help="sbatch options", options=SBATCH_OPTIONS),
}


def options(group: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def inner(func: Callable[P, R]) -> Callable[P, R]:
        for option, kwargs in reversed(OPTION_GROUPS[group].options.items()):
            func = optgroup.option(f"--{option}", **kwargs)(func)

        # click-option-group loses typing information and triggers mypy
        return cast(Callable[P, R], optgroup.group(OPTION_GROUPS[group].help)(func))

    return inner


def get_options_from_context(ctx: click.Context, group: str) -> Tuple[Dict[str, Any], Dict[str, bool]]:
    all_group_options = {option.replace("-", "_") for option in OPTION_GROUPS[group].options}

    group_options = {k: ctx.params[k] for k in (all_group_options & ctx.params.keys())}
    group_key_value_options = {k: v for k, v in group_options.items() if not isinstance(v, bool)}
    group_flag_options = {k: v for k, v in group_options.items() if isinstance(v, bool)}
    return group_key_value_options, group_flag_options


def load_config(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    with open(path, mode="rb") as file:
        return tomli.load(file)


def get_global_rdvc_config_path() -> Path:
    return Path(os.environ.get("GLOBAL_RDVC_CONFIG", Path("~/.config/rdvc/config.toml").expanduser()))


def get_project_rdvc_config_path(path: Optional[Path] = None) -> Path:
    return get_git_root(path) / ".rdvc/config.toml"


def get_cli_defaults() -> Dict[str, Any]:
    rdvc_global_config = load_config(get_global_rdvc_config_path())
    rdvc_project_config = load_config(get_project_rdvc_config_path())

    try:
        job_repo = get_job_repo(os.getcwd())
    except OutsideRepositoryError:
        return {}

    def merge_configs(key: str) -> Dict[str, Any]:
        # Set job name to rdvc-{cmd}:REPO_NAME:BRANCH as default
        rdvc_dynamic_config = {"job-name": f"rdvc-{key}:{job_repo.name}:{job_repo.branch}"}

        merged = {**rdvc_dynamic_config, **rdvc_global_config.get(key, {}), **rdvc_project_config.get(key, {})}

        # Click internally replaces dashes with underscores so we conform
        return {k.replace("-", "_"): v for k, v in merged.items()}

    cluster_configs = merge_configs("cluster")
    return {
        "init": {**cluster_configs, **merge_configs("init")},
        "run": {**cluster_configs, **merge_configs("run")},
        "queue": {"start": {**cluster_configs, **merge_configs("run")}},
    }
