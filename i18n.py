"""
Textos do servidor e do relatório em inglês (en) e português do Brasil (pt-BR).
Os textos da página ficam no próprio template.html.
"""
IDIOMAS = ("en", "pt-BR")

MSG = {
    "en": {
        # servidor
        "inicio_pasta": "Projects folder: {p}",
        "inicio_excluir": "Delete repositories: {s}",
        "ligado": "ON", "desligado": "off",
        "buscando": "Fetching repositories from GitHub...",
        "carregados": "{n} repositories from {u} loaded.",
        "pagina_em": "Page at {e}  (close this window or press Ctrl+C to stop)",
        "encerrado": "Stopped.",
        "porta_em_uso": "Port {p} is already in use. Close the other server window or change 'porta' in config.json.",
        "sem_gh": "GitHub CLI (gh) not found. Install it from https://cli.github.com and run: gh auth login",
        "sem_git": "git not found. Install it from https://git-scm.com",
        "erro_gh": "Error calling gh:\n{e}\nIf you are not logged in, run: gh auth login",
        "token_invalido": "invalid token",
        "nao_encontrado": "not found",
        "pasta_existe": "The folder {p} already exists.",
        "sem_pasta_git": "gh finished, but there is no .git folder in {p}.",
        "clonado_ok": "✔ Cloned to {p}\nLast commit: {c}",
        "repo_vazio": "empty repository, no commits",
        "desarquivado_ok": "Unarchived",
        "excluir_desligado": "delete is off (permitir_excluir in config.json)",
        "confirmacao_ausente": "deletion confirmation missing",
        "inicio_org": "Transfer to organization: {o}",
        "transferir_desligado": "transfer is off (organizacao_destino in config.json)",
        "ja_na_org": "already belongs to {o}",
        "transferido_ok": "now at {u}",
        "remote_ok": "local remote updated: {p}",
        "remote_erro": "could not update the remote in {p}: {e}",
        "remote_nenhum": "no local clone found",
        "aviso_org": "Warning: could not list the repositories of {o}: {e}",
        "aviso_time": "Warning: could not read team {t} of {o}: {e}",
        "devolvido_ok": "back at {u}",
        "devolver_so_org": "only repositories of {o} can be brought back",
        "time_ok": "team {t}: {p} ✔",
        "time_erro": "team {t}: {e}",
        "sem_time_dev": "no dev team set (time_dev in config.json)",
        "sem_tkinter": "tkinter is not installed (on Linux: sudo apt install python3-tk). Type the path in the field.",
        "titulo_pasta": "Choose the folder to clone into",
        "pagina_gerada": "{n} repositories. Page generated at: {p}",
        # relatório
        "rel_titulo": "Repository review report",
        "rel_gerado": "generated on {d}",
        "rel_excluido": "Deleted", "rel_arquivado": "Archived", "rel_transferido": "Transferred", "rel_devolvido": "Brought back", "rel_clonado": "Cloned",
        "rel_vazio": "No records.",
        "rel_obs": "Note",
        "nota_recriado": "exists again on GitHub",
        "nota_desarquivado": "unarchived",
        "nota_desarquivado_em": "unarchived on {d}",
        "nota_pasta_removida": "folder removed",
        "nota_devolvido_em": "brought back on {d}",
    },
    "pt-BR": {
        "inicio_pasta": "Pasta de projetos: {p}",
        "inicio_excluir": "Excluir repositórios: {s}",
        "ligado": "LIGADO", "desligado": "desligado",
        "buscando": "Buscando repositórios no GitHub...",
        "carregados": "{n} repositórios de {u} carregados.",
        "pagina_em": "Página em {e}  (feche esta janela ou Ctrl+C para encerrar)",
        "encerrado": "Encerrado.",
        "porta_em_uso": "A porta {p} já está em uso. Feche a outra janela do servidor ou mude 'porta' no config.json.",
        "sem_gh": "GitHub CLI (gh) não encontrado. Instale em https://cli.github.com e rode: gh auth login",
        "sem_git": "git não encontrado. Instale em https://git-scm.com",
        "erro_gh": "Erro ao chamar o gh:\n{e}\nSe não estiver logado, rode: gh auth login",
        "token_invalido": "token inválido",
        "nao_encontrado": "não encontrado",
        "pasta_existe": "A pasta {p} já existe.",
        "sem_pasta_git": "O gh terminou, mas não há pasta .git em {p}.",
        "clonado_ok": "✔ Clonado em {p}\nÚltimo commit: {c}",
        "repo_vazio": "repositório vazio, sem commits",
        "desarquivado_ok": "Desarquivado",
        "excluir_desligado": "exclusão desligada (permitir_excluir no config.json)",
        "confirmacao_ausente": "confirmação de exclusão ausente",
        "inicio_org": "Transferir para a organização: {o}",
        "transferir_desligado": "transferência desligada (organizacao_destino no config.json)",
        "ja_na_org": "já pertence a {o}",
        "transferido_ok": "agora em {u}",
        "remote_ok": "remote local atualizado: {p}",
        "remote_erro": "não foi possível atualizar o remote em {p}: {e}",
        "remote_nenhum": "nenhum clone local encontrado",
        "aviso_org": "Aviso: não foi possível listar os repositórios de {o}: {e}",
        "aviso_time": "Aviso: não foi possível ler o time {t} de {o}: {e}",
        "devolvido_ok": "de volta em {u}",
        "devolver_so_org": "só repositórios de {o} podem ser devolvidos",
        "time_ok": "time {t}: {p} ✔",
        "time_erro": "time {t}: {e}",
        "sem_time_dev": "nenhum time dev definido (time_dev no config.json)",
        "sem_tkinter": "tkinter não está instalado (no Linux: sudo apt install python3-tk). Digite o caminho no campo.",
        "titulo_pasta": "Escolha a pasta onde clonar",
        "pagina_gerada": "{n} repositórios. Página gerada em: {p}",
        "rel_titulo": "Relatório de revisão dos repositórios",
        "rel_gerado": "gerado em {d}",
        "rel_excluido": "Excluídos", "rel_arquivado": "Arquivados", "rel_transferido": "Transferidos", "rel_devolvido": "Devolvidos", "rel_clonado": "Clonados",
        "rel_vazio": "Nenhum registro.",
        "rel_obs": "Obs",
        "nota_recriado": "existe de novo no GitHub",
        "nota_desarquivado": "desarquivado",
        "nota_desarquivado_em": "desarquivado em {d}",
        "nota_pasta_removida": "pasta removida",
        "nota_devolvido_em": "devolvido em {d}",
    },
}


def idioma_valido(idioma, padrao="en"):
    return idioma if idioma in IDIOMAS else padrao


def t(idioma, chave, **valores):
    """Texto traduzido; cai para o inglês se faltar a chave."""
    texto = MSG.get(idioma, MSG["en"]).get(chave) or MSG["en"][chave]
    return texto.format(**valores)


def data_fmt(iso, idioma):
    """'2026-10-14T15:20' -> '10/14/2026 3:20 PM' (en) ou '14/10/2026 15:20' (pt-BR)."""
    if not iso:
        return "—"
    ano, mes, dia = iso[:10].split("-")
    if idioma == "pt-BR":
        texto = f"{dia}/{mes}/{ano}"
        return f"{texto} {iso[11:16]}" if len(iso) > 10 else texto
    texto = f"{mes}/{dia}/{ano}"
    if len(iso) > 10:
        h, m = int(iso[11:13]), iso[14:16]
        texto += f" {h % 12 or 12}:{m} {'PM' if h >= 12 else 'AM'}"
    return texto
