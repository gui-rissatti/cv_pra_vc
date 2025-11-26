# Guia de Troubleshooting - CV Sob Medida

Este documento ajuda a resolver problemas comuns ao executar a aplicação CV Sob Medida no Windows.

## Índice

1. [Erros de Inicialização](#erros-de-inicialização)
2. [Problemas de Uvicorn](#problemas-de-uvicorn)
3. [Problemas de Frontend](#problemas-de-frontend)
4. [Problemas de Configuração](#problemas-de-configuração)
5. [Problemas de Rede](#problemas-de-rede)
6. [Problemas de Dependências](#problemas-de-dependências)

---

## Erros de Inicialização

### start_app.bat fecha imediatamente

**Sintomas**: Ao executar `start_app.bat`, uma ou ambas as janelas fecham rapidamente.

**Causas Possíveis**:
1. Validação falhou
2. Backend ou frontend não conseguiu iniciar
3. Erro silencioso em um dos scripts

**Solução**:
1. Execute `validate_startup.bat` para diagnosticar:
   ```bash
   validate_startup.bat
   ```

2. Se a validação passou, execute manualmente para ver o erro:
   ```bash
   start_backend.bat
   ```

3. Se a janela fechar imediatamente, execute no terminal:
   ```bash
   cd backend
   .venv\Scripts\activate.bat
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

---

## Problemas de Uvicorn

### [ERRO] ModuleNotFoundError: No module named 'uvicorn'

**Sintomas**: Backend não inicia com erro `ModuleNotFoundError: No module named 'uvicorn'`

**Causas Possíveis**:
1. Dependências não foram instaladas
2. Ambiente virtual não foi ativado corretamente
3. Python venv está corrompido

**Solução**:

**Opção 1 - Reinstalar dependências**:
```bash
cd backend
.venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
```

**Opção 2 - Recriar venv**:
```bash
cd backend
REM Deletar venv antigo
rmdir .venv /s /q

REM Criar novo venv
python -m venv .venv

REM Ativar
.venv\Scripts\activate.bat

REM Instalar dependencias
pip install -r requirements.txt
```

---

### [ERRO] Address already in use: 127.0.0.1:8000

**Sintomas**: Erro "Address already in use" ao iniciar o backend

**Causas Possíveis**:
1. Outro processo está usando a porta 8000
2. Uma instância anterior ainda está rodando
3. Aplicação não foi finalizada corretamente

**Solução**:

**Opção 1 - Matar processo da porta 8000**:
```bash
REM Abrir terminal como administrador e executar:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Opção 2 - Usar porta diferente**:
```bash
cd backend
.venv\Scripts\activate.bat
set PYTHONPATH=%CD%\src
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

**Opção 3 - Reiniciar computador**:
Se nenhuma das opções acima funcionar, reinicie o computador para liberar a porta.

---

### Backend inicia mas aplicação não responde

**Sintomas**: Backend inicia normalmente, mas frontend não consegue se conectar

**Verificar**:
1. Backend realmente está rodando em http://localhost:8000
2. Abra em um navegador: http://localhost:8000/docs
3. Verifique se mostra a documentação da API

**Se não funcionar**:
1. Verifique se há erro no terminal do backend
2. Verifique se GOOGLE_API_KEY está configurada em `backend/.env`
3. Verifique os logs estruturados no terminal

---

## Problemas de Frontend

### [ERRO] npm command not found

**Sintomas**: Erro "npm: command not found" ao executar `start_frontend.bat`

**Causas Possíveis**:
1. Node.js não está instalado
2. Node.js não foi adicionado ao PATH do Windows
3. Nova terminal aberta antes da reinstalação

**Solução**:
1. Verifique Node.js instalado:
   ```bash
   node --version
   npm --version
   ```

2. Se não funcionar, reinicie Node.js:
   - Desinstale Node.js via "Programas e Funcionalidades"
   - Reinicie o computador
   - Reinstale Node.js do https://nodejs.org/

3. Abra uma **NOVA terminal** após reinstalar

---

### Frontend inicia mas não consegue conectar ao backend

**Sintomas**: Aplicação carrega em http://localhost:5173, mas mostra erro de conexão com API

**Verificar**:
1. Backend está rodando em http://localhost:8000?
2. Frontend `.env` tem `VITE_API_URL=http://localhost:8000`?

**Solução**:
1. Verifique `frontend/.env`:
   ```env
   VITE_API_URL=http://localhost:8000
   ```

2. Se arquivo está errado, corrija e reinicie frontend (CTRL+C e `start_frontend.bat`)

3. No DevTools do navegador (F12), verifique a aba "Network" para ver as requisições

---

### [ERRO] ENOSPC: no space left on device

**Sintomas**: Erro "no space left on device" ao instalar dependências do frontend

**Causa**: Disco rígido cheio

**Solução**:
1. Libere espaço em disco
2. Delete `node_modules`:
   ```bash
   cd frontend
   rmdir node_modules /s /q
   ```
3. Tente novamente: `npm install`

---

## Problemas de Configuração

### [ERRO] GOOGLE_API_KEY not set

**Sintomas**: Backend falha com "GOOGLE_API_KEY not set"

**Causas Possíveis**:
1. Arquivo `backend/.env` não existe
2. GOOGLE_API_KEY não foi configurada em `.env`
3. `.env` foi editado incorretamente

**Solução**:
1. Verifique se arquivo existe: `backend/.env`
2. Se não existir, crie com:
   ```
   GOOGLE_API_KEY=sua_chave_aqui
   LOG_LEVEL=INFO
   ALLOWED_HOSTS=localhost,127.0.0.1
   CORS_ORIGINS=http://localhost:5173
   ```

3. Obter GOOGLE_API_KEY:
   - Acesse: https://console.cloud.google.com/
   - Crie um novo projeto
   - Ative "Generative Language API"
   - Crie uma API Key

4. Reinicie o backend

---

### [ERRO] Arquivo .env não encontrado

**Solução - Backend**:
```batch
cd backend
echo GOOGLE_API_KEY=sua_chave > .env
echo LOG_LEVEL=INFO >> .env
echo ALLOWED_HOSTS=localhost,127.0.0.1 >> .env
echo CORS_ORIGINS=http://localhost:5173 >> .env
```

**Solução - Frontend**:
```batch
cd frontend
echo VITE_API_URL=http://localhost:8000 > .env
```

---

## Problemas de Rede

### Não consegue acessar http://localhost:5173

**Verificar**:
1. Frontend está rodando?
2. Há mensagem no terminal do frontend?
3. Porta 5173 está disponível?

**Solução**:
1. Reinicie frontend:
   ```bash
   CTRL+C na janela do frontend
   start_frontend.bat
   ```

2. Tente porta diferente:
   ```bash
   cd frontend
   npm run dev -- --port 5174
   ```

---

### Ports 8000 ou 5173 ocupadas

**Verificar quais processos estão usando**:
```bash
netstat -ano | findstr :8000
netstat -ano | findstr :5173
```

**Matar processo** (como administrador):
```bash
taskkill /PID <numero_pid> /F
```

---

## Problemas de Dependências

### pip freeze mostra versões antigas

**Sintomas**: Requirements.txt tem versões diferentes do que está instalado

**Solução**:
1. Fazer upgrade dos pacotes:
   ```bash
   cd backend
   .venv\Scripts\activate.bat
   pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt --upgrade
   ```

---

### npm audit vulnerabilities

**Sintomas**: `npm audit` mostra vulnerabilidades

**Solução**:
```bash
cd frontend

REM Ver vulnerabilidades
npm audit

REM Tentar consertar
npm audit fix

REM Se não funcionar
npm audit fix --force
```

---

### ModuleNotFoundError para módulos específicos

**Sintomas**: Erro como "No module named 'langchain'" ou "No module named 'pydantic'"

**Solução**:
1. Verifique venv ativado:
   ```bash
   cd backend
   .venv\Scripts\activate.bat
   ```

2. Reinstale módulo específico:
   ```bash
   pip install langchain --force-reinstall
   ```

3. Se não funcionar, reinstale tudo:
   ```bash
   pip install -r requirements.txt --force-reinstall --no-cache-dir
   ```

---

## Debug Detalhado

### Ver logs completos do backend

1. Execute backend com logging detalhado:
   ```bash
   cd backend
   .venv\Scripts\activate.bat
   set LOG_LEVEL=DEBUG
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --log-level debug
   ```

### Ver requisições HTTP do frontend

1. Abra DevTools (F12) no navegador
2. Vá para aba "Network"
3. Monitore requisições para http://localhost:8000

### Ver variaveis de ambiente

**Backend**:
```bash
cd backend
.venv\Scripts\activate.bat
python -c "import os; print(os.environ)"
```

**Frontend**:
```javascript
// No console do navegador (F12)
console.log(import.meta.env)
```

---

## Se Nada Funcionar

### Opção 1 - Setup Completo

Reinicie completamente:
```bash
setup.bat
```

Este script:
1. Recria venv Python
2. Reinstala todas as dependências do backend
3. Reinstala todas as dependências do frontend
4. Reconfigura arquivos .env

### Opção 2 - Deletar Tudo e Recomçar

```bash
REM Deletar venvs
rmdir backend\.venv /s /q
rmdir frontend\node_modules /s /q

REM Deletar .env
del backend\.env
del frontend\.env

REM Executar setup novamente
setup.bat
```

### Opção 3 - Procurar Ajuda

1. Verifique se há issue relacionada: https://github.com/gui-rissatti/cv_pra_vc/issues
2. Execute `test_startup_validation.py` para diagnosticar:
   ```bash
   python test_startup_validation.py
   ```
3. Crie uma nova issue com:
   - Sua versão do Windows
   - Resultado de `test_startup_validation.py`
   - Erros que vê no terminal
   - Passos que executou

---

## Checklist de Verificação Rápida

Se tudo parou de funcionar:

- [ ] `python --version` mostra 3.11+?
- [ ] `node --version` mostra 18+?
- [ ] `backend/.env` existe com GOOGLE_API_KEY?
- [ ] `backend/.venv\Scripts\python.exe` existe?
- [ ] `frontend/node_modules` existe?
- [ ] `frontend/.env` existe com VITE_API_URL?
- [ ] Executar `validate_startup.bat` mostra todos [OK]?
- [ ] Portas 8000 e 5173 estão livres?
- [ ] Terminal aberta COMO ADMINISTRADOR?

---

**Última atualização**: 2025-11-26
**Versão**: 0.1.0
