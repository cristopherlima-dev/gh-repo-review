"""
Servidor local do gh-repo-review.

Serve a página em http://localhost:<porta> e executa as ações pedidas por ela:
salvar revisão, escolher pasta, clonar, arquivar, desarquivar, transferir para a organização,
devolver para a sua conta, liberar/tirar do time dev, excluir e relatório (via git/gh).

Uso:  python servidor.py   (ou abrir.bat / abrir.sh)
Para parar: feche a janela ou Ctrl+C.
"""
import json
import secrets
import shutil
import subprocess
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

from config import CONFIG
from gerar_lista import (PASTA_PROJETOS, REVISAO, buscar_repos, carregar_revisao,
                         montar_dados, existe_local, gerar_html_texto, usuario_logado)
from relatorio import registrar, gerar_relatorio
from i18n import t, idioma_valido

PORTA = CONFIG["porta"]
TOKEN = secrets.token_hex(16)   # senha da sessão: só a página gerada por este servidor pode dar ordens
cache = {"dados": None}         # lista de repositórios em memória (evita chamar o GitHub a cada clique)
IDIOMA = idioma_valido(CONFIG["idioma"])   # idioma do terminal e padrão das respostas
ORG = CONFIG["organizacao_destino"]          # organização que recebe as transferências (vazio = desligado)
TIME_DEV = CONFIG["time_dev"] if ORG else ""  # time controlado pelo botão "Liberar p/ dev"
pedido = {"idioma": IDIOMA}     # idioma do pedido atual (vem da página; o servidor atende um pedido por vez)


def msg(chave, **valores):
    """Mensagem no idioma escolhido na página."""
    return t(pedido["idioma"], chave, **valores)


# ---------- ações ----------

def repos_do_time(time_slug):
    """Nomes (dono/nome, minúsculo) dos repositórios que o time já acessa."""
    ok, saida = gh("api", f"orgs/{ORG}/teams/{time_slug}/repos?per_page=100", "--paginate", "--jq", ".[].full_name")
    if not ok:
        print(t(IDIOMA, "aviso_time", t=time_slug, o=ORG, e=saida))
        return set()
    return {linha.strip().lower() for linha in saida.splitlines() if linha.strip()}


def atualizar_cache():
    cache["dados"] = montar_dados(buscar_repos(), carregar_revisao(), usuario_logado())
    cache["dados"]["token"] = TOKEN
    cache["dados"]["servidor"] = True
    no_dev = repos_do_time(TIME_DEV) if TIME_DEV else set()
    for r in cache["dados"]["repos"]:
        r["no_dev"] = r["id"].lower() in no_dev


def repo_por_id(repo_id):
    return next(r for r in cache["dados"]["repos"] if r["id"] == repo_id)


def salvar_revisao(revisao):
    REVISAO.write_text(json.dumps(revisao, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in cache["dados"]["repos"]:
        marcacao = revisao.get(r["id"], {})
        r["status"], r["obs"] = marcacao.get("status", ""), marcacao.get("obs", "")
        r["dev_acao"] = marcacao.get("dev", "")


def limpar_status(revisao, r):
    """Tira o status do repositório (mantém a observação)."""
    r["status"] = ""
    if r["id"] in revisao:
        revisao[r["id"]]["status"] = ""
        if not revisao[r["id"]].get("obs") and not revisao[r["id"]].get("dev"):
            revisao.pop(r["id"])


def limpar_dev(revisao, r):
    """Tira a marcação do time dev (mantém status e observação)."""
    r["dev_acao"] = ""
    marcacao = revisao.get(r["id"])
    if marcacao:
        marcacao.pop("dev", None)
        if not marcacao.get("status") and not marcacao.get("obs"):
            revisao.pop(r["id"])


def escolher_pasta(inicial):
    """Abre a janela 'Selecionar pasta' do sistema (precisa do tkinter)."""
    try:
        import tkinter
        from tkinter import filedialog
    except ImportError:
        raise RuntimeError(msg("sem_tkinter"))
    raiz = tkinter.Tk()
    raiz.withdraw()                       # esconde a janela principal vazia do tkinter
    raiz.attributes("-topmost", True)     # garante que a janela apareça na frente do navegador
    pasta = filedialog.askdirectory(initialdir=inicial or str(PASTA_PROJETOS),
                                    title=msg("titulo_pasta"))
    raiz.destroy()
    return str(Path(pasta)) if pasta else ""


def gh(*args):
    """Roda um comando do gh e devolve (deu_certo, mensagem)."""
    res = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8")
    return res.returncode == 0, (res.stdout + res.stderr).strip()


def clonar(repo_id, pasta):
    r = repo_por_id(repo_id)
    destino = Path(pasta).expanduser() / r["nome"]
    if destino.exists():
        return False, msg("pasta_existe", p=destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    ok, saida = gh("repo", "clone", repo_id, str(destino))
    if not ok:
        return False, saida

    # Confere se o clone ficou completo: tem a pasta .git e o último commit pode ser lido
    if not (destino / ".git").exists():
        return False, msg("sem_pasta_git", p=destino)
    log = subprocess.run(["git", "-C", str(destino), "log", "-1", "--format=%h %s (%cd)", "--date=short"],
                         capture_output=True, text=True, encoding="utf-8")
    ultimo = log.stdout.strip() or msg("repo_vazio")

    r["local"] = existe_local(r["nome"])
    registrar("clonado", r, str(destino))
    return True, msg("clonado_ok", p=destino, c=ultimo)


def desarquivar(repo_id):
    r = repo_por_id(repo_id)
    ok, saida = gh("repo", "unarchive", repo_id, "--yes")
    if ok:
        r["arquivado"] = False
        registrar("desarquivado", r)
        revisao = carregar_revisao()
        limpar_status(revisao, r)   # evita que seja arquivado de novo no próximo "Aplicar"
        salvar_revisao(revisao)
    return ok, saida or msg("desarquivado_ok")


def clones_locais(nome):
    """Pastas <pasta_projetos>/<linguagem>/<nome> que são clones git (pode haver mais de uma)."""
    achados = []
    if PASTA_PROJETOS.exists():
        for pasta_ling in PASTA_PROJETOS.iterdir():
            if not pasta_ling.is_dir():
                continue
            for p in pasta_ling.iterdir():
                if p.is_dir() and p.name.lower() == nome.lower() and (p / ".git").exists():
                    achados.append(p)
    return achados


def atualizar_remote(pasta, id_antigo, id_novo):
    """
    Troca 'dono/nome' por 'org/nome' no endereço do origin, mantendo o formato (https ou ssh).
    Devolve (deu_certo, mensagem); ignora clones cujo origin aponta para outro repositório.
    """
    git = lambda *a: subprocess.run(["git", "-C", str(pasta), *a], capture_output=True, text=True, encoding="utf-8")
    atual = git("config", "--get", "remote.origin.url")   # endereço gravado, sem reescritas (insteadOf)
    if atual.returncode != 0:
        return False, msg("remote_erro", p=pasta, e=atual.stderr.strip())
    url = atual.stdout.strip()
    pos = url.lower().find(id_antigo.lower())
    if pos < 0:
        return None, ""   # esse clone é de outro repositório com o mesmo nome: não mexe
    nova = url[:pos] + id_novo + url[pos + len(id_antigo):]
    res = git("remote", "set-url", "origin", nova)
    if res.returncode != 0:
        return False, msg("remote_erro", p=pasta, e=res.stderr.strip())
    return True, msg("remote_ok", p=pasta)


def dar_acesso_time(time_slug, repo_id, permissao, tentativas=5):
    """
    Dá ao time a permissão no repositório da ORG (pull, triage, push, maintain, admin).
    Logo após uma transferência o GitHub ainda pode estar movendo o repositório: tenta algumas vezes.
    """
    for i in range(tentativas):
        ok, saida = gh("api", "-X", "PUT", f"orgs/{ORG}/teams/{time_slug}/repos/{repo_id}",
                       "-f", f"permission={permissao}")
        if ok or i == tentativas - 1:
            return ok, saida
        time.sleep(2)


def mover(r, novo_dono):
    """
    Transfere o repositório para novo_dono, atualiza o remote dos clones locais e o próprio
    item da lista (que continua aparecendo, agora com o dono novo). Devolve (ok, linhas, id_novo).
    """
    # O gh não tem comando pronto para transferir; usamos a API REST direto
    ok, saida = gh("api", "-X", "POST", f"repos/{r['id']}/transfer", "-f", f"new_owner={novo_dono}")
    if not ok:
        return False, [saida], ""

    id_antigo, id_novo = r["id"], f"{novo_dono}/{r['nome']}"
    linhas, pastas = [], []
    for pasta in clones_locais(r["nome"]):
        certo, texto = atualizar_remote(pasta, id_antigo, id_novo)
        if certo is not None:
            linhas.append(texto)
            if certo:
                pastas.append(str(pasta))
    if not linhas:
        linhas.append(msg("remote_nenhum"))

    r.update(id=id_novo, dono=novo_dono, url=f"https://github.com/{id_novo}", status="", no_dev=False)
    r["_pastas"] = "; ".join(pastas)
    return True, linhas, id_antigo


def transferir(r):
    """Leva o repositório da sua conta para a ORG e aplica os times_ao_transferir. Devolve (ok, mensagem)."""
    if not ORG:
        return False, msg("transferir_desligado")
    if r["dono"].lower() == ORG.lower():
        return False, msg("ja_na_org", o=ORG)
    ok, linhas, _ = mover(r, ORG)
    if not ok:
        return False, linhas[0]
    linhas.insert(0, msg("transferido_ok", u=r["url"]))
    for time_slug, permissao in CONFIG["times_ao_transferir"].items():
        certo, saida = dar_acesso_time(time_slug, r["id"], permissao)
        linhas.append(msg("time_ok", t=time_slug, p=permissao) if certo else msg("time_erro", t=time_slug, e=saida))
        if certo and time_slug.lower() == TIME_DEV.lower():
            r["no_dev"] = True
    registrar("transferido", r, r.pop("_pastas"))
    return True, "\n".join(linhas)


def devolver(r):
    """Traz o repositório da ORG de volta para a sua conta (ex.: transferência indevida)."""
    if not ORG or r["dono"].lower() != ORG.lower():
        return False, msg("devolver_so_org", o=ORG or "?")
    ok, linhas, _ = mover(r, cache["dados"]["usuario"])
    if not ok:
        return False, linhas[0]
    linhas.insert(0, msg("devolvido_ok", u=r["url"]))
    registrar("devolvido", r, r.pop("_pastas"))
    return True, "\n".join(linhas)


def alternar_dev(repo_id, liberar):
    """Dá Write ao time dev (liberar=True) ou tira o repositório do time (False)."""
    if not TIME_DEV:
        return False, msg("sem_time_dev")
    r = repo_por_id(repo_id)
    if liberar:
        ok, saida = dar_acesso_time(TIME_DEV, repo_id, "push", tentativas=1)
    else:
        ok, saida = gh("api", "-X", "DELETE", f"orgs/{ORG}/teams/{TIME_DEV}/repos/{repo_id}")
    if ok:
        r["no_dev"] = liberar
        registrar("dev_liberado" if liberar else "dev_removido", r)
    return ok, saida


def aplicar(revisao):
    """Arquiva, libera/tira do time dev, transfere, devolve e exclui no GitHub. Devolve o resultado de cada um."""
    salvar_revisao(revisao)
    resultados = []
    for r in list(cache["dados"]["repos"]):
        # Time dev primeiro: só vale para repositórios que estão (e vão continuar) na organização
        if r.get("dev_acao"):
            liberar = r["dev_acao"] == "liberar"
            if TIME_DEV and ORG and r["dono"].lower() == ORG.lower() and r["status"] != "devolver" \
                    and liberar != r.get("no_dev", False):
                ok, saida = alternar_dev(r["id"], liberar)
                resultados.append({"id": r["id"], "acao": "dev_" + r["dev_acao"], "ok": ok, "msg": saida})
                if ok:
                    limpar_dev(revisao, r)
            else:
                limpar_dev(revisao, r)   # não se aplica mais (já está assim, ou saiu da organização)

        if r["status"] == "arquivar" and not r["arquivado"]:
            ok, saida = gh("repo", "archive", r["id"], "--yes")
            if ok:
                r["arquivado"] = True
                registrar("arquivado", r)
                limpar_status(revisao, r)   # já está arquivado; a marcação cumpriu o papel
            resultados.append({"id": r["id"], "acao": "arquivar", "ok": ok, "msg": saida})
        elif r["status"] in ("transferir", "devolver"):
            id_antes, acao = r["id"], r["status"]   # guardados antes: mover() troca o id e limpa o status
            ok, saida = (transferir if acao == "transferir" else devolver)(r)
            if ok:
                revisao.pop(id_antes, None)   # o item continua na lista, com o dono novo e sem marcação
                if r.get("obs"):
                    revisao[r["id"]] = {"status": "", "obs": r["obs"]}
            resultados.append({"id": id_antes, "acao": acao, "ok": ok, "msg": saida})
        elif r["status"] == "excluir":
            if not CONFIG["permitir_excluir"]:
                resultados.append({"id": r["id"], "acao": "excluir", "ok": False, "msg": msg("excluir_desligado")})
                continue
            ok, saida = gh("repo", "delete", r["id"], "--yes")
            if ok:
                registrar("excluido", r)
                cache["dados"]["repos"].remove(r)
                revisao.pop(r["id"], None)
            resultados.append({"id": r["id"], "acao": "excluir", "ok": ok, "msg": saida})
    salvar_revisao(revisao)
    return resultados


# ---------- servidor HTTP ----------

class Manipulador(BaseHTTPRequestHandler):

    def responder(self, codigo, corpo, tipo="application/json"):
        dados = corpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo + "; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.responder(200, gerar_html_texto(cache["dados"]), "text/html")
        else:
            self.responder(404, json.dumps({"erro": msg("nao_encontrado")}, ensure_ascii=False))

    def do_POST(self):
        pedido["idioma"] = idioma_valido(self.headers.get("X-Idioma"), IDIOMA)
        if self.headers.get("X-Token") != TOKEN:
            return self.responder(403, json.dumps({"erro": msg("token_invalido")}, ensure_ascii=False))
        tamanho = int(self.headers.get("Content-Length", 0))
        corpo = json.loads(self.rfile.read(tamanho) or "{}")
        try:
            if self.path == "/api/revisao":
                salvar_revisao(corpo["revisao"])
                resposta = {"ok": True}
            elif self.path == "/api/escolher-pasta":
                resposta = {"pasta": escolher_pasta(corpo.get("inicial", ""))}
            elif self.path == "/api/clonar":
                ok, texto = clonar(corpo["id"], corpo["pasta"])
                resposta = {"ok": ok, "msg": texto}
            elif self.path == "/api/desarquivar":
                ok, texto = desarquivar(corpo["id"])
                resposta = {"ok": ok, "msg": texto}
            elif self.path == "/api/aplicar":
                tem_exclusao = any(v.get("status") == "excluir" for v in corpo["revisao"].values())
                confirmado = corpo.get("confirmacao") in ("DELETE", "EXCLUIR")   # palavra em inglês ou português
                if tem_exclusao and CONFIG["permitir_excluir"] and not confirmado:
                    return self.responder(400, json.dumps({"erro": msg("confirmacao_ausente")}, ensure_ascii=False))
                resposta = {"resultados": aplicar(corpo["revisao"])}
            elif self.path == "/api/relatorio":
                atualizar_cache()   # pega a situação real do GitHub antes de montar o relatório
                arquivo = gerar_relatorio(cache["dados"]["usuario"], cache["dados"]["repos"], pedido["idioma"])
                webbrowser.open(arquivo.as_uri())   # abre o relatório numa nova aba
                resposta = {"arquivo": str(arquivo)}
            elif self.path == "/api/atualizar":
                atualizar_cache()
                resposta = {"ok": True}
            else:
                return self.responder(404, json.dumps({"erro": msg("nao_encontrado")}, ensure_ascii=False))
            self.responder(200, json.dumps(resposta, ensure_ascii=False))
        except Exception as erro:
            self.responder(500, json.dumps({"erro": str(erro)}, ensure_ascii=False))

    def log_message(self, formato, *args):
        pass   # silencia o log padrão de cada requisição


def main():
    if not shutil.which("gh"):
        raise SystemExit(t(IDIOMA, "sem_gh"))
    if not shutil.which("git"):
        raise SystemExit(t(IDIOMA, "sem_git"))

    print(t(IDIOMA, "inicio_pasta", p=PASTA_PROJETOS))
    print(t(IDIOMA, "inicio_excluir", s=t(IDIOMA, "ligado" if CONFIG["permitir_excluir"] else "desligado")))
    print(t(IDIOMA, "inicio_org", o=ORG or t(IDIOMA, "desligado")) + (f"  ·  dev: {TIME_DEV}" if TIME_DEV else ""))
    print(t(IDIOMA, "buscando"))
    atualizar_cache()
    print(t(IDIOMA, "carregados", n=len(cache["dados"]["repos"]), u=cache["dados"]["usuario"]))

    try:
        servidor = HTTPServer(("127.0.0.1", PORTA), Manipulador)   # 127.0.0.1 = só este computador acessa
    except OSError:
        raise SystemExit(t(IDIOMA, "porta_em_uso", p=PORTA))
    endereco = f"http://localhost:{PORTA}"
    print(t(IDIOMA, "pagina_em", e=endereco))
    if CONFIG["abrir_navegador"]:
        webbrowser.open(endereco)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print(t(IDIOMA, "encerrado"))


if __name__ == "__main__":
    main()
