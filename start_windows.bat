@echo off
cd /d "%~dp0"
python bot.py
if errorlevel 1 (
    echo.
    echo XATO: Yuqoridagi xabarni tekshiring. Python va .env sozlamalarini ko'ring.
    pause
)
