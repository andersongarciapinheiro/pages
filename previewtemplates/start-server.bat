@echo off
title Email Preview — Servidor Local
echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   Email Preview - Servidor Local         ║
echo  ║   http://localhost:8080                  ║
echo  ╚══════════════════════════════════════════╝
echo.
echo  Pressione Ctrl+C para encerrar o servidor.
echo.

cd /d "%~dp0"

:: Gera o manifest antes de iniciar
echo  Gerando manifest.json...
python generate-manifest.py
echo.

:: Abre no navegador
echo  Abrindo no navegador...
start "" "http://localhost:8080"

:: Sobe o servidor
python -m http.server 8080

pause
