from dataclasses import dataclass
from pathlib import Path

@dataclass
class FileBlock:
    prefix: str
    files: list[Path]
    email: str | None = None
