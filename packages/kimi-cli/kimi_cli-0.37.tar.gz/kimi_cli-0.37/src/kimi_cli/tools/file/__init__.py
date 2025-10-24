from enum import Enum


class FileOpsWindow:
    """Maintains a window of file operations."""

    pass


class FileActions(str, Enum):
    READ = "read file"
    EDIT = "edit file"


from .glob import Glob  # noqa: E402
from .grep import Grep  # noqa: E402
from .patch import PatchFile  # noqa: E402
from .read import ReadFile  # noqa: E402
from .replace import StrReplaceFile  # noqa: E402
from .write import WriteFile  # noqa: E402

__all__ = (
    "ReadFile",
    "Glob",
    "Grep",
    "WriteFile",
    "StrReplaceFile",
    "PatchFile",
)
