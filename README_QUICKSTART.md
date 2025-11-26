# CV Sob Medida - Quick Start

Guia rápido para começar com a aplicação em 5 minutos.

## Pré-requisitos (Obrigatório)

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)

## Passo 1: Setup Inicial (5 minutos)

Execute este arquivo **uma única vez**:

```bash
setup.bat
```

Este script:
- ✅ Cria ambiente Python
- ✅ Instala dependências backend (uvicorn, fastapi, etc)
- ✅ Instala dependências frontend (react, vite, etc)
- ✅ Configura arquivos .env

## Passo 2: Configure GOOGLE_API_KEY

Abra o arquivo `backend/.env` e configure:

```env
GOOGLE_API_KEY=sua_chave_aqui
```

Como obter a chave:
1. Acesse https://console.cloud.google.com/
2. Crie um projeto novo
3. Ative "Generative Language API"
4. Crie uma API Key
5. Cole em `backend/.env`

## Passo 3: Inicie a Aplicação

```bash
start_app.bat
```

O script irá:
1. ✅ Validar tudo está instalado
2. ✅ Iniciar backend (porta 8000)
3. ✅ Iniciar frontend (porta 5173)
4. ✅ Abrir navegador automaticamente

## Pronto!

Acesse: http://localhost:5173

## Próximas Vezes

Simplesmente execute:
```bash
start_app.bat
```

## Dicas

### Se aplicação não abrir

1. Verifique se validação passou:
   ```bash
   validate_startup.bat
   ```

2. Se há erros, consulte [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### Se precisa resetar tudo

```bash
setup.bat
```

### Para parar

Pressione `CTRL+C` em cada janela (backend e frontend)

## Documentação Completa

- [GETTING_STARTED.md](GETTING_STARTED.md) - Guia detalhado
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Resolução de problemas
- [API Docs](http://localhost:8000/docs) - Documentação da API (quando rodando)

---

**Pronto em 3 passos!** 🚀
