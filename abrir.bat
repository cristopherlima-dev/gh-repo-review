@echo off
title gh-repo-review

rem Vai para a pasta onde este .bat esta (funciona mesmo por atalho)
cd /d "%~dp0"
set PYTHONUTF8=1

rem Prefere o inicializador py.exe do Windows: nao depende do PATH,
rem que pode estar desatualizado quando o .bat e aberto pelo Explorer.
set "PY=%SystemRoot%\py.exe"
if not exist "%PY%" set "PY=python"
"%PY%" --version >nul 2>&1 || (echo Python 3 nao encontrado. Instale em https://www.python.org/downloads/ & pause & exit /b 1)

chcp 65001 >nul
"%PY%" servidor.py

rem Se o servidor parar com erro, mantem a janela aberta para ler a mensagem
if errorlevel 1 pause
