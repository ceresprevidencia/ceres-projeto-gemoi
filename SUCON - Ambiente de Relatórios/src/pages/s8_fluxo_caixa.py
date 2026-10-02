"""
Risco de Liquidez - Fluxo de Caixa

Confronta os recebimentos programados da carteira (query de recebimentos) com a
necessidade líquida previdencial de cada plano (fluxo atuarial fixo em
utils/fluxo_previdenciario.py). Toda a regra de cálculo está em utils/fluxo_caixa.py.
"""

from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.fluxo_caixa import (
    BASES,
    CATEGORIA_PRIVADO,
    CATEGORIA_PUBLICO,
    PREMISSAS,
    calcular_painel,
    planos_com_fluxo,
)
from utils.gerar_pdf_fluxo_caixa import gerar_pdf_fluxo_caixa
from utils.helpers import (
    card_geral,
    de_para_produto,
    fmt_br,
    formatar_numero,
    nome_plano,
    renderizar_tabela_estilizada,
    titulo_section,
)
from utils.queries.recebimentos import buscar_dados_recebimentos

try:  # query futura de fundos caixa D0: o painel ativa a opção quando o arquivo existir
    from utils.queries.fundos_caixa import buscar_dados_fundos_caixa
except ImportError:
    buscar_dados_fundos_caixa = None


# ── CONSTANTES VISUAIS ───────────────────────────────────────────────────────

CONSOLIDADO = "[CONSOLIDADO]"
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

COR_PUBLICO = "#016837"
COR_PRIVADO = "#A8EC7D"
COR_CAIXA = "#E8D9A8"
COR_NECESSIDADE = "#D64550"
COR_ACUMULADO = "#5a5a5a"
COR_COBERTURA = "#6D597A"
COR_TEXTO = "#333333"
COR_TITULO = "#0B2F13"

FAIXAS_COBERTURA = [  # (limite inferior, cor, rótulo)
    (1.0, "#2DC25F", "≥ 100%"),
    (0.5, "#E8A33D", "50% a 100%"),
    (0.0, "#E35D5D", "< 50%"),
]

LAYOUT_BASE = dict(
    font=dict(family="Figtree", size=13, color=COR_TEXTO),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    separators=",.",
    hoverlabel=dict(bgcolor="#FBFCEC", bordercolor=COR_TITULO, font=dict(family="Figtree", size=13, color=COR_TITULO)),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=12)),
    margin=dict(l=10, r=10, t=30, b=10),
)


def nome_exibicao(tesouraria: str) -> str:
    if tesouraria == CONSOLIDADO:
        return "Consolidado"
    if tesouraria == "EROS FIM CREDITO PRIVADO":
        return "EROS FIM CP"
    return nome_plano(tesouraria)


def brl_curto(valor) -> str:
    return "—" if pd.isna(valor) else formatar_numero(valor, prefixo="R$ ")


def brl_extenso(valor) -> str:
    return "—" if pd.isna(valor) else f"R$ {fmt_br(valor)}"


def pct(valor, casas: int = 0) -> str:
    return "—" if pd.isna(valor) else f"{valor * 100:,.{casas}f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def anos_fmt(valor) -> str:
    return "—" if pd.isna(valor) else f"{valor:.1f}".replace(".", ",") + " anos"


def liquidez_fmt(valor) -> str:
    return "Sem necessidade" if not valor else brl_curto(valor)


def duration_fmt(ativo, passivo) -> str:
    curto = lambda v: "—" if pd.isna(v) else f"{v:.1f}".replace(".", ",")  # noqa: E731
    return f"{curto(ativo)} | {curto(passivo)}"


# ── DADOS ────────────────────────────────────────────────────────────────────

@st.cache_data(ttl="1h", show_spinner=False)
def carregar_recebimentos() -> pd.DataFrame:
    df = buscar_dados_recebimentos()
    df["DATA_COTACAO"] = pd.to_datetime(df["DATA_COTACAO"]).dt.normalize()
    return df


@st.cache_data(ttl="1h", show_spinner=False)
def carregar_caixa(data_base: date) -> dict[str, float]:
    """Fundos caixa D0 por tesouraria na data-base (colunas: TESOURARIA, DATA_COTACAO, POSICAO)."""
    if buscar_dados_fundos_caixa is None:
        return {}
    df = buscar_dados_fundos_caixa()
    df.columns = df.columns.str.upper()
    df = df[pd.to_datetime(df["DATA_COTACAO"]).dt.date == data_base]
    return df.groupby("TESOURARIA")["POSICAO"].sum().to_dict()


@st.cache_data(ttl="1h", show_spinner="Calculando fluxo de caixa...")
def calcular(data_base, plano, ano_fim, base, treze, so_com_fluxo, contrib_ativos, ipca, com_caixa) -> dict:
    return calcular_painel(
        carregar_recebimentos(), data_base, plano, ano_fim,
        base=base, treze_parcelas=treze, consolidado_so_com_fluxo=so_com_fluxo,
        deduzir_contrib_ativos=contrib_ativos, ipca_aa=ipca,
        caixa_d0=carregar_caixa(data_base) if com_caixa else None,
        de_para_produto=de_para_produto,
    )


@st.cache_data(ttl="1h", show_spinner=False)
def gerar_pdf(*params) -> bytes:
    return gerar_pdf_fluxo_caixa(calcular(*params), nome_exibicao=nome_exibicao)


df_receb = carregar_recebimentos()
datas_disponiveis = sorted(df_receb["DATA_COTACAO"].dt.date.unique())

if "fc-data-base" not in st.session_state:
    st.session_state["fc-data-base"] = datas_disponiveis[-1]


# ── ESTILO DA PÁGINA ─────────────────────────────────────────────────────────

st.html("""
<style>
    .block-container { padding-top: 3.8rem; padding-left: 0rem; padding-right: 0rem; }
    .st-key-fc-cabecalho { background-color: #0B2F13; padding: 30px 20px; width: 100%; box-sizing: border-box; }
    .st-key-fc-conteudo { padding-left: 3rem; padding-right: 3rem; }
    .fc-aviso { background: rgba(232,163,61,.12); border-left: 4px solid #E8A33D; padding: 10px 14px;
                font-family: 'Figtree', sans-serif; font-size: 14px; color: #5a4200; margin: 6px 0 4px; }
    .fc-nota { font-family: 'Figtree', sans-serif; font-size: 13px; color: #5a5a5a; line-height: 1.55; }
    @media print {
        header, [data-testid="stToolbar"], .stDownloadButton, [data-testid="stExpander"] { display: none !important; }
        .js-plotly-plot { break-inside: avoid; }
    }
</style>
""")

with st.container(key="fc-cabecalho"):
    st.html("""
        <p style="text-align:center; color:#FAFBEB; margin:0; font-size:clamp(20px,3vw,29px); font-weight:400;">
            Risco de Liquidez -
            <span style='color:#A8EC7D; font-family:"Source Serif 4",serif; font-style:italic; font-weight:600;'>Fluxo de Caixa</span>
        </p>
    """)

with st.container(horizontal_alignment="center", gap=None, key="fc-conteudo"):
    with st.container(width=1200):

        # ── DESCRIÇÃO + DATA-BASE ────────────────────────────────────────────
        col_txt, _, col_data = st.columns([1, 0.1, 0.5])
        with col_txt:
            st.markdown(
                """
                <div style="padding-left:20px; text-align:justify; color:#5a5a5a; font-size:16px;">
                    Este painel confronta os recebimentos programados da carteira de renda fixa
                    (cupons e vencimentos de títulos públicos e privados) com a necessidade líquida
                    de caixa previdencial de cada plano — pagamentos de benefícios menos contribuições
                    de assistidos, conforme a avaliação atuarial.
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_data:
            st.date_input(
                "Data-base dos recebimentos",
                format="DD/MM/YYYY",
                min_value=datas_disponiveis[0],
                max_value=datas_disponiveis[-1],
                key="fc-data-base",
                help=f"Datas disponíveis: {datas_disponiveis[0]:%d/%m/%Y} a {datas_disponiveis[-1]:%d/%m/%Y}.",
            )

        data_base = st.session_state["fc-data-base"]
        if data_base not in datas_disponiveis:
            anterior = next((d for d in reversed(datas_disponiveis) if d < data_base), None)
            posterior = next((d for d in datas_disponiveis if d > data_base), None)
            msg = f"**Nenhum recebimento disponível para {data_base:%d/%m/%Y}.**"
            if anterior:
                msg += f"\n\nData anterior mais próxima: **{anterior:%d/%m/%Y}**"
            if posterior:
                msg += f"\n\nData posterior mais próxima: **{posterior:%d/%m/%Y}**"
            st.warning(msg)
            st.stop()

        receb_data = df_receb[df_receb["DATA_COTACAO"].dt.date == data_base]
        ano_max = int(pd.to_datetime(receb_data["DATA_PAGAMENTO"]).dt.year.max())
        ano_max = max(ano_max, data_base.year + 1)

        tesourarias = sorted(set(receb_data["TESOURARIA"]) | planos_com_fluxo(), key=nome_exibicao)
        opcoes_plano = [CONSOLIDADO] + tesourarias

        st.space("small")

        # ── FILTROS ──────────────────────────────────────────────────────────
        f1, f2, f3, f4, f5 = st.columns([1.3, 1.6, 0.9, 0.9, 1.0], vertical_alignment="bottom")
        with f1:
            plano = st.selectbox("Plano", opcoes_plano, format_func=nome_exibicao, key="fc-plano")
        with f2:
            ano_fim = st.select_slider(
                "Horizonte de análise (até)",
                options=list(range(data_base.year, ano_max + 1)),
                value=ano_max,
                key="fc-ano-fim",
                help="Último ano considerado nos indicadores de horizonte, no gráfico anual e no mapa de cobertura.",
            )
        with f3:
            visao = st.segmented_control("Visão", ["Mensal", "Anual"], default="Mensal", key="fc-visao") or "Mensal"
        with f4:
            base = st.segmented_control(
                "Base de comparação", list(BASES), format_func=lambda b: "Fluxo nominal" if b == "nominal" else "Valor presente",
                default="nominal", key="fc-base",
                help="Fluxo nominal: recebimento projetado × passivo corrigido pelo IPCA (o que efetivamente entra e sai do caixa). "
                     "Valor presente: os dois lados descontados pela mesma curva, implícita nos títulos públicos.",
            ) or "nominal"
        with f5:
            parcelas = st.segmented_control(
                "Distribuição anual", ["÷ 12", "13 parcelas"], default="÷ 12", key="fc-parcelas",
                help="13 parcelas: dezembro recebe o dobro, representando o abono anual (13º benefício).",
            ) or "÷ 12"

        with st.expander("Premissas e opções"):
            p1, p2, p3 = st.columns(3)
            with p1:
                ipca = st.number_input(
                    "IPCA aplicado ao passivo (% a.a.)", min_value=0.0, max_value=20.0, step=0.25,
                    value=PREMISSAS["ipca_aa"] * 100, key="fc-ipca",
                    help=f"Corrige o fluxo atuarial de {PREMISSAS['data_referencia_passivo']:%d/%m/%Y} para valores nominais. "
                         "Use 0 se a planilha atuarial já estiver em valores nominais.",
                ) / 100
            with p2:
                contrib_ativos = st.toggle(
                    "Deduzir contribuições de ativos", value=False, key="fc-ativos",
                    help="Abate do passivo as contribuições de participantes ativos e patrocinadora "
                         "(linha 'Recebimentos de Ativos' da avaliação atuarial).",
                )
                so_com_fluxo = True
                if plano == CONSOLIDADO:
                    so_com_fluxo = st.toggle(
                        "Consolidar só planos com fluxo previdencial", value=True, key="fc-so-fluxo",
                        help="Desligado, soma os recebimentos de todos os planos, inclusive os sem fluxo atuarial, "
                             "o que superestima a cobertura. EROS FIM fica sempre de fora.",
                    )
            with p3:
                com_caixa = st.toggle(
                    "Somar fundos caixa D0", value=False, key="fc-caixa",
                    disabled=buscar_dados_fundos_caixa is None,
                    help="Soma a posição em fundos de liquidez D0 como recurso disponível na data-base."
                         + ("" if buscar_dados_fundos_caixa else " Disponível quando a query utils/queries/fundos_caixa.py for criada."),
                )

        treze = parcelas == "13 parcelas"
        params = (data_base, plano, ano_fim, base, treze, so_com_fluxo, contrib_ativos, ipca, com_caixa)
        res = calcular(*params)
        k, mensal, anual_df = res["kpis"], res["mensal"], res["anual"]

        _, col_pdf = st.columns([0.8, 0.2])
        with col_pdf:
            st.download_button(
                "Baixar relatório em PDF",
                data=gerar_pdf(*params),
                file_name=f"fluxo_caixa_{nome_exibicao(plano).replace(' ', '_')}_{data_base:%Y%m%d}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )

        if not k["tem_passivo"]:
            st.html(
                f'<div class="fc-aviso"><b>{nome_exibicao(plano)}</b> não tem fluxo previdencial na avaliação '
                "atuarial carregada. O painel exibe apenas os recebimentos; indicadores de cobertura ficam em branco.</div>"
            )

        # ── INDICADORES: PRÓXIMOS 12 MESES ──────────────────────────────────
        sem = (lambda v: v) if k["tem_passivo"] else (lambda v: "—")  # noqa: E731
        rotulo_rec = "Recebimentos + caixa" if res["com_caixa"] else "Recebimentos"
        titulo_section(
            "Próximos 12 meses",
            help=f"De {data_base:%d/%m/%Y} até o fim do 11º mês seguinte. O mês da data-base entra pro rata.",
        )
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            card_geral(rotulo_rec, brl_curto(k["recursos_12m"]), valor_extenso=brl_extenso(k["recursos_12m"]),
                       help="Cupons e vencimentos programados nos próximos 12 meses"
                            + (f", mais {brl_curto(k['caixa'])} em fundos caixa D0." if res["com_caixa"] else "."))
        with c2:
            card_geral("Necessidade líquida", sem(brl_curto(k["nec_12m"])),
                       valor_extenso=brl_extenso(k["nec_12m"]) if k["tem_passivo"] else None,
                       help="Benefícios − contribuições de assistidos"
                            + (" − contribuições de ativos." if res["deduzir_contrib_ativos"] else "."))
        with c3:
            card_geral("Cobertura", pct(k["cobertura_12m"]),
                       help="Recursos ÷ necessidade líquida em 12 meses.")
        with c4:
            card_geral("Saldo líquido", sem(brl_curto(k["saldo_12m"])),
                       valor_extenso=brl_extenso(k["saldo_12m"]) if k["tem_passivo"] else None,
                       help="Recursos − necessidade líquida em 12 meses.")
        with c5:
            card_geral("Necessidade de liquidez 12m", sem(liquidez_fmt(k["liquidez_12m"])),
                       valor_extenso=(f"{brl_extenso(k['liquidez_12m'])} em {k['liquidez_12m_mes'].strftime('%m/%Y')}"
                                      if k["liquidez_12m_mes"] is not None else None),
                       help="Maior déficit acumulado nos 12 meses: quanto de outros recursos (caixa, ativos líquidos, "
                            "contribuições) precisa estar disponível no pior momento do período.")

        # ── INDICADORES: LIQUIDEZ E PRAZOS ──────────────────────────────────
        titulo_section("Liquidez e prazos", help="Janelas de 24 meses e 5 anos a partir da data-base; duration pela curva implícita.")
        h1, h2, h3, h4, h5 = st.columns(5)
        with h1:
            card_geral("Necessidade de liquidez 24m", sem(liquidez_fmt(k["liquidez_24m"])),
                       valor_extenso=(f"{brl_extenso(k['liquidez_24m'])} em {k['liquidez_24m_mes'].strftime('%m/%Y')}"
                                      if k["liquidez_24m_mes"] is not None else None),
                       help="Maior déficit acumulado nos 24 meses.")
        with h2:
            card_geral("Cobertura em 5 anos", pct(k["cobertura_5a"]),
                       help="Recursos ÷ necessidade líquida nos 60 meses a partir da data-base.")
        with h3:
            card_geral("1º ano em déficit", sem(str(k["primeiro_ano_deficit"] or "Nenhum")),
                       help="Primeiro ano completo em que os recursos ficam abaixo da necessidade líquida.")
        with h4:
            card_geral("Duration ativo | passivo", duration_fmt(k["duration_ativo"], k["duration_passivo"]),
                       help="Em anos. Duration de Macaulay dos recebimentos e da necessidade líquida, ambos descontados "
                            "pela mesma curva nominal implícita nos títulos públicos.")
        with h5:
            card_geral(f"Passivo após {k['ultimo_ano_receb']}", sem(pct(k["nec_pos_receb_pct"], 1)),
                       valor_extenso=brl_extenso(k["nec_pos_receb"]) if k["tem_passivo"] else None,
                       help="Parcela da necessidade líquida total (na base escolhida) posterior ao último recebimento "
                            "programado — sem ativo casado hoje.")

        st.space("small")

        # ── GRÁFICO PRINCIPAL ────────────────────────────────────────────────
        if visao == "Mensal":
            titulo_section("Recebimentos × necessidade líquida — mensal",
                           help="Barras: recursos por origem. Linha tracejada: necessidade líquida do mês. "
                                "Linha cinza (eixo à direita): saldo acumulado desde a data-base.")
            anos_janela = sorted(mensal["ANO"].unique())
            janela = st.select_slider(
                "Janela do gráfico", options=anos_janela,
                value=(anos_janela[0], anos_janela[min(4, len(anos_janela) - 1)]),
                key="fc-janela", label_visibility="collapsed",
            )
            dados = mensal[(mensal["ANO"] >= janela[0]) & (mensal["ANO"] <= janela[1])]
            eixo_x = [f"{MESES[m - 1]}/{str(a)[2:]}" for a, m in zip(dados["ANO"], dados["MES"])]
        else:
            titulo_section("Recebimentos × necessidade líquida — anual",
                           help="Barras: recebimentos anuais. Linha tracejada: necessidade líquida anual. "
                                "Linha roxa (eixo à direita): cobertura. O ano da data-base considera só o período restante.")
            dados = anual_df
            eixo_x = [f"{a}*" if a == data_base.year else str(a) for a in dados["ANO"]]

        with st.container(border=True):
            fig = go.Figure()
            hover_valor = "%{x}<br>%{fullData.name}: R$ %{y:,.2f}<extra></extra>"
            fig.add_bar(x=eixo_x, y=dados["PUBLICOS"], name=CATEGORIA_PUBLICO, marker_color=COR_PUBLICO, hovertemplate=hover_valor)
            fig.add_bar(x=eixo_x, y=dados["PRIVADOS"], name=CATEGORIA_PRIVADO, marker_color=COR_PRIVADO, hovertemplate=hover_valor)
            if res["com_caixa"]:
                fig.add_bar(x=eixo_x, y=dados["CAIXA"], name="Fundos caixa D0", marker_color=COR_CAIXA, hovertemplate=hover_valor)
            if k["tem_passivo"]:
                fig.add_scatter(x=eixo_x, y=dados["NECESSIDADE"], name="Necessidade líquida", mode="lines",
                                line=dict(color=COR_NECESSIDADE, width=2.4, dash="dash"), hovertemplate=hover_valor)
                if visao == "Mensal":
                    fig.add_scatter(x=eixo_x, y=dados["SALDO_ACUM"], name="Saldo acumulado", mode="lines", yaxis="y2",
                                    line=dict(color=COR_ACUMULADO, width=1.6), hovertemplate=hover_valor)
                    eixo2 = dict(title="Saldo acumulado", tickprefix="R$ ", tickformat="~s")
                else:
                    fig.add_scatter(x=eixo_x, y=dados["COBERTURA"], name="Cobertura", mode="lines+markers", yaxis="y2",
                                    line=dict(color=COR_COBERTURA, width=1.8), marker=dict(size=5),
                                    hovertemplate="%{x}<br>Cobertura: %{y:.0%}<extra></extra>")
                    eixo2 = dict(title="Cobertura", tickformat=".0%", rangemode="tozero")
                    if k["primeiro_ano_deficit"] in set(dados["ANO"]):
                        pos = eixo_x[list(dados["ANO"]).index(k["primeiro_ano_deficit"])]
                        fig.add_vline(x=pos, line=dict(color=COR_NECESSIDADE, width=1, dash="dot"))
                        fig.add_annotation(x=pos, y=1, yref="paper", text="1º déficit", showarrow=False,
                                           font=dict(color=COR_NECESSIDADE, size=11), xanchor="left", yanchor="top")
                fig.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False, zeroline=False, **eixo2))
            fig.update_layout(
                **LAYOUT_BASE, barmode="stack", height=420, bargap=0.25,
                yaxis=dict(tickprefix="R$ ", tickformat="~s", gridcolor="rgba(11,47,19,0.08)", zeroline=False),
                xaxis=dict(showgrid=False, tickangle=-45 if len(eixo_x) > 24 else 0, type="category"),
            )
            st.plotly_chart(fig, config={"displayModeBar": False}, width="stretch", key="fc-grafico-principal")

        # ── MAPA DE COBERTURA ────────────────────────────────────────────────
        if k["tem_passivo"]:
            titulo_section("Mapa de cobertura mensal",
                           help="Cobertura do mês (recebimentos ÷ necessidade líquida). Meses sem cupom ou vencimento "
                                "aparecem em vermelho: o desenho mostra a concentração dos recebimentos no ano.")
            with st.container(border=True):
                grade = mensal.pivot_table(index="MES", columns="ANO", values="COBERTURA", aggfunc="first").reindex(range(1, 13))
                receb_grade = mensal.pivot_table(index="MES", columns="ANO", values="RECURSOS", aggfunc="first").reindex(range(1, 13))
                nec_grade = mensal.pivot_table(index="MES", columns="ANO", values="NECESSIDADE", aggfunc="first").reindex(range(1, 13))

                def faixa(v):
                    if pd.isna(v):
                        return None
                    return 2 if v >= 1 else 1 if v >= 0.5 else 0

                z = grade.apply(lambda coluna: coluna.map(faixa))
                texto_hover = [
                    [
                        (f"{MESES[m - 1]}/{a}<br>Cobertura: {pct(grade.at[m, a])}<br>"
                         f"Recursos: {brl_curto(receb_grade.at[m, a])}<br>Necessidade: {brl_curto(nec_grade.at[m, a])}")
                        if not pd.isna(grade.at[m, a]) else ""
                        for a in grade.columns
                    ]
                    for m in grade.index
                ]
                cores = [c for _, c, _ in reversed(FAIXAS_COBERTURA)]
                fig_hm = go.Figure(go.Heatmap(
                    z=z.values, x=[f"'{str(a)[2:]}" for a in grade.columns], y=MESES,
                    colorscale=[[0, cores[0]], [0.33, cores[0]], [0.34, cores[1]], [0.66, cores[1]], [0.67, cores[2]], [1, cores[2]]],
                    zmin=0, zmax=2, showscale=False, xgap=2, ygap=2,
                    text=texto_hover, hovertemplate="%{text}<extra></extra>",
                ))
                fig_hm.update_layout(**{**LAYOUT_BASE, "margin": dict(l=10, r=10, t=10, b=10)}, height=330,
                                     yaxis=dict(autorange="reversed", showgrid=False), xaxis=dict(showgrid=False, side="top"))
                st.plotly_chart(fig_hm, config={"displayModeBar": False}, width="stretch", key="fc-heatmap")
                legenda = " &nbsp; ".join(
                    f'<span style="display:inline-block;width:10px;height:10px;background:{c};border-radius:2px;"></span> {r}'
                    for _, c, r in FAIXAS_COBERTURA
                )
                st.html(f'<div class="fc-nota">{legenda} &nbsp; · &nbsp; células vazias: antes da data-base</div>')

        # ── COMPOSIÇÃO DOS RECEBIMENTOS ─────────────────────────────────────
        comp = res["composicao"]
        titulo_section(f"Composição dos recebimentos até {ano_fim}",
                       help="Quebras dos recebimentos do horizonte por emissor, tipo de evento, produto e data.")
        cc1, cc2 = st.columns(2)
        with cc1:
            with st.container(border=True):
                ev = comp["evento"].pivot_table(index="CATEGORIA", columns="EVENTO", values="VALOR", aggfunc="sum", fill_value=0)
                fig_ev = go.Figure()
                for evento, cor in [("Cupom/juros", "#2DC25F"), ("Vencimento", COR_TITULO)]:
                    if evento in ev.columns:
                        fig_ev.add_bar(y=ev.index, x=ev[evento], name=evento, orientation="h", marker_color=cor,
                                       hovertemplate="%{y} · %{fullData.name}: R$ %{x:,.2f}<extra></extra>")
                fig_ev.update_layout(**LAYOUT_BASE, barmode="stack", height=230,
                                     title=dict(text="Emissor × tipo de evento", font=dict(size=14, color=COR_TEXTO)),
                                     xaxis=dict(tickprefix="R$ ", tickformat="~s", showgrid=False),
                                     yaxis=dict(showgrid=False))
                fig_ev.update_layout(margin=dict(l=10, r=10, t=60, b=10))
                st.plotly_chart(fig_ev, config={"displayModeBar": False}, width="stretch", key="fc-evento")

                cat = comp["categoria"].set_index("CATEGORIA")["PCT"]
                st.html(
                    f'<div class="fc-nota">Públicos: <b>{pct(cat.get(CATEGORIA_PUBLICO, 0), 1)}</b> · '
                    f'Privados: <b>{pct(cat.get(CATEGORIA_PRIVADO, 0), 1)}</b> · '
                    f'10 maiores datas concentram <b>{pct(comp["datas"]["PCT"].sum(), 1)}</b> do total</div>'
                )
        with cc2:
            with st.container(border=True):
                prod = comp["produtos"].sort_values("VALOR")
                fig_pr = go.Figure(go.Bar(
                    y=prod["PRODUTO_NOME"], x=prod["VALOR"], orientation="h",
                    marker_color=[COR_PUBLICO if c == CATEGORIA_PUBLICO else COR_PRIVADO for c in prod["CATEGORIA"]],
                    customdata=prod["PCT"], hovertemplate="%{y}: R$ %{x:,.2f} (%{customdata:.1%})<extra></extra>",
                ))
                fig_pr.update_layout(**LAYOUT_BASE, height=300,
                                     title=dict(text="Top 10 produtos", font=dict(size=14, color=COR_TEXTO)),
                                     xaxis=dict(tickprefix="R$ ", tickformat="~s", showgrid=False),
                                     yaxis=dict(showgrid=False, automargin=True))
                fig_pr.update_layout(margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig_pr, config={"displayModeBar": False}, width="stretch", key="fc-produtos")

        # ── RANKING POR PLANO ───────────────────────────────────────────────
        titulo_section("Comparativo por plano",
                       help="Todos os planos na data-base, com as mesmas premissas. "
                            "Planos sem fluxo previdencial exibem apenas recebimentos.")
        rk = res["ranking"].copy()
        rk["_ordem"] = rk["nec_12m"].where(rk["tem_passivo"], -1)
        rk = rk.sort_values(["_ordem", "receb_12m"], ascending=False)
        tp = rk["tem_passivo"]
        tabela_rk = pd.DataFrame({
            "Plano": [("▸ " if t == plano else "") + nome_exibicao(t) for t in rk["TESOURARIA"]],
            "Receb. 12m": rk["receb_12m"].map(brl_curto),
            "Necess. 12m": [brl_curto(v) if t else "sem fluxo" for v, t in zip(rk["nec_12m"], tp)],
            "Cobert. 12m": rk["cobertura_12m"].map(pct),
            "Liquidez 12m": [liquidez_fmt(v) if t else "—" for v, t in zip(rk["liquidez_12m"], tp)],
            "Liquidez 24m": [liquidez_fmt(v) if t else "—" for v, t in zip(rk["liquidez_24m"], tp)],
            "Cobert. 5 anos": rk["cobertura_5a"].map(pct),
            "1º ano déficit": [str(int(v)) if pd.notna(v) else ("Nenhum" if t else "—") for v, t in zip(rk["primeiro_ano_deficit"], tp)],
            "Duration A | P": [duration_fmt(a, b) for a, b in zip(rk["duration_ativo"], rk["duration_passivo"])],
        })
        renderizar_tabela_estilizada(tabela_rk, primeira_coluna_larga=True, key="fc-tabela-ranking")

        # ── DETALHE DO PERÍODO ──────────────────────────────────────────────
        titulo_section("Detalhe do período", help="Escolha o ano para ver mês a mês; a tabela anual cobre todo o horizonte.")
        anos_detalhe = sorted(mensal["ANO"].unique())
        ano_det = st.pills("Ano", anos_detalhe, default=anos_detalhe[0], key="fc-ano-detalhe", label_visibility="collapsed") or anos_detalhe[0]

        def tabela_fluxo(df: pd.DataFrame, rotulos: list[str]) -> pd.DataFrame:
            out = pd.DataFrame({
                "Período": rotulos,
                "Públicos": df["PUBLICOS"].map(brl_extenso),
                "Privados": df["PRIVADOS"].map(brl_extenso),
                "Recebimentos": df["RECEBIMENTOS"].map(brl_extenso),
            })
            if res["com_caixa"]:
                out["Fundos caixa D0"] = df["CAIXA"].map(brl_extenso)
            if k["tem_passivo"]:
                out["Necessidade"] = df["NECESSIDADE"].map(brl_extenso)
                out["Saldo"] = df["SALDO"].map(brl_extenso)
                out["Saldo acumulado"] = df["SALDO_ACUM"].map(brl_extenso)
                out["Cobertura"] = df["COBERTURA"].map(pct)
            return out

        det = mensal[mensal["ANO"] == ano_det]
        renderizar_tabela_estilizada(
            tabela_fluxo(det, [f"{MESES[m - 1]}/{a}" for a, m in zip(det["ANO"], det["MES"])]),
            primeira_coluna_larga=False, key="fc-tabela-mensal",
        )
        with st.expander("Tabela anual do horizonte"):
            renderizar_tabela_estilizada(
                tabela_fluxo(anual_df, [f"{a}*" if a == data_base.year else str(a) for a in anual_df["ANO"]]),
                primeira_coluna_larga=False, rolagem=True, altura_max="420px", key="fc-tabela-anual",
            )

        # ── NOTA METODOLÓGICA ───────────────────────────────────────────────
        with st.expander("Nota metodológica"):
            planos_calc = ", ".join(nome_exibicao(p) for p in res["planos_calculo"])
            prem = res["premissas"]
            st.html(f"""
            <div class="fc-nota">
            <p><b>Ativo.</b> Recebimentos programados (cupons e vencimentos) da consulta [SUCON] Projeção Rendimentos na
            data-base {data_base:%d/%m/%Y}. Títulos públicos federais (NTN, LTN, LFT) separados dos demais pelo nome do produto.
            {"Fundos caixa D0 entram como recurso disponível no mês da data-base." if res["com_caixa"] else ""}</p>
            <p><b>Passivo.</b> Linha "Fluxos de seguridade para o cálculo da duration (Fi)" da avaliação atuarial com sinal
            invertido (benefícios − contribuições de assistidos){" menos contribuições de ativos" if res["deduzir_contrib_ativos"] else ""}.
            {"Valores reais de " + f"{prem['data_referencia_passivo']:%d/%m/%Y}" + f" corrigidos por IPCA de {pct(res['ipca_aa'], 2)} a.a." if prem["passivo_em_valores_reais"] else "Valores nominais."}</p>
            <p><b>Base de comparação.</b> {BASES[res["base"]]}. {"Recebimento projetado (nominal) × passivo nominal." if res["base"] == "nominal"
            else "Recebimento a valor presente × passivo nominal descontado pela curva implícita nos títulos públicos (Σ presente ÷ Σ projetado por data)."}
            A duration dos dois lados usa sempre essa curva.</p>
            <p><b>Distribuição mensal.</b> Ano da data-base: pro rata a partir da data-base. Demais anos:
            {'÷ 13, com dezembro em dobro (abono anual)' if treze else '÷ 12'}.</p>
            <p><b>Limitações.</b> Não considera {"caixa, " if not res["com_caixa"] else ""}ativos líquidos sem fluxo programado,
            reinvestimento, renda variável, imóveis e fundos. EROS FIM fica fora do consolidado para evitar dupla contagem.</p>
            <p><b>Planos no cálculo:</b> {planos_calc}.</p>
            </div>
            """)