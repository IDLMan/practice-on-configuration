# Эмулятор UNIX shell — вариант 21

Практическая работа № 1, этапы 1–3. Python 3.10+, только stdlib.

## 1. REPL

Интерфейс CLI, приглашение `username@hostname:~$ ` из настоящих данных ОС.
Простой парсер делит ввод по пробелам (кавычки не интерпретируются).
`ls`, `cd` пока заглушки, печатающие имя и аргументы. `exit` завершает
оболочку; неизвестная команда и `exit` с аргументами дают ошибку.

## 2. Конфигурация

Параметры `--vfs`, `--prompt`, `--script`, `--config` доступны из CLI,
ключи JSON: `vfs`, `prompt`, `script`. CLI имеет приоритет над JSON.
Пути внутри JSON отсчитываются от его каталога, а CLI — от текущего.
Параметры выводятся в отладочный лог при запуске.

Стартовый скрипт поддерживает комментарии `#` (в том числе после команд).
Команда и её ответ печатаются вместе; ошибка отмечается номером строки.
После сценария приложение завершается; если были ошибки, код возврата 1.

## 3. Виртуальная файловая система (VFS)

CSV-источник загружается в оперативную память, не распаковывается и не
меняется на диске. Все последующие операции производятся над объектами
Python, без работы с оригинальными файлами. При отсутствии `--vfs`
используется `data/nested.csv`. Ошибка загрузки приводит к коду возврата 1.

CSV-схема: `path,kind,content_base64`.
`path` — канонический абсолютный POSIX-путь (`/docs/file.txt`),
`kind` — `dir` или `file`, `content_base64` — base64 содержимого файла.
У директорий содержимое пустое. Корень `/` существует автоматически;
промежуточные каталоги должны иметь явные записи в CSV.
Пример: `/docs`, `/docs/tutorial`, `/docs/tutorial/lesson.txt`.

Три тестовых образа: `data/minimal.csv`, `data/files.csv`,
`data/nested.csv` (3+ уровня, в том числе бинарный файл).
На этапе 3 `ls`/`cd` остаются заглушками; логика появится на этапе 4.

## Команды для запуска и тестов

```bash
./run.sh
./run.sh --config examples/config.json
./run.sh --vfs data/minimal.csv --script examples/demo_vfs.txt
python3 -m unittest discover -s tests -v
./examples/run_vfs_minimal.sh
./examples/run_vfs_files.sh
./examples/run_vfs_nested.sh
./examples/run_vfs_error.sh
./examples/run_vfs_command_errors.sh
```

Скрипты ОС для конфигурации: `examples/run_defaults.sh`,
`examples/run_custom_prompt.sh`, `examples/run_from_config.sh`.
Linux/macOS: `./run.sh`; Windows: `run.bat`.
Для ошибок команд есть `examples/demo_vfs_errors.txt` и сценарий ОС
`examples/run_vfs_command_errors.sh`, который проверяет код возврата.
После успешного тестирования сделать коммит третьего этапа.
