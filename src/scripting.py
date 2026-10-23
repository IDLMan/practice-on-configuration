"""Исполнение команд из стартового скрипта с выводом диалога."""

from pathlib import Path
from typing import TextIO

from .shell import Shell


def run_script(shell: Shell, path: str, output: TextIO) -> bool:
    """Выполнить скрипт, пропуская комментарии, и сообщить об ошибках."""
    content = Path(path).read_text(encoding="utf-8")
    succeeded = True
    for number, source in enumerate(content.splitlines(), start=1):
        line = source.partition("#")[0].strip()
        if not line:
            continue
        print(f"{shell.prompt}{line}", file=output)
        result = shell.execute(line)
        if result.output:
            print(
                result.output, file=output,
                end="" if result.output.endswith("\n") else "\n",
            )
        if not result.ok:
            print(f"Script error at line {number}", file=output)
            succeeded = False
        if result.exit_requested:
            break
    return succeeded
