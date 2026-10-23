"""Настройки CLI и JSON с приоритетом аргументов командной строки."""

import argparse
from dataclasses import dataclass
import json
from pathlib import Path


class ConfigError(ValueError):
    """Неверный формат или содержимое файла конфигурации."""


@dataclass(frozen=True)
class Settings:
    """Итоговые параметры оболочки."""

    vfs: str | None
    prompt: str | None
    script: str | None
    config: str | None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Разобрать аргументы командной строки эмулятора."""
    parser = argparse.ArgumentParser(description="UNIX shell emulator")
    parser.add_argument("--vfs", help="Path to VFS CSV (from stage 3)")
    parser.add_argument("--prompt", help="REPL prompt override")
    parser.add_argument("--script", help="Startup command script")
    parser.add_argument("--config", help="Path to JSON configuration")
    return parser.parse_args(argv)


def load_config(path: str | None) -> dict[str, str]:
    """Прочитать JSON и проверить имена и типы параметров."""
    if path is None:
        return {}
    try:
        content = Path(path).read_text(encoding="utf-8")
        data = json.loads(content)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Cannot read config {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError("Config must be a JSON object")
    allowed = {"vfs", "prompt", "script"}
    if set(data) - allowed:
        raise ConfigError("Unknown configuration keys")
    if any(not isinstance(value, str) for value in data.values()):
        raise ConfigError("Configuration values must be strings")
    base = Path(path).resolve().parent
    for key in ("vfs", "script"):
        if key in data:
            data[key] = str((base / data[key]).resolve())
    return data


def get_settings(argv: list[str] | None = None) -> Settings:
    """Совместить JSON и CLI; переданные в CLI значения главнее."""
    args = parse_args(argv)
    data = load_config(args.config)
    return Settings(
        vfs=args.vfs if args.vfs is not None else data.get("vfs"),
        prompt=args.prompt if args.prompt is not None else data.get("prompt"),
        script=args.script if args.script is not None else data.get("script"),
        config=args.config,
    )
