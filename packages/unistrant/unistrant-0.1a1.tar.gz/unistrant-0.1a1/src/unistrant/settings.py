import importlib
import os
import tomllib
from collections.abc import Generator, Mapping
from dataclasses import dataclass
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any

import unistrant.data
from unistrant.error import UnistrantError


@dataclass(frozen=True)
class Settings(Mapping):
    settings: Mapping[str, Any]
    logging: Mapping[str, Any]

    def __contains__(self, key: Any) -> bool:
        return key in self.settings

    def __getitem__(self, key: Any) -> Any:
        return self.settings[key]

    def __iter__(self) -> Generator:
        yield from self.settings

    def __len__(self) -> int:
        return len(self.settings)

    def required(self, key: Any) -> Any:
        try:
            return self.settings[key]
        except KeyError:
            raise UnistrantError(f"Required setting {key} missing")


def find_settings(settings_path: Path | None) -> Path | None:
    if settings_path:
        return settings_path

    if home := os.getenv("HOME"):
        home_settings_path = (Path(home) / ".config/sams/unistrant/unistrant.toml").expanduser()
        if home_settings_path.exists():
            return home_settings_path

    system_settings_path = Path("/etc/sams/unistrant/unistrant.toml")
    if system_settings_path.exists():
        return system_settings_path

    return None


def load_settings(settings_path: Path | None) -> Settings:
    settings = {}

    def merge(path: Traversable) -> None:
        try:
            with path.open(mode="rb") as settings_file:
                toml = tomllib.load(settings_file)
        except OSError as e:
            raise UnistrantError(f"Unable to read settings file: {str(e)}")
        except tomllib.TOMLDecodeError as e:
            raise UnistrantError(f"Unable to decode settings file: {str(e)}")
        settings.update(toml)

    merge(importlib.resources.files(unistrant.data) / "settings.toml")

    if settings_path is not None:
        merge(settings_path)

    def flatten(s: dict, base: str = "") -> Any:
        for key, value in s.items():
            full_key = f"{base}.{key}" if base else key
            if isinstance(value, dict):
                yield from flatten(value, full_key)
            else:
                yield full_key, value

    return Settings(settings=dict(flatten(settings)), logging=settings.get("logging", {}))
