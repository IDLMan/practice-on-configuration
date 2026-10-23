@echo off
cd /d "%~dp0\.."
call run.bat --config examples/config.json --prompt "windows$ "
