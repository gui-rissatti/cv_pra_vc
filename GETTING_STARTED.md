# Como Começar - CV Sob Medida

Este documento descreve como instalar, configurar e executar a aplicação **CV Sob Medida** no seu computador Windows.

## Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Instalação Inicial](#instalação-inicial)
3. [Configuração de Ambiente](#configuração-de-ambiente)
4. [Executando a Aplicação](#executando-a-aplicação)
5. [Acessando a Aplicação](#acessando-a-aplicação)
6. [Parando a Aplicação](#parando-a-aplicação)
7. [Troubleshooting](#troubleshooting)

## Pré-requisitos

Antes de começar, você precisa ter instalado em seu computador:

### 1. Python 3.11+
- **Download**: [python.org](https://www.python.org/downloads/)
- **Instalação**:
  - Execute o instalador
  - **IMPORTANTE**: Marque a opção "Add Python to PATH" durante a instalação
  - Verifique a instalação abrindo terminal e digitando: `python --version`

### 2. Node.js 18+ (recomendado v22+)
- **Download**: [nodejs.org](https://nodejs.org/)
- **Instalação**:
  - Execute o instalador e siga as instruções
  - Verifique: `node --version` e `npm --version`

### 3. Git (opcional, mas recomendado)
- **Download**: [git-scm.com](https://git-scm.com/)
- Necessário apenas se você quiser clonar o repositório via git

## Instalação Inicial

### Opção 1: Clonar Repositório (com Git)

```bash
git clone https://github.com/gui-rissatti/cv_pra_vc.git
cd cv_pra_vc
```

### Opção 2: Download Manual

1. Acesse: https://github.com/gui-rissatti/cv_pra_vc
2. Clique em "Code" → "Download ZIP"
3. Extraia o arquivo em uma pasta de sua escolha
4. Abra terminal nessa pasta

### Criando Ambientes Virtuais

Execute este script para criar os ambientes virtuais necessários:

**Windows**:
```bash
# Criar venv para backend
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
deactivate
cd ..
```

## Configuração de Ambiente

### Backend - Arquivo `.env`

Você precisa configurar a chave da API do Google para o backend funcionar:

1. Acesse: [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Ative a API "Generative Language API"
4. Crie uma chave de API (API Key)
5. Abra o arquivo `backend/.env` e adicione:

```env
GOOGLE_API_KEY=sua_chave_aqui
LOG_LEVEL=INFO
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:5173
```

### Frontend - Arquivo `.env`

O arquivo `frontend/.env` é criado automaticamente, mas você pode verificar:

```env
VITE_API_URL=http://localhost:8000
```

## Executando a Aplicação

### Método 1: Script Automático (Recomendado)

Simplesmente execute:

```bash
start_app.bat
```

**O que este script faz:**
1. ✅ Valida todos os pré-requisitos
2. ✅ Inicia o backend FastAPI (porta 8000)
3. ✅ Inicia o frontend Vite (porta 5173)
4. ✅ Abre o navegador automaticamente
5. ✅ Mostra os endereços dos servidores

### Método 2: Iniciar Manualmente

Se preferir mais controle, execute em **duas janelas do terminal**:

**Terminal 1 - Backend:**
```bash
start_backend.bat
```

**Terminal 2 - Frontend:**
```bash
start_frontend.bat
```

## Acessando a Aplicação

Após executar `start_app.bat`, você pode acessar:

| Serviço | URL | Descrição |
|---------|-----|-----------|
| **Aplicação** | http://localhost:5173 | Interface principal da aplicação |
| **API Backend** | http://localhost:8000 | Servidor FastAPI |
| **API Docs** | http://localhost:8000/docs | Documentação interativa (Swagger) |
| **ReDoc** | http://localhost:8000/redoc | Documentação alternativa |

### Testando a Conexão

1. Abra a aplicação em http://localhost:5173
2. A aplicação deve carregar sem erros
3. Tente utilizar a funcionalidade de extração de jobs

## Parando a Aplicação

### Se Está em Execução via `start_app.bat`

1. **Terminal Backend**: Pressione `CTRL+C`
2. **Terminal Frontend**: Pressione `CTRL+C`
3. Feche ambas as janelas

### Se Está em Execução Manual

Faça o mesmo em cada janela de terminal onde você iniciou os serviços.

## Troubleshooting

### Problema: Python não encontrado

**Erro**: `python is not recognized as an internal or external command`

**Solução**:
1. Abra "Variáveis de Ambiente" do Windows
2. Verifique se o Python está no PATH
3. Reinstale Python marcando "Add Python to PATH"

### Problema: Node.js/npm não encontrado

**Erro**: `node is not recognized` ou `npm is not recognized`

**Solução**:
1. Verifique a instalação: `node --version`
2. Se não funcionar, reinstale Node.js
3. Abra uma nova janela de terminal após reinstalar

### Problema: GOOGLE_API_KEY não configurada

**Erro**: `ValueError: GOOGLE_API_KEY not set`

**Solução**:
1. Abra `backend/.env`
2. Adicione sua chave: `GOOGLE_API_KEY=sk-...`
3. Reinicie o backend

### Problema: Porta 8000 ou 5173 já em uso

**Erro**: `Address already in use` ou erro similar

**Solução - Opção 1 - Fechar aplicações**:
- Verifique se há outra instância rodando
- Feche completamente todos os servidores e tente novamente

**Solução - Opção 2 - Mudar porta**:

Para backend, abra `backend/src/app/main.py` e mude a porta.
Para frontend, modifique `frontend/vite.config.ts`.

### Problema: npm install falha

**Erro**: `npm ERR! code ERESOLVE`

**Solução**:
```bash
cd frontend
npm cache clean --force
npm install --force
cd ..
```

### Problema: Validação falha ao executar start_app.bat

**Erro**: `ERRO: VALIDACAO FALHOU`

**Solução**:
1. Execute `validate_startup.bat` para ver os erros específicos:
   ```bash
   validate_startup.bat
   ```
2. Resolva cada erro listado
3. Tente executar `start_app.bat` novamente

### Problema: Frontend não consegue se conectar ao backend

**Erro**: Erro de conexão na interface da aplicação

**Solução**:
1. Verifique que o backend está rodando em http://localhost:8000
2. Verifique o arquivo `frontend/.env`:
   ```env
   VITE_API_URL=http://localhost:8000
   ```
3. Abra o DevTools (F12) e verifique os erros de rede

## Estrutura do Projeto

```
cv_pra_vc/
├── backend/                    # Servidor FastAPI
│   ├── src/
│   │   ├── app/main.py        # Aplicação principal
│   │   ├── api/               # Rotas da API
│   │   ├── agents/            # Agentes LLM
│   │   ├── services/          # Serviços
│   │   └── core/              # Configurações centrais
│   ├── .env                   # Configurações do backend
│   └── requirements.txt       # Dependências Python
│
├── frontend/                   # Aplicação React/Vite
│   ├── src/
│   │   ├── components/        # Componentes React
│   │   ├── pages/            # Páginas da aplicação
│   │   ├── store/            # Gerenciamento de estado
│   │   └── services/         # Serviços HTTP
│   ├── .env                  # Configurações do frontend
│   └── package.json          # Dependências Node
│
├── start_app.bat             # Inicia aplicação completa
├── start_backend.bat         # Inicia apenas backend
├── start_frontend.bat        # Inicia apenas frontend
└── validate_startup.bat      # Valida pré-requisitos
```

## Próximos Passos

Após conseguir executar a aplicação:

1. **Explorar a Interface**: Familiarize-se com a aplicação
2. **Ler Documentação da API**: Visite http://localhost:8000/docs
3. **Consultar Contribuição**: Veja CONTRIBUTING.md para desenvolver
4. **Relatar Bugs**: Abra uma issue no GitHub se encontrar problemas

## Suporte

Se você encontrar problemas:

1. Primeiro, execute `validate_startup.bat` para diagnosticar
2. Verifique a seção [Troubleshooting](#troubleshooting)
3. Consulte as issues no GitHub: https://github.com/gui-rissatti/cv_pra_vc/issues
4. Abra uma nova issue descrevendo o problema

## Informações Adicionais

- **Linguagem Backend**: Python 3.11+
- **Framework Backend**: FastAPI
- **Framework Frontend**: React + Vite
- **LLM Provider**: Google Generative AI (Gemini)
- **Banco de Dados**: Não utiliza (arquitetura stateless)
- **Autenticação**: Não implementada (fase futura)

## Licença

Este projeto é licenciado sob a licença MIT. Veja LICENSE para mais detalhes.

---

**Última atualização**: 2025-11-26
**Versão**: 0.1.0
