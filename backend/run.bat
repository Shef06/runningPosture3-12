@echo off
echo Avvio Backend Flask...
echo.

REM Attiva ambiente virtuale se esiste
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo ATTENZIONE: Ambiente virtuale non trovato!
    echo Creare l'ambiente con: python -m venv venv
    echo Poi installare dipendenze con: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Avvia l'applicazione Flask
python app.py

pause

