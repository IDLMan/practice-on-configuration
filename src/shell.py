"""REPL и реализация базовых команд над виртуальной файловой системой."""

from dataclasses import dataclass
import getpass
import posixpath
import socket

from .vfs import VFSError, VirtualFileSystem


MAX_PATH_ARGS = 1
COPY_ARG_COUNT = 2


@dataclass(frozen=True)
class Result:
    """Результат команды, включая флаг ошибки и признак завершения."""

    output: str = ""
    ok: bool = True
    exit_requested: bool = False


class Shell:
    """Интерактивная оболочка с текущим виртуальным каталогом."""

    def __init__(
        self, prompt: str | None = None,
        vfs: VirtualFileSystem | None = None,
    ) -> None:
        """Создать оболочку и получить приглашение из данных ОС."""
        user = getpass.getuser()
        host = socket.gethostname()
        self.prompt = prompt if prompt is not None else f"{user}@{host}:~$ "
        self.vfs = vfs
        self.cwd = "/"

    def execute(self, line: str) -> Result:
        """Разобрать команду простым разделением по пробелам."""
        tokens = line.split()
        if not tokens:
            return Result()
        command, *arguments = tokens
        if command == "exit":
            if arguments:
                return Result("exit: arguments are not supported", False)
            return Result(exit_requested=True)
        if self.vfs is None and command in {"ls", "cd"}:
            return Result(f"{command}: arguments={arguments!r}")
        handlers = {
            "ls": self._ls, "cd": self._cd,
            "tac": self._tac, "pwd": self._pwd,
        }
        if command not in handlers:
            return Result(f"{command}: command not found", False)
        try:
            return handlers[command](arguments)
        except VFSError as exc:
            return Result(f"{command}: {exc}", False)

    def _ls(self, args: list[str]) -> Result:
        """Показать дочерние имена каталога либо имя самого файла."""
        if len(args) > MAX_PATH_ARGS:
            return Result("ls: expected at most one path", False)
        if self.vfs is None:
            return Result("ls: VFS is not loaded", False)
        path = self.vfs.normalize(args[0] if args else ".", self.cwd)
        entry = self.vfs.require(path)
        if not entry.is_dir:
            return Result(posixpath.basename(path))
        return Result("\n".join(self.vfs.list_dir(path)))

    def _cd(self, args: list[str]) -> Result:
        """Сменить виртуальную директорию (без аргумента — корень)."""
        if len(args) > MAX_PATH_ARGS:
            return Result("cd: expected at most one path", False)
        if self.vfs is None:
            return Result("cd: VFS is not loaded", False)
        path = self.vfs.normalize(args[0] if args else "/", self.cwd)
        self.vfs.require_dir(path)
        self.cwd = path
        return Result()

    def _pwd(self, args: list[str]) -> Result:
        """Напечатать абсолютный путь текущего каталога VFS."""
        if args:
            return Result("pwd: arguments are not supported", False)
        return Result(self.cwd)

    def _tac(self, args: list[str]) -> Result:
        """Вывести строки каждого виртуального файла в обратном порядке."""
        if not args:
            return Result("tac: expected at least one file", False)
        if self.vfs is None:
            return Result("tac: VFS is not loaded", False)
        output = []
        for argument in args:
            path = self.vfs.normalize(argument, self.cwd)
            try:
                content = self.vfs.read_file(path).decode("utf-8")
            except UnicodeDecodeError:
                return Result(f"tac: file is not valid UTF-8: {path}", False)
            output.append("".join(reversed(content.splitlines(keepends=True))))
        return Result("".join(output))

    def repl(self) -> None:
        """Выполнять команды до exit, Ctrl+C или конца ввода."""
        while True:
            try:
                line = input(self.prompt)
            except (EOFError, KeyboardInterrupt):
                print()
                break
            result = self.execute(line)
            if result.output:
                ending = "" if result.output.endswith("\n") else "\n"
                print(result.output, end=ending)
            if result.exit_requested:
                break
