# CV Sob Medida - Claude Code Development Guide

## 🎯 Project Context

**Type**: Full-stack SaaS - Job Materials Generator  
**Stack**: 
- Backend: Python 3.11+, FastAPI, LangChain, Google Gemini
- Frontend: React 18+, TypeScript, Vite, Tailwind, Zustand, IndexedDB
- Shared: TypeScript types, contracts
- Infra: Docker, Windows batch scripts, GitHub Actions

**Location**: 
- Backend: `backend/src/`
- Frontend: `frontend/src/`
- Shared: `shared/`
- Specs: `specs/001-cv-generation-from-url/`

## 📐 Architecture Decisions

### Backend Principles
- **Framework**: FastAPI with Pydantic v2 for strict validation
- **Model**: Gemini-2.5-flash (atualizado em 2025)
- **LangChain**: Agents para extraction e generation
- **Error Handling**: Structured exceptions, logging com contexto
- **Testing**: pytest, unit + integration tests
- **Environment**: PYTHONPATH=src/ obrigatório

### Frontend Principles
- **State**: Zustand (simples, não Redux)
- **Styling**: Tailwind com prefixos customizados
- **Storage**: IndexedDB (histórico local)
- **API Client**: axios com retry logic
- **Build**: Vite para HMR rápido
- **Testing**: Vitest + React Testing Library

## 🔧 Development Workflow

### Setup Local
