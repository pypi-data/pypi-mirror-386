import json
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import MutableMapping

from . import atomic
from .file import FileProxy


def modify_dict(target: Mapping, source: MutableMapping):
    for name, value in source.items():
        if isinstance(value, dict):
            new_target = target.setdefault(name, dict())
            modify_dict(new_target, value)
        else:
            target[name] = value


class JsonProxy(FileProxy):
    SCHEME = "json"
    EXTENSIONS = [".json"]
    ALLOW_PATH_IN_FILE = False

    def _dump(self, path: Path, data: Any, **_):
        with atomic.atomic_write(path) as f:
            json.dump(data, f)

    def _load(self, path: Path):
        with open(path, mode="r") as f:
            return json.load(f)
