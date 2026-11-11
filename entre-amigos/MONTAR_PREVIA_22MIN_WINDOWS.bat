@echo off
chcp 65001 >nul
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title ENTRE AMIGOS - PREVIA 22 MIN (Full HD)
echo.
echo ===============================================================
echo    ENTRE AMIGOS 2024 - MONTAR A PREVIA DO MANIFESTO ATUAL
echo ===============================================================
echo.
echo Esta montagem usa as 33 cenas e os complementos definidos em
echo projeto_v1.json, sem inserir novas gravacoes ou repetir blocos.
echo.
echo Obrigatorio antes de iniciar:
echo 1. Pasta de videos, fotos e musicas originais disponivel offline.
echo 2. blocos\BLOCO_01.mp4 (Descript, 2min43s, inclui abertura).
echo 3. blocos\BLOCO_02.mp4 (Descript, 1min11s).
echo.
echo O programa primeiro mostra TODOS os arquivos ausentes.
echo Se houver falta, o MP4 nao sera declarado como pronto.
echo.
call "%~dp0MONTAR_V1_WINDOWS.bat" %*
if errorlevel 1 goto :FALHA_MONTAGEM
if defined ENTRE_AMIGOS_TESTE_SO_VERIFICAR (
  echo Teste do BAT de verificacao concluido.
  exit /b 0
)
echo.
echo ===============================================================
echo    VALIDANDO E COPIANDO A PREVIA PARA O NOME SOLICITADO
echo ===============================================================
echo.
py -3 "%~dp0validar_previa.py"
if errorlevel 1 goto :FALHA_VALIDACAO
echo.
echo PRONTO, ASSISTA:
echo "%~dp0saida\ENTRE_AMIGOS_V1_PREVIA_22MIN.mp4"
echo.
echo A duracao exata foi exibida acima, nao necessariamente 22 minutos.
pause
exit /b 0
:FALHA_MONTAGEM
echo.
echo NAO FOI GERADA A PREVIA: fonte faltando ou montagem incompleta.
echo Corrija a lista exibida e execute este BAT novamente.
echo As cenas concluidas serao reaproveitadas.
pause
exit /b 3
:FALHA_VALIDACAO
echo.
echo NOME DE ENTREGA NAO GERADO. Falhou a verificacao do MP4 real.
echo Veja o detalhe acima; nao compartilhe o arquivo como completo.
pause
exit /b 4
