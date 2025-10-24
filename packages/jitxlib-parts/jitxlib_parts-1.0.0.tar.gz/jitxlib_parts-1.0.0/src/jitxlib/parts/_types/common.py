"""Help to avoid circular imports."""

from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Any


@dataclass_json
@dataclass(frozen=True)
class KeyValue:
    key: str
    value: Any
