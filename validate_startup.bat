@echo off
REM ====================================================================
REM Validar Pre-requisitos para Iniciar Aplicacao
REM ====================================================================

setlocal enabledelayedexpansion

set "ERRORS=0"

echo.
echo ====================================================================
echo    VALIDACAO DE PRE-REQUISITOS
echo ====================================================================
echo.

REM ====================================================================
REM 1. Validar Node.js
REM ====================================================================
echo [1/5] Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo   [ERRO] Node.js nao encontrado
    echo   Baixe em: https://nodejs.org/
    set /a ERRORS=ERRORS+1
) else (
    for /f "tokens=*" %%i in ('node --version') do (
        echo   [OK] Node.js %%i encontrado
    )
)
echo.

REM ====================================================================
REM 2. Validar Python venv
REM ====================================================================
echo [2/5] Verificando Python venv...
if not exist "backend\.venv\Scripts\python.exe" (
    echo   [ERRO] Python venv nao encontrado em backend\.venv
    set /a ERRORS=ERRORS+1
) else (
    for /f "tokens=*" %%i in ('backend\.venv\Scripts\python.exe --version') do (
        echo   [OK] Python %%i encontrado
    )
)
echo.

REM ====================================================================
REM 3. Validar backend/.env
REM ====================================================================
echo [3/5] Verificando backend/.env...
if not exist "backend\.env" (
    echo   [ERRO] Arquivo backend/.env nao encontrado
    echo   Configure sua GOOGLE_API_KEY antes de continuar
    set /a ERRORS=ERRORS+1
) else (
    echo   [OK] backend/.env encontrado
)
echo.

REM ====================================================================
REM 4. Validar frontend/node_modules
REM ====================================================================
echo [4/5] Verificando frontend/node_modules...
if not exist "frontend\node_modules" (
    echo   [AVISO] node_modules nao encontrado, sera instalado automaticamente
) else (
    echo   [OK] frontend/node_modules encontrado
)
echo.

REM ====================================================================
REM 5. Validar frontend/.env
REM ====================================================================
echo [5/5] Verificando frontend/.env...
if not exist "frontend\.env" (
    echo   [AVISO] frontend/.env nao encontrado, sera criado automaticamente
) else (
    echo   [OK] frontend/.env encontrado
)
echo.

REM ====================================================================
REM Resumo
REM ====================================================================
echo ====================================================================
if !ERRORS! equ 0 (
    echo    TUDO VALIDADO COM SUCESSO
    echo    Voce pode executar: start_app.bat
    echo ====================================================================
    echo.
    exit /b 0
) else (
    echo    !ERRORS! ERRO(S) ENCONTRADO(S)
    echo    Resolva os erros acima e tente novamente
    echo ====================================================================
    echo.
    pause
    exit /b 1
)
