import os
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Optional, Union

from dulwich import porcelain
from dulwich.repo import Repo
from rdvc.dir import get_git_root


@dataclass
class RDvcJobRepo:
    name: str
    url: str
    branch: str
    rev: str
    pipeline: Optional[str]


class RepositoryError(Exception):
    """Exception raised for rDVC operations when the local and remote repo states
    do not match up.

    Attributes:
        status (dulwich.porcelain.GitStatus): contains status of the local repo.
        message (str): message displayed to the user
    """

    def __init__(
        self,
        dulwich_status: porcelain.GitStatus,
        message: str = "The current state of this repository contains unstaged files or unpushed commits.",
    ):
        self.dulwich_status = dulwich_status
        self.message = message
        super().__init__(self.message)


class OutsideRepositoryError(Exception):
    pass


def _get_pipeline(path: Union[str, os.PathLike]) -> Optional[str]:
    rel_path = Path(path).relative_to(get_git_root(path))

    if len(rel_path.parts) > 0 and rel_path.parts[0] == "pipelines":
        return rel_path.parts[1]

    return None


def get_job_repo(path: Union[str, os.PathLike]) -> RDvcJobRepo:
    repo = Repo(str(get_git_root(path)))

    # NOTE Running outside of a git repo raises an IndexError here
    try:
        repo_branch = porcelain.active_branch(repo).decode("utf-8")
    except IndexError as err:
        raise OutsideRepositoryError from err

    return RDvcJobRepo(
        name=Path(repo.path).name,
        url=porcelain.get_remote_repo(repo)[-1],
        branch=repo_branch,
        rev=repo.head().decode(),
        pipeline=_get_pipeline(path),
    )


def check_local_repo_consistent_with_remote(repo: Repo) -> None:
    dulwich_status = porcelain.status(repo.path)

    if len(dulwich_status.unstaged) > 0:
        raise RepositoryError(dulwich_status, message="Stash or stage, commit and push your local Git changes.")

    staged_files = list(chain.from_iterable(dulwich_status.staged.values()))
    if len(staged_files) > 0:
        raise RepositoryError(dulwich_status, message="Stash or commit and push your local Git changes.")

    # Get the hashes of the current local and remote branches and compare
    refs = repo.get_refs()
    head_tree_hash = refs.get(b"HEAD", None)
    if head_tree_hash is None:
        raise RepositoryError(dulwich_status, message="Do not work with detached HEAD.")

    remote_branch = porcelain.get_branch_remote(repo) + b"/" + porcelain.active_branch(repo)
    remote_tree_hash = refs.get(b"refs/remotes/" + remote_branch, None)
    if head_tree_hash != remote_tree_hash:
        raise RepositoryError(dulwich_status, message="Push your local Git changes.")
