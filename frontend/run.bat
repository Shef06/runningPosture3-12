@echo off
echo Avvio Frontend Svelte...
echo.

REM Controlla se node_modules esiste
if not exist node_modules (
    echo ATTENZIONE: Dipendenze non installate!
    echo Installazione dipendenze in corso...
    call npm install
)

REM Avvia il server di sviluppo
call npm run dev

pause

