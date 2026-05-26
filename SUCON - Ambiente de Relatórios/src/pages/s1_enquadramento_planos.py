
import streamlit as st
import pandas as pd
from utils.gerar_pdf import gerar_pdf
from utils.queries.enquadramento import buscar_dados
from utils.helpers import estilizar_tabela, aplicar_destaque, get_css_responsivo, nome_plano, formatar_percentual_br, limpar_texto, remove_grp
import os
import datetime


# Seleção inicial do plano
if "regime_ativo" not in st.session_state:
    st.session_state["regime_ativo"] = "Política de Investimentos"



# ── DADOS ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_time=True)
def carregar_dados() -> pd.DataFrame:
    return buscar_dados()

df = carregar_dados()
df.columns = df.columns.str.upper()


# Aviso se DataFrame principal estiver vazio
if df.empty:
    st.warning('Nenhum dado encontrado para o filtro selecionado.')
    st.stop()

st.markdown(
    """<style>
   
    /* 3. PROTEÇÃO CONTRA O BUG DO EXPANDER */
    [data-testid="stExpanderToggleIcon"] {
        font-family: "Material Symbols Outlined", "Material Icons", sans-serif !important;
        display: none !important;
    }
    [data-testid="stExpanderSummary"] span:not(:first-child) {
        display: none !important;
    }
    [data-testid="stExpanderSummary"] p {
        font-family: 'Figtree', sans-serif !important;
        margin-right: 0 !important;
        padding-right: 0 !important;
        width: 100% !important;
    }

  
    /* --- Pills - estado base --- SÓ NA PÁGINA PRINCIPAL */
    [data-testid="stMainBlockContainer"] [data-testid="stButtonGroup"] button[kind="pills"] {
        background-color: transparent !important;
        border-color: #c0392b !important;
        color: #c0392b !important;
        border-radius: 6px !important;
        font-family: 'Figtree', sans-serif !important;
        transition: background-color 0s, border-color 0s, color 0s !important;
    }

    /* --- Pills - hover --- */
    [data-testid="stMainBlockContainer"] [data-testid="stButtonGroup"] button[kind="pills"]:hover {
        background-color: rgba(192, 57, 43, 0.15) !important;
        border-color: #a93226 !important;
        color: #a93226 !important;
    }

    /* --- Pills - clique/foco/selecionado --- */
    [data-testid="stMainBlockContainer"] [data-testid="stButtonGroup"] button[kind="pills"]:active,
    [data-testid="stMainBlockContainer"] [data-testid="stButtonGroup"] button[kind="pills"]:focus,
    [data-testid="stMainBlockContainer"] [data-testid="stButtonGroup"] button[kind="pills"][aria-checked="true"],
    [data-testid="stMainBlockContainer"] [data-testid="stButtonGroup"] button[kind="pills"][aria-pressed="true"] {
        background-color: rgba(192, 57, 43, 0.15) !important;
        border-color: #c0392b !important;
        color: #c0392b !important;
        box-shadow: none !important;
        outline: none !important;
    }

    /* --- Pills selecionado - vermelho --- */
    [data-testid="stMainBlockContainer"] [data-testid="stButtonGroup"] button[kind="pills"][aria-checked="true"] {
        background-color: #c0392b !important;
        border-color: #c0392b !important;
        color: white !important;
    }

    /* --- Botão PRIMARY - SÓ NA PÁGINA PRINCIPAL --- */
    [data-testid="stMainBlockContainer"] [data-testid="stBaseButton-primary"],
    [data-testid="stMainBlockContainer"] [data-testid="stBaseButton-primary"]:hover,
    [data-testid="stMainBlockContainer"] [data-testid="stBaseButton-primary"]:focus {
        background-color: #0b2f13 !important;
        color: white !important;
        border: 2px solid #0b2f13 !important;
    }

    /* --- Botão SECONDARY - SÓ NA PÁGINA PRINCIPAL --- */
    [data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondary"],
    [data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondary"]:hover,
    [data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondary"]:focus {
        background-color: transparent !important;
        color: #0b2f13 !important;
        border: 2px solid #0b2f13 !important;
    }

    /* --- Radio --- */
    [data-testid="stMainBlockContainer"] [data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {
        background-color: transparent !important;
        border: 2px solid #0b2f13 !important;
    }
    [data-testid="stMainBlockContainer"] [data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child > div {
        background-color: transparent !important;
    }
    [data-testid="stMainBlockContainer"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) > div:first-child > div {
        background-color: #0b2f13 !important;
    }

    /* --- Multiselect --- */
    [data-testid="stMainBlockContainer"] [data-testid="stMultiSelect"] span[data-baseweb="tag"] {
        background-color: #0b2f13 !important;
    }
    [data-testid="stMainBlockContainer"] [data-testid="stMultiSelect"] li[aria-selected="true"] {
        background-color: rgba(11, 47, 19, 0.2) !important;
    }

    /* --- Borda foco inputs --- */
    [data-testid="stMainBlockContainer"] [data-baseweb="select"] [data-baseweb="input"]:focus-within {
        border-color: #0b2f13 !important;
    }

    :root {
        --primary-color: #014d2a !important;
    }

    /* --- Selectbox e Multiselect - remove borda colorida no foco --- */
    [data-testid="stMainBlockContainer"] [data-testid="stSelectbox"] [data-baseweb="select"] > div:first-child,
    [data-testid="stMainBlockContainer"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div:first-child {
        border-color: rgba(0, 0, 0, 0.2) !important;
        box-shadow: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Aplica CSS responsivo para tabelas
st.markdown(get_css_responsivo(), unsafe_allow_html=True)

# Inicializa a chave permanente
if 'data_posicao' not in st.session_state:
    st.session_state['data_posicao'] = df['DATA_COTACAO'].max().date()

# Callback: salva o valor temporário na chave permanente
def armazena_data():
    st.session_state['data_posicao'] = st.session_state['_data_posicao']

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<h1 style="color: #0B2F13; margin: 0;">Enquadramento Diário - Fundação Ceres</h1>', unsafe_allow_html=True)
with col2:
    ultima_data_disponivel = df['DATA_COTACAO'].max().date()
    primeira_data_disponivel = df['DATA_COTACAO'].min().date()
    ajuda_data_input = f"As datas disponíveis estão entre {primeira_data_disponivel.strftime('%d/%m/%Y')} e {ultima_data_disponivel.strftime('%d/%m/%Y')}."

    # ✅ Carrega o valor permanente na chave temporária ANTES de renderizar o widget
    st.session_state['_data_posicao'] = st.session_state['data_posicao']

    data_posicao = st.date_input(
        "Selecione a data posição",
        format="DD/MM/YYYY",
        help=ajuda_data_input,
        min_value=primeira_data_disponivel,
        max_value=ultima_data_disponivel,
        key="_data_posicao",        # chave temporária
        on_change=armazena_data     # salva na chave permanente ao mudar
    )

df_filtrado_data = df[df['DATA_COTACAO'] == pd.to_datetime(data_posicao)]

# Espaço entre o cabeçalho e o conteúdo
st.markdown("<br>", unsafe_allow_html=True)


container = st.container(border=True)
container.write("O Relatório tem como objetivo verificar a aderência dos investimentos do plano às diretrizes de aplicações estabelecidas pela Política de Investimentos vigente e pela " \
            "Resolução CMN N° 4.994 vigente." \
            )
st.divider()


#___SELECIONAR REGIME ________

# Botões de Regime
col1, col2, col3 = st.columns([4, 1.5, 1.5]) 

def set_regime(nome):
    st.session_state["regime_ativo"] = nome

with col2:
    st.markdown("**Regime:**")
    tipo_pi = "primary" if st.session_state["regime_ativo"] == "Política de Investimentos" else "secondary"
    st.button(
        "Política de Investimentos",
        type=tipo_pi,
        use_container_width=True,
        on_click=set_regime,
        args=("Política de Investimentos",),
    )

with col3:
    st.markdown("&nbsp;", unsafe_allow_html=True)
    tipo_res = "primary" if st.session_state["regime_ativo"] == "Resolução 4994" else "secondary"
    st.button(
        "Resolução 4994",
        type=tipo_res,
        use_container_width=True,
        on_click=set_regime,
        args=("Resolução 4994",),
    )
# Filtragem final 
df_filtrado = df_filtrado_data[df_filtrado_data["CONJUNTO"] == st.session_state["regime_ativo"]]

# ── MÉTRICAS GERAIS ────────────────────────────────────────
planos = sorted(df_filtrado["ESTRUTURA_ASSOCIADA"].unique())

planos_desenquadrados_orig = sorted(
    df_filtrado.ESTRUTURA_ASSOCIADA[df_filtrado['STATUS']=='Desenquadrado'].unique()
)

# Mapeia nome amigável <-> valor original dos desenquadrados
nome_para_orig = {nome_plano(p): p for p in planos_desenquadrados_orig}
orig_para_nome = {v: k for k, v in nome_para_orig.items()}
opcoes = list(nome_para_orig.keys())

# Callbacks de sincronização
def on_pills_change():
    sel = st.session_state.get("pills_desenq")
    if sel:
        st.session_state["selectbox_plano"] = nome_para_orig[sel]
        st.session_state["pills_desenq"] = None 
    # Se pills desmarcou (None), não mexe no selectbox

def on_selectbox_change():
    sel = st.session_state.get("selectbox_plano")
    if sel in orig_para_nome:
        st.session_state["pills_desenq"] = None
    else:
        st.session_state["pills_desenq"] = None

# Inicializa pills_desenq se não existir
if "pills_desenq" not in st.session_state:
    st.session_state["pills_desenq"] = None

if planos_desenquadrados_orig:
    st.pills(
        "Planos desenquadrados:",
        opcoes,
        key="pills_desenq",
        on_change=on_pills_change,

    )

# ── SELETOR DE PLANO ────────────────────────────────────────


# Garante que o plano salvo existe na lista atual, senão reseta
try:

    if "selectbox_plano" not in st.session_state:
        st.session_state["selectbox_plano"] = planos[0]

    plano_salvo = st.session_state["selectbox_plano"]
    if plano_salvo in planos:
        idx = planos.index(plano_salvo)
    else:
        idx = 0
        st.session_state["selectbox_plano"] = planos[0]

    plano = st.selectbox(
        "Plano",
        options=planos,
        format_func=nome_plano,
        key="selectbox_plano",
        on_change=on_selectbox_change,
    )


except Exception as e:
    datas_disponiveis = df["DATA_COTACAO"].sort_values().unique()
    data_posicao_ts = pd.Timestamp(data_posicao)  
    for idx, data in enumerate(datas_disponiveis[:-1]):
        data_ts = pd.Timestamp(data)
        proxima_ts = pd.Timestamp(datas_disponiveis[idx + 1])
        if data_ts < data_posicao_ts < proxima_ts:
            st.warning(
                f'Nenhum plano encontrado para a data selecionada, considere selecionar a data mais próxima: '
                f'{data_ts.strftime("%d/%m/%Y")} ou {proxima_ts.strftime("%d/%m/%Y")}.'
            )
            break

    st.stop()
   
# ── FILTRA O DATAFRAME DO PLANO ──────────────────────────────
df_plano = df_filtrado[df_filtrado["ESTRUTURA_ASSOCIADA"] == plano].copy()
if df_plano.empty:
    st.warning('Nenhum dado encontrado para o plano selecionado.')
    st.stop()

# ── EXPORTAR PDF ─────────────────────────────────────────────────────────────

import zipfile
import tempfile

col_vazio, col_export = st.columns([3, 1])
with col_export:
    summary = st.expander("Exportar dados (PDF ou CSV)", icon=None, key="exportar_dados_expander")
    with summary:
        tipo_export = st.radio(
            "Formato de exportação:",
            ["PDF", "CSV"],
            horizontal=True,
            key="tipo_exportacao_radio",
        )
        planos_multiplos = st.multiselect(
            "Selecione os planos para exportar:",
            options=planos,
            format_func=nome_plano,
            key="multiplos_planos_export",
        )

        if planos_multiplos:
            if tipo_export == "PDF":
                if len(planos_multiplos) == 1:
                    pdf_bytes = gerar_pdf(df_filtrado_data, planos_multiplos[0], data_posicao, st.session_state["regime_ativo"])
                    st.download_button(
                        label="Exportar PDF",
                        data=pdf_bytes,
                        file_name=f"enquadramento_{nome_plano(planos_multiplos[0]).replace(' ', '_')}_{data_posicao.strftime('%d/%m/%Y').replace('/', '-')}_{st.session_state['regime_ativo']}.pdf",
                        mime="application/pdf",
                    )
                else:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        zip_path = os.path.join(tmpdir, "enquadramento_planos.zip")
                        with zipfile.ZipFile(zip_path, "w") as zf:
                            for plano_sel in planos_multiplos:
                                pdf = gerar_pdf(df_filtrado_data, plano_sel, data_posicao, st.session_state["regime_ativo"])
                                nome_pdf = f"enquadramento_{nome_plano(plano_sel).replace(' ', '_')}_{data_posicao}_{st.session_state['regime_ativo']}.pdf"
                                zf.writestr(nome_pdf, pdf)
                        with open(zip_path, "rb") as f:
                            st.download_button(
                                label="Exportar ZIP com PDFs",
                                data=f.read(),
                                file_name=f"enquadramento_planos_{data_posicao}_{st.session_state['regime_ativo']}.zip",
                                mime="application/zip",
                            )
            else:
                import io
                if len(planos_multiplos) == 1:
                    plano_sel = planos_multiplos[0]
                    df_csv = df_filtrado_data[(df_filtrado_data["ESTRUTURA_ASSOCIADA"] == plano_sel) & (df_filtrado_data['CONJUNTO'] == st.session_state["regime_ativo"])]
                    csv_bytes = df_csv.to_csv(index=False).encode("utf-8-sig")
                    st.download_button(
                        label="Exportar CSV",
                        data=csv_bytes,
                        file_name=f"enquadramento_{nome_plano(plano_sel).replace(' ', '_')}_{data_posicao}_{st.session_state['regime_ativo']}.csv",
                        mime="text/csv",
                    )
                else:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        zip_path = os.path.join(tmpdir, "enquadramento_planos_csv.zip")
                        with zipfile.ZipFile(zip_path, "w") as zf:
                            for plano_sel in planos_multiplos:
                                df_csv = df_filtrado_data[(df_filtrado_data["ESTRUTURA_ASSOCIADA"] == plano_sel) & (df_filtrado_data['CONJUNTO'] == st.session_state["regime_ativo"])]
                                nome_csv = f"enquadramento_{nome_plano(plano_sel).replace(' ', '_')}_{data_posicao}_{st.session_state['regime_ativo']}.csv"
                                zf.writestr(nome_csv, df_csv.to_csv(index=False))
                        with open(zip_path, "rb") as f:
                            st.download_button(
                                label="Exportar ZIP com CSVs",
                                data=f.read(),
                                file_name=f"enquadramento_planos_{data_posicao}_{st.session_state['regime_ativo']}.zip",
                                mime="application/zip",
                            )


# ── TABELAS POR SEGMENTO ──────────────────────────────

# Define a ordem esperada dos segmentos
ordem_segmentos_politica = ['Renda Fixa', 'Renda Variável', 'Imobiliário', 'Estruturado', 'Operações com Participantes', 'Exterior']

# Ordena os segmentos de acordo com a lista de ordem
segmentos = df_plano["SEGMENTO"].unique()
segmentos = sorted(segmentos, key=lambda x: ordem_segmentos_politica.index(x) if x in ordem_segmentos_politica else len(ordem_segmentos_politica))


    #________________TABELA AGREGADA__________________




if st.session_state["regime_ativo"] == "Política de Investimentos":

    st.subheader("Limites de Alocação e Concentração", text_alignment="center")
    st.space(size="xxsmall")

    # 1. Filtro e Ordenação
    agregado = ["Renda Fixa", "Renda Variável", "Imobiliário", "Estruturado", "Operações com Participantes", "Exterior"]
    df_agregado = df_plano[df_plano['DESCRICAO'].isin(agregado)].copy()
    df_agregado['DESCRICAO'] = pd.Categorical(df_agregado['DESCRICAO'], categories=agregado, ordered=True)
    df_agregado = df_agregado.sort_values('DESCRICAO')


    #1.5 Calculando coluna do posição %
    df_agregado["PCT_ATUAL"] = (df_agregado["VALOR_ATUAL"] / df_agregado["VALOR_REFERENCIA"]) * 100

    # 2. Seleção e Renomeação
    colunas_map = {
        "DESCRICAO": "Segmento de Aplicação",
        "LIMITE_PERCENTUAL": "Limite %",
        "VALOR_LIMITE_REGRA": "Limite R$",
        "PCT_ATUAL": "Posição %",
        "VALOR_ATUAL": "Posição R$",
        "PERCENTUAL_UTILIZADO": "Limite Utilizado %",
        "STATUS": "Status"
    }
    df_agregado = df_agregado[list(colunas_map.keys())].rename(columns=colunas_map)

    
    # 3. Cálculo de Totais (Soma numérica antes da formatação)
    total_pos_rs = df_agregado["Posição R$"].sum()
    total_pos_pct = df_agregado["Posição %"].sum()

    linha_total = pd.DataFrame({
        "Segmento de Aplicação": ["Total de Recursos Garantidores"],
        "Posição %": [total_pos_pct],  #
        "Posição R$": [total_pos_rs],
        
    })
    df_agregado = pd.concat([df_agregado, linha_total], ignore_index=True)

    # 4. Formatação e Tratamento de Nulos
    df_agregado['Limite %'] = df_agregado['Limite %'].apply(lambda x: formatar_percentual_br(x) if pd.notnull(x) else "-")
    df_agregado["Limite Utilizado %"] = df_agregado["Limite Utilizado %"].apply(lambda x: formatar_percentual_br(x) if pd.notnull(x) else "-")
    df_agregado["Posição %"] = df_agregado["Posição %"].apply(lambda x: formatar_percentual_br(round(x,2)) if pd.notnull(x) else "-")
    df_agregado['Posição R$'] = df_agregado['Posição R$'].apply(lambda x: f"{x:,.2f}".replace(',', 'v').replace('.', ',').replace('v', '.') if pd.notnull(x) else "-")
    df_agregado['Limite R$'] = df_agregado['Limite R$'].apply(lambda x: f"{x:,.2f}".replace(',', 'v').replace('.', ',').replace('v', '.') if pd.notnull(x) else "-")

    # Preenche qualquer outro valor nulo (como o Status na linha do Total) com "-"
    df_agregado = df_agregado.fillna("-")

    # 5. Destaque e Exibição
    mask_desenquadrado = df_agregado["Status"].str.upper() == "DESENQUADRADO"
    styled = aplicar_destaque(df_agregado, mask_desenquadrado)
    st.html(f'<div class="tabela-responsiva">{styled.to_html()}</div>')

st.divider()



for segmento in segmentos:
    df_segmento = df_plano[df_plano["SEGMENTO"] == segmento]
    df_segmento = df_segmento.sort_values(by="ORDEM")
    df_segmento["DESCRICAO"] = df_segmento["DESCRICAO"].apply(limpar_texto)
    
    # Resumo enquadramento para o segmento
    status_classe = (df_segmento['STATUS'] == 'Desenquadrado').any()
    status_classe = 'Desenquadrado' if status_classe else 'Enquadrado'

    label = f"{segmento}"
       
    
    if st.session_state["regime_ativo"] == "Resolução 4994":
        
    
        if segmento not in ['Emissores (Art. 27)', 'Emissores (Art. 28)']:
            st.subheader(label)
            df_exibir = df_segmento[[
                "DESCRICAO",
                "LIMITE_PERCENTUAL",
                "VALOR_LIMITE_REGRA",
                "VALOR_ATUAL",
                "PERCENTUAL_UTILIZADO",
                "PERCENTUAL_ULTRAPASSADO",
                "PERCENTUAL_TOTAL",
                "STATUS",
            ]].copy()

            df_exibir.columns = [
                "Descrição",
                "Limite %",
                "Limite R$",
                "Posição R$",
                "Limite Utilizado %",
                "% Ultrapassado",
                "% Total",
                "Status",
            ]

            df_exibir["Limite Utilizado %"] = df_exibir["Limite Utilizado %"].apply(formatar_percentual_br)
            df_exibir["% Ultrapassado"] = df_exibir["% Ultrapassado"].apply(formatar_percentual_br)
            #df_exibir["% Total"] = df_exibir["% Total"].apply(formatar_percentual_br)
            df_exibir['Posição R$'] = df_exibir['Posição R$'].apply(lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            df_exibir['Limite R$'] = df_exibir['Limite R$'].apply(lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            mask_desenquadrado = df_exibir["Status"].str.upper() == "DESENQUADRADO"
            df_exibir['Limite %'] = df_exibir['Limite %'].apply(formatar_percentual_br)

            df_exibir = df_exibir.drop(columns=["% Total", "% Ultrapassado"])

            styled = aplicar_destaque(df_exibir, mask_desenquadrado)
            st.html(f'<div class="tabela-responsiva">{styled.to_html()}</div>')
        else:
            
            st.subheader(label)
            df_segmento['DESCRICAO'] = df_segmento['DESCRICAO'].str.strip()
            df_segmento['GRP_ECONOMICO'] = df_segmento['AGREGACAO'].apply(remove_grp)
            df_segmento = df_segmento.sort_values(by=['ORDEM', 'DESCRICAO'])
            
            df_exibir = df_segmento[[
                "DESCRICAO",
                "GRP_ECONOMICO",
                "VALOR_LIMITE_REGRA",
                "VALOR_ATUAL",
                "PERCENTUAL_UTILIZADO",
                "PERCENTUAL_ULTRAPASSADO",
                "PERCENTUAL_TOTAL",
                "STATUS"
            ]].copy()

            df_exibir.columns = [
                "Descrição", "Grupo Econômico", "Limite R$", "Posição R$", 
                "Limite Utilizado %", "% Ultrapassado", "% Total", "Status"
            ]

            # Formatações de percentual
            df_exibir["Limite Utilizado %"] = df_exibir["Limite Utilizado %"].apply(formatar_percentual_br)
            df_exibir["% Ultrapassado"] = df_exibir["% Ultrapassado"].apply(formatar_percentual_br)
            df_exibir["% Total"] = df_exibir["% Total"].apply(formatar_percentual_br)
            df_exibir['Posição R$'] = df_exibir['Posição R$'].apply(lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            df_exibir['Limite R$'] = df_exibir['Limite R$'].apply(lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            
            
            # Lógica de "Merge" Visual
            df_exibir["Descrição"] = df_exibir["Descrição"].where(
                df_exibir["Descrição"] != df_exibir["Descrição"].shift(), ""
            )

            # Guarda quais linhas são desenquadradas antes de remover a coluna
            mask_desenquadrado = df_exibir["Status"].str.upper() == "DESENQUADRADO"
            df_exibir = df_exibir.drop(columns=["% Total", "% Ultrapassado"])

            styled = aplicar_destaque(df_exibir, mask_desenquadrado)
            st.html(f'<div class="tabela-responsiva">{styled.to_html()}</div>')

    else:
        
        segmento_politica = ['Renda Fixa', 'Renda Variável', 'Imobiliário', 'Estruturado', 'Operações com Participantes', 'Exterior']
        ordem_regras = [
        "Renda Fixa",
        "Títulos da dívida pública mobiliária federal",
        "Cotas de classes de ETF de RF composto exclusivamente por títulos públicos",
        "Ativos financeiros RF de instituições financeiras autorizadas pelo Bacen",
        "Ativos financeiros RF de sociedade por ações cap aberto e cias securitizadoras",
        "Cotas de classes de ETF de RF",
        "Títulos das dívidas públicas mobiliárias estaduais e municipais",
        "Obrigações de organismos multilaterais emitidas no País",
        "Ativos financeiros RF de inst. financeiras não bancárias e cooperativas de crédito",
        "Debêntures Incentivadas - Lei 12.431 e Debêntures de Infraestrutura - Lei 14.801",
        "Cotas de classe FIDC e cotas de classes de cotas de FIDCs, CCBs e CCCBs",
        "CPRs, CRAs, CDCAs e Was",
        "Demais ativos",
        "Renda Variável",
        "Ações e cotas de classes de fundos de índice segmento especial",
        "Ações e cotas de classe de fundos de índice segmento não especial",
        "Brazilian Depositary Receipts (BDR) e ETF internacional",
        "Certificado de Ouro físico padrão negociado em bolsa de mercadorias e de futuros",
        "Estruturado",
        "Cotas de classes Fundos de Investimento em Participações - FIP",
        "Cotas de classes Fundos de Invest. nas Cadeias Produtivas Agroindustriais - FIAGRO",
        "Certificado de Operações Estruturadas - COE",
        "Cotas de classes de fundos de investimento \"Ações - Mercado de Acesso\"",
        "Cotas de classes de Fundos tipificadas como Multimercado",
        "Créditos de descarbonização – CBIO e Créditos de Carbono",
        "Imobiliário",
        "Cotas de classes Fundo de Invest. Imobiliário (FII) e Cotas de Classes em Cotas de FII",
        "Certificados de recebíveis imobiliários - CRI",
        "Células de crédito imobiliário - CCI",
        "Imóveis",
        "Operações com Participantes",
        "Empréstimo Simples",
        "Financiamento Imobiliário",
        "Exterior",
        "Cotas de classes de fundos e cotas de classe de FICs Renda Fixa - Dívida Externa",
        "Cotas de classes de FI, destinados a investidores qualificados e Offshore",
        "Cotas de classes de FI, destinados a investidores qualificados e ativos no exterior",
        "Cotas de classes de FI, destinados ao público em geral e Offshore",
        "Ativos financeiros no exterior pertencentes às carteiras dos fundos locais"
    ]

        


        # Garante que apenas segmentos válidos são processados
        if segmento not in segmento_politica:
            st.warning(f"Segmento '{segmento}' não está na lista de segmentos esperados.")
            continue
        
        # Ordena apenas pela DESCRICAO conforme ordem_regras (já filtrado por segmento no loop)
        df_segmento["DESCRICAO"] = pd.Categorical(df_segmento["DESCRICAO"], categories=ordem_regras, ordered=True)
        df_segmento = df_segmento.sort_values(by="DESCRICAO")

        df_exibir = df_segmento[[
                "DESCRICAO",
                "LIMITE_PERCENTUAL",
                "VALOR_LIMITE_REGRA",
                "VALOR_ATUAL",
                "PERCENTUAL_UTILIZADO",
                "PERCENTUAL_ULTRAPASSADO",
                "PERCENTUAL_TOTAL",
                "STATUS",
            ]].copy()

        df_exibir.columns = [
                "Descrição",
                "Limite %",
                "Limite R$",
                "Posição R$",
                "Limite Utilizado %",
                "% Ultrapassado",
                "% Total",
                "Status",
            ]
        
        df_exibir["Limite Utilizado %"] = df_exibir["Limite Utilizado %"].apply(formatar_percentual_br)
        df_exibir["% Ultrapassado"] = df_exibir["% Ultrapassado"].apply(formatar_percentual_br)
        df_exibir["% Total"] = df_exibir["% Total"].apply(formatar_percentual_br)
        df_exibir['Posição R$'] = df_exibir['Posição R$'].apply(lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        df_exibir['Limite R$'] = df_exibir['Limite R$'].apply(lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        df_exibir['Limite %'] = df_exibir['Limite %'].apply(formatar_percentual_br)
        mask_desenquadrado = df_exibir["Status"].str.upper() == "DESENQUADRADO"
        
        df_exibir = df_exibir.drop(columns=["% Total", "% Ultrapassado"])

        df_exibir = df_exibir.iloc[1:]

        st.subheader(label)
        styled = aplicar_destaque(df_exibir, mask_desenquadrado)
        st.html(f'<div class="tabela-responsiva">{styled.to_html()}</div>')

