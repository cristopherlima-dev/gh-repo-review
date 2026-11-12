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
from i18n import t, idioma_valido

IDIOMA = idioma_valido(CONFIG["idioma"])   # idioma das mensagens no terminal

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
        raise SystemExit(t(IDIOMA, "sem_gh"))
    if res.returncode != 0:
        raise SystemExit(t(IDIOMA, "erro_gh", e=res.stderr.strip()))
    return res.stdout


def usuario_logado():
    return rodar_gh("api", "user", "--jq", ".login").strip()


def ler_objetos(texto):
    """O gh devolve um objeto JSON por linha; lemos um por um."""
    texto = texto.strip()
    objetos, leitor, pos = [], json.JSONDecoder(), 0
    while pos < len(texto):
        objeto, pos = leitor.raw_decode(texto, pos)
        objetos.append(objeto)
        while pos < len(texto) and texto[pos].isspace():
            pos += 1
    return objetos


def buscar_repos():
    """
    Lista os repositórios do usuário logado (e das organizações, se configurado).
    Os da organizacao_destino entram sempre: são os que você transferiu e pode devolver.
    """
    afiliacao = "owner,organization_member" if CONFIG["incluir_organizacoes"] else "owner"
    repos = ler_objetos(rodar_gh("api", f"user/repos?affiliation={afiliacao}&per_page=100",
                                 "--paginate", "--jq", ".[]"))
    org = CONFIG["organizacao_destino"]
    if org:
        res = subprocess.run(["gh", "api", f"orgs/{org}/repos?per_page=100", "--paginate", "--jq", ".[]"],
                             capture_output=True, text=True, encoding="utf-8")
        if res.returncode == 0:
            ja = {r["full_name"].lower() for r in repos}
            repos += [r for r in ler_objetos(res.stdout) if r["full_name"].lower() not in ja]
        else:   # organização errada ou sem acesso: avisa e segue só com os seus
            print(t(IDIOMA, "aviso_org", o=org, e=res.stderr.strip()))
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
            "dev_acao": marcacao.get("dev", ""),   # "liberar" / "tirar" do time dev (pendente)
        })
    return {
        "usuario": usuario,
        "gerado_em": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "pasta_projetos": str(PASTA_PROJETOS),
        "sep": os.sep,
        "anos_parado": CONFIG["anos_parado"],
        "permitir_excluir": CONFIG["permitir_excluir"],
        "organizacao_destino": CONFIG["organizacao_destino"],
        "time_dev": CONFIG["time_dev"],
        "idioma": IDIOMA,
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
    print(t(IDIOMA, "buscando"))
    dados = montar_dados(buscar_repos(), carregar_revisao(), usuario_logado())
    SAIDA.parent.mkdir(exist_ok=True)
    SAIDA.write_text(gerar_html_texto(dados), encoding="utf-8")
    print(t(IDIOMA, "pagina_gerada", n=len(dados["repos"]), p=SAIDA))
    webbrowser.open(SAIDA.as_uri())


if __name__ == "__main__":
    main()
