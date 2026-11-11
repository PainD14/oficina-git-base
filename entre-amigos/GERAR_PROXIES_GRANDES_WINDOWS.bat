@echo off
chcp 65001 >nul
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title ENTRE AMIGOS - 20 Proxies de Analise
echo.
echo ==========================================================
echo ENTRE AMIGOS: PROXIES DOS 20 VIDEOS GRANDES
echo ==========================================================
echo.
echo Esse processo gera COPIAS leves em 720p, com AUDIO.
echo Os 20 arquivos ORIGINAIS continuam intactos.
echo A saida sera salva na pasta "proxies_para_decupagem".
echo.
where ffmpeg >nul 2>&1
if errorlevel 1 goto :FALTA_FFMPEG
where ffprobe >nul 2>&1
if errorlevel 1 goto :FALTA_FFMPEG
py -3 --version >nul 2>&1
if errorlevel 1 goto :FALTA_PYTHON
echo.
set "MIDIAS=%~1"
if not defined MIDIAS set /p "MIDIAS=Local da pasta original do Drive: "
set "MIDIAS=%MIDIAS:"=%"
if not exist "%MIDIAS%\" goto :FALTA_PASTA
echo.
echo Procurando e convertendo os 20 originais grandes.
echo Pode levar tempo, e possivel interromper e executar novamente.
py -3 "%~dp0gerar_proxies.py" --midias "%MIDIAS%" --dest "%~dp0proxies_para_decupagem"
if errorlevel 1 (
    echo.
    echo Alguns arquivos nao foram processados. Consulte INDICE_PROXIES.json.
    echo Execute o BAT novamente depois de corrigir as pendencias.
    pause
    exit /b 3
)
echo.
echo Proxies prontos. Pasta: %~dp0proxies_para_decupagem
echo Encaminhe os proxies para revisao, nao use como video final.
pause
exit /b 0
:FALTA_FFMPEG
echo ERRO: FFmpeg/FFprobe nao encontrados.
echo PowerShell: winget install --id Gyan.FFmpeg --exact
pause
exit /b 2
:FALTA_PYTHON
echo ERRO: Python 3 nao encontrado.
pause
exit /b 2
:FALTA_PASTA
echo ERRO: pasta do Google Drive nao localizada.
pause
exit /b 2
