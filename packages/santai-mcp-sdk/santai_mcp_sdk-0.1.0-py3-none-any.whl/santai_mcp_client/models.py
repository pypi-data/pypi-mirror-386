from typing import Dict, Any
from dataclasses import dataclass


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass(frozen=True)
class Decision:
    tool: Dict[str, any]
    args: Dict[str, any]
