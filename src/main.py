"""Точка входа в CLI-эмулятор."""

from .shell import Shell


def main() -> int:
    """Запустить интерактивную оболочку."""
    Shell().repl()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
