# Análise de Autenticação - CV Sob Medida

**Data:** 26 de Novembro de 2025  
**Versão:** 1.0  
**Escopo:** Identificação de necessidades, gargalos e blueprint para autenticação robusta, escalável, confiável e segura

---

## Índice

1. [Resumo Executivo](#1-resumo-executivo)
2. [Análise do Estado Atual](#2-análise-do-estado-atual)
3. [Riscos e Vulnerabilidades](#3-riscos-e-vulnerabilidades)
4. [Arquitetura de Autenticação Proposta](#4-arquitetura-de-autenticação-proposta)
5. [Requisitos de Backend](#5-requisitos-de-backend)
6. [Requisitos de Frontend](#6-requisitos-de-frontend)
7. [Requisitos de DevOps/Infraestrutura](#7-requisitos-de-devopsinfrastrutura)
8. [Escalabilidade e Performance](#8-escalabilidade-e-performance)
9. [Roadmap de Implementação](#9-roadmap-de-implementação)
10. [Checklist de Segurança](#10-checklist-de-segurança)

---

## 1. Resumo Executivo

### 1.1 Objetivo

Este documento apresenta uma análise completa das necessidades de autenticação para a aplicação **CV Sob Medida**, unindo conhecimentos de **engenharia de software** e **DevOps** para propor uma solução robusta, escalável, confiável e segura.

### 1.2 Principais Descobertas

| Categoria | Status Atual | Risco | Prioridade |
|-----------|--------------|-------|------------|
| Autenticação de Usuários | 🔴 AUSENTE | CRÍTICO | P0 |
| Proteção de APIs | 🟡 PARCIAL (Rate Limit apenas) | ALTO | P0 |
| Gerenciamento de Sessões | 🔴 AUSENTE | CRÍTICO | P0 |
| Autorização/RBAC | 🔴 AUSENTE | MÉDIO | P1 |
| Auditoria de Segurança | 🔴 AUSENTE | MÉDIO | P1 |
| Multi-tenant | 🔴 AUSENTE | BAIXO | P2 |

### 1.3 Recomendação Principal

Implementar um sistema de autenticação **baseado em JWT + OAuth 2.0** com suporte a **provedores externos (Google, GitHub, LinkedIn)**, utilizando:
- Backend: **FastAPI + python-jose + passlib**
- Frontend: **Zustand + axios interceptors**
- Infraestrutura: **Redis para sessions + PostgreSQL para users**

---

## 2. Análise do Estado Atual

### 2.1 Mapeamento de Endpoints (Sem Autenticação)

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         ENDPOINTS EXPOSTOS (SEM AUTH)                       │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  POST /extract-job-details     ← 🔴 Público (qualquer um pode usar)       │
│  POST /generate-materials      ← 🔴 Público (consome API Gemini)          │
│  POST /extract-cv-text         ← 🔴 Público (aceita uploads de arquivos)  │
│  GET  /health                  ← 🟢 Público (esperado)                    │
│  GET  /docs                    ← 🟡 Público em dev (deve proteger em prod)│
│  GET  /redoc                   ← 🟡 Público em dev (deve proteger em prod)│
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Mecanismos de Segurança Existentes

| Mecanismo | Implementado | Localização | Eficácia |
|-----------|--------------|-------------|----------|
| Rate Limiting | ✅ | `core/rate_limit.py` | PARCIAL - Por IP apenas |
| CORS | ✅ | `app/main.py` | OK - Origens configuráveis |
| Trusted Hosts | ✅ | `app/main.py` | OK |
| Input Validation | ✅ | Pydantic models | BOM |
| API Key (Gemini) | ✅ | `core/config.py` | OK - Mas exposto em .env |

### 2.3 Gaps Críticos Identificados

#### 2.3.1 Ausência de Autenticação de Usuários

**Código atual (`app/main.py`):**
```python
def create_app() -> FastAPI:
    # ...
    application.add_middleware(SlowAPIMiddleware)
    application.add_middleware(CORSMiddleware, ...)
    application.add_middleware(TrustedHostMiddleware, ...)
    # ❌ NENHUM middleware de autenticação
    # ❌ NENHUMA proteção de rotas
    register_routes(application)
    return application
```

**Impacto:**
- Qualquer pessoa pode consumir a API ilimitadamente (apenas rate limit por IP)
- Sem rastreabilidade de quem usa o serviço
- Impossível implementar quotas por usuário
- Dados de CV processados sem controle de acesso

#### 2.3.2 Ausência de Persistência de Usuários

**Código atual (`frontend/src/services/db.ts`):**
```typescript
// IndexedDB local apenas - sem sincronização ou persistência server-side
// Histórico de aplicações NÃO está vinculado a um usuário
```

**Impacto:**
- Dados perdidos ao limpar browser
- Sem compartilhamento entre dispositivos
- Sem backup ou recuperação

#### 2.3.3 Rate Limiting Limitado

**Código atual (`core/rate_limit.py`):**
```python
limiter = Limiter(key_func=get_remote_address)
```

**Impacto:**
- Rate limit apenas por IP
- Fácil de contornar com VPN/proxies
- Impossível diferenciar usuários legítimos de abusadores

---

## 3. Riscos e Vulnerabilidades

### 3.1 Matriz de Riscos

| ID | Risco | Probabilidade | Impacto | Severidade | Mitigação |
|----|-------|---------------|---------|------------|-----------|
| R1 | Abuso de API (consumo excessivo Gemini) | ALTA | CRÍTICO | 🔴 P0 | Autenticação + quotas |
| R2 | Vazamento de dados de CV | MÉDIA | ALTO | 🔴 P0 | Criptografia + auth |
| R3 | DDoS nos endpoints | ALTA | MÉDIO | 🟡 P1 | Auth + rate limit por user |
| R4 | Web scraping não autorizado | MÉDIA | BAIXO | 🟢 P2 | Auth + CAPTCHA |
| R5 | Escalação de privilégios | N/A (sem roles) | N/A | 🟡 P1 | Implementar RBAC |
| R6 | Sessões roubadas/hijacking | N/A (sem sessões) | N/A | 🟡 P1 | JWT + refresh tokens |

### 3.2 Vulnerabilidades Técnicas

#### 3.2.1 Exposição de Documentação em Produção

**Arquivo: `app/main.py` (linha 21-26)**
```python
application = FastAPI(
    title="CV Sob Medida API",
    version="0.1.0",
    docs_url="/docs",      # ❌ Exposto em produção
    redoc_url="/redoc",    # ❌ Exposto em produção
)
```

**Recomendação:**
```python
settings = get_settings()
docs_url = "/docs" if settings.environment != "production" else None
redoc_url = "/redoc" if settings.environment != "production" else None
```

#### 3.2.2 Sem HTTPS Enforcement

**Arquivo: `docker-compose.yml`**
```yaml
ports:
  - '8000:8000'  # ❌ HTTP apenas, sem SSL/TLS
```

**Recomendação:** Adicionar TLS termination via reverse proxy (nginx/traefik)

#### 3.2.3 API Key em Variáveis de Ambiente

**Arquivo: `core/config.py` (linha 36)**
```python
google_api_key: str | None = None  # ❌ Pode vazar em logs/errors
```

**Recomendação:** Usar secret manager (Vault, AWS Secrets Manager)

---

## 4. Arquitetura de Autenticação Proposta

### 4.1 Visão Geral

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ARQUITETURA DE AUTENTICAÇÃO                          │
└─────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────┐
                                    │   Browser   │
                                    │  (Frontend) │
                                    └──────┬──────┘
                                           │
                              ┌────────────┴────────────┐
                              │   API Gateway / LB      │
                              │   (nginx + SSL/TLS)     │
                              └────────────┬────────────┘
                                           │
              ┌────────────────────────────┼────────────────────────────┐
              │                            │                            │
              ▼                            ▼                            ▼
     ┌────────────────┐          ┌────────────────┐          ┌────────────────┐
     │  Auth Service  │          │  Main API      │          │  OAuth Providers│
     │  (/auth/*)     │          │  (Protected)   │          │  Google/GitHub  │
     └───────┬────────┘          └───────┬────────┘          └────────┬───────┘
             │                           │                            │
             │    ┌──────────────────────┘                            │
             │    │                                                   │
             ▼    ▼                                                   │
     ┌────────────────┐                                               │
     │   Auth Layer   │◄──────────────────────────────────────────────┘
     │   (FastAPI)    │
     │                │
     │ ┌────────────┐ │
     │ │ JWT Verify │ │
     │ └────────────┘ │
     │ ┌────────────┐ │
     │ │ OAuth Flow │ │
     │ └────────────┘ │
     │ ┌────────────┐ │
     │ │ API Keys   │ │
     │ └────────────┘ │
     └───────┬────────┘
             │
     ┌───────┴────────┐
     │                │
     ▼                ▼
┌─────────┐    ┌──────────┐
│ Redis   │    │PostgreSQL│
│(Sessions│    │ (Users)  │
│ Cache)  │    │          │
└─────────┘    └──────────┘
```

### 4.2 Estratégias de Autenticação

#### 4.2.1 JWT (JSON Web Tokens) - Recomendado

**Fluxo:**
```
1. User → POST /auth/login (email, password)
2. Server → Valida credenciais
3. Server → Gera JWT (access_token, refresh_token)
4. User ← Recebe tokens
5. User → GET /protected (Authorization: Bearer <token>)
6. Server → Valida JWT, extrai user_id
7. Server ← Processa request
```

**Vantagens:**
- Stateless (escalável horizontalmente)
- Pode incluir claims (roles, permissions)
- Suporte nativo em FastAPI

**Implementação:**
```python
# core/auth/jwt.py
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext

class JWTManager:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def create_access_token(self, data: dict, expires_delta: timedelta = timedelta(minutes=15)) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, data: dict, expires_delta: timedelta = timedelta(days=7)) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise InvalidTokenError("Invalid or expired token")
```

#### 4.2.2 OAuth 2.0 + OpenID Connect

**Provedores Suportados:**
- Google (profissionais de RH)
- GitHub (desenvolvedores)
- LinkedIn (networking profissional)

**Fluxo OAuth:**
```
1. User → Click "Login with Google"
2. Frontend → Redirect to Google OAuth
3. User → Autentica no Google
4. Google → Redirect callback com code
5. Backend → Troca code por access_token
6. Backend → Obtém user info do Google
7. Backend → Cria/atualiza user local
8. Backend → Gera JWT próprio
9. User ← Recebe JWT
```

#### 4.2.3 API Keys (para integrações B2B)

**Uso:** Automações, webhooks, integrações de terceiros

```python
# core/auth/api_key.py
class APIKeyManager:
    async def create_api_key(self, user_id: str, name: str, scopes: list[str]) -> str:
        key = secrets.token_urlsafe(32)
        hashed = hashlib.sha256(key.encode()).hexdigest()
        
        await self.db.api_keys.insert_one({
            "user_id": user_id,
            "name": name,
            "key_hash": hashed,
            "scopes": scopes,
            "created_at": datetime.utcnow(),
            "last_used": None,
            "is_active": True
        })
        
        return f"cvsobmedida_{key}"  # Prefix para identificação
```

### 4.3 Modelo de Dados de Usuários

```sql
-- PostgreSQL Schema

-- Tabela principal de usuários
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    password_hash VARCHAR(255),  -- NULL para OAuth-only users
    full_name VARCHAR(255),
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE
);

-- Provedores OAuth vinculados
CREATE TABLE oauth_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,  -- google, github, linkedin
    provider_user_id VARCHAR(255) NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(provider, provider_user_id)
);

-- API Keys para integrações
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(64) NOT NULL,  -- SHA-256
    scopes TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Refresh tokens (para rotação)
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL,
    device_info JSONB,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(token_hash)
);

-- Índices para performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_oauth_accounts_user_id ON oauth_accounts(user_id);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);
```

---

## 5. Requisitos de Backend

### 5.1 Dependências a Adicionar

```txt
# requirements.txt - Adicionar

# Auth & Security
python-jose[cryptography]==3.3.0   # JWT handling
passlib[bcrypt]==1.7.4             # Password hashing
authlib==1.3.0                     # OAuth 2.0 client
python-multipart==0.0.9            # Form data (já existe)

# Database
asyncpg==0.29.0                    # PostgreSQL async driver
sqlalchemy[asyncio]==2.0.25        # ORM async
alembic==1.13.1                    # Database migrations

# Cache & Sessions
redis[hiredis]==5.0.1              # Redis client
```

### 5.2 Estrutura de Módulos

```
backend/src/
├── auth/
│   ├── __init__.py
│   ├── dependencies.py       # FastAPI dependencies (get_current_user)
│   ├── jwt.py               # JWT manager
│   ├── oauth.py             # OAuth providers
│   ├── password.py          # Password hashing
│   ├── permissions.py       # RBAC / Scopes
│   └── schemas.py           # Auth Pydantic models
├── api/
│   └── routes/
│       ├── auth.py          # /auth/* endpoints
│       └── users.py         # /users/* endpoints (profile)
├── models/
│   ├── user.py             # SQLAlchemy User model
│   ├── oauth_account.py    # OAuth accounts
│   └── api_key.py          # API keys
├── services/
│   └── user_service.py     # User CRUD operations
└── core/
    ├── database.py         # Async SQLAlchemy setup
    └── redis.py            # Redis connection
```

### 5.3 Implementação de Endpoints de Auth

```python
# api/routes/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse)
async def register(
    payload: RegisterRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Registrar novo usuário com email/senha."""
    if await user_service.get_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    user = await user_service.create(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name
    )
    return user

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service),
    jwt_manager: JWTManager = Depends(get_jwt_manager)
):
    """Login com email/senha."""
    user = await user_service.authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = jwt_manager.create_access_token({"sub": str(user.id)})
    refresh_token = jwt_manager.create_refresh_token({"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest,
    jwt_manager: JWTManager = Depends(get_jwt_manager)
):
    """Renovar access token usando refresh token."""
    try:
        payload = jwt_manager.verify_token(payload.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        access_token = jwt_manager.create_access_token({"sub": payload["sub"]})
        return TokenResponse(
            access_token=access_token,
            token_type="bearer"
        )
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.get("/google")
async def google_login():
    """Iniciar OAuth flow com Google."""
    # Redirect to Google OAuth
    pass

@router.get("/google/callback")
async def google_callback(code: str):
    """Callback do Google OAuth."""
    # Exchange code for tokens, create/update user
    pass

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis)
):
    """Logout - invalidar tokens."""
    # Add token to blacklist in Redis
    pass
```

### 5.4 Dependency Injection para Proteção de Rotas

```python
# auth/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    jwt_manager: JWTManager = Depends(get_jwt_manager),
    user_service: UserService = Depends(get_user_service)
) -> User:
    """Extrair usuário do JWT token."""
    try:
        payload = jwt_manager.verify_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await user_service.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        return user
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
    api_key: str | None = Depends(api_key_header),
    jwt_manager: JWTManager = Depends(get_jwt_manager),
    user_service: UserService = Depends(get_user_service)
) -> User | None:
    """Retorna usuário se autenticado, None caso contrário."""
    if token:
        try:
            return await get_current_user(token, jwt_manager, user_service)
        except HTTPException:
            pass
    
    if api_key:
        # Validate API key
        pass
    
    return None

def require_scopes(*scopes: str):
    """Decorator para verificar scopes/permissions."""
    async def dependency(user: User = Depends(get_current_user)):
        if not all(scope in user.scopes for scope in scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user
    return dependency
```

### 5.5 Atualização dos Endpoints Existentes

```python
# api/routes/extraction.py - ATUALIZADO

from auth.dependencies import get_current_user, get_current_user_optional

@router.post("/extract-job-details", ...)
@limiter.limit("10/minute")  # Pode ser dinâmico baseado no user tier
async def extract_job_details(
    request: Request,
    payload: ExtractJobDetailsRequest = Body(...),
    current_user: User | None = Depends(get_current_user_optional),  # ← NOVO
    scraper: WebScraperService = Depends(get_scraper_service),
    agent: ExtractionAgent = Depends(get_extraction_agent),
) -> JobResponse:
    """
    Scrape a job posting and return normalized payload.
    
    - Usuários anônimos: rate limit global (10/min por IP)
    - Usuários autenticados: rate limit por user (50/min)
    - Usuários premium: rate limit maior (200/min)
    """
    # Log para auditoria se autenticado
    if current_user:
        logger.info("Job extraction", user_id=str(current_user.id), url=str(payload.url))
    
    # ... resto da lógica
```

---

## 6. Requisitos de Frontend

### 6.1 Estrutura de Módulos

```
frontend/src/
├── auth/
│   ├── AuthContext.tsx      # Context para auth state
│   ├── AuthProvider.tsx     # Provider wrapper
│   ├── useAuth.ts           # Hook para acessar auth
│   ├── guards/
│   │   ├── ProtectedRoute.tsx
│   │   └── GuestRoute.tsx
│   └── components/
│       ├── LoginForm.tsx
│       ├── RegisterForm.tsx
│       └── SocialLoginButtons.tsx
├── services/
│   ├── api.ts               # Atualizar com interceptors
│   └── authService.ts       # Novo - chamadas de auth
└── store/
    └── useAuthStore.ts      # Novo - auth state (Zustand)
```

### 6.2 Auth Store (Zustand)

```typescript
// store/useAuthStore.ts

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  email: string
  fullName: string | null
  avatarUrl: string | null
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  
  setTokens: (accessToken: string, refreshToken: string) => void
  setUser: (user: User) => void
  logout: () => void
  refreshAccessToken: () => Promise<boolean>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      
      setTokens: (accessToken, refreshToken) => {
        set({ accessToken, refreshToken, isAuthenticated: true })
      },
      
      setUser: (user) => {
        set({ user })
      },
      
      logout: () => {
        set({ 
          user: null, 
          accessToken: null, 
          refreshToken: null, 
          isAuthenticated: false 
        })
      },
      
      refreshAccessToken: async () => {
        const { refreshToken } = get()
        if (!refreshToken) return false
        
        try {
          const response = await fetch('/auth/refresh', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken })
          })
          
          if (!response.ok) {
            get().logout()
            return false
          }
          
          const data = await response.json()
          set({ accessToken: data.access_token })
          return true
        } catch {
          get().logout()
          return false
        }
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        refreshToken: state.refreshToken,
        user: state.user
      })
    }
  )
)
```

### 6.3 Axios Interceptors

```typescript
// services/api.ts - ATUALIZADO

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '../store/useAuthStore'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - adiciona token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const accessToken = useAuthStore.getState().accessToken
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - refresh token automático
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true
      
      const refreshed = await useAuthStore.getState().refreshAccessToken()
      if (refreshed) {
        const newToken = useAuthStore.getState().accessToken
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return api(originalRequest)
      }
    }
    
    return Promise.reject(error)
  }
)

export default api
```

### 6.4 Componentes de Autenticação

```typescript
// auth/components/LoginForm.tsx

import { useState } from 'react'
import { useAuthStore } from '../../store/useAuthStore'
import { authService } from '../../services/authService'

export const LoginForm = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  
  const { setTokens, setUser } = useAuthStore()
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    
    try {
      const tokens = await authService.login(email, password)
      setTokens(tokens.access_token, tokens.refresh_token)
      
      const user = await authService.getMe()
      setUser(user)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao fazer login')
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        className="input input-bordered w-full"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Senha"
        className="input input-bordered w-full"
        required
      />
      {error && <div className="text-error text-sm">{error}</div>}
      <button 
        type="submit" 
        className="btn btn-primary w-full"
        disabled={loading}
      >
        {loading ? 'Entrando...' : 'Entrar'}
      </button>
    </form>
  )
}
```

### 6.5 Protected Routes

```typescript
// auth/guards/ProtectedRoute.tsx

import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../store/useAuthStore'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const { isAuthenticated, isLoading } = useAuthStore()
  const location = useLocation()
  
  if (isLoading) {
    return <div className="loading loading-spinner loading-lg" />
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  
  return <>{children}</>
}
```

---

## 7. Requisitos de DevOps/Infraestrutura

### 7.1 Atualização do Docker Compose

```yaml
# docker-compose.yml - ATUALIZADO

version: '3.9'

services:
  # PostgreSQL para persistência de usuários
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: cvsobmedida
      POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}
      POSTGRES_DB: cvsobmedida
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - '5432:5432'
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cvsobmedida"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Redis para sessions e cache
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-changeme}
    volumes:
      - redis_data:/data
    ports:
      - '6379:6379'
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      PYTHONPATH: /app/src
      DATABASE_URL: postgresql+asyncpg://cvsobmedida:${DB_PASSWORD:-changeme}@postgres:5432/cvsobmedida
      REDIS_URL: redis://:${REDIS_PASSWORD:-changeme}@redis:6379/0
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      JWT_ALGORITHM: HS256
      ACCESS_TOKEN_EXPIRE_MINUTES: 15
      REFRESH_TOKEN_EXPIRE_DAYS: 7
      GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}
      GOOGLE_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET}
    env_file:
      - ./backend/.env
    ports:
      - '8000:8000'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: unless-stopped
    depends_on:
      - backend
    environment:
      VITE_API_URL: http://localhost:8000
      VITE_GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}
    ports:
      - '5173:5173'

  # Nginx Reverse Proxy (para produção)
  nginx:
    image: nginx:alpine
    restart: unless-stopped
    depends_on:
      - backend
      - frontend
    ports:
      - '80:80'
      - '443:443'
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - certbot_data:/var/www/certbot:ro

volumes:
  postgres_data:
  redis_data:
  certbot_data:
```

### 7.2 Configuração Nginx para TLS

```nginx
# nginx/nginx.conf

events {
    worker_connections 1024;
}

http {
    # Rate limiting zone
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    
    # Upstream servers
    upstream backend {
        server backend:8000;
    }
    
    upstream frontend {
        server frontend:5173;
    }
    
    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }
    
    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name cvsobmedida.com;
        
        # SSL certificates (Let's Encrypt)
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        
        # SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 1d;
        ssl_session_tickets off;
        
        # HSTS
        add_header Strict-Transport-Security "max-age=63072000" always;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        
        # API endpoints
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Auth endpoints (mais restritivo)
        location /auth/ {
            limit_req zone=api_limit burst=5 nodelay;
            
            proxy_pass http://backend/auth/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

### 7.3 GitHub Actions - CI/CD com Security Checks

```yaml
# .github/workflows/security.yml

name: Security Checks

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # Scan for secrets in code
      - name: GitLeaks Scan
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      
      # Python dependency vulnerabilities
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install Safety
        run: pip install safety
      
      - name: Check Python Dependencies
        run: safety check -r backend/requirements.txt
      
      # Node dependency vulnerabilities
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Audit npm packages
        working-directory: frontend
        run: npm audit --audit-level=high
      
      # SAST scan
      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/security-audit
            p/secrets
            p/owasp-top-ten

  docker-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # Scan Docker images for vulnerabilities
      - name: Build Backend Image
        run: docker build -t cvsobmedida-backend:scan ./backend
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'cvsobmedida-backend:scan'
          format: 'table'
          exit-code: '1'
          ignore-unfixed: true
          severity: 'CRITICAL,HIGH'
```

### 7.4 Kubernetes Manifests (para produção escalável)

```yaml
# k8s/auth-deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: cvsobmedida-backend
  labels:
    app: cvsobmedida
    component: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cvsobmedida
      component: backend
  template:
    metadata:
      labels:
        app: cvsobmedida
        component: backend
    spec:
      containers:
        - name: backend
          image: cvsobmedida/backend:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: cvsobmedida-secrets
                  key: database-url
            - name: JWT_SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: cvsobmedida-secrets
                  key: jwt-secret
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: cvsobmedida-secrets
                  key: redis-url
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 20
---
apiVersion: v1
kind: Service
metadata:
  name: cvsobmedida-backend
spec:
  selector:
    app: cvsobmedida
    component: backend
  ports:
    - port: 8000
      targetPort: 8000
  type: ClusterIP
```

---

## 8. Escalabilidade e Performance

### 8.1 Estratégias de Escalabilidade

| Aspecto | Solução | Benefício |
|---------|---------|-----------|
| **Sessões** | JWT stateless + Redis | Scale horizontal sem problemas |
| **Database** | Connection pooling (asyncpg) | Reduz conexões abertas |
| **Cache** | Redis para tokens invalidados | Consultas rápidas |
| **Rate Limit** | Redis-backed com sliding window | Consistente em múltiplas instâncias |
| **OAuth Tokens** | Cache por user_id | Evita chamadas desnecessárias |

### 8.2 Benchmarks Esperados

```
┌────────────────────────────────────────────────────────────────────────┐
│                    PERFORMANCE TARGETS                                  │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Endpoint              │ P99 Latency  │ RPS (per instance)            │
│  ─────────────────────────────────────────────────────────────────────│
│  POST /auth/login      │ < 100ms      │ 500 req/s                     │
│  POST /auth/register   │ < 200ms      │ 100 req/s                     │
│  GET  /auth/me         │ < 50ms       │ 1000 req/s                    │
│  JWT Validation        │ < 5ms        │ 5000 req/s                    │
│  Token Refresh         │ < 100ms      │ 500 req/s                     │
│                                                                        │
│  Total capacity (3 instances): 3000+ concurrent users                 │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 8.3 Caching Strategy

```python
# core/cache.py

from functools import wraps
from typing import Callable
import redis.asyncio as redis

class CacheManager:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def get_user_session(self, user_id: str) -> dict | None:
        """Buscar sessão do usuário do cache."""
        data = await self.redis.get(f"session:{user_id}")
        if data:
            return json.loads(data)
        return None
    
    async def set_user_session(self, user_id: str, session: dict, ttl: int = 3600):
        """Cachear sessão do usuário."""
        await self.redis.setex(
            f"session:{user_id}",
            ttl,
            json.dumps(session)
        )
    
    async def invalidate_token(self, token_jti: str, ttl: int):
        """Adicionar token à blacklist."""
        await self.redis.setex(f"blacklist:{token_jti}", ttl, "1")
    
    async def is_token_blacklisted(self, token_jti: str) -> bool:
        """Verificar se token está na blacklist."""
        return await self.redis.exists(f"blacklist:{token_jti}") > 0

def cache_result(ttl: int = 300, key_prefix: str = "cache"):
    """Decorator para cachear resultados de funções."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{hash(args)}"
            
            cached = await self.cache.redis.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = await func(self, *args, **kwargs)
            await self.cache.redis.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

---

## 9. Roadmap de Implementação

### 9.1 Timeline de Implementação

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         ROADMAP DE AUTENTICAÇÃO                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  FASE 1 - FUNDAÇÃO (Semana 1-2)                                           │
│  ────────────────────────────────────────────────────────────────────────│
│  [x] Análise de necessidades (este documento)                             │
│  [ ] Setup PostgreSQL + Redis                                              │
│  [ ] Criar models SQLAlchemy (User, OAuthAccount, APIKey)                 │
│  [ ] Implementar JWT Manager                                               │
│  [ ] Criar endpoints básicos (/auth/login, /register, /refresh)           │
│  [ ] Testes unitários para auth                                            │
│                                                                            │
│  FASE 2 - INTEGRAÇÃO BACKEND (Semana 3-4)                                 │
│  ────────────────────────────────────────────────────────────────────────│
│  [ ] Implementar get_current_user dependency                              │
│  [ ] Proteger endpoints existentes                                         │
│  [ ] Implementar rate limit por usuário                                    │
│  [ ] Adicionar logging de auditoria                                        │
│  [ ] Setup OAuth providers (Google)                                        │
│  [ ] Testes de integração                                                  │
│                                                                            │
│  FASE 3 - INTEGRAÇÃO FRONTEND (Semana 5-6)                                │
│  ────────────────────────────────────────────────────────────────────────│
│  [ ] Criar useAuthStore (Zustand)                                         │
│  [ ] Implementar axios interceptors                                        │
│  [ ] Criar páginas Login/Register                                          │
│  [ ] Implementar ProtectedRoute                                            │
│  [ ] Adicionar Social Login buttons                                        │
│  [ ] Testes E2E                                                            │
│                                                                            │
│  FASE 4 - DEVOPS/PRODUÇÃO (Semana 7-8)                                    │
│  ────────────────────────────────────────────────────────────────────────│
│  [ ] Atualizar docker-compose.yml                                         │
│  [ ] Configurar nginx com SSL                                              │
│  [ ] Setup CI/CD com security checks                                       │
│  [ ] Configurar monitoramento (auth metrics)                              │
│  [ ] Documentar runbook de incidentes                                      │
│  [ ] Load testing                                                          │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Estimativas de Esforço

| Fase | Tarefa | Esforço | Prioridade |
|------|--------|---------|------------|
| 1 | Setup Database (PostgreSQL + Redis) | 4h | P0 |
| 1 | Models SQLAlchemy | 6h | P0 |
| 1 | JWT Manager | 4h | P0 |
| 1 | Auth Endpoints básicos | 8h | P0 |
| 1 | Testes unitários | 6h | P0 |
| 2 | Dependency get_current_user | 2h | P0 |
| 2 | Proteger endpoints | 4h | P0 |
| 2 | Rate limit por usuário | 4h | P1 |
| 2 | OAuth Google | 8h | P1 |
| 2 | Logging auditoria | 4h | P1 |
| 3 | useAuthStore | 4h | P0 |
| 3 | Axios interceptors | 2h | P0 |
| 3 | Páginas Login/Register | 8h | P0 |
| 3 | Social Login | 4h | P1 |
| 4 | Docker compose update | 4h | P0 |
| 4 | Nginx + SSL | 4h | P0 |
| 4 | CI/CD security | 4h | P1 |
| 4 | Monitoramento | 4h | P2 |

**Total estimado:** ~84 horas (~2-3 sprints de 2 semanas)

---

## 10. Checklist de Segurança

### 10.1 Pré-Implementação

- [ ] Secret rotation policy definida
- [ ] JWT secret com pelo menos 256 bits
- [ ] Password policy documentada (min 8 chars, complexidade)
- [ ] Rate limiting configurado para auth endpoints
- [ ] CORS configurado corretamente

### 10.2 Durante Implementação

- [ ] Passwords hasheados com bcrypt (cost factor >= 12)
- [ ] Tokens JWT com expiration curta (15 min access, 7 dias refresh)
- [ ] Refresh token rotation implementada
- [ ] Token blacklist para logout
- [ ] Input validation em todos os endpoints
- [ ] SQL injection protegido (SQLAlchemy ORM)
- [ ] XSS protegido (escape de dados)
- [ ] CSRF protegido (SameSite cookies ou custom header)

### 10.3 Pós-Implementação

- [ ] Penetration testing executado
- [ ] OWASP Top 10 checklist validado
- [ ] Dependency audit sem vulnerabilidades críticas
- [ ] Logs de auditoria funcionando
- [ ] Alertas de brute force configurados
- [ ] Backup de dados de usuários testado
- [ ] Runbook de incidentes documentado

### 10.4 OWASP Top 10 Mapping

| OWASP Risk | Mitigação Implementada |
|------------|------------------------|
| A01:2021 Broken Access Control | RBAC + JWT scopes |
| A02:2021 Cryptographic Failures | bcrypt + TLS 1.3 |
| A03:2021 Injection | SQLAlchemy ORM + Pydantic |
| A04:2021 Insecure Design | Auth architecture review |
| A05:2021 Security Misconfiguration | Environment-based config |
| A06:2021 Vulnerable Components | Dependabot + Safety |
| A07:2021 Auth Failures | JWT + OAuth + MFA (future) |
| A08:2021 Data Integrity | Signed JWTs + HTTPS |
| A09:2021 Security Logging | Structured logging + audit |
| A10:2021 SSRF | URL validation |

---

## Apêndice A: Configurações de Ambiente

```bash
# .env.example - Variáveis necessárias para autenticação

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/cvsobmedida

# Redis
REDIS_URL=redis://:password@localhost:6379/0

# JWT Settings
JWT_SECRET_KEY=your-256-bit-secret-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth - Google
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# OAuth - GitHub (optional)
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# Security
ALLOWED_ORIGINS=http://localhost:5173,https://cvsobmedida.com
```

---

## Apêndice B: Diagrama de Sequência - Login Flow

```
┌─────┐          ┌──────────┐          ┌────────┐          ┌───────┐
│User │          │ Frontend │          │Backend │          │  DB   │
└──┬──┘          └────┬─────┘          └───┬────┘          └───┬───┘
   │                  │                    │                   │
   │  1. Enter credentials                 │                   │
   │─────────────────>│                    │                   │
   │                  │                    │                   │
   │                  │ 2. POST /auth/login│                   │
   │                  │───────────────────>│                   │
   │                  │                    │                   │
   │                  │                    │ 3. Query user     │
   │                  │                    │──────────────────>│
   │                  │                    │                   │
   │                  │                    │ 4. User record    │
   │                  │                    │<──────────────────│
   │                  │                    │                   │
   │                  │                    │ 5. Verify password│
   │                  │                    │ (bcrypt compare)  │
   │                  │                    │                   │
   │                  │                    │ 6. Generate JWT   │
   │                  │                    │ (access+refresh)  │
   │                  │                    │                   │
   │                  │ 7. Return tokens   │                   │
   │                  │<───────────────────│                   │
   │                  │                    │                   │
   │                  │ 8. Store tokens    │                   │
   │                  │ (Zustand/localStorage)                 │
   │                  │                    │                   │
   │  9. Redirect to app                   │                   │
   │<─────────────────│                    │                   │
   │                  │                    │                   │
```

---

**Documento gerado:** 26 de Novembro de 2025  
**Autor:** Análise automatizada  
**Próxima revisão:** Após implementação da Fase 1
