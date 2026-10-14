#!/usr/bin/env sh
# Abre o gh-repo-review no Linux/macOS.  Uso: ./abrir.sh

# Vai para a pasta onde este script está (funciona de qualquer lugar)
cd "$(dirname "$0")" || exit 1

# Procura o Python 3
if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo "Python 3 não encontrado. Instale pelo gerenciador de pacotes ou em https://www.python.org/downloads/"
    exit 1
fi

exec "$PY" servidor.py
