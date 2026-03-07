@echo off
chcp 65001 >nul
echo ===================================================
echo Zatrzymywanie projektu...
echo ===================================================

docker-compose down

echo.
echo ===================================================
echo Projekt zatrzymany!
echo ===================================================
pause
