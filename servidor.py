"""
Servidor local do gh-repo-review.

Serve a página em http://localhost:<porta> e executa as ações pedidas por ela:
salvar revisão, escolher pasta, clonar, arquivar, desarquivar, excluir e relatório (via git/gh).

Uso:  python servidor.py   (ou abrir.bat / abrir.sh)
Para parar: feche a janela ou Ctrl+C.
"""
import json
import secrets
import shutil
import subprocess
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
pedido = {"idioma": IDIOMA}     # idioma do pedido atual (vem da página; o servidor atende um pedido por vez)


def msg(chave, **valores):
    """Mensagem no idioma escolhido na página."""
    return t(pedido["idioma"], chave, **valores)


# ---------- ações ----------

def atualizar_cache():
    cache["dados"] = montar_dados(buscar_repos(), carregar_revisao(), usuario_logado())
    cache["dados"]["token"] = TOKEN
    cache["dados"]["servidor"] = True


def repo_por_id(repo_id):
    return next(r for r in cache["dados"]["repos"] if r["id"] == repo_id)


def salvar_revisao(revisao):
    REVISAO.write_text(json.dumps(revisao, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in cache["dados"]["repos"]:
        marcacao = revisao.get(r["id"], {})
        r["status"], r["obs"] = marcacao.get("status", ""), marcacao.get("obs", "")


def limpar_status(revisao, r):
    """Tira o status do repositório (mantém a observação)."""
    r["status"] = ""
    if r["id"] in revisao:
        revisao[r["id"]]["status"] = ""
        if not revisao[r["id"]].get("obs"):
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


def aplicar(revisao):
    """Arquiva e exclui no GitHub conforme a revisão. Devolve o resultado de cada um."""
    salvar_revisao(revisao)
    resultados = []
    for r in list(cache["dados"]["repos"]):
        if r["status"] == "arquivar" and not r["arquivado"]:
            ok, saida = gh("repo", "archive", r["id"], "--yes")
            if ok:
                r["arquivado"] = True
                registrar("arquivado", r)
                limpar_status(revisao, r)   # já está arquivado; a marcação cumpriu o papel
            resultados.append({"id": r["id"], "acao": "arquivar", "ok": ok, "msg": saida})
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
                ok, msg = clonar(corpo["id"], corpo["pasta"])
                resposta = {"ok": ok, "msg": msg}
            elif self.path == "/api/desarquivar":
                ok, msg = desarquivar(corpo["id"])
                resposta = {"ok": ok, "msg": msg}
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
