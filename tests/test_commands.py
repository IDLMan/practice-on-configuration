"""Проверки настоящих UNIX-подобных команд этапа 4."""

from pathlib import Path
import unittest

from src.shell import Shell
from src.vfs import VirtualFileSystem


DATA = Path(__file__).resolve().parents[1] / "data" / "nested.csv"


class CommandsTests(unittest.TestCase):
    """Проверка успешных сценариев и обработки ошибочных аргументов."""

    def set_up(self) -> None:
        """Подготовить виртуальную иерархию в памяти."""
        self.vfs = VirtualFileSystem.from_csv(str(DATA))
        self.shell = Shell(prompt="test$ ", vfs=self.vfs)

    def test_ls_root(self) -> None:
        """ls перечисляет директории и файлы верхнего уровня."""
        result = self.shell.execute("ls /")
        self.assertEqual(result.output, "bin\ndocs\nnotes.txt")

    def test_ls_file(self) -> None:
        """ls конкретного файла возвращает только его имя."""
        self.assertEqual(self.shell.execute("ls /notes.txt").output,
                         "notes.txt")

    def test_cd_and_pwd(self) -> None:
        """cd работает с абсолютными и относительными путями."""
        self.assertTrue(self.shell.execute("cd /docs/tutorial").ok)
        self.assertEqual(self.shell.execute("pwd").output,
                         "/docs/tutorial")
        self.assertTrue(self.shell.execute("cd ..").ok)
        self.assertEqual(self.shell.execute("pwd").output, "/docs")
        self.assertTrue(self.shell.execute("cd").ok)
        self.assertEqual(self.shell.execute("pwd").output, "/")

    def test_tac(self) -> None:
        """tac отображает содержимое файла в обратном порядке строк."""
        result = self.shell.execute("tac /docs/readme.txt")
        self.assertEqual(result.output,
                         "line three\nline two\nline one\n")

    def test_tac_relative_path(self) -> None:
        """tac корректно раскрывает относительный путь."""
        self.shell.execute("cd /docs")
        result = self.shell.execute("tac tutorial/lesson.txt")
        self.assertEqual(result.output, "gamma\nbeta\nalpha\n")

    def test_tac_rejects_binary(self) -> None:
        """Бинарный файл с неверным UTF-8 вызывает понятную ошибку."""
        result = self.shell.execute("tac /bin/image.bin")
        self.assertFalse(result.ok)
        self.assertIn("not valid UTF-8", result.output)

    def test_missing_paths(self) -> None:
        """cd и ls не принимают несуществующие пути."""
        self.assertFalse(self.shell.execute("cd /missing").ok)
        self.assertFalse(self.shell.execute("ls /missing").ok)
        self.assertEqual(self.shell.cwd, "/")

    def test_invalid_arguments(self) -> None:
        """Проверки arity для всех базовых команд."""
        for command in ("pwd extra", "cd a b", "ls a b", "tac"):
            with self.subTest(command=command):
                self.assertFalse(self.shell.execute(command).ok)

    def test_cannot_cd_to_file(self) -> None:
        """cd отвергает обычные файлы."""
        result = self.shell.execute("cd /notes.txt")
        self.assertFalse(result.ok)

    def test_no_os_commands(self) -> None:
        """Оболочка не запускает команды реальной ОС."""
        result = self.shell.execute("python -V")
        self.assertFalse(result.ok)

setattr(CommandsTests, "setUp", CommandsTests.set_up)