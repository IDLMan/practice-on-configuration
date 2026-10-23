"""Неизменяемый источник CSV и файловая система в оперативной памяти."""

import base64
import binascii
import csv
from dataclasses import dataclass
from pathlib import Path
import posixpath


class VFSError(ValueError):
    """Ошибочная операция с виртуальной файловой системой."""


@dataclass
class Entry:
    """Узел каталога или файла с двоичным содержимым."""

    is_dir: bool
    content: bytes = b""


class VirtualFileSystem:
    """Иерархия файлов, полностью хранимая в словаре памяти."""

    def __init__(self) -> None:
        """Создать пустую виртуальную корневую директорию."""
        self.entries: dict[str, Entry] = {"/": Entry(is_dir=True)}

    @staticmethod
    def normalize(path: str, current: str = "/") -> str:
        """Привести относительный/абсолютный путь к абсолютному POSIX."""
        if not path:
            return current
        combined = posixpath.join(current, path)
        return posixpath.normpath(combined)

    @staticmethod
    def validate_csv_path(path: str) -> None:
        """Отвергнуть неканонические пути в исходном CSV."""
        if not path.startswith("/") or path.startswith("//"):
            raise VFSError(f"CSV path must be absolute: {path}")
        if path != posixpath.normpath(path):
            raise VFSError(f"Non-canonical CSV path: {path}")
        if any(item in {".", ".."} for item in path.split("/")):
            raise VFSError(f"Invalid CSV path component: {path}")

    def require(self, path: str) -> Entry:
        """Получить существующий узел или выбросить понятную ошибку."""
        if path not in self.entries:
            raise VFSError(f"No such file or directory: {path}")
        return self.entries[path]

    def require_dir(self, path: str) -> Entry:
        """Проверить существование каталога."""
        entry = self.require(path)
        if not entry.is_dir:
            raise VFSError(f"Not a directory: {path}")
        return entry

    def list_dir(self, path: str) -> list[str]:
        """Перечислить имена непосредственных дочерних элементов."""
        self.require_dir(path)
        return sorted(
            posixpath.basename(name)
            for name in self.entries
            if name != path and posixpath.dirname(name) == path
        )

    def read_file(self, path: str) -> bytes:
        """Считать содержимое виртуального файла, не обращаясь к диску."""
        entry = self.require(path)
        if entry.is_dir:
            raise VFSError(f"Is a directory: {path}")
        return entry.content

    def copy_file(
        self, source: str, destination: str, current: str = "/",
    ) -> str:
        """Копировать файл в памяти с UNIX-подобной семантикой cp."""
        source_path = self.normalize(source, current)
        target_path = self.normalize(destination, current)
        content = self.read_file(source_path)
        target = self.entries.get(target_path)
        if target is not None and target.is_dir:
            target_path = posixpath.join(
                target_path, posixpath.basename(source_path),
            )
        existing = self.entries.get(target_path)
        if existing is not None and existing.is_dir:
            raise VFSError(f"Cannot overwrite directory: {target_path}")
        self.require_dir(posixpath.dirname(target_path))
        if target_path == source_path:
            raise VFSError("Source and destination are the same file")
        self.entries[target_path] = Entry(is_dir=False, content=content)
        return target_path

    @staticmethod
    def decode_content(path: str, encoded: str) -> bytes:
        """Декодировать base64 с диагностикой некорректных данных."""
        try:
            return base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise VFSError(f"Invalid base64 at {path}") from exc

    @staticmethod
    def validate_csv_row(row: dict[str, str]) -> None:
        """Проверить наличие всех трёх строковых полей CSV."""
        expected = {"path", "kind", "content_base64"}
        if set(row) != expected:
            raise VFSError("CSV row has invalid fields")
        if any(not isinstance(value, str) for value in row.values()):
            raise VFSError("CSV row has missing or invalid values")

    def add_csv_row(self, row: dict[str, str]) -> None:
        """Вставить один узел, удостоверившись в наличии родителя."""
        self.validate_csv_row(row)
        path = row["path"]
        self.validate_csv_path(path)
        if row["kind"] not in {"dir", "file"}:
            raise VFSError(f"Invalid kind at {path}")
        if path in self.entries and path != "/":
            raise VFSError(f"Duplicate CSV path: {path}")
        if path == "/" and row["kind"] != "dir":
            raise VFSError("Root must be a directory")
        content = self.decode_content(path, row["content_base64"])
        if row["kind"] == "dir" and content:
            raise VFSError(f"Directory has content: {path}")
        if path != "/":
            self.require_dir(posixpath.dirname(path))
        self.entries[path] = Entry(row["kind"] == "dir", content)

    @classmethod
    def from_csv(cls, filename: str) -> "VirtualFileSystem":
        """Загрузить CSV в память без изменения исходного файла."""
        try:
            with Path(filename).open(newline="", encoding="utf-8") as stream:
                reader = csv.DictReader(stream)
                expected = ["path", "kind", "content_base64"]
                if reader.fieldnames != expected:
                    raise VFSError("Invalid CSV header")
                rows = list(reader)
        except (OSError, UnicodeError, csv.Error) as exc:
            raise VFSError(f"Cannot load VFS {filename}: {exc}") from exc
        vfs = cls()
        seen: set[str] = set()
        rows.sort(key=lambda row: (row.get("path") or "").count("/"))
        for row in rows:
            path = row.get("path")
            if path in seen:
                raise VFSError(f"Duplicate CSV path: {path}")
            seen.add(path)
            vfs.add_csv_row(row)
        return vfs
