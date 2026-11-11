@echo off
chcp 65001 >nul
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title ENTRE AMIGOS - Renderizador seguro da Versao 1

echo.
echo ===========================================================
echo    ENTRE AMIGOS 2024 - MONTAGEM V1 (WINDOWS)
echo ===========================================================
echo.
echo Este programa NAO modifica os videos e fotos originais.
echo Salva o progresso em "saida\PROGRESSO.json".
echo.
where ffmpeg >nul 2>&1
if errorlevel 1 goto :NO_FFMPEG
where ffprobe >nul 2>&1
if errorlevel 1 goto :NO_FFMPEG

py -3 --version >nul 2>&1
if errorlevel 1 goto :NO_PYTHON
py -3 -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)"
if errorlevel 1 goto :OLD_PYTHON

if not exist "%~dp0blocos\BLOCO_01.mp4" goto :NO_BLOCK_1
if not exist "%~dp0blocos\BLOCO_02.mp4" goto :NO_BLOCK_2

echo.
echo Caminho da pasta ORIGINAL do documentario no seu computador.
echo Essa pasta deve conter subpastas com videos, fotos e musicas.
echo Exemplo: G:\Meu Drive\ENTRE AMIGOS
set "MIDIAS="
set /p "MIDIAS=Cole o caminho completo: "
set "MIDIAS=%MIDIAS:"=%"
if not defined MIDIAS goto :BAD_FOLDER
if not exist "%MIDIAS%\" goto :BAD_FOLDER

echo.
echo [1/4] Conferindo bibliotecas para fotos JPG e HEIC...
py -3 -c "import PIL, pillow_heif" >nul 2>&1
if errorlevel 1 (
  py -3 -m pip install -r "%~dp0requirements.txt"
  if errorlevel 1 goto :PIP_FAILED
)

echo.
echo [2/4] Verificando manifesto, blocos, fontes e trilhas...
py -3 "%~dp0montar_v1.py" --midias "%MIDIAS%" --blocos "%~dp0blocos" --verificar
if errorlevel 1 goto :CHECK_FAILED

echo.
echo [3/4] Renderizando. Cenas e cortes prontos sao reutilizados
echo APENAS se o material e as configuracoes nao mudaram.
echo NAO sao usadas tomadas extras selecionadas apenas pela data.
echo.
py -3 "%~dp0montar_v1.py" --midias "%MIDIAS%" --blocos "%~dp0blocos"
if errorlevel 1 goto :RENDER_FAILED

echo.
echo [4/4] Arquivo final e informacoes:
echo    "%~dp0saida\ENTRE_AMIGOS_V1_REVISAO.mp4"
echo    "%~dp0saida\RESULTADO.json"
echo.
echo Confirme o video no seu reprodutor antes de publicar.
pause
exit /b 0

:NO_FFMPEG
echo.
echo ERRO: FFmpeg ou FFprobe nao encontrado.
echo No PowerShell, execute: winget install --id Gyan.FFmpeg --exact
echo Depois, feche e abra novamente este BAT.
pause
exit /b 2
:NO_PYTHON
echo.
echo ERRO: Python 3 nao localizado. Instale Python 3.12 ou superior.
echo Em Windows, consulte https://www.python.org/downloads/windows/
pause
exit /b 2
:OLD_PYTHON
echo.
echo ERRO: o Python deve ter versao 3.12 ou superior.
pause
exit /b 2
:NO_BLOCK_1
echo.
echo ERRO: falta "blocos\BLOCO_01.mp4".
echo Assista e baixe: https://share.descript.com/view/7aTMx3UqC9x
pause
exit /b 2
:NO_BLOCK_2
echo.
echo ERRO: falta "blocos\BLOCO_02.mp4".
echo Assista e baixe: https://share.descript.com/view/WNgRx7FydqK
pause
exit /b 2
:BAD_FOLDER
echo.
echo ERRO: pasta do documentario nao encontrada.
echo Verifique a unidade do Google Drive e o caminho digitado.
pause
exit /b 2
:PIP_FAILED
echo.
echo ERRO: nao foi possivel instalar as bibliotecas de imagens.
pause
exit /b 2
:CHECK_FAILED
echo.
echo VERIFICACAO BLOQUEOU A MONTAGEM: confira a lista de
echo arquivos e musicas ausentes acima. Nada foi renderizado.
pause
exit /b 2
:RENDER_FAILED
echo.
echo A MONTAGEM FOI INTERROMPIDA OU ESTA INCOMPLETA.
echo Veja "saida\PROGRESSO.json" e "saida\segmentos".
echo Depois de corrigir, execute este BAT novamente.
echo Os trechos validos serao reaproveitados.
pause
exit /b 3
