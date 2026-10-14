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
    "pasta_dados": "dados",
    "porta": 8765,
    "anos_parado": 2,
    "permitir_excluir": False,
    "incluir_organizacoes": False,
    "abrir_navegador": True,
    "idioma": "en",
    "pasta_sem_linguagem": "outros",
    "apelidos": {},
}


def carregar():
    if not ARQ_CONFIG.exists():
        shutil.copy(ARQ_EXEMPLO, ARQ_CONFIG)
        print(f"Created {ARQ_CONFIG.name} from the example - check 'pasta_projetos' in it. / "
              f"Criado {ARQ_CONFIG.name} a partir do exemplo - revise a 'pasta_projetos' nele.")
    try:
        dados = json.loads(ARQ_CONFIG.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erro:
        raise SystemExit(f"Error in {ARQ_CONFIG.name}, line {erro.lineno}: {erro.msg}. "
                         "Tip: on Windows use double backslashes, e.g. \"D:\\\\PROJETOS\". / "
                         f"Erro no {ARQ_CONFIG.name}, linha {erro.lineno}. Dica: use barras duplas.")
    cfg = {**PADRAO, **{k: v for k, v in dados.items() if not k.startswith("_")}}
    cfg["pasta_projetos"] = caminho(cfg["pasta_projetos"])
    # Pasta dos dados de revisão/histórico/relatórios; caminho relativo = dentro da pasta do projeto
    cfg["pasta_dados"] = BASE / caminho(cfg["pasta_dados"] or "dados")
    cfg["pasta_dados"].mkdir(parents=True, exist_ok=True)
    return cfg


def caminho(texto):
    """Expande ~ e variáveis de ambiente (%USERPROFILE%, $HOME...)."""
    return Path(os.path.expandvars(texto)).expanduser()


CONFIG = carregar()
