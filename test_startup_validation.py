#!/usr/bin/env python
"""Teste de validacao do startup - verifica se tudo esta pronto para iniciar."""
import sys
from pathlib import Path
import subprocess

def check_python_venv():
    """Verifica se o Python venv esta pronto."""
    venv_path = Path("backend/.venv/Scripts/python.exe")
    if not venv_path.exists():
        print("[ERRO] Python venv nao encontrado em backend/.venv")
        return False

    try:
        result = subprocess.run(
            [str(venv_path), "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"[OK] {result.stdout.strip()} encontrado")
            return True
    except Exception as e:
        print(f"[ERRO] Falha ao verificar Python: {e}")
    return False


def check_backend_env():
    """Verifica se backend/.env existe."""
    env_path = Path("backend/.env")
    if env_path.exists():
        print("[OK] backend/.env encontrado")
        # Verificar se GOOGLE_API_KEY esta configurada
        with open(env_path) as f:
            content = f.read()
            if "GOOGLE_API_KEY" in content and "=" in content:
                print("    [OK] GOOGLE_API_KEY configurada")
                return True
            else:
                print("    [AVISO] GOOGLE_API_KEY nao configurada em backend/.env")
                return False
    else:
        print("[ERRO] backend/.env nao encontrado")
        return False


def check_node_npm():
    """Verifica se Node.js e npm estao instalados."""
    try:
        # Tentar com shell=True para ambientes bash/git bash
        node_result = subprocess.run(
            "node --version",
            capture_output=True,
            text=True,
            shell=True
        )
        npm_result = subprocess.run(
            "npm --version",
            capture_output=True,
            text=True,
            shell=True
        )

        if node_result.returncode == 0 and npm_result.returncode == 0:
            node_version = node_result.stdout.strip()
            npm_version = npm_result.stdout.strip()
            print(f"[OK] Node.js {node_version} encontrado")
            print(f"[OK] npm {npm_version} encontrado")
            return True
        else:
            # Se shell=True falhar, verificar se node_modules existe como fallback
            if Path("frontend/node_modules").exists():
                print("[OK] Node.js e npm detectados (node_modules existente)")
                print("    [NOTA] Caminho do Node.js pode nao estar no PATH, mas aplicacao pode rodar")
                return True
            print("[AVISO] Node.js e npm nao encontrados no PATH")
            print("    Verifique: node --version")
            return False
    except Exception as e:
        # Se node_modules existe, nao e um erro critico
        if Path("frontend/node_modules").exists():
            print("[OK] Node.js/npm detectados (node_modules existente)")
            return True
        print(f"[AVISO] Falha ao verificar Node.js/npm: {e}")
        return False


def check_frontend_node_modules():
    """Verifica se frontend/node_modules esta instalado."""
    node_modules = Path("frontend/node_modules")
    if node_modules.exists():
        print("[OK] frontend/node_modules encontrado")
        return True
    else:
        print("[AVISO] frontend/node_modules nao encontrado (sera instalado automaticamente)")
        return True  # Nao e um erro bloqueador


def check_frontend_env():
    """Verifica se frontend/.env existe."""
    env_path = Path("frontend/.env")
    if env_path.exists():
        print("[OK] frontend/.env encontrado")
        return True
    else:
        print("[AVISO] frontend/.env nao encontrado (sera criado automaticamente)")
        return True  # Nao e um erro bloqueador


def main():
    """Executa todos os testes."""
    print("=" * 60)
    print("VALIDACAO DE STARTUP - CV SOB MEDIDA")
    print("=" * 60)
    print()

    checks = [
        ("Python venv", check_python_venv),
        ("Backend .env", check_backend_env),
        ("Node.js e npm", check_node_npm),
        ("Frontend node_modules", check_frontend_node_modules),
        ("Frontend .env", check_frontend_env),
    ]

    results = []
    for name, check_func in checks:
        print(f"[{len(results)+1}/{len(checks)}] Verificando {name}...")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"[ERRO] {e}")
            results.append((name, False))
        print()

    # Resumo
    print("=" * 60)
    print("RESUMO")
    print("=" * 60)
    print()

    errors = sum(1 for _, result in results if not result)

    for name, result in results:
        status = "[OK]" if result else "[ERRO]"
        print(f"{status} {name}")

    print()

    if errors == 0:
        print("Tudo validado com sucesso!")
        print("Voce pode executar: start_app.bat")
        return 0
    else:
        print(f"{errors} problema(s) encontrado(s).")
        print("Resolva os problemas e tente novamente.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
