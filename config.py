"""
Leitura da configuração (config.json).

Na primeira execução, copia o config.example.json para config.json.
Cada pessoa edita o seu config.json, que não vai para o git.
"""
import json
import os
import shutil
from pathlib import Path

BASE = Path(__file__).parent
ARQ_CONFIG = BASE / "config.json"
ARQ_EXEMPLO = BASE / "config.example.json"

# Valores usados quando a chave não existir no config.json
PADRAO = {
    "pasta_projetos": "~/projetos",
    "porta": 8765,
    "anos_parado": 2,
    "permitir_excluir": False,
    "incluir_organizacoes": False,
    "abrir_navegador": True,
    "pasta_sem_linguagem": "outros",
    "apelidos": {},
}


def carregar():
    if not ARQ_CONFIG.exists():
        shutil.copy(ARQ_EXEMPLO, ARQ_CONFIG)
        print(f"Criado {ARQ_CONFIG.name} a partir do exemplo. Revise a 'pasta_projetos' nele.")
    try:
        dados = json.loads(ARQ_CONFIG.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erro:
        raise SystemExit(f"Erro no {ARQ_CONFIG.name}, linha {erro.lineno}: {erro.msg}. "
                         "Dica: no Windows use barras duplas, ex.: \"D:\\\\PROJETOS\".")
    cfg = {**PADRAO, **{k: v for k, v in dados.items() if not k.startswith("_")}}
    cfg["pasta_projetos"] = Path(os.path.expandvars(cfg["pasta_projetos"])).expanduser()
    return cfg


CONFIG = carregar()
