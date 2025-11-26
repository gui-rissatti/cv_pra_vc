@echo off
REM ====================================================================
REM Setup Inicial - CV Sob Medida
REM ====================================================================
REM Script para configurar completamente o projeto na primeira vez
REM ====================================================================

setlocal enabledelayedexpansion

echo.
echo ====================================================================
echo    SETUP INICIAL - CV SOB MEDIDA
echo ====================================================================
echo.
echo Este script ira:
echo   1. Criar ambiente virtual Python
echo   2. Instalar dependencias do backend
echo   3. Instalar dependencias do frontend
echo   4. Configurar arquivos .env
echo.
echo Pressione ENTER para continuar ou CTRL+C para cancelar...
pause >nul

REM ====================================================================
REM ETAPA 1: Validar Python
REM ====================================================================
echo.
echo [ETAPA 1/4] Verificando Python...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo.
    echo Baixe e instale Python 3.11+:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANTE: Marque "Add Python to PATH" durante a instalacao
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] !PYTHON_VERSION! encontrado
echo.

REM ====================================================================
REM ETAPA 2: Setup Backend
REM ====================================================================
echo [ETAPA 2/4] Configurando backend...
echo.

cd /d "%~dp0backend"

REM Criar venv se nao existir
if not exist ".venv" (
    echo Criando ambiente virtual Python...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar ambiente virtual!
        cd /d "%~dp0"
        pause
        exit /b 1
    )
    echo [OK] Ambiente virtual criado
) else (
    echo [OK] Ambiente virtual ja existe
)

REM Ativar venv
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERRO] Falha ao ativar ambiente virtual!
    cd /d "%~dp0"
    pause
    exit /b 1
)

REM Instalar dependencias
echo.
echo Instalando dependencias do backend...
echo (isso pode demorar alguns minutos)
echo.

pip install --upgrade pip setuptools wheel >nul 2>&1
pip install -r requirements.txt

if errorlevel 1 (
    echo [AVISO] Alguns pacotes podem ter falhado
    echo Tentando instalar com --force-reinstall...
    pip install -r requirements.txt --force-reinstall --no-cache-dir
)

echo.
echo [OK] Dependencias do backend instaladas
echo.

REM Criar .env se nao existir
if not exist ".env" (
    echo Criando arquivo .env...
    echo GOOGLE_API_KEY=sua_chave_aqui > .env
    echo LOG_LEVEL=INFO >> .env
    echo ALLOWED_HOSTS=localhost,127.0.0.1 >> .env
    echo CORS_ORIGINS=http://localhost:5173 >> .env
    echo.
    echo [AVISO] Arquivo .env criado
    echo Configure sua GOOGLE_API_KEY no arquivo backend\.env
) else (
    echo [OK] Arquivo .env ja existe
)

REM Desativar venv
call .venv\Scripts\deactivate.bat

cd /d "%~dp0"
echo.

REM ====================================================================
REM ETAPA 3: Setup Frontend
REM ====================================================================
echo [ETAPA 3/4] Configurando frontend...
echo.

cd /d "%~dp0frontend"

REM Verificar Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Node.js nao encontrado!
    echo.
    echo Baixe e instale Node.js 18+:
    echo   https://nodejs.org/
    echo.
    cd /d "%~dp0"
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo [OK] Node.js !NODE_VERSION! encontrado
echo.

REM Instalar dependencias
echo Instalando dependencias do frontend...
echo (isso pode demorar alguns minutos)
echo.

call npm install

if errorlevel 1 (
    echo [AVISO] Alguns pacotes podem ter falhado
    echo Tentando com --force...
    call npm install --force
)

echo.
echo [OK] Dependencias do frontend instaladas
echo.

REM Criar .env se nao existir
if not exist ".env" (
    echo Criando arquivo .env...
    echo VITE_API_URL=http://localhost:8000 > .env
    echo [OK] Arquivo .env criado
) else (
    echo [OK] Arquivo .env ja existe
)

cd /d "%~dp0"
echo.

REM ====================================================================
REM ETAPA 4: Validacao Final
REM ====================================================================
echo [ETAPA 4/4] Validando setup...
echo.

python test_startup_validation.py

if errorlevel 1 (
    echo.
    echo [AVISO] Alguns problemas foram detectados
    echo Resolva os problemas listados acima
) else (
    echo.
    echo ====================================================================
    echo    SETUP CONCLUIDO COM SUCESSO!
    echo ====================================================================
    echo.
    echo Proximas etapas:
    echo   1. Configure sua GOOGLE_API_KEY em backend\.env
    echo   2. Execute: start_app.bat
    echo.
    echo ====================================================================
)

echo.
pause
exit /b 0
