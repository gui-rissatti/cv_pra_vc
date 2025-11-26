@echo off
REM ====================================================================
REM Iniciar Frontend - CV Sob Medida
REM ====================================================================
REM Script robusto para iniciar o servidor Vite com validacoes
REM ====================================================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%frontend"

echo.
echo ====================================================================
echo    INICIANDO FRONTEND - CV SOB MEDIDA
echo ====================================================================
echo.

REM ====================================================================
REM ETAPA 1: Verificar Node.js
REM ====================================================================
echo [1/4] Verificando Node.js...
echo.

node --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Node.js nao encontrado!
    echo.
    echo Baixe e instale Node.js em: https://nodejs.org/
    echo Depois abra uma nova janela de terminal e tente novamente.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo [OK] Node.js !NODE_VERSION! encontrado
echo.

REM ====================================================================
REM ETAPA 2: Verificar/instalar node_modules
REM ====================================================================
echo [2/4] Verificando dependencias...
echo.

if not exist "node_modules\" (
    echo Instalando dependencias do frontend...
    echo (isso pode demorar alguns minutos na primeira vez)
    echo.
    call npm install
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar dependencias!
        echo.
        echo Tente executar manualmente:
        echo   npm install --force
        echo.
        pause
        exit /b 1
    )
    echo.
    echo [OK] Dependencias instaladas
    echo.
) else (
    echo [OK] node_modules encontrado
    echo.
)

REM ====================================================================
REM ETAPA 3: Configurar .env
REM ====================================================================
echo [3/4] Configurando ambiente...
echo.

if not exist ".env" (
    echo Criando arquivo .env...
    echo VITE_API_URL=http://localhost:8000 > .env
    echo [OK] Arquivo .env criado
) else (
    echo [OK] Arquivo .env ja existe
)
echo.

REM ====================================================================
REM ETAPA 4: Iniciar servidor Vite
REM ====================================================================
echo [4/4] Iniciando servidor Vite...
echo.
echo Aguarde alguns segundos para o servidor iniciar...
echo.
echo [CTRL+C para parar o servidor]
echo.
echo ====================================================================
echo Frontend estara disponivel em:
echo   http://localhost:5173
echo ====================================================================
echo.

REM Tentar executar npm dev
npm run dev

REM Se chegou aqui, npm falhou ou foi parado
echo.
echo [ERRO] Servidor parou inesperadamente
echo.
pause
exit /b 1
