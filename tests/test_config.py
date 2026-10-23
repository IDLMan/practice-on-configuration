"""Проверки JSON-конфигурации и приоритетов CLI."""

import json
from pathlib import Path
import tempfile
import unittest

from src.config import ConfigError, get_settings, load_config


class ConfigTests(unittest.TestCase):
    """Тестирование входных параметров и ошибок."""

    def setUp(self) -> None:
        """Создать временную папку для конфигурации."""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "config.json"

    def write_config(self, data: object) -> None:
        """Записать тестовую конфигурацию."""
        self.path.write_text(json.dumps(data), encoding="utf-8")

    def test_cli_priority(self) -> None:
        """Значения командной строки перекрывают JSON."""
        self.write_config({"prompt": "json$ ", "vfs": "vfs.csv"})
        settings = get_settings([
            "--config", str(self.path), "--prompt", "cli$ ",
            "--vfs", "cli.csv",
        ])
        self.assertEqual(settings.prompt, "cli$ ")
        self.assertEqual(settings.vfs, "cli.csv")

    def test_resolve_config_relative_paths(self) -> None:
        """Пути внутри JSON разрешаются относительно самого JSON."""
        self.write_config({"script": "demo.txt", "vfs": "data.csv"})
        settings = get_settings(["--config", str(self.path)])
        self.assertEqual(
            Path(settings.script).name,
            "demo.txt",
        )
        self.assertTrue(
            Path(settings.script).parent.samefile(self.path.parent)
        )
        self.assertEqual(
            Path(settings.vfs).name,
            "data.csv",
        )
        self.assertTrue(
            Path(settings.vfs).parent.samefile(self.path.parent)
        )

    def test_invalid_json(self) -> None:
        """Ошибки синтаксиса JSON обнаруживаются до запуска."""
        self.path.write_text("{broken", encoding="utf-8")
        with self.assertRaises(ConfigError):
            load_config(str(self.path))

    def test_unknown_key(self) -> None:
        """Неизвестные поля JSON отклоняются."""
        self.write_config({"unexpected": 1})
        with self.assertRaises(ConfigError):
            load_config(str(self.path))

    def test_wrong_type(self) -> None:
        """Поля JSON должны быть строками."""
        self.write_config({"prompt": 5})
        with self.assertRaises(ConfigError):
            load_config(str(self.path))

    def test_without_config(self) -> None:
        """Параметры могут быть получены только из CLI."""
        settings = get_settings(["--prompt", "only-cli$ "])
        self.assertEqual(settings.prompt, "only-cli$ ")
        self.assertIsNone(settings.vfs)
