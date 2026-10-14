"""
Histórico das ações (clonar, arquivar, desarquivar, excluir) e relatório em HTML.

O histórico fica em historico.json: uma lista de registros, um por ação (nunca é apagado).
O relatório cruza o histórico com a situação atual (GitHub + disco) e é salvo em
<pasta_dados>/relatorios/relatorio_AAAA-MM-DD_HHMM.html
"""
import json
from datetime import datetime
from html import escape
from pathlib import Path

from config import CONFIG

HISTORICO = CONFIG["pasta_dados"] / "historico.json"
PASTA_RELATORIOS = CONFIG["pasta_dados"] / "relatorios"

# Ordem e aparência das seções do relatório
SECOES = [
    ("excluido", "Excluídos", "#a32d2d"),
    ("arquivado", "Arquivados", "#854f0b"),
    ("clonado", "Clonados", "#3b6d11"),
]


def carregar_historico():
    if HISTORICO.exists():
        return json.loads(HISTORICO.read_text(encoding="utf-8"))
    return []


def registrar(acao, repo, pasta=""):
    """Acrescenta uma ação ao historico.json."""
    historico = carregar_historico()
    historico.append({
        "data": datetime.now().strftime("%Y-%m-%dT%H:%M"),
        "acao": acao,
        "id": repo["id"],
        "url": repo["url"],
        "obs": repo.get("obs", ""),
        "pasta": pasta,
    })
    HISTORICO.write_text(json.dumps(historico, ensure_ascii=False, indent=2), encoding="utf-8")


def data_br(iso):
    """2026-10-14T10:44 -> 14/10/2026 10:44 (registros sem hora mostram só a data)."""
    if not iso:
        return "—"
    dia = "/".join(reversed(iso[:10].split("-")))
    return f"{dia} {iso[11:16]}" if len(iso) > 10 else dia


def ultimo_por_id(historico, acao):
    """Último registro de cada repositório para uma ação (o histórico pode ter repetidos)."""
    ultimos = {}
    for h in sorted(historico, key=lambda h: h["data"]):
        if h["acao"] == acao:
            ultimos[h["id"]] = h
    return ultimos


def situacao_atual(repos):
    """
    Monta as seções cruzando o histórico com a situação REAL de agora.
    Nada some do relatório: o que mudou depois ganha uma "nota" explicando.
    """
    historico = carregar_historico()
    por_id = {r["id"]: r for r in repos}

    excluidos = [{**h, "nota": "existe de novo no GitHub" if i in por_id else ""}
                 for i, h in ultimo_por_id(historico, "excluido").items()]

    reg_arq = ultimo_por_id(historico, "arquivado")
    reg_desarq = ultimo_por_id(historico, "desarquivado")
    arquivados = []
    for i, r in por_id.items():
        reg = reg_arq.get(i)
        if r["arquivado"]:
            arquivados.append({"data": reg["data"] if reg else "", "url": r["url"],
                               "obs": r["obs"], "pasta": "", "nota": ""})
        elif reg:   # foi arquivado e hoje não está mais
            desarq = reg_desarq.get(i)
            nota = f"desarquivado em {data_br(desarq['data'])}" if desarq else "desarquivado"
            arquivados.append({**reg, "obs": r["obs"], "nota": nota})

    clonados = [{**h, "nota": "" if Path(h["pasta"]).exists() else "pasta removida"}
                for h in ultimo_por_id(historico, "clonado").values()]

    ordenar = lambda lista: sorted(lista, key=lambda h: h["data"], reverse=True)
    return {"excluido": ordenar(excluidos), "arquivado": ordenar(arquivados), "clonado": ordenar(clonados)}


def gerar_relatorio(usuario, repos):
    """Gera o HTML do relatório e devolve o caminho do arquivo."""
    secoes = situacao_atual(repos)
    agora = datetime.now()
    contagem = " · ".join(f"{sum(1 for h in secoes[a] if not h['nota'])} {t.lower()}" for a, t, _ in SECOES)

    secoes_html = ""
    for acao, titulo, cor in SECOES:
        linhas = ""
        for h in secoes[acao]:
            nota = f' <span class="nota">{escape(h["nota"])}</span>' if h["nota"] else ""
            detalhes = f'<div class="det">{escape(h["pasta"])}</div>' if h.get("pasta") else ""
            if h.get("obs"):
                detalhes += f'<div class="det">Obs: {escape(h["obs"])}</div>'
            linhas += (f'<tr><td class="data">{data_br(h["data"])}</td><td>'
                       f'<a href="{escape(h["url"])}" target="_blank">{escape(h["url"])}</a>{nota}{detalhes}</td></tr>')
        linhas = linhas or '<tr><td colspan="2" class="det">Nenhum registro.</td></tr>'
        secoes_html += f'<h2 style="color:{cor}">{titulo} ({len(secoes[acao])})</h2><table>{linhas}</table>'

    html = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>Relatório de revisão dos repositórios</title>
<style>
  body {{ font: 14px/1.5 "Segoe UI", system-ui, sans-serif; color: #1f1f1d; max-width: 900px; margin: 32px auto; padding: 0 16px; }}
  h1 {{ font-size: 20px; margin: 0; }}
  h2 {{ font-size: 16px; margin: 24px 0 6px; }}
  .sub {{ color: #6b6a65; font-size: 13px; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td {{ padding: 4px 8px 4px 0; vertical-align: top; border-bottom: 1px solid #ecebe6; }}
  td.data {{ color: #6b6a65; white-space: nowrap; width: 130px; }}
  .det {{ color: #6b6a65; font-size: 12px; }}
  .nota {{ font-size: 11px; padding: 1px 7px; border-radius: 6px; background: #faeeda; color: #854f0b; white-space: nowrap; }}
  a {{ color: #185fa5; }}
</style></head><body>
<h1>Relatório de revisão dos repositórios</h1>
<div class="sub">{escape(usuario)} · gerado em {agora.strftime("%d/%m/%Y %H:%M")} · {contagem}</div>
{secoes_html}
</body></html>"""

    PASTA_RELATORIOS.mkdir(exist_ok=True)
    arquivo = PASTA_RELATORIOS / f"relatorio_{agora.strftime('%Y-%m-%d_%H%M')}.html"
    arquivo.write_text(html, encoding="utf-8")
    return arquivo
