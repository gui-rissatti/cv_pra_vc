@echo off
REM ====================================================================
REM Iniciar Backend - CV Sob Medida
REM ====================================================================
REM Script robusto para iniciar o servidor FastAPI com validacoes
REM ====================================================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%backend"

echo.
echo ====================================================================
echo    INICIANDO BACKEND - CV SOB MEDIDA
echo ====================================================================
echo.

REM ====================================================================
REM ETAPA 1: Verificar pre-requisitos
REM ====================================================================
echo [1/4] Verificando pre-requisitos...
echo.

REM Verificar ambiente virtual
if not exist ".venv\" (
    echo [ERRO] Ambiente virtual nao encontrado em .venv
    echo.
    echo Para criar o ambiente virtual, execute na pasta backend:
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Verificar .env
if not exist ".env" (
    echo [ERRO] Arquivo .env nao encontrado!
    echo.
    echo Configure sua GOOGLE_API_KEY:
    echo   1. Abra arquivo backend\.env
    echo   2. Adicione: GOOGLE_API_KEY=sua_chave_aqui
    echo.
    pause
    exit /b 1
)

echo [OK] Pre-requisitos validados
echo.

REM ====================================================================
REM ETAPA 2: Ativar ambiente virtual
REM ====================================================================
echo [2/4] Ativando ambiente virtual...

call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERRO] Falha ao ativar ambiente virtual!
    pause
    exit /b 1
)

echo [OK] Ambiente virtual ativado
echo.

REM ====================================================================
REM ETAPA 3: Configurar variaveis de ambiente
REM ====================================================================
echo [3/4] Configurando variaveis de ambiente...

set "PYTHONPATH=%CD%\src"
echo PYTHONPATH=%PYTHONPATH%

REM Carregar variaveis do .env (necessario para GOOGLE_API_KEY)
for /f "usebackq tokens=* delims==" %%A in (".env") do (
    set "%%A"
)

echo [OK] Variaveis configuradas
echo.

REM ====================================================================
REM ETAPA 4: Iniciar servidor
REM ====================================================================
echo [4/4] Iniciando servidor uvicorn...
echo.
echo Aguarde alguns segundos para o servidor iniciar...
echo.
echo [CTRL+C para parar o servidor]
echo.
echo ====================================================================
echo Backend estara disponivel em:
echo   http://localhost:8000
echo   http://localhost:8000/docs
echo ====================================================================
echo.

REM Tentar executar uvicorn
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload 2>&1

REM Se chegou aqui, uvicorn falhou ou foi parado
echo.
echo [ERRO] Servidor parou inesperadamente
echo.
pause
exit /b 1
