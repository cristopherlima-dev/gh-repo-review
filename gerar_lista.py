"""
Busca os repositórios no GitHub (via gh) e monta a página HTML.

Uso sozinho:  python gerar_lista.py
  -> gera saida/repositorios.html (modo estático: só visualizar e marcar, sem botões de ação)
O servidor.py reaproveita as funções daqui.
"""
import json
import os
import re
import subprocess
import webbrowser
from datetime import datetime

from config import BASE, CONFIG

PASTA_PROJETOS = CONFIG["pasta_projetos"]
TEMPLATE = BASE / "template.html"
REVISAO = CONFIG["pasta_dados"] / "revisao.json"
SAIDA = BASE / "saida" / "repositorios.html"


def pasta_da_linguagem(linguagem):
    """Nome da pasta para a linguagem (ex.: C# -> csharp, Python -> python)."""
    if not linguagem:
        return CONFIG["pasta_sem_linguagem"]
    return CONFIG["apelidos"].get(linguagem, linguagem.lower())


def rodar_gh(*args):
    """Roda o gh e devolve o texto da saída; encerra com mensagem clara se falhar."""
    try:
        res = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit("GitHub CLI (gh) não encontrado. Instale em https://cli.github.com e rode: gh auth login")
    if res.returncode != 0:
        raise SystemExit("Erro ao chamar o gh:\n" + res.stderr.strip()
                         + "\nSe não estiver logado, rode: gh auth login")
    return res.stdout


def usuario_logado():
    return rodar_gh("api", "user", "--jq", ".login").strip()


def buscar_repos():
    """Lista os repositórios do usuário logado (e das organizações, se configurado)."""
    afiliacao = "owner,organization_member" if CONFIG["incluir_organizacoes"] else "owner"
    texto = rodar_gh("api", f"user/repos?affiliation={afiliacao}&per_page=100",
                     "--paginate", "--jq", ".[]").strip()
    # O gh devolve um objeto JSON por linha; lemos um por um
    repos, leitor, pos = [], json.JSONDecoder(), 0
    while pos < len(texto):
        objeto, pos = leitor.raw_decode(texto, pos)
        repos.append(objeto)
        while pos < len(texto) and texto[pos].isspace():
            pos += 1
    return repos


def carregar_revisao():
    if REVISAO.exists():
        return json.loads(REVISAO.read_text(encoding="utf-8"))
    return {}


def pastas_locais():
    """Nomes (em minúsculo) das pastas em <pasta_projetos>/<qualquer linguagem>/."""
    nomes = set()
    if PASTA_PROJETOS.exists():
        for pasta_ling in PASTA_PROJETOS.iterdir():
            if pasta_ling.is_dir():
                nomes.update(p.name.lower() for p in pasta_ling.iterdir() if p.is_dir())
    return nomes


def existe_local(nome):
    return nome.lower() in pastas_locais()


def montar_dados(repos, revisao, usuario):
    locais = pastas_locais()
    lista = []
    for r in repos:
        marcacao = revisao.get(r["full_name"], {})
        lista.append({
            "id": r["full_name"],            # dono/nome: identifica o repositório sem ambiguidade
            "nome": r["name"],
            "dono": r["owner"]["login"],
            "linguagem": r["language"] or "",
            "pasta": pasta_da_linguagem(r["language"]),
            "criado_em": r["created_at"][:10],
            "atualizado_em": (r["pushed_at"] or r["updated_at"])[:10],
            "privado": r["private"],
            "arquivado": r["archived"],
            "descricao": r["description"] or "",
            "url": r["html_url"],
            "local": r["name"].lower() in locais,
            "status": marcacao.get("status", ""),
            "obs": marcacao.get("obs", ""),
        })
    return {
        "usuario": usuario,
        "gerado_em": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "pasta_projetos": str(PASTA_PROJETOS),
        "sep": os.sep,
        "anos_parado": CONFIG["anos_parado"],
        "permitir_excluir": CONFIG["permitir_excluir"],
        "repos": lista,
    }


def gerar_html_texto(dados):
    """Devolve o HTML do template com os dados encaixados entre os marcadores."""
    modelo = TEMPLATE.read_text(encoding="utf-8")
    # "<\/" evita que uma descrição com </script> quebre a página
    json_texto = json.dumps(dados, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return re.sub(
        r"/\*__DADOS_INICIO__\*/.*?/\*__DADOS_FIM__\*/",
        lambda _: "/*__DADOS_INICIO__*/" + json_texto + "/*__DADOS_FIM__*/",
        modelo,
        flags=re.DOTALL,
    )


def main():
    print("Buscando repositórios no GitHub...")
    dados = montar_dados(buscar_repos(), carregar_revisao(), usuario_logado())
    SAIDA.parent.mkdir(exist_ok=True)
    SAIDA.write_text(gerar_html_texto(dados), encoding="utf-8")
    print(f"{len(dados['repos'])} repositórios. Página gerada em: {SAIDA}")
    webbrowser.open(SAIDA.as_uri())


if __name__ == "__main__":
    main()
