@echo off
cd /d "%~dp0"
python new_project.py
if errorlevel 1 (
    echo.
    echo Python est introuvable ou une erreur s'est produite.
    echo Verifiez que Python est installe et accessible dans le PATH.
    pause
)
