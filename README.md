# Эмулятор UNIX shell — вариант 21

Практическая работа № 1; Python 3.10+ без сторонних зависимостей.

## Этапы 1–2: REPL и конфигурация

CLI выводит приглашение `username@hostname:~$ ` на основе данных реальной ОС.
Строка разбивается по пробелам; кавычки не поддерживаются по варианту.
Команды `ls`, `cd` являются заглушками, `exit` завершает приложение.
Неизвестные команды и недопустимые аргументы `exit` дают ошибку.

Настройки: `--vfs PATH`, `--prompt TEXT`, `--script PATH`, `--config PATH`.
В JSON допустимы строковые ключи `vfs`, `prompt`, `script`.
Пути к VFS и скрипту в JSON отсчитываются от папки JSON-файла,
пути CLI — от текущего рабочего каталога. CLI имеет приоритет над JSON.
На этапе 2 путь VFS только печатается; загрузка VFS будет на этапе 3.
При запуске выводятся все четыре настроечных параметра для отладки.

Стартовый сценарий: одна команда на строке, строки и хвосты после `#`
считаются комментариями (синтаксис Python). Ввод и вывод печатаются
как диалог. Ошибки фиксируются с номером строки, выполнение продолжается;
код завершения приложения — 1, если была хотя бы одна ошибка.
`exit` прекращает выполнение сценария. При `--script` REPL не запускается.

## Запуск, тесты и скрипты ОС

```bash
python3 -m src.main
python3 -m src.main --prompt 'custom$ ' --script examples/startup.txt
python3 -m src.main --config examples/config.json
python3 -m unittest discover -s tests -v
./run.sh --config examples/config.json
```

Скрипты реальной ОС: `examples/run_defaults.sh`,
`examples/run_custom_prompt.sh`, `examples/run_from_config.sh`
(аналог под Windows — `examples/run_from_config.bat`).

Пример:

```text
Configuration: None
VFS: None
Prompt: custom$ 
Startup script: examples/startup.txt
custom$ ls docs
ls: arguments=['docs']
custom$ cd /docs
cd: arguments=['/docs']
custom$ exit
```

Linux/macOS: `./run.sh`. Windows: `run.bat`.
После проверки тестов сохранить второй этап отдельным коммитом.
