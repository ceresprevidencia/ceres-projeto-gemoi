"""
Página "Índice ASG - Carteira Consolidada" do Painel de Controle.

render() desenha a tela inteira (exceto barra de navegação), para poder
ser chamada pelo app principal do Painel ou rodar sozinha via app.py.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from . import consolidacao as C
from . import materialidade as M
from . import parametros as P
from . import relatorio as R
from . import ui

FMT_MI = lambda v: f"R$ {R.mi(v)} mi"  # noqa: E731
FMT_BI = lambda v: f"R$ {R.bi(v)} bi"  # noqa: E731


# ---------------------------------------------------------------------------
# Estado e cache
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Consolidando a carteira...")
def _processar(conteudo: bytes) -> pd.DataFrame:
    import io
    return C.consolidar(C.ler_estoque(io.BytesIO(conteudo)))


def _estado():
    ss = st.session_state
    ss.setdefault("asg_notas", M.carregar_notas())
    ss.setdefault("asg_ver_emis", 0)
    ss.setdefault("asg_ver_fund", 0)
    ss.setdefault("asg_ver_choque", 0)
    ss.setdefault("asg_msg", None)
    return ss


def _gravar_edicoes(chave_editor: str, chave_mapa: str, chave_versao: str) -> None:
    """Callback dos editores de nota: aplica, persiste e renova o editor."""
    ss = st.session_state
    edicoes = ss.get(chave_editor, {}).get("edited_rows", {})
    mapa = ss.get(chave_mapa, [])
    for idx, mudancas in edicoes.items():
        idx = int(idx)
        if idx >= len(mapa):
            continue
        for dim, valor in mudancas.items():
            if dim in M.DIMS:
                M.definir_nota(ss["asg_notas"], mapa[idx], dim, P.NOTA_NEUTRA if valor is None else valor)
    M.salvar_notas(ss["asg_notas"])
    ss[chave_versao] += 1


def _carregar_referencia():
    ss = st.session_state
    n = M.aplicar_avaliacao_referencia(ss["asg_notas"])
    M.salvar_notas(ss["asg_notas"])
    ss["asg_ver_emis"] += 1
    ss["asg_msg"] = f"{n} emissores receberam a avaliação de referência. Os demais seguem no valor neutro (5)."


def _restaurar_neutro():
    ss = st.session_state
    ss["asg_notas"] = {}
    M.salvar_notas({})
    ss["asg_ver_emis"] += 1
    ss["asg_ver_fund"] += 1
    ss["asg_msg"] = "Todas as notas voltaram ao valor neutro (5)."


# ---------------------------------------------------------------------------
# Página
# ---------------------------------------------------------------------------
def render(mostrar_hero: bool = True) -> None:
    ss = _estado()
    notas = ss["asg_notas"]

    if mostrar_hero:
        ui.hero("Índice ASG", "Carteira Consolidada",
                "Dupla materialidade nos investimentos · Portaria Previc nº 728/2026")

    # Linha de seletores, como no painel de Rentabilidade
    c1, c2, c3 = st.columns([2.2, 1, 1], vertical_alignment="bottom")
    with c1:
        arquivo = st.file_uploader("Arquivo de Estoque (.xlsx)", type=["xlsx", "xls"],
                                   help="Planilha diária de Estoque, aba 'Posição de Ativos'.")
    with c2:
        data_base = C.data_base_do_nome(arquivo.name) if arquivo else None
        st.text_input("Data-base do Estoque", value=data_base or "-", disabled=True)
    with c3:
        excluir_soberano = st.toggle("Desconsiderar título público", value=False,
                                     help="O soberano concentra cerca de 72% da carteira e domina a leitura "
                                          "setorial. Desligue-o para enxergar a carteira de crédito e ações.")

    if arquivo is None:
        st.markdown(
            "<div class='vazio'><h3>Carregue o Estoque para começar</h3>"
            "<p>O painel consolida a carteira a partir da CERES CONSOLIDADA, abre os seis fundos exclusivos "
            "(look-through), remove o que não é exposição de investimento e calcula os dois eixos da dupla "
            "materialidade: score financeiro e índice de impacto.</p>"
            "<p>O processamento é feito nesta máquina. As notas qualitativas ficam salvas na pasta "
            "<code>dados/</code> do projeto.</p></div>", unsafe_allow_html=True)
        return

    try:
        consolidado_total = _processar(arquivo.getvalue())
    except Exception as erro:  # noqa: BLE001
        st.error(f"Não foi possível ler o arquivo: {erro}")
        return
    if consolidado_total.empty:
        st.warning("Nenhuma posição encontrada para a CERES CONSOLIDADA (9124) neste arquivo.")
        return

    consolidado = C.filtrar_soberano(consolidado_total, excluir_soberano)
    emissores = C.agregar_emissores(consolidado)
    fundos = C.agregar_fundos(consolidado)
    total = float(consolidado["valor"].sum())
    val_fundos = float(fundos["valor"].sum()) if not fundos.empty else 0.0
    cobertura = 100 * (1 - val_fundos / total) if total else 0.0
    scores = M.calcular_scores(emissores, fundos, notas)
    emis_sc = M.tabela_com_scores(emissores, notas, eh_fundo=False)
    fund_sc = M.tabela_com_scores(fundos, notas, eh_fundo=True)
    n_avaliados = sum(not M.eh_neutro(notas, e) for e in emissores["emissor"])
    n_carteiras = consolidado["carteira"].nunique()

    # Cards de indicador
    ui.kpis([
        {"l": "Patrimônio analisado", "v": FMT_BI(total),
         "s": "sem soberano" if excluir_soberano else "sem duplicidade de cotas",
         "info": "Carteira consolidada após look-through dos 6 fundos e exclusão de caixa, contas a "
                 "receber/pagar, empréstimos e futuros."},
        {"l": "Emissores mapeados", "v": f"{len(emissores)}", "s": f"{n_avaliados} com avaliação documentada",
         "info": "Emissores diretos (ações, debêntures, letras financeiras, CRI e títulos públicos)."},
        {"l": "Avaliado pela gestora", "v": FMT_MI(val_fundos),
         "s": f"{len(fundos)} fundos · {R.br(100 - cobertura)}% do total",
         "info": "Fundos sem abertura ao nível de ativo, avaliados pela nota ASG da gestora responsável."},
        {"l": "Cobertura ao nível de ativo", "v": f"{R.br(cobertura)}%", "barra": cobertura,
         "info": "Percentual do patrimônio mapeado diretamente por emissor."},
    ])

    ui.chips([(f"{n_carteiras} carteiras consolidadas", ui.VERDE),
              (f"{len(emissores)} emissores classificados", ui.VERDE_VIVO),
              (f"{len(fundos)} fundos avaliados pela gestora", ui.CINZA_VERDE)])

    aba_geral, aba_emis, aba_fund, aba_sim, aba_div = st.tabs(
        ["Visão geral", "Emissores", "Fundos pela gestora", "Simulador de eventos", "Divulgação"])

    with aba_geral:
        _aba_visao_geral(scores, emissores, emis_sc, total)
    with aba_emis:
        _aba_emissores(emis_sc, notas, n_avaliados)
    with aba_fund:
        _aba_fundos(fund_sc, val_fundos)
    with aba_sim:
        _aba_simulador(emissores, fundos, notas, total, scores)
    with aba_div:
        _aba_divulgacao(dict(
            total=total, cobertura=cobertura, avaliado_gestora=val_fundos, n_carteiras=n_carteiras,
            emissores=emissores, fundos=fundos, scores=scores, notas=notas,
            setores=emissores.groupby("setor")["valor"].sum().sort_values(ascending=False),
            emissores_scores=emis_sc, excluir_soberano=excluir_soberano, data_base=data_base,
        ), consolidado)


# ---------------------------------------------------------------------------
# Abas
# ---------------------------------------------------------------------------
def _aba_visao_geral(scores, emissores, emis_sc, total):
    ui.titulo_secao("Dupla materialidade da carteira")
    eixos = []
    for chave, nome, sub, cor in (("financeiro", "Materialidade financeira", "efeito do ASG no valor dos ativos", ui.VERDE),
                                  ("impacto", "Materialidade de impacto", "efeito da carteira no ambiente e na sociedade", ui.VERDE_CLARO)):
        termo, cls = M.nivel(scores[chave]["geral"])
        eixos.append(dict(nome=nome, sub=sub, cor=cor, scores=scores[chave], leitura=termo,
                          cor_nivel=ui.COR_NIVEL[cls]))
    ui.cards_eixos(eixos)
    ui.aviso("Os dois eixos são reportados separadamente, nunca como um indicador único (arts. 9º e 10 da "
             "Portaria). Escala de 0 a 10: abaixo de 4 exige atenção, de 4 a 7 é moderado, a partir de 7 é favorável.")

    col1, col2 = st.columns(2, gap="medium")
    with col1, st.container(border=True, key="painel_setores"):
        ui.titulo_painel("Composição por setor", f"% sobre {FMT_BI(total)} do patrimônio analisado")
        setores = emissores.groupby("setor")["valor"].sum().sort_values()
        pct = setores / total * 100
        cores = [ui.CINZA_VERDE if s == P.SOBERANO else ui.VERDE_CLARO for s in setores.index]
        fig = go.Figure(go.Bar(
            x=pct.values, y=setores.index, orientation="h", marker_color=cores, marker_line_width=0,
            text=[f"{R.br(v)}%" for v in pct.values], textposition="outside", cliponaxis=False,
            customdata=[FMT_MI(v) for v in setores.values],
            hovertemplate="<b>%{y}</b><br>%{customdata} · %{text}<extra></extra>"))
        ui.layout_plotly(fig, altura=max(300, 22 * len(setores) + 30))
        fig.update_xaxes(visible=False, range=[0, pct.max() * 1.18 if len(pct) else 1])
        st.plotly_chart(fig, **ui.ESTICAR, config=ui.PLOTLY_CONFIG)

    with col2, st.container(border=True, key="painel_matriz"):
        ui.titulo_painel("Matriz de dupla materialidade",
                         "Cada bolha é um emissor; tamanho proporcional à exposição")
        base = emis_sc[emis_sc["setor"] != P.SOBERANO].head(40)
        if base.empty:
            st.caption("Sem emissores para exibir.")
        else:
            avaliado = ~base["chave"].map(lambda c: M.eh_neutro(st.session_state["asg_notas"], c))
            tam = (base["valor"] / base["valor"].max()) ** 0.5 * 38 + 6
            fig = go.Figure()
            for flag, cor, nome in ((False, "#C7CCB5", "Neutro (5), sem avaliação"),
                                    (True, ui.VERDE, "Com avaliação documentada")):
                sub = base[avaliado == flag]
                fig.add_trace(go.Scatter(
                    x=sub["score_fin"], y=sub["score_imp"], mode="markers", name=nome,
                    marker=dict(size=tam[avaliado == flag], color=cor, opacity=.8,
                                line=dict(width=1, color="#FFFFFF")),
                    customdata=list(zip(sub["emissor"].str.strip(), sub["setor"], sub["valor"].map(FMT_MI))),
                    hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} · %{customdata[2]}"
                                  "<br>Financeiro %{x:.1f} · Impacto %{y:.1f}<extra></extra>"))
            ui.layout_plotly(fig, altura=max(300, 22 * len(emissores.groupby('setor')) + 30))
            fig.add_hline(y=5, line=dict(color=ui.LINHA, width=1, dash="dot"))
            fig.add_vline(x=5, line=dict(color=ui.LINHA, width=1, dash="dot"))
            fig.update_xaxes(title_text="Score financeiro", range=[0, 10], dtick=2, showgrid=False,
                             title_font=dict(size=11, color=ui.TINTA_SUAVE))
            fig.update_yaxes(title_text="Índice de impacto", range=[0, 10], dtick=2,
                             title_font=dict(size=11, color=ui.TINTA_SUAVE), tickfont=dict(color=ui.TINTA_SUAVE))
            fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.08, x=0, font=dict(size=11)))
            st.plotly_chart(fig, **ui.ESTICAR, config=ui.PLOTLY_CONFIG)
            n_neutros = int((~avaliado).sum())
            st.caption(f"Exibe os 40 maiores emissores, sem o soberano. {n_neutros} deles seguem no valor "
                       "neutro e ficam sobrepostos no ponto (5; 5) até receberem avaliação.")


def _aba_emissores(emis_sc, notas, n_avaliados):
    ss = st.session_state
    c1, c2, c3 = st.columns([2.3, 1.5, 1.2], vertical_alignment="bottom")
    with c1:
        busca = st.text_input("Buscar emissor", placeholder="Ex.: VALE, PETROBRAS, ITAU")
    with c2:
        setores = ["Todos os setores"] + sorted(emis_sc["setor"].unique())
        setor = st.selectbox("Setor", setores)
    with c3:
        so_neutros = st.toggle("Só não avaliados", value=False)

    b1, b2, _ = st.columns([1.4, 1.1, 2.5])
    with b1:
        st.button("Carregar avaliação de referência", type="primary", on_click=_carregar_referencia,
                  **ui.ESTICAR)
    with b2:
        with st.popover("Restaurar notas neutras", **ui.ESTICAR):
            st.caption("Todas as notas A/S/G (emissores e fundos) voltam para 5. Não há como desfazer.")
            st.button("Confirmar", on_click=_restaurar_neutro, type="primary")
    if ss.get("asg_msg"):
        ui.aviso(ss.pop("asg_msg"), ok=True)

    df = emis_sc
    if busca:
        df = df[df["emissor"].str.upper().str.contains(busca.strip().upper(), regex=False)]
    if setor != "Todos os setores":
        df = df[df["setor"] == setor]
    if so_neutros:
        df = df[df["chave"].map(lambda c: M.eh_neutro(notas, c))]
    df = df.reset_index(drop=True)

    with st.container(border=True, key="painel_emissores"):
        ui.titulo_painel(
            "Emissores: notas A/S/G e dupla materialidade",
            f"{len(df)} de {len(emis_sc)} emissores · {n_avaliados} com avaliação documentada · "
            "edite as notas nas colunas A, S e G (0 a 10); os scores se recalculam na hora")
        ss["asg_mapa_emis"] = df["chave"].tolist()
        chave = f"asg_ed_emis_{ss['asg_ver_emis']}"
        st.data_editor(
            pd.DataFrame({"Emissor": df["emissor"].str.strip(), "Setor": df["setor"],
                          "Exposição (R$ mi)": df["valor"] / 1e6,
                          "A": df["A"], "S": df["S"], "G": df["G"],
                          "Score financeiro": df["score_fin"], "Índice de impacto": df["score_imp"]}),
            key=chave, hide_index=True, **ui.ESTICAR, height=min(560, 38 + 35 * max(len(df), 1)),
            disabled=["Emissor", "Setor", "Exposição (R$ mi)", "Score financeiro", "Índice de impacto"],
            on_change=_gravar_edicoes, args=(chave, "asg_mapa_emis", "asg_ver_emis"),
            column_config=_colunas_notas(),
        )


def _colunas_notas():
    nota_col = lambda rot, ajuda: st.column_config.NumberColumn(  # noqa: E731
        rot, min_value=0.0, max_value=10.0, step=0.5, format="%.1f", width="small", help=ajuda)
    return {
        "Exposição (R$ mi)": st.column_config.NumberColumn(format="localized", width="medium"),
        "A": nota_col("A", "Nota Ambiental (0 a 10)"),
        "S": nota_col("S", "Nota Social (0 a 10)"),
        "G": nota_col("G", "Nota de Governança (0 a 10)"),
        "Score financeiro": st.column_config.ProgressColumn(min_value=0, max_value=10, format="%.1f",
                                                            help="Notas ponderadas pela matriz financeira do setor"),
        "Índice de impacto": st.column_config.ProgressColumn(min_value=0, max_value=10, format="%.1f",
                                                             help="Notas ponderadas pela matriz de impacto do setor"),
    }


def _aba_fundos(fund_sc, val_fundos):
    ss = st.session_state
    if fund_sc.empty:
        st.info("Nenhum fundo sem abertura ao nível de ativo neste recorte.")
        return
    resumo = fund_sc.groupby("tipo").agg(valor=("valor", "sum"), n=("nome", "count")).sort_values("valor", ascending=False)
    ui.kpis([{"l": tipo, "v": FMT_MI(r.valor), "s": f"{int(r.n)} fundo{'s' if r.n > 1 else ''}"}
             for tipo, r in resumo.head(4).iterrows()])
    with st.container(border=True, key="painel_fundos"):
        ui.titulo_painel("Fundos avaliados pela gestora",
                         f"{len(fund_sc)} fundos · {FMT_MI(val_fundos)} · nota A/S/G atribuída à gestora "
                         "responsável, com materialidade por tipo de fundo")
        ss["asg_mapa_fund"] = fund_sc["chave"].tolist()
        chave = f"asg_ed_fund_{ss['asg_ver_fund']}"
        st.data_editor(
            pd.DataFrame({"Fundo": fund_sc["nome"], "Tipo": fund_sc["tipo"], "Origem": fund_sc["origem"],
                          "Exposição (R$ mi)": fund_sc["valor"] / 1e6,
                          "A": fund_sc["A"], "S": fund_sc["S"], "G": fund_sc["G"],
                          "Score financeiro": fund_sc["score_fin"], "Índice de impacto": fund_sc["score_imp"]}),
            key=chave, hide_index=True, **ui.ESTICAR, height=min(560, 38 + 35 * len(fund_sc)),
            disabled=["Fundo", "Tipo", "Origem", "Exposição (R$ mi)", "Score financeiro", "Índice de impacto"],
            on_change=_gravar_edicoes, args=(chave, "asg_mapa_fund", "asg_ver_fund"),
            column_config=_colunas_notas(),
        )


def _aba_simulador(emissores, fundos, notas, total, scores):
    ss = st.session_state
    ui.aviso("Choques de preço ilustrativos por setor, no espírito da análise de cenários do TCFD. Servem para "
             "dimensionar a materialidade financeira (art. 10, I) e não substituem o stress test formal de "
             "risco de mercado.")
    c1, c2 = st.columns([1.3, 1], gap="medium")
    with c1:
        opcoes = {"": "Sem cenário de catálogo"} | {k: v["nome"] for k, v in P.CENARIOS_ASG.items()}
        cen = st.selectbox("Cenário do catálogo", list(opcoes), format_func=opcoes.get)
        if cen:
            st.caption(P.CENARIOS_ASG[cen]["descricao"])
            st.dataframe(
                pd.DataFrame({"Setor ou tipo de fundo": list(P.CENARIOS_ASG[cen]["choques"]),
                              "Choque (%)": [v * 100 for v in P.CENARIOS_ASG[cen]["choques"].values()]}),
                hide_index=True, **ui.ESTICAR,
                column_config={"Choque (%)": st.column_config.NumberColumn(format="%+.0f%%")})
    with c2:
        st.markdown("<div class='titulo-painel' style='margin-top:4px'>Choques manuais</div>"
                    "<div class='sub-painel'>Somam-se ao cenário; se o setor repetir, vale o manual.</div>",
                    unsafe_allow_html=True)
        manual = st.data_editor(
            pd.DataFrame({"Setor": pd.Series(dtype="str"), "Choque (%)": pd.Series(dtype="float")}),
            key=f"asg_choque_{ss['asg_ver_choque']}", num_rows="dynamic", hide_index=True,
            **ui.ESTICAR,
            column_config={
                "Setor": st.column_config.SelectboxColumn(options=M.categorias_simulaveis(), required=True),
                "Choque (%)": st.column_config.NumberColumn(min_value=-100.0, max_value=100.0, step=1.0,
                                                            format="%+.1f%%", required=True)})

    b1, b2, _ = st.columns([1, 1, 3])
    aplicar = b1.button("Aplicar choque", type="primary", **ui.ESTICAR)
    if b2.button("Limpar", **ui.ESTICAR):
        ss["asg_ver_choque"] += 1
        ss.pop("asg_sim", None)
        st.rerun()

    if aplicar:
        choques = dict(P.CENARIOS_ASG[cen]["choques"]) if cen else {}
        for r in manual.dropna().itertuples(index=False):
            choques[r[0]] = float(r[1]) / 100
        if not choques:
            st.warning("Escolha um cenário do catálogo ou informe ao menos um choque manual.")
        else:
            ss["asg_sim"] = M.simular_evento(emissores, fundos, notas, choques)

    res: M.ResultadoSimulacao | None = ss.get("asg_sim")
    if res is None:
        return
    pos = res.impacto_total >= 0
    antes, depois = scores["financeiro"]["geral"], res.scores_pos["financeiro"]["geral"]
    ui.titulo_secao("Resultado da simulação")
    ui.kpis([
        {"l": "Impacto financeiro", "v": f"{'+' if pos else '−'}{FMT_MI(abs(res.impacto_total))}",
         "s": "ganho" if pos else "perda", "s_cls": "pos" if pos else "neg"},
        {"l": "Impacto % do patrimônio", "v": f"{R.br(res.impacto_total / total * 100, 2)}%"},
        {"l": "Patrimônio pós-choque", "v": FMT_BI(total + res.impacto_total)},
        {"l": "Score financeiro pós-choque", "v": R.sc(depois), "s": f"antes: {R.sc(antes)}",
         "info": "Recalculado com as exposições já chocadas: setores que perdem valor perdem peso no score."},
    ])
    if res.detalhe.empty:
        st.info("Nenhum setor da carteira foi atingido pelos choques escolhidos.")
        return
    with st.container(border=True, key="painel_simulacao"):
        ui.titulo_painel("Impacto por setor afetado", "R$ milhões")
        det = res.detalhe
        fig = go.Figure(go.Bar(
            x=det["impacto"] / 1e6, y=det["categoria"], orientation="h",
            marker_color=[ui.ALERTA if v < 0 else ui.VERDE_VIVO for v in det["impacto"]],
            text=[f"{'+' if v >= 0 else '−'}{R.mi(abs(v))}" for v in det["impacto"]], textposition="outside",
            cliponaxis=False,
            customdata=list(zip(det["exposicao"].map(FMT_MI), det["choque"].map(lambda c: f"{c * 100:+.0f}%"))),
            hovertemplate="<b>%{y}</b><br>Exposição %{customdata[0]} · choque %{customdata[1]}<extra></extra>"))
        ui.layout_plotly(fig, altura=max(220, 34 * len(det) + 40))
        fig.update_yaxes(autorange="reversed")  # maior perda no topo
        lim = (det["impacto"].abs().max() / 1e6) * 1.25
        fig.update_xaxes(visible=False, range=[-lim if det["impacto"].min() < 0 else 0,
                                               lim if det["impacto"].max() > 0 else lim * 0.05])
        st.plotly_chart(fig, **ui.ESTICAR, config=ui.PLOTLY_CONFIG)


def _aba_divulgacao(dados, consolidado):
    ui.aviso("Rascunho da Divulgação de Impactos ASG (arts. 13 e 14 da Portaria), gerado com os números desta "
             "apuração. Abra o arquivo no navegador e use <b>Imprimir / salvar PDF</b>. Para incluir a "
             "fundamentação das notas, carregue antes a avaliação de referência na aba Emissores.", ok=True)
    html = R.gerar_relatorio_html(dados)
    sufixo = (dados["data_base"] or "").replace("/", "") or "sem_data"
    c1, c2, _ = st.columns([1.3, 1.3, 2])
    c1.download_button("Baixar relatório (.html)", data=html.encode("utf-8"),
                       file_name=f"Divulgacao_Impactos_ASG_{sufixo}.html", mime="text/html",
                       type="primary", **ui.ESTICAR)
    c2.download_button("Baixar base consolidada (.xlsx)",
                       data=C.exportar_excel(consolidado, dados["emissores_scores"].drop(columns="chave"),
                                             M.tabela_com_scores(dados["fundos"], dados["notas"], True).drop(columns="chave")),
                       file_name=f"Base_ASG_consolidada_{sufixo}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       **ui.ESTICAR)
    with st.expander("Pré-visualizar relatório", expanded=False):
        ui.embutir_html(html, altura=900)
