"""Интерактивный цикл REPL и диспетчер команд эмулятора."""

from dataclasses import dataclass
import getpass
import socket

from .vfs import VirtualFileSystem


@dataclass(frozen=True)
class Result:
    """Результат выполнения команды оболочки."""

    output: str = ""
    ok: bool = True
    exit_requested: bool = False


class Shell:
    """Простая оболочка с командами-заглушками."""

    def __init__(
        self, prompt: str | None = None,
        vfs: VirtualFileSystem | None = None,
    ) -> None:
        """Создать оболочку с приглашением из данных ОС по умолчанию."""
        user = getpass.getuser()
        host = socket.gethostname()
        self.prompt = prompt if prompt is not None else f"{user}@{host}:~$ "
        self.vfs = vfs
        self.cwd = "/"

    def execute(self, line: str) -> Result:
        """Разделить строку по пробелам и выполнить команду."""
        tokens = line.split()
        if not tokens:
            return Result()
        command, *arguments = tokens
        if command == "exit":
            if arguments:
                return Result("exit: arguments are not supported", False)
            return Result(exit_requested=True)
        if command in {"ls", "cd"}:
            return Result(f"{command}: arguments={arguments!r}")
        return Result(f"{command}: command not found", False)

    def repl(self) -> None:
        """Обрабатывать ввод команд до exit или конца входного потока."""
        while True:
            try:
                line = input(self.prompt)
            except (EOFError, KeyboardInterrupt):
                print()
                break
            result = self.execute(line)
            if result.output:
                print(result.output)
            if result.exit_requested:
                break
