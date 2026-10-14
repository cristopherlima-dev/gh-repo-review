"""
Histórico das ações (clonar, arquivar, desarquivar, excluir) e relatório em HTML.

O histórico fica em historico.json: uma lista de registros, um por ação (nunca é apagado).
O relatório cruza o histórico com a situação atual (GitHub + disco) e é salvo em
<pasta_dados>/relatorios/relatorio_AAAA-MM-DD_HHMM.html, no idioma escolhido na página.
"""
import json
from datetime import datetime
from html import escape
from pathlib import Path

from config import CONFIG
from i18n import t, data_fmt

HISTORICO = CONFIG["pasta_dados"] / "historico.json"
PASTA_RELATORIOS = CONFIG["pasta_dados"] / "relatorios"

# Ordem e cor das seções do relatório
SECOES = [("excluido", "#a32d2d"), ("arquivado", "#854f0b"), ("clonado", "#3b6d11")]


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
    Nada some do relatório: o que mudou depois ganha uma "nota" (chave de texto + data opcional).
    """
    historico = carregar_historico()
    por_id = {r["id"]: r for r in repos}

    excluidos = [{**h, "nota": ("nota_recriado", "") if i in por_id else None}
                 for i, h in ultimo_por_id(historico, "excluido").items()]

    reg_arq = ultimo_por_id(historico, "arquivado")
    reg_desarq = ultimo_por_id(historico, "desarquivado")
    arquivados = []
    for i, r in por_id.items():
        reg = reg_arq.get(i)
        if r["arquivado"]:
            arquivados.append({"data": reg["data"] if reg else "", "url": r["url"],
                               "obs": r["obs"], "pasta": "", "nota": None})
        elif reg:   # foi arquivado e hoje não está mais
            desarq = reg_desarq.get(i)
            nota = ("nota_desarquivado_em", desarq["data"]) if desarq else ("nota_desarquivado", "")
            arquivados.append({**reg, "obs": r["obs"], "nota": nota})

    clonados = [{**h, "nota": None if Path(h["pasta"]).exists() else ("nota_pasta_removida", "")}
                for h in ultimo_por_id(historico, "clonado").values()]

    ordenar = lambda lista: sorted(lista, key=lambda h: h["data"], reverse=True)
    return {"excluido": ordenar(excluidos), "arquivado": ordenar(arquivados), "clonado": ordenar(clonados)}


def gerar_relatorio(usuario, repos, idioma="en"):
    """Gera o HTML do relatório e devolve o caminho do arquivo."""
    secoes = situacao_atual(repos)
    agora = datetime.now()
    titulo = lambda acao: t(idioma, "rel_" + acao)
    contagem = " · ".join(f"{sum(1 for h in secoes[a] if not h['nota'])} {titulo(a).lower()}" for a, _ in SECOES)

    secoes_html = ""
    for acao, cor in SECOES:
        linhas = ""
        for h in secoes[acao]:
            nota = ""
            if h["nota"]:
                chave, data = h["nota"]
                nota = f' <span class="nota">{escape(t(idioma, chave, d=data_fmt(data, idioma)))}</span>'
            detalhes = f'<div class="det">{escape(h["pasta"])}</div>' if h.get("pasta") else ""
            if h.get("obs"):
                detalhes += f'<div class="det">{t(idioma, "rel_obs")}: {escape(h["obs"])}</div>'
            linhas += (f'<tr><td class="data">{data_fmt(h["data"], idioma)}</td><td>'
                       f'<a href="{escape(h["url"])}" target="_blank">{escape(h["url"])}</a>{nota}{detalhes}</td></tr>')
        linhas = linhas or f'<tr><td colspan="2" class="det">{t(idioma, "rel_vazio")}</td></tr>'
        secoes_html += f'<h2 style="color:{cor}">{titulo(acao)} ({len(secoes[acao])})</h2><table>{linhas}</table>'

    gerado = t(idioma, "rel_gerado", d=data_fmt(agora.strftime("%Y-%m-%dT%H:%M"), idioma))
    html = f"""<!doctype html>
<html lang="{idioma}"><head><meta charset="utf-8">
<title>{t(idioma, "rel_titulo")}</title>
<style>
  body {{ font: 14px/1.5 "Segoe UI", system-ui, sans-serif; color: #1f1f1d; max-width: 900px; margin: 32px auto; padding: 0 16px; }}
  h1 {{ font-size: 20px; margin: 0; }}
  h2 {{ font-size: 16px; margin: 24px 0 6px; }}
  .sub {{ color: #6b6a65; font-size: 13px; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td {{ padding: 4px 8px 4px 0; vertical-align: top; border-bottom: 1px solid #ecebe6; }}
  td.data {{ color: #6b6a65; white-space: nowrap; width: 150px; }}
  .det {{ color: #6b6a65; font-size: 12px; }}
  .nota {{ font-size: 11px; padding: 1px 7px; border-radius: 6px; background: #faeeda; color: #854f0b; white-space: nowrap; }}
  a {{ color: #185fa5; }}
</style></head><body>
<h1>{t(idioma, "rel_titulo")}</h1>
<div class="sub">{escape(usuario)} · {gerado} · {contagem}</div>
{secoes_html}
</body></html>"""

    PASTA_RELATORIOS.mkdir(exist_ok=True)
    arquivo = PASTA_RELATORIOS / f"relatorio_{agora.strftime('%Y-%m-%d_%H%M')}.html"
    arquivo.write_text(html, encoding="utf-8")
    return arquivo
