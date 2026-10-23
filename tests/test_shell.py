"""Проверки первого этапа: парсер, заглушки и завершение."""

import contextlib
import io
import unittest
from unittest.mock import patch

from src.shell import Shell


class ShellTests(unittest.TestCase):
    """Сценарии минимального REPL."""

    def setUp(self) -> None:
        """Создать оболочку с предсказуемым приглашением."""
        self.shell = Shell(prompt="test$ ")

    def test_simple_parser(self) -> None:
        """Парсер разделяет строку по пробельным символам."""
        result = self.shell.execute("  ls   first    second ")
        self.assertEqual(result.output, "ls: arguments=['first', 'second']")

    def test_cd_stub(self) -> None:
        """Заглушка cd сообщает аргументы, но не меняет каталог."""
        result = self.shell.execute("cd /tmp")
        self.assertEqual(result.output, "cd: arguments=['/tmp']")

    def test_empty_input(self) -> None:
        """Пустая строка ничего не выводит."""
        self.assertEqual(self.shell.execute("  ").output, "")

    def test_unknown_command(self) -> None:
        """Неизвестная команда возвращает ошибку."""
        result = self.shell.execute("missing")
        self.assertFalse(result.ok)
        self.assertIn("command not found", result.output)

    def test_exit(self) -> None:
        """Команда exit завершает цикл только без аргументов."""
        self.assertTrue(self.shell.execute("exit").exit_requested)
        self.assertFalse(self.shell.execute("exit now").ok)

    def test_default_prompt_uses_os_data(self) -> None:
        """Приглашение строится на настоящих учётных данных ОС."""
        with patch("getpass.getuser", return_value="alice"):
            with patch("socket.gethostname", return_value="workstation"):
                shell = Shell()
        self.assertEqual(shell.prompt, "alice@workstation:~$ ")

    def test_repl(self) -> None:
        """Цикл печатает результаты и останавливается на exit."""
        output = io.StringIO()
        with patch("builtins.input", side_effect=["ls", "wrong", "exit"]):
            with contextlib.redirect_stdout(output):
                self.shell.repl()
        self.assertIn("ls: arguments=[]", output.getvalue())
        self.assertIn("wrong: command not found", output.getvalue())
