"""Точка входа: чтение параметров, сценарий или интерактивный REPL."""

import sys

from .config import ConfigError, Settings, get_settings
from .scripting import run_script
from .shell import Shell


def show_settings(settings: Settings) -> None:
    """Отладочная печать всех настроек при запуске эмулятора."""
    print(f"Configuration: {settings.config}")
    print(f"VFS: {settings.vfs}")
    print(f"Prompt: {settings.prompt}")
    print(f"Startup script: {settings.script}")


def main(argv: list[str] | None = None) -> int:
    """Проверить конфигурацию и запустить скрипт или оболочку."""
    try:
        settings = get_settings(argv)
        show_settings(settings)
        shell = Shell(prompt=settings.prompt)
        if settings.script is not None:
            return 0 if run_script(shell, settings.script, sys.stdout) else 1
        shell.repl()
        return 0
    except (ConfigError, OSError, UnicodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
