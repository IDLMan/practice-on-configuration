"""Проверки копирования виртуальных файлов только в памяти."""

from pathlib import Path
import unittest

from src.shell import Shell
from src.vfs import Entry, VFSError, VirtualFileSystem


SOURCE = Path(__file__).resolve().parents[1] / "data" / "nested.csv"


class CopyTests(unittest.TestCase):
    """Сценарии cp с различными путями, файлами и ошибками."""

    def setUp(self) -> None:
        """Создать свежую VFS и оболочку для каждого теста."""
        self.vfs = VirtualFileSystem.from_csv(str(SOURCE))
        self.shell = Shell(prompt="test$ ", vfs=self.vfs)

    def test_copy_to_new_file(self) -> None:
        """cp создаёт копию с новым именем в каталоге."""
        self.assertTrue(self.shell.execute(
            "cp /docs/readme.txt /docs/duplicate.txt",
        ).ok)
        self.assertEqual(self.vfs.read_file("/docs/duplicate.txt"),
                         self.vfs.read_file("/docs/readme.txt"))

    def test_copy_into_existing_directory(self) -> None:
        """При копировании в каталог сохраняется исходное имя."""
        self.assertTrue(self.shell.execute(
            "cp /notes.txt /docs",
        ).ok)
        self.assertIn("notes.txt", self.vfs.list_dir("/docs"))

    def test_copy_relative_paths(self) -> None:
        """cp разрешает относительные пути от cwd."""
        self.shell.execute("cd /docs")
        result = self.shell.execute("cp readme.txt tutorial/copy.txt")
        self.assertTrue(result.ok)
        self.assertEqual(self.vfs.read_file("/docs/tutorial/copy.txt"),
                         self.vfs.read_file("/docs/readme.txt"))

    def test_overwrite_existing_file(self) -> None:
        """Существующий файл назначения заменяется в памяти."""
        source = self.vfs.read_file("/docs/readme.txt")
        self.assertTrue(self.shell.execute(
            "cp /docs/readme.txt /notes.txt",
        ).ok)
        self.assertEqual(self.vfs.read_file("/notes.txt"), source)

    def test_copy_binary_file(self) -> None:
        """Побайтовое копирование сохраняет нетекстовые данные."""
        self.assertTrue(self.shell.execute(
            "cp /bin/image.bin /bin/second.bin",
        ).ok)
        self.assertEqual(self.vfs.read_file("/bin/second.bin"), b"\x00\xffB")

    def test_invalid_copy_paths(self) -> None:
        """cp не допускает отсутствующий источник или каталог-источник."""
        for command in (
            "cp /missing /notes.txt",
            "cp /docs /bin/new",
            "cp /notes.txt /missing/new.txt",
            "cp /notes.txt /notes.txt",
        ):
            with self.subTest(command=command):
                self.assertFalse(self.shell.execute(command).ok)

    def test_directory_remains_directory_after_copy_error(self) -> None:
        """cp не должен повреждать каталог с совпадающим именем."""
        self.vfs.entries["/docs/notes.txt"] = Entry(is_dir=True)
        self.vfs.entries["/docs/notes.txt/child"] = Entry(
            is_dir=False, content=b"protected",
        )
        result = self.shell.execute("cp /notes.txt /docs")
        self.assertFalse(result.ok)
        self.assertTrue(self.vfs.require("/docs/notes.txt").is_dir)
        self.assertEqual(
            self.vfs.read_file("/docs/notes.txt/child"), b"protected",
        )

    def test_invalid_number_of_arguments(self) -> None:
        """cp требует ровно два аргумента."""
        self.assertFalse(self.shell.execute("cp").ok)
        self.assertFalse(self.shell.execute("cp a").ok)
        self.assertFalse(self.shell.execute("cp a b c").ok)

    def test_source_csv_not_modified(self) -> None:
        """Изменения остаются в памяти и не затрагивают исходный CSV."""
        before = SOURCE.read_bytes()
        self.shell.execute("cp /notes.txt /docs/copy.txt")
        self.assertEqual(SOURCE.read_bytes(), before)
        reloaded = VirtualFileSystem.from_csv(str(SOURCE))
        with self.assertRaises(VFSError):
            reloaded.read_file("/docs/copy.txt")

    def test_copied_file_available_for_commands(self) -> None:
        """Копия доступна через ls и tac сразу после выполнения cp."""
        self.shell.execute("cp /docs/readme.txt /docs/new.txt")
        self.assertIn("new.txt", self.shell.execute("ls /docs").output)
        self.assertIn("line three", self.shell.execute(
            "tac /docs/new.txt",
        ).output)
