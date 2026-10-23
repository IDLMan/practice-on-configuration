"""Встроенная проверка правил таблицы оформления репозитория."""

import ast
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_LINES = 1000
MAX_LINE_LENGTH = 80
MAX_FUNCTION_LINES = 40
MAX_ARGUMENTS = 7
MAX_COMPLEXITY = 10
NAME_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")
CLASS_PATTERN = re.compile(r"^[A-Z][A-Za-z0-9]*$")
UNITTEST_METHODS = {"setUp", "tearDown", "setUpClass"}


def python_sources() -> list[Path]:
    """Получить исходные файлы и тесты, исключая кеши."""
    return sorted([
        *ROOT.joinpath("src").rglob("*.py"),
        *ROOT.joinpath("tests").rglob("*.py"),
    ])


def get_complexity(function: ast.AST) -> int:
    """Приблизить цикломатическую сложность по развилкам AST."""
    complexity = 1
    branching = (ast.If, ast.For, ast.While, ast.IfExp,
                 ast.ExceptHandler, ast.AsyncFor)
    for node in ast.walk(function):
        if isinstance(node, branching):
            complexity += 1
        if isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
    return complexity


class QualityTests(unittest.TestCase):
    """Автоматическая проверка норм качества Python-кода."""

    def test_line_and_file_lengths(self) -> None:
        """Проверить Р1 и Р2: размер файла и длину строк."""
        for path in python_sources():
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertLessEqual(len(lines), MAX_FILE_LINES, str(path))
            for number, line in enumerate(lines, start=1):
                with self.subTest(path=str(path), line=number):
                    self.assertLessEqual(len(line), MAX_LINE_LENGTH)

    def test_function_limits_and_docstrings(self) -> None:
        """Проверить Ф1, А1 и К1 для каждого определения."""
        for path in python_sources():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            self.assertIsNotNone(ast.get_docstring(tree), str(path))
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    continue
                self.assertIsNotNone(ast.get_docstring(node), str(path))
                if isinstance(node, ast.FunctionDef):
                    self.check_function(node, path)

    def check_function(self, node: ast.FunctionDef, path: Path) -> None:
        """Проверить длину и число явных аргументов функции."""
        count = node.end_lineno - node.lineno + 1
        self.assertLessEqual(count, MAX_FUNCTION_LINES, str(path))
        arguments = node.args.posonlyargs + node.args.args
        arguments += node.args.kwonlyargs
        if arguments and arguments[0].arg in {"self", "cls"}:
            arguments = arguments[1:]
        self.assertLessEqual(len(arguments), MAX_ARGUMENTS, str(path))

    def test_complexity_and_magic_numbers(self) -> None:
        """Проверить Ц1 и М1: ветвления и числа в сравнениях."""
        for path in python_sources():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    score = get_complexity(node)
                    self.assertLessEqual(score, MAX_COMPLEXITY,
                                         f"{path}: {node.name}")
                if isinstance(node, ast.Compare):
                    operands = [node.left, *node.comparators]
                    for operand in operands:
                        if isinstance(operand, ast.Constant):
                            value = operand.value
                            self.assertNotIsInstance(value, (int, float))

    def test_names(self) -> None:
        """Проверить базовые правила И1 (PEP 8)."""
        for path in python_sources():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self.assertRegex(node.name, CLASS_PATTERN, str(path))
                if isinstance(node, ast.FunctionDef):
                    if node.name in UNITTEST_METHODS:
                        continue
                    self.assertRegex(node.name, NAME_PATTERN, str(path))
