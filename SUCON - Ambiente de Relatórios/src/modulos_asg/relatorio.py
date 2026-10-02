"""
Relatório de Divulgação de Impactos ASG (HTML pronto para imprimir/PDF).

Mesma estrutura do app anterior: introdução, sumário executivo, as duas
materialidades em separado, composição setorial, principais emissores,
avaliação qualitativa pesquisada, fundos avaliados pela gestora, nota
metodológica e conclusão gerada a partir dos números apurados.
"""
from __future__ import annotations

from datetime import date
from html import escape

import pandas as pd

from . import parametros as P
from .materialidade import DIMS, NOME_DIM, eh_neutro, nivel, nota

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


def br(v: float, casas: int = 1) -> str:
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def mi(v: float) -> str:
    return br(v / 1e6, 1)


def bi(v: float) -> str:
    return br(v / 1e9, 2)


def sc(v: float | None) -> str:
    return "N/D" if v is None else br(v, 1)


def _data_extenso(d: date) -> str:
    return f"{d.day:02d} de {MESES[d.month - 1]} de {d.year}"


COR_NIVEL = {"ok": "#1E8E4A", "atencao": "#B7791F", "alerta": "#B23A2E", "neutro": "#55624A"}


def _conclusao(d: dict) -> str:
    fin, imp = d["scores"]["financeiro"], d["scores"]["impacto"]
    notas = d["notas"]
    partes = []
    tf, cf = nivel(fin["geral"])
    ti, ci = nivel(imp["geral"])
    partes.append(
        f"<p>O score financeiro consolidado da carteira ficou em <strong>{sc(fin['geral'])}</strong>, "
        f"patamar <span style='color:{COR_NIVEL[cf]};font-weight:600'>{tf}</span> quanto ao efeito dos "
        f"fatores ASG sobre o valor econômico dos investimentos. O índice de impacto consolidado ficou em "
        f"<strong>{sc(imp['geral'])}</strong>, patamar <span style='color:{COR_NIVEL[ci]};font-weight:600'>{ti}</span> "
        f"quanto ao efeito da carteira sobre o meio ambiente e a sociedade.</p>")

    if fin["geral"] is not None and imp["geral"] is not None:
        diff = fin["geral"] - imp["geral"]
        if abs(diff) >= 0.3:
            maior, menor = ("financeira", "de impacto") if diff > 0 else ("de impacto", "financeira")
            partes.append(
                f"<p>Os dois eixos divergem: a materialidade {maior} está mais favorável que a materialidade "
                f"{menor}. É exatamente por isso que a dupla materialidade pede leitura separada: um indicador "
                f"único esconderia a diferença, e a divulgação deve apresentar os dois números.</p>")
        else:
            partes.append(
                "<p>Os dois eixos estão próximos nesta apuração. É o esperado no estágio atual, em que boa parte "
                "dos emissores ainda está no valor neutro (5); a diferença entre as duas óticas tende a crescer "
                "à medida que mais emissores recebem avaliação individual.</p>")

    def pior(eixo):
        validos = [x for x in DIMS if eixo[x] is not None]
        return min(validos, key=lambda x: eixo[x]) if validos else None

    pf, pi = pior(fin), pior(imp)
    if pf and pi:
        partes.append(
            f"<p>Por dimensão, o ponto mais fraco do eixo financeiro é <strong>{NOME_DIM[pf]}</strong> "
            f"({sc(fin[pf])}) e o do eixo de impacto é <strong>{NOME_DIM[pi]}</strong> ({sc(imp[pi])}). "
            f"São os pontos de partida naturais para engajamento com emissores e gestoras.</p>")

    emissores, fundos = d["emissores"], d["fundos"]
    neutros = [e for e in emissores["emissor"] if eh_neutro(notas, e)][:3]
    recs = []
    if neutros:
        recs.append("Priorizar a avaliação qualitativa dos emissores de maior exposição ainda no valor neutro, "
                    f"a começar por {', '.join(escape(n.strip()) for n in neutros)}.")
    if not fundos.empty:
        recs.append("Buscar documentação ASG formal junto às gestoras dos fundos de maior exposição avaliados só "
                    f"pelo tipo de fundo, a começar por {escape(fundos.iloc[0]['nome'])}.")
    recs.append("Formalizar na Política de Investimentos o processo de julgamento de materialidade demonstrado "
                "neste relatório, com periodicidade de revisão e instância de aprovação.")
    recs.append("Reportar os dois eixos de materialidade separadamente na Divulgação de Impactos ASG, sem "
                "resumir a avaliação num indicador combinado.")
    if d["cobertura"] < 70:
        recs.append(f"Ampliar a cobertura ao nível de ativo (hoje em {br(d['cobertura'])}%), priorizando os "
                    "fundos de maior exposição.")
    partes.append("<h3>O que a Ceres pode fazer para melhorar</h3><ul>"
                  + "".join(f"<li>{r}</li>" for r in recs) + "</ul>")
    return "".join(partes)


CSS = """
:root { --navy:#0B2F13; --verde:#016837; --ink:#16210F; --soft:#55624A; --line:#DDE3CE; --alerta:#B23A2E; }
* { box-sizing:border-box; }
html,body { background:#fff; margin:0; padding:0; }
body { font-family:'Figtree',-apple-system,'Segoe UI',sans-serif; color:var(--ink); }
.toolbar { padding:14px 24px; text-align:right; border-bottom:1px solid var(--line); }
.toolbar button { font-family:inherit; font-weight:700; font-size:13px; border-radius:100px; padding:9px 18px;
  cursor:pointer; border:none; background:var(--verde); color:#fff; }
.paper { max-width:800px; margin:0 auto; padding:40px 50px 60px; }
.eyebrow { font-size:11px; letter-spacing:.1em; text-transform:uppercase; color:var(--verde); font-weight:700; margin-bottom:8px; }
h1 { font-family:'Source Serif 4',Georgia,serif; font-size:23px; margin:0 0 4px; color:var(--navy); }
.meta { font-size:12px; color:var(--soft); margin-bottom:28px; border-bottom:1px solid var(--line); padding-bottom:16px; }
h2 { font-size:15px; color:var(--navy); border-bottom:2px solid var(--navy); padding-bottom:6px; margin:30px 0 12px; break-after:avoid; }
h3 { font-size:12.5px; color:var(--verde); margin:18px 0 8px; text-transform:uppercase; letter-spacing:.04em; }
p, li { font-size:13px; line-height:1.65; }
p { margin:0 0 10px; }
table { width:100%; border-collapse:collapse; font-size:12px; margin:10px 0 6px; }
thead { display:table-header-group; }
th { text-align:left; font-size:10.5px; text-transform:uppercase; color:var(--soft); border-bottom:2px solid var(--navy); padding:6px 8px; }
td { padding:6px 8px; border-bottom:1px solid var(--line); }
tr, td, th { break-inside:avoid; }
td.num, th.num { text-align:right; font-variant-numeric:tabular-nums; }
.kpis { display:flex; gap:12px; margin:10px 0 6px; break-inside:avoid; }
.kpi { flex:1; border:1px solid var(--line); border-left:4px solid var(--verde); border-radius:6px; padding:12px 14px; }
.kpi .l { font-size:10px; text-transform:uppercase; color:var(--soft); font-weight:700; margin-bottom:4px; }
.kpi .v { font-size:17px; font-weight:700; color:var(--navy); }
.nota { font-size:11.5px; color:var(--soft); background:#FAFBEB; border-left:3px solid var(--alerta); padding:10px 14px; margin:12px 0; break-inside:avoid; }
.foot { margin-top:40px; padding-top:16px; border-top:1px solid var(--line); font-size:11px; color:var(--soft); }
@media print { .toolbar { display:none !important; } .paper { padding:0; max-width:none; } }
@page { margin:16mm 14mm; }
"""


def gerar_relatorio_html(d: dict) -> str:
    """d: total, cobertura, avaliado_gestora, n_carteiras, emissores, fundos,
    scores, setores (Series), notas, excluir_soberano, data_base."""
    emissores: pd.DataFrame = d["emissores"]
    fundos: pd.DataFrame = d["fundos"]
    notas = d["notas"]
    total = d["total"]

    def linha_eixo(rotulo, eixo):
        return (f"<tr><td>{rotulo}</td>" + "".join(f"<td class='num'>{sc(eixo[x])}</td>" for x in DIMS)
                + f"<td class='num' style='font-weight:700'>{sc(eixo['geral'])}</td></tr>")

    cab_eixo = ("<thead><tr><th>Eixo</th><th class='num'>Ambiental</th><th class='num'>Social</th>"
                "<th class='num'>Governança</th><th class='num'>Geral</th></tr></thead>")

    setores_html = "".join(
        f"<tr><td>{escape(s)}</td><td class='num'>R$ {mi(v)} mi</td><td class='num'>{br(v / total * 100)}%</td></tr>"
        for s, v in d["setores"].head(8).items())

    top = d["emissores_scores"].head(10)
    top_html = "".join(
        f"<tr><td>{escape(r.emissor)}</td><td>{escape(r.setor)}</td><td class='num'>R$ {mi(r.valor)} mi</td>"
        f"<td class='num'>{sc(r.score_fin)}</td><td class='num'>{sc(r.score_imp)}</td></tr>"
        for r in top.itertuples())

    presentes = set(emissores["emissor"])
    avaliados = [(e, av) for e, av in P.AVALIACAO_REFERENCIA.items()
                 if e in presentes and not eh_neutro(notas, e)]
    valor_por_emissor = dict(zip(emissores["emissor"], emissores["valor"]))
    avaliados.sort(key=lambda x: -valor_por_emissor.get(x[0], 0))
    if avaliados:
        aval_html = ("<table><thead><tr><th>Emissor</th><th class='num'>A</th><th class='num'>S</th>"
                     "<th class='num'>G</th><th>Fundamentação</th></tr></thead><tbody>"
                     + "".join(
                         f"<tr><td>{escape(e)}</td>"
                         + "".join(f"<td class='num'>{br(nota(notas, e, x))}</td>" for x in DIMS)
                         + f"<td style='font-size:11px'>{escape(av['nota'])}</td></tr>"
                         for e, av in avaliados)
                     + "</tbody></table>")
    else:
        aval_html = ("<div class='nota'>Nenhuma avaliação de referência carregada nesta apuração. Use o botão "
                     "\"Carregar avaliação de referência\" no painel antes de emitir o relatório.</div>")

    fundos_html = "".join(
        f"<tr><td>{escape(r.nome)}</td><td>{escape(r.tipo)}</td><td class='num'>R$ {mi(r.valor)} mi</td></tr>"
        for r in fundos.head(15).itertuples())
    extra_fundos = (f"<p style='font-size:11.5px;color:#55624A'>+ {len(fundos) - 15} fundo(s) não listado(s) "
                    "por espaço.</p>") if len(fundos) > 15 else ""

    base_txt = "carteira consolidada" + (" (excluindo título público federal)" if d["excluir_soberano"] else "")
    data_base = f" · Data-base do Estoque: {d['data_base']}" if d.get("data_base") else ""

    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">
<title>Divulgação de Impactos ASG - Ceres</title>
<link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&family=Source+Serif+4:wght@600;700&display=swap" rel="stylesheet">
<style>{CSS}</style></head>
<body>
<div class="toolbar"><button onclick="window.print()">Imprimir / salvar PDF</button></div>
<div class="paper">
<div class="eyebrow">Ceres Previdência · SURIC</div>
<h1>Divulgação de Impactos ASG na Carteira de Investimentos</h1>
<div class="meta">Base: {base_txt}{data_base} · Emitido em {_data_extenso(date.today())}<br>
Estrutura alinhada à Portaria Previc nº 728/2026 (arts. 13 e 14) e à dupla materialidade da Resolução Previc nº 26/2025</div>

<h2>Introdução</h2>
<p>A Portaria Previc nº 728, de 16 de setembro de 2026, estabelece os parâmetros para a análise de relevância e de materialidade dos fatores ambientais, sociais e de governança nos investimentos das EFPC e para a Divulgação de Impactos ASG. A análise deve considerar duas óticas independentes: a materialidade financeira, que mede o efeito desses fatores sobre o valor dos ativos e a capacidade do plano de honrar suas obrigações, e a materialidade de impacto, que mede o efeito dos investimentos sobre o meio ambiente e a sociedade.</p>
<p>Este relatório é gerado pelo Índice de Materialidade e Impacto ASG, desenvolvido pela Supervisão de Riscos e Controles Internos (SURIC). O modelo consolida a carteira, classifica cada emissor e cada fundo por setor econômico ou tipo de fundo, aplica duas matrizes de materialidade independentes e calcula um score ponderado pela exposição em cada eixo. Entram tanto os ativos mapeados ao nível de emissor quanto os fundos avaliados pela ótica da gestora responsável.</p>

<h2>1. Sumário executivo</h2>
<div class="kpis">
<div class="kpi"><div class="l">Patrimônio analisado</div><div class="v">R$ {bi(total)} bi</div></div>
<div class="kpi"><div class="l">Cobertura ao nível de ativo</div><div class="v">{br(d['cobertura'])}%</div></div>
<div class="kpi"><div class="l">Emissores mapeados</div><div class="v">{len(emissores)}</div></div>
<div class="kpi"><div class="l">Fundos pela gestora</div><div class="v">{len(fundos)}</div></div>
</div>
<p>A carteira consolidada reúne {d['n_carteiras']} carteiras (planos e fundos exclusivos), com {len(emissores)} emissores mapeados diretamente ao nível de ativo. Do patrimônio analisado, R$ {mi(d['avaliado_gestora'])} milhões estão em fundos avaliados pela ótica da gestora, sem abertura ao nível de ativo final.</p>

<h2>2. Materialidade financeira</h2>
<p>Quanto os fatores ASG afetam o valor econômico dos investimentos (risco de crédito, de mercado e reputacional). Escala de 0 a 10, ponderada pela exposição e pela materialidade setorial de cada fator.</p>
<table>{cab_eixo}<tbody>{linha_eixo('Score financeiro', d['scores']['financeiro'])}</tbody></table>

<h2>3. Materialidade de impacto</h2>
<p>Quanto os investimentos afetam o meio ambiente e a sociedade, independentemente do efeito no retorno. Mesma nota qualitativa de entrada, ponderada por uma matriz de materialidade distinta.</p>
<table>{cab_eixo}<tbody>{linha_eixo('Índice de impacto', d['scores']['impacto'])}</tbody></table>

<h2>4. Composição setorial</h2>
<table><thead><tr><th>Setor</th><th class="num">Exposição</th><th class="num">% do patrimônio</th></tr></thead><tbody>{setores_html}</tbody></table>

<h2>5. Principais emissores</h2>
<table><thead><tr><th>Emissor</th><th>Setor</th><th class="num">Exposição</th><th class="num">Score financeiro</th><th class="num">Índice de impacto</th></tr></thead><tbody>{top_html}</tbody></table>

<h2>6. Avaliação qualitativa pesquisada</h2>
<p>Notas A/S/G documentadas para os emissores de maior exposição e relevância reputacional, com fonte pública declarada. Os demais emissores permanecem no valor neutro (5) até avaliação individual.</p>
{aval_html}

<h2>7. Fundos avaliados pela gestora</h2>
<p>Posições sem abertura ao nível de ativo final, avaliadas pela nota ASG da gestora responsável.</p>
<table><thead><tr><th>Fundo</th><th>Tipo</th><th class="num">Exposição</th></tr></thead><tbody>{fundos_html}</tbody></table>
{extra_fundos}

<h2>8. Nota metodológica e limitações</h2>
<p>Materialidade atribuída por setor econômico do emissor, em duas matrizes independentes (financeira e de impacto), seguindo a dupla materialidade prevista na Portaria Previc nº 728/2026 e no referencial europeu ESRS. Fundos sem abertura ao nível de ativo recebem materialidade por tipo de fundo (crédito privado, ações, renda fixa, imobiliário, multimercado).</p>
<div class="nota">As notas A/S/G combinam avaliação pesquisada (seção 6) para os emissores de maior relevância e valor neutro (5) para os demais. Os pesos das matrizes são uma calibração inicial. Os scores devem ser lidos considerando esse grau de cobertura, e não como avaliação ASG completa e definitiva da carteira (art. 13, V).</div>

<h2>9. Conclusão</h2>
{_conclusao(d)}

<div class="foot">Relatório gerado automaticamente pelo Índice de Materialidade e Impacto ASG · SURIC, Ceres Previdência</div>
</div></body></html>"""
