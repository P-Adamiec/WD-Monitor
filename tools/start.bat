@echo off
chcp 65001 >nul
echo ===================================================
echo Uruchamianie monitora WD...
echo ===================================================

echo Sprawdzanie czy Docker dziala...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [BŁĄD] Docker nie jest uruchomiony! Uruchom aplikacje Docker Desktop i sprobuj ponownie.
    pause
    exit /b
)

echo Budowanie i uruchamianie kontenerow (Docker)...
docker-compose up -d --build

echo.
echo ===================================================
echo Projekt zostal uruchomiony w tle!
echo Aplikacja powinna byc wrotce dostepna pod adresem:
echo http://localhost:5000
echo ===================================================
pause
