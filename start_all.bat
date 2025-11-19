@echo off
echo ========================================
echo   Jump Analyzer Pro - Avvio Sistema
echo ========================================
echo.

REM Avvia backend in una nuova finestra
echo Avvio Backend Flask...
start "Backend Flask" cmd /k "cd backend && call run.bat"

REM Attendi 3 secondi per dare tempo al backend di avviarsi
timeout /t 3 /nobreak >nul

REM Avvia frontend in una nuova finestra
echo Avvio Frontend Svelte...
start "Frontend Svelte" cmd /k "cd frontend && call run.bat"

echo.
echo Sistema avviato!
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Premi un tasto per chiudere questa finestra...
pause >nul

