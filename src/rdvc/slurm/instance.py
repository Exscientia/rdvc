from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


@dataclass
# pylint: disable=too-many-instance-attributes
class InstanceType:
    name: str
    partition: str
    gpus: int
    cpus: int
    mem: int = 0
    exclusive: bool = True
    nodes: int = 1

    def to_key_value_options(self) -> Dict[str, Any]:
        return {
            "partition": self.partition,
            "gpus": self.gpus,
            "cpus-per-task": self.cpus,
            "constraint": self.name,
            "mem": self.mem,
            "nodes": self.nodes,
        }

    def to_flag_options(self) -> List[str]:
        if self.exclusive:
            return ["exclusive"]

        return []


class InstanceTypes(Enum):
    # general
    T3_XLARGE = InstanceType(name="t3.xlarge", partition="general", gpus=0, cpus=2)
    # single-gpu
    G5_XLARGE = InstanceType(name="g5.xlarge", partition="single-gpu", gpus=1, cpus=2)
    # multi-gpu
    G5_12XLARGE = InstanceType(name="g5.12xlarge", partition="multi-gpu", gpus=4, cpus=24)

    @classmethod
    def to_dict(cls) -> Dict[str, InstanceType]:
        return {instance.value.name: instance.value for instance in cls}

    @classmethod
    def from_name(cls, name: str) -> InstanceType:
        return cls.to_dict()[name]
