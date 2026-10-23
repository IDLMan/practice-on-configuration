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
        """Создать оболочку и настроить приглашение."""
        self.user = getpass.getuser()
        self.host = socket.gethostname()
        self.custom_prompt = prompt
        self.prompt = (
            prompt if prompt is not None
            else f"{self.user}@{self.host}:~$ "
        )
        self.vfs = vfs
        self.cwd = "/"
        self.previous_cwd: str | None = None


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
            "tac": self._tac, "pwd": self._pwd, "cp": self._cp,
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
        """Сменить каталог с поддержкой возврата через cd -."""
        if len(args) > MAX_PATH_ARGS:
            return Result("cd: expected at most one path", False)
        if self.vfs is None:
            return Result("cd: VFS is not loaded", False)

        go_back = bool(args) and args[0] == "-"

        if go_back and self.previous_cwd is None:
            return Result("cd: OLDPWD not set", False)

        target = (
            self.previous_cwd if go_back
            else args[0] if args else "/"
        )

        path = self.vfs.normalize(target, self.cwd)
        self.vfs.require_dir(path)

        self.previous_cwd = self.cwd
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

    def _cp(self, args: list[str]) -> Result:
        """Копировать файл VFS, не модифицируя источник на диске."""
        if len(args) != COPY_ARG_COUNT:
            return Result("cp: expected source and destination", False)
        if self.vfs is None:
            return Result("cp: VFS is not loaded", False)
        self.vfs.copy_file(args[0], args[1], self.cwd)
        return Result()


    def current_prompt(self) -> str:
        """Сформировать приглашение с текущим путём VFS."""
        if self.custom_prompt is not None or self.vfs is None:
            return self.prompt
        return f"{self.user}@{self.host}:{self.cwd}$ "


    def repl(self) -> None:
        """Выполнять команды до exit, Ctrl+C или конца ввода."""
        while True:
            try:
                line = input(self.current_prompt())
            except (EOFError, KeyboardInterrupt):
                print()
                break
            result = self.execute(line)
            if result.output:
                ending = "" if result.output.endswith("\n") else "\n"
                print(result.output, end=ending)
            if result.exit_requested:
                break
