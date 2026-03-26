@echo off
title NTL-SysToolbox - Démarrage
:: On se déplace dans le dossier du script
cd /d "%~dp0"
:: On lance le main avec Python
python main.py
:: Si le programme crash, on laisse la fenêtre ouverte pour lire l'erreur
if %errorlevel% neq 0 pause