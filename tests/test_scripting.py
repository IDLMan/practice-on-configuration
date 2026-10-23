"""Проверки стартовых скриптов с комментариями."""

import io
from pathlib import Path
import tempfile
import unittest

from src.scripting import run_script
from src.shell import Shell


class ScriptingTests(unittest.TestCase):
    """Тесты исполнения строк сценария."""

    def setUp(self) -> None:
        """Создать временный файл сценария."""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "demo.txt"
        self.output = io.StringIO()
        self.shell = Shell(prompt="demo$ ")

    def test_comments_and_echo(self) -> None:
        """Комментарии пропускаются, команды и результат видны."""
        self.path.write_text(
            "# ignore this\nls a b # comment\nexit\nls not-run\n",
            encoding="utf-8",
        )
        self.assertTrue(run_script(self.shell, str(self.path), self.output))
        result = self.output.getvalue()
        self.assertIn("demo$ ls a b", result)
        self.assertNotIn("not-run", result)
        self.assertNotIn("ignore this", result)

    def test_reports_command_errors(self) -> None:
        """Ошибка содержит номер строки, выполнение продолжается."""
        self.path.write_text("# note\nbad\nls\n", encoding="utf-8")
        self.assertFalse(run_script(self.shell, str(self.path), self.output))
        self.assertIn("Script error at line 2", self.output.getvalue())
        self.assertIn("demo$ ls", self.output.getvalue())
