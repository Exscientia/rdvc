from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List

from dvc.repo import Repo as DvcRepo
from rdvc.repo import get_job_repo


@dataclass
class QueuedCommand:
    run_options: str

    def __str__(self) -> str:
        return f"dvc exp run --queue {self.run_options}"


class CommandQueue:
    def __init__(self, pipeline_dir: Path):
        self.pipeline_dir = pipeline_dir
        self.job_repo = get_job_repo(self.pipeline_dir)

    def put(self, run_options: Iterable[str]) -> None:
        command = QueuedCommand(run_options=" ".join(run_options))

        # Create empty file if it doesn't exist
        if not self.queue_path.exists():
            with open(self.queue_path, "w") as _:
                pass

        with open(self.queue_path, "a") as f:
            f.write(command.run_options + "\n")

    def clear(self) -> None:
        with open(self.queue_path, "w") as _:
            pass

    @property
    def queue_path(self) -> Path:
        return self.pipeline_dir / ".rdvc/queue"

    @property
    def commands(self) -> List[QueuedCommand]:
        commands: List[QueuedCommand] = []
        if self.queue_path.exists():
            with open(self.queue_path, "r") as f:
                for line in f.readlines():
                    commands.append(QueuedCommand(run_options=line.strip()))
        return commands

    def __iter__(self) -> Iterator[QueuedCommand]:
        return iter(self.commands)

    def __len__(self) -> int:
        return len(self.commands)

    def __str__(self) -> str:
        return "\n".join(str(command) for command in self.commands)


def local_queue_active(pipeline_dir: Path) -> bool:
    dvc_repo = DvcRepo(pipeline_dir)
    exp_states = dvc_repo.experiments.show(hide_failed=True)
    # pylint throws up linting error without dict
    for exp_state in exp_states:
        if exp_state.experiments is None:
            continue
        for exp in exp_state.experiments:
            if exp.executor is None:
                continue
            if exp.executor.state in ["queued", "running"]:
                return True

    return False
