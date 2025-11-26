@echo off
REM ====================================================================
REM Iniciar Aplicacao Completa - CV Sob Medida
REM ====================================================================
REM Este script inicia backend e frontend em janelas separadas
REM Com validacao automatica de pre-requisitos
REM ====================================================================

echo.
echo ====================================================================
echo    CV SOB MEDIDA - INICIALIZACAO COMPLETA
echo ====================================================================
echo.

REM ====================================================================
REM ETAPA 1: Validar Pre-requisitos
REM ====================================================================
echo Validando pre-requisitos...
echo.

call "%~dp0validate_startup.bat" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ====================================================================
    echo    ERRO: VALIDACAO FALHOU
    echo ====================================================================
    echo.
    echo Execute validate_startup.bat para mais detalhes:
    echo   "%~dp0validate_startup.bat"
    echo.
    echo Resolva os problemas listados e tente novamente.
    echo.
    echo ====================================================================
    echo.
    pause
    exit /b 1
)

echo [OK] Pre-requisitos validados com sucesso!
echo.

REM ====================================================================
REM ETAPA 2: Iniciar Servidores
REM ====================================================================
echo Abrindo backend e frontend em janelas separadas...
echo.

REM Iniciar backend em nova janela
start "CV Sob Medida - Backend" cmd /k "%~dp0start_backend.bat"

REM Aguardar 5 segundos para backend iniciar
echo Aguardando backend iniciar...
timeout /t 5 /nobreak >nul

REM Iniciar frontend em nova janela
start "CV Sob Medida - Frontend" cmd /k "%~dp0start_frontend.bat"

echo.
echo ====================================================================
echo    SERVIDORES INICIADOS
echo ====================================================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo Docs:     http://localhost:8000/docs
echo.
echo Duas janelas foram abertas. Nao feche-as enquanto usa a aplicacao.
echo.
echo Para parar os servidores: Pressione CTRL+C em cada janela
echo.
echo ====================================================================
echo.

REM ====================================================================
REM ETAPA 3: Abrir Navegador
REM ====================================================================
REM Aguardar mais 5 segundos para frontend estar pronto
echo Aguardando frontend iniciar (5 segundos)...
timeout /t 5 /nobreak >nul

echo Abrindo navegador...
start http://localhost:5173

echo.
echo [OK] Navegador aberto!
echo.
echo ====================================================================
echo    APLICACAO INICIADA COM SUCESSO
echo ====================================================================
echo.
pause
