@echo off
chcp 65001 >nul
setlocal EnableExtensions
title ENTRE AMIGOS - MONTAGEM V1

echo.
echo ==============================================
echo ENTRE AMIGOS 2024 - RENDERIZADOR WINDOWS
echo ==============================================
echo.
where ffmpeg >nul 2>&1
if errorlevel 1 (
  echo ERRO: FFmpeg nao foi encontrado no PATH.
  echo Instale em uma janela do PowerShell com:
  echo   winget install --id Gyan.FFmpeg --exact
  echo Feche e abra novamente esta janela depois de instalar.
  pause
  exit /b 2
)
where ffprobe >nul 2>&1
if errorlevel 1 (
  echo ERRO: ffprobe nao encontrado. Reinstale FFmpeg completo.
  pause
  exit /b 2
)
py -3 --version >nul 2>&1
if errorlevel 1 (
  echo ERRO: Python 3 nao encontrado.
  echo Instale Python 3.12 pelo site python.org ou pelo winget.
  pause
  exit /b 2
)
if not exist "%~dp0blocos\BLOCO_01.mp4" (
  echo ERRO: Falta BLOCO_01.mp4 em "%~dp0blocos".
  echo Baixe de https://share.descript.com/view/7aTMx3UqC9x
  pause
  exit /b 2
)
if not exist "%~dp0blocos\BLOCO_02.mp4" (
  echo ERRO: Falta BLOCO_02.mp4 em "%~dp0blocos".
  echo Baixe de https://share.descript.com/view/WNgRx7FydqK
  pause
  exit /b 2
)
echo.
echo Cole abaixo o caminho LOCAL da pasta principal do seu Drive.
echo Exemplo: G:\Meu Drive\Documentario ou D:\ENTRE AMIGOS
set /p "MIDIAS=Caminho da pasta das midias: "
set "MIDIAS=%MIDIAS:"=%"
if not exist "%MIDIAS%" (
  echo ERRO: Essa pasta nao existe: "%MIDIAS%"
  pause
  exit /b 2
)
echo.
echo Instalando biblioteca de fotos e formato HEIC...
py -3 -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
  echo Erro ao instalar bibliotecas. Consulte o erro acima.
  pause
  exit /b 2
)
echo.
echo Validando fontes locais sem editar os arquivos...
py -3 "%~dp0montar_v1.py" --midias "%MIDIAS%" --blocos "%~dp0blocos" --verificar
if errorlevel 1 (
  echo ERRO DE VERIFICACAO. Nao iniciou a renderizacao.
  pause
  exit /b 2
)
echo.
echo Iniciando V1 com tomadas extras reais, sem repetir arquivos e sem
echo prolongar tomadas para atingir a duracao de 40 min.
echo As extras por data ainda precisarao de revisao humana.
py -3 "%~dp0montar_v1.py" --midias "%MIDIAS%" --blocos "%~dp0blocos" --extras
if errorlevel 1 (
  echo.
  echo Houve um erro. O progresso salvo esta na pasta saida.
  echo Rode este mesmo BAT depois de corrigir. Cenas prontas sao reutilizadas.
  pause
  exit /b 1
)
echo.
echo ====================================================
echo MONTAGEM GERADA:
echo %~dp0saida\ENTRE_AMIGOS_V1_REVISAO.mp4
echo Os tempos e pendencias reais estao no RESULTADO.json.
echo ====================================================
pause
