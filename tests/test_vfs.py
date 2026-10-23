"""Проверки CSV, base64, иерархии и работы строго в памяти."""

import csv
from pathlib import Path
import tempfile
import unittest

from src.vfs import VFSError, VirtualFileSystem


DATA = Path(__file__).resolve().parents[1] / "data"


class VFSTests(unittest.TestCase):
    """Изолированные сценарии загрузки виртуального диска."""

    def setUp(self) -> None:
        """Создать временный каталог для неправильных CSV."""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "test.csv"

    def write_rows(self, rows: list[tuple[str, str, str]]) -> None:
        """Сохранить CSV с тестовыми записями."""
        with self.path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["path", "kind", "content_base64"])
            writer.writerows(rows)

    def test_dot_at_root(self) -> None:
        """Путь '.' из корня соответствует ровно '/' (не '//')."""
        self.assertEqual(VirtualFileSystem.normalize(".", "/"), "/")

    def test_minimal(self) -> None:
        """Минимальная файловая система содержит только корень."""
        vfs = VirtualFileSystem.from_csv(str(DATA / "minimal.csv"))
        self.assertEqual(vfs.list_dir("/"), [])

    def test_many_files(self) -> None:
        """Корневой каталог содержит два отсортированных файла."""
        vfs = VirtualFileSystem.from_csv(str(DATA / "files.csv"))
        self.assertEqual(vfs.list_dir("/"), ["hello.txt", "info.txt"])

    def test_nested_and_binary(self) -> None:
        """Вложенность и бинарные данные восстанавливаются из base64."""
        vfs = VirtualFileSystem.from_csv(str(DATA / "nested.csv"))
        self.assertEqual(vfs.read_file("/bin/image.bin"), b"\x00\xffB")
        self.assertIn("lesson.txt", vfs.list_dir("/docs/tutorial"))
        self.assertEqual(vfs.normalize("../readme.txt", "/docs/tutorial"),
                         "/docs/readme.txt")

    def test_source_is_not_modified(self) -> None:
        """Загрузка и чтение не затрагивают содержимое CSV на диске."""
        path = DATA / "nested.csv"
        original = path.read_bytes()
        vfs = VirtualFileSystem.from_csv(str(path))
        vfs.read_file("/notes.txt")
        self.assertEqual(path.read_bytes(), original)

    def test_invalid_parent(self) -> None:
        """Без родительской директории файл недопустим."""
        self.write_rows([("/missing/file", "file", "")])
        with self.assertRaises(VFSError):
            VirtualFileSystem.from_csv(str(self.path))

    def test_path_traversal(self) -> None:
        """Неканонические пути не допускаются в источнике."""
        self.write_rows([("/docs/../secret", "file", "")])
        with self.assertRaises(VFSError):
            VirtualFileSystem.from_csv(str(self.path))

    def test_invalid_base64(self) -> None:
        """Ошибочное содержимое файла приводит к VFSError."""
        self.write_rows([("/bad", "file", "***")])
        with self.assertRaises(VFSError):
            VirtualFileSystem.from_csv(str(self.path))

    def test_incomplete_csv_row(self) -> None:
        """Пропущенное поле CSV даёт VFSError, а не TypeError."""
        self.path.write_text(
            "path,kind,content_base64\n/file,file\n", encoding="utf-8",
        )
        with self.assertRaises(VFSError):
            VirtualFileSystem.from_csv(str(self.path))

    def test_double_root_row(self) -> None:
        """Повторное описание корня отклоняется как дубликат."""
        self.write_rows([("/", "dir", ""), ("/", "dir", "")])
        with self.assertRaises(VFSError):
            VirtualFileSystem.from_csv(str(self.path))

    def test_missing_file(self) -> None:
        """Отсутствующий CSV не подменяется физической файловой системой."""
        with self.assertRaises(VFSError):
            VirtualFileSystem.from_csv(str(self.path))

    def test_file_is_not_a_directory(self) -> None:
        """Список файлов нельзя получить у обычного файла."""
        vfs = VirtualFileSystem.from_csv(str(DATA / "files.csv"))
        with self.assertRaises(VFSError):
            vfs.list_dir("/hello.txt")

    def test_duplicate_path(self) -> None:
        """Дублирующиеся пути недопустимы."""
        self.write_rows([("/x", "file", ""), ("/x", "file", "")])
        with self.assertRaises(VFSError):
            VirtualFileSystem.from_csv(str(self.path))
