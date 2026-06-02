import streamlit as st
import pandas as pd
from utils.helpers import nome_plano, fmt_br, gerar_tabela_estilizada
from utils.queries.lim_operacionais import buscar_dados 
from utils.gerar_pdf import gerar_pdf_limites_operacionais
import plotly.graph_objects as go
import zipfile
from io import BytesIO
from datetime import datetime
import numpy as np

#/* ============================================================================
## CARDS HTML
#   ============================================================================ */
def gasto_card(titulo: str, gasto: float, limite: float):
    pct = min(max(gasto / limite * 100, 0), 100)
    def lerp(a, b, t): return a + (b - a) * t
    p = pct / 100
    if p <= 0.5:
        t = p / 0.5
        r, g, b = int(lerp(99,186,t)), int(lerp(196,117,t)), int(lerp(87,23,t))
    else:
        t = (p - 0.5) / 0.5
        r, g, b = int(lerp(186,226,t)), int(lerp(117,75,t)), int(lerp(23,74,t))
    color = f"rgb({r},{g},{b})"
    bg_alpha = round(pct / 100 * 0.08, 4)
    card_bg = f"rgba({r},{g},{b},{bg_alpha})"

    if pct < 30:
        badge_bg, badge_fg = "#EAF3DE", "#3B6D11"  # Verde Sucesso (Bom)
    elif pct < 50:
        badge_bg, badge_fg = "#F3F7DE", "#557A18"  # Verde Limão / Transição
    elif pct < 65:
        badge_bg, badge_fg = "#FFFBE6", "#8F7000"  # Amarelo Atenção
    elif pct < 75:
        badge_bg, badge_fg = "#FAEEDA", "#854F0B"  # Laranja Claro / Alerta Inicial
    elif pct < 85:
        badge_bg, badge_fg = "#FCECD9", "#9C4E05"  # Laranja Intermediário
    elif pct < 95:
        badge_bg, badge_fg = "#FAECE7", "#993C1D"  # Vermelho Alaranjado / Crítico
    else:
        badge_bg, badge_fg = "#FCEBEB", "#A32D2D"  # Vermelho Escuro (Grave)
    disponivel = limite - gasto

    gasto_fmt = fmt_br(gasto, 2)
    limite_fmt = fmt_br(limite, 2)
    disponivel_fmt = fmt_br(disponivel, 2)
    
    st.markdown(f"""
    <div class="gasto-card" style="background:{card_bg}; border: 1px solid {color}; border-radius:16px; padding:20px 24px; margin-bottom:12px; font-family: 'Figtree', sans-serif;">
      <div class="gasto-card-header" style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
        <div style="flex: 1; min-width: 0;">
          <p class="gasto-card-titulo" style="background:#0b2f13; color:#a8ec7d; font-size:20px; font-weight:normal; word-break: break-word; display: inline-block; border-radius: 6px; padding: 1px 5px; margin: 0 -8px 8px;">{titulo}</p>
          <div style="display:flex; align-items:baseline; gap:6px; flex-wrap: wrap;">
            <span class="gasto-card-valor" style="font-size:36px; font-weight:400; color:{color}; white-space: nowrap;">
              R$ {gasto_fmt}
            </span>
            <span class="gasto-card-limite" style="font-size:14px; color:#888; white-space: nowrap;">/ R$ {limite_fmt}</span>
          </div>
        </div>
        <span class="gasto-card-badge" style="background:{badge_bg}; color:{badge_fg}; font-size:14px; font-weight:600;
                     padding:4px 12px; border-radius:99px; white-space: nowrap; flex-shrink: 0; margin-left: 8px;">{pct:.0f}%</span>
      </div>
      <div style="background:rgba(255,255,255,0.08); border-radius:99px; height:8px; overflow:hidden; margin-bottom:10px;">
        <div style="width:{pct}%; height:100%; background:{color}; border-radius:99px;
                    box-shadow:0 0 6px {color};"></div>
      </div>
      <div class="gasto-card-footer" style="display:flex; justify-content:space-between; flex-wrap: wrap; gap: 8px;">
        <span style="font-size:12px; color:#666;">Disponível</span>
        <span style="font-size:12px; font-weight:500; color:{color if pct >= 75 else '#888'}; white-space: nowrap;">
          R$ {disponivel_fmt}
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)



def card_titulo(texto):
    st.markdown(
        f'<span style="background-color: #0b2f13; color: #a8ec7d; font-size: 20px; '
        f'padding: 1px 5px; border-radius: 6px; font-weight: normal; '
        f'display: inline-block;">{texto}</span>',
        unsafe_allow_html=True
    )

@st.cache_data(ttl='21600' ,show_time=True)  
def load_data():
    return buscar_dados()

data = load_data()

# SESSION_STATE PADRÃO
if "data_selecionada" not in st.session_state:
    st.session_state.data_selecionada = data['DATA_COTACAO'].max().date()


#/* ============================================================================
## TABELA COM INFOS DA IFS
#   ============================================================================ */

dados_limites = [
    ["BANCO COOPEREATIVO SICREDI S.A.", "SICREDI",None, None, None,100000000.00],
    ["Banco Cooperativo do Brasil S.A.", "BANCO SICOOB",None, None, None,100000000.00],
    ["Banco Safra S.A.", "SAFRA", None,None, None,100000000.00],
    ["ITAU UNIBANCO S.A.", "ITAÚ UNIBANCO", None,None, None,100000000.00],
    ["BANCO ABC BRASIL S.A.", "ABC BRASIL", None, None, None,100000000.00],
    ["BANCO BTG PACTUAL S.A.", "BTG PACTUAL",None, None, None,100000000.00],
    ["BANCO DAYCOVAL S/A", "DAYCOVAL", None, None, None,100000000.00],
    ["BANCO MERCANTIL DO BRASIL SA", "MERCANTIL", None, None, None,100000000.00],
    ["BANCO SANTANDER (BRASIL) S.A.","SANTANDER (BRASIL)", None, None,None,100000000.00],
    ["BANCO VOTORANTIM S.A.", "BANCO BV", None, None, None,100000000.00],
    ["BANCO SOFISA SA", "SOFISA",None, None, None,100000000.00],
    ["BANCO BRADESCO SA", "BRADESCO (*)", None,None, None,None],
    ["PARANA BANCO S/A", "PARANA BANCO (*)", None,None, None,None],
    ["BANCO PAN S.A.", "PAN (**)", None, None,None, None]
]

dados_risco = [
    ["ABC BRASIL", "Médio Porte", 11.02, None, 6604060.00, "Até 5 anos", "BRLP 3"],
    ["BANCO BV", "Grande Porte", 9.77, None, 13397130.00, "Até 5 anos", "BRLP 3"],
    ["SOFISA", "Médio Porte", 9.19, None, 1144639.00, "Até 3 anos", "BRMP 1"],

    ["SICREDI", "Grande Porte", 11.35, None, 5432089.00, "Até 5 anos", "BRLP 3"],

    ["BANCO SICOOB", "Grande Porte", 11.25, None, 5505854.00, "Até 5 anos", "BRLP 3"],
    ["BTG PACTUAL", "Grande Porte", 10.68, None, 69335302.00, "Até 5 anos", "BRLP 3"],
    ["DAYCOVAL", "Médio Porte", 10.44, None, 7666905.00, "Até 5 anos", "BRLP 3"],
    ["ITAÚ UNIBANCO", "Grande Porte", 11.17, None, 209552000.00, "Até 10 anos", "BRLP 1"],
    ["MERCANTIL", "Médio Porte", 10.07, None, 2106362.00, "Até 3 anos", "BRMP 1"],
    ["SAFRA", "Grande Porte", 11.25, None, 19777134.00, "Até 5 anos", "BRLP 3"],
    ["SANTANDER (BRASIL)", "Grande Porte", 9.91, None, 94089614.00, "Até 10 anos", "BRLP 1"],
    ["BRADESCO (*)", "Médio Porte", 9.19, "CI", 1144639.00, "Até 3 anos", "BRMP 1"],
    ["PARANA BANCO (*)", "Médio Porte", 9.19, "A", 1144639.00, "Até 3 anos", "BRMP 1"],
    ["PAN (**)", "Médio Porte", 9.19, None, 1144639.00, "Até 3 anos", "BRMP 1"]
]
# 2. Cabeçalhos padronizados e limpos para o seu sistema
colunas_limites = [
    "ID_MITRA",
    "INSTITUICAO_FINANCEIRA",
    "EXPOSICAO",
    "EXPOSICAO_2026",
    "FINANCEIRO_AQUISICAO",
    'LIMITE_ALOCACAO_2026'
]

colunas_risco = [
    "Instituição Financeira",
    "Porte da Instituição",
    "Índice RiskBank",
    "Alerta",
    "Patrimônio Líquido (R$ Mil)",
    "Prazo Máximo de Aplicação",
    "Classificação de Risco",
 
]

# 3. Criação do DataFrame
df_limites = pd.DataFrame(data=dados_limites, columns=colunas_limites)
df_risco = pd.DataFrame(data=dados_risco, columns=colunas_risco)
df_risco = df_risco.sort_values(by="Índice RiskBank", ascending=False).reset_index(drop=True)
df_risco["Índice RiskBank"] = df_risco["Índice RiskBank"].apply(lambda x: fmt_br(x, 2))

#/* ============================================================================
#---------------------CABEÇALHO E DATA---------------------
#   ============================================================================ */

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<h1 style="color: #0B2F13; margin: 0;">Limites Operacionais - Instituições Financeiras</h1>', unsafe_allow_html=True)

with col2:
    ultima_data_disponivel = data['DATA_COTACAO'].max().date()
    primeira_data_disponivel = data['DATA_COTACAO'].min().date()
    ajuda_data_input = f"As datas disponíveis estão entre {primeira_data_disponivel.strftime('%d/%m/%Y')} e {ultima_data_disponivel.strftime('%d/%m/%Y')}."
    st.date_input(
        "Data posição",
        value=st.session_state.data_selecionada,
        format="DD/MM/YYYY",
        help=ajuda_data_input,
        min_value=primeira_data_disponivel,
        max_value=ultima_data_disponivel,
        key='data_selecionada')

st.space()


# Verificar se existem dados na data selecionada
datas_disponiveis = sorted(data['DATA_COTACAO'].dt.date.unique())

if st.session_state.data_selecionada not in datas_disponiveis:
    # Encontrar data anterior mais próxima
    data_anterior = None
    data_posterior = None
    
    for d in reversed(datas_disponiveis):
        if d < st.session_state.data_selecionada:
            data_anterior = d
            break
    
    # Encontrar data posterior mais próxima
    for d in datas_disponiveis:
        if d > st.session_state.data_selecionada:
            data_posterior = d
            break
    
    # Montar mensagem de aviso
    msg_aviso = f"**Nenhum dado disponível para {st.session_state.data_selecionada.strftime('%d/%m/%Y')}.**\n\n"
    if data_anterior:
        msg_aviso += f"Data anterior mais próxima: **{data_anterior.strftime('%d/%m/%Y')}**\n"
    if data_posterior:
        msg_aviso += f"\nData posterior mais próxima: **{data_posterior.strftime('%d/%m/%Y')}**"
    
    st.warning(msg_aviso)


#---------------------DESCRIÇÃO--------------------------------
container = st.container(border=True)
container.write('Este relatório tem por objetivo estabelecer e monitorar limites de aplicação em Títulos e Valores'
        ' Mobiliários de Renda Fixa emitidos ou coobrigados por Instituições Financeiras, em conformidade'
        ' com a legislação vigente e as diretrizes da Política de Investimentos da Ceres.')



#---------------------EXPORTAR PDF---------------------
df_exibir = df_limites.copy()

df_filtrado = data[data["DATA_COTACAO"].dt.date == st.session_state.data_selecionada].copy()
df_filtrado = df_filtrado.drop(columns=["TESOURARIA"])

# Calcular totais para exportação
data_temp = data.copy()

total_alocacao_26 = 100000000

condicao = (
    (data_temp["DATA_AQUISICAO"] >= pd.to_datetime('2026-01-01')) & 
    (data_temp["DATA_COTACAO"] == pd.to_datetime(st.session_state.data_selecionada))
)

condicao2 = (
    (data_temp["DATA_COTACAO"] == pd.to_datetime(st.session_state.data_selecionada))
)

total_alocacao = data_temp.loc[condicao, 'FINANCEIRO_AQUISICAO'].sum()

total_exposicao = data_temp.loc[condicao2, 'EXPOSICAO'].sum()



# ============= PREPARAR DATAFRAME PARA EXPORTAÇÃO (ANTES DO PDF) =============
df_filtrado['DATA_AQUISICAO'] = pd.to_datetime(df_filtrado['DATA_AQUISICAO'])


df_filtrado['TIPO'] = df_filtrado['DATA_AQUISICAO'].apply(
    lambda x: 'ALOCACAO_2026' if x >= pd.to_datetime('2026-01-01') else 'ALOCACAO_ANTIGA'
)

df_filtrado['FINANCEIRO_AQUISICAO_2026'] = np.where(
    df_filtrado['TIPO'] == 'ALOCACAO_2026', 
    df_filtrado['FINANCEIRO_AQUISICAO'],
    0
    
)

df_filtrado["EXPOSICAO_2026"] = np.where(
    df_filtrado['TIPO'] == 'ALOCACAO_2026', 
    df_filtrado['EXPOSICAO'],
    0
    
)


grp_expo = df_filtrado.groupby('EMISSOR')['EXPOSICAO'].sum()
grp_expo_26 = df_filtrado.groupby('EMISSOR')['EXPOSICAO_2026'].sum()
grp_alocacao_2026 = df_filtrado.groupby('EMISSOR')['FINANCEIRO_AQUISICAO_2026'].sum()


df_exibir['EXPOSICAO_2026'] = df_exibir['EXPOSICAO_2026'].fillna(df_exibir['ID_MITRA'].map(grp_expo_26)).astype('float64')
df_exibir['EXPOSICAO'] = df_exibir['EXPOSICAO'].fillna(df_exibir['ID_MITRA'].map(grp_expo)).astype('float64')
df_exibir['FINANCEIRO_AQUISICAO'] = df_exibir['ID_MITRA'].map(grp_alocacao_2026).fillna(0).astype('float64')




df_exibir['LIMITE_ALOCACAO_2026'] = df_exibir['LIMITE_ALOCACAO_2026'] - df_exibir['FINANCEIRO_AQUISICAO']

# Definir todas as colunas a exibir (sem ID_MITRA e INSTITUICAO_FINANCEIRA)
colunas_exibir = ["EXPOSICAO", "EXPOSICAO_2026", "FINANCEIRO_AQUISICAO","LIMITE_ALOCACAO_2026"]

df_principal_exibir = df_exibir[["ID_MITRA", "INSTITUICAO_FINANCEIRA"] + colunas_exibir]


# ===============================================================================
col1, col2, col3 = st.columns([3, 1, 1])
with col3:
 
        
        # Reprocessar dados para o plano selecionado (igual ao código de múltiplos PDFs)
        df_filtrado_unico = data[(data["DATA_COTACAO"].dt.date == st.session_state.data_selecionada)].copy()
        
        if len(df_filtrado_unico) > 0:
            # Preparar dados com TIPO (ALOCAÇÃO 2026 vs EXPOSICAO_ANTIGA)
            df_filtrado_unico['DATA_AQUISICAO'] = pd.to_datetime(df_filtrado_unico['DATA_AQUISICAO'])
            df_filtrado_unico['TIPO'] = df_filtrado_unico['DATA_AQUISICAO'].apply(
                lambda x: 'ALOCAÇÃO 2026' if x >= pd.to_datetime('2026-01-01') else 'EXPOSICAO_ANTIGA'
            )
            
            # Agrupar por emissor
            grp_emissor_unico = df_filtrado_unico.pivot_table(
                index='EMISSOR', 
                columns='TIPO', 
                values='EXPOSICAO', 
                aggfunc='sum'
            ).reset_index()
            
            grp_emissor_unico = grp_emissor_unico.fillna(0)
            grp_emissor_unico.columns.name = None
            
            if 'ALOCAÇÃO 2026' not in grp_emissor_unico.columns:
                grp_emissor_unico['ALOCAÇÃO 2026'] = 0.0
            if 'EXPOSICAO_ANTIGA' not in grp_emissor_unico.columns:
                grp_emissor_unico['EXPOSICAO_ANTIGA'] = 0.0
            
            grp_emissor_unico['EXPOSICAO'] = grp_emissor_unico['EXPOSICAO_ANTIGA'] + grp_emissor_unico['ALOCAÇÃO 2026']

            grp_expo_26_unico = df_filtrado_unico.loc[
                df_filtrado_unico['DATA_AQUISICAO'] >= pd.to_datetime('2026-01-01')
            ].groupby('EMISSOR')['EXPOSICAO'].sum()

            grp_alocacao_2026_unico = df_filtrado_unico.loc[
                df_filtrado_unico['DATA_AQUISICAO'] >= pd.to_datetime('2026-01-01')
            ].groupby('EMISSOR')['FINANCEIRO_AQUISICAO'].sum()
            
            # Preparar df_exibir para o plano único
            df_exibir_unico = df_limites.copy()
            
            df_exibir_unico['EXPOSICAO'] = df_exibir_unico['EXPOSICAO'].fillna(
                df_exibir_unico['ID_MITRA'].map(grp_emissor_unico.set_index('EMISSOR')['EXPOSICAO'])
            ).astype('float64')

            df_exibir_unico['EXPOSICAO_2026'] = df_exibir_unico['ID_MITRA'].map(
                grp_expo_26_unico
            ).fillna(0).astype('float64')

            df_exibir_unico['FINANCEIRO_AQUISICAO'] = df_exibir_unico['ID_MITRA'].map(
                grp_alocacao_2026_unico
            ).fillna(0).astype('float64')

            df_exibir_unico['LIMITE_ALOCACAO_2026'] = df_exibir_unico['LIMITE_ALOCACAO_2026'] - df_exibir_unico['FINANCEIRO_AQUISICAO']
            
            # Selecionar apenas colunas necessárias para o PDF
            colunas_exibir_principal_unico = ["ID_MITRA",
                                    "INSTITUICAO_FINANCEIRA",
                                    "EXPOSICAO",
                                    "EXPOSICAO_2026",
                                    "FINANCEIRO_AQUISICAO",
                                    "LIMITE_ALOCACAO_2026"]
            
            df_principal_exibir_unico = df_exibir_unico[colunas_exibir_principal_unico].copy()
        else:
            df_principal_exibir_unico = pd.DataFrame()
        
        # Calcular valores dos cards para o PDF
        df_plano_temp = data[(data["DATA_COTACAO"].dt.date == st.session_state.data_selecionada)].copy()
        total_exp_pdf = df_plano_temp['EXPOSICAO'].sum() if len(df_plano_temp) > 0 else 0
        total_aloc_pdf = df_plano_temp[df_plano_temp['DATA_AQUISICAO'] >= pd.to_datetime('2026-01-01')]['FINANCEIRO_AQUISICAO'].sum() if len(df_plano_temp) > 0 else 0
        total_exp_26_plano_pdf = df_plano_temp[df_plano_temp['DATA_AQUISICAO'] >= pd.to_datetime('2026-01-01')]['EXPOSICAO'].sum() if len(df_plano_temp) > 0 else 0

        # Gerar PDF com dados do plano específico
        df_grafico_pdf = df_principal_exibir_unico[df_principal_exibir_unico["EXPOSICAO"] > 0] if not df_principal_exibir_unico.empty else pd.DataFrame()
        pdf_bytes = gerar_pdf_limites_operacionais(
            df_principal_exibir_unico,
            data_posicao=st.session_state.data_selecionada,
            titulo_relatorio="Limites Operacionais -",
            disponivel_alocacao_26=100000000,
            total_exposicao=total_exp_pdf,
            total_exposicao_26=total_exp_26_plano_pdf,
            alocado_26 =total_alocacao,
            df_risco=df_risco
        )
        
        st.download_button(
            label="Baixar PDF",
            data=pdf_bytes,
            file_name=f"limites_operacionais_{st.session_state.data_selecionada.strftime('%d%m%Y')}.pdf",
            mime="application/pdf",
            width='stretch',
            type="primary",
            key="download_pdf_unico"
        )
    

st.divider()
#==================================================================
#----------------------CARDS--------------------------------------
#==================================================================
total_exposicao = float(df_filtrado['EXPOSICAO'].sum() or 0)
total_exposicao_26 = float(df_filtrado[df_filtrado['DATA_AQUISICAO'] >= pd.to_datetime('2026-01-01')]['EXPOSICAO'].sum() or 0)



col1, col2 = st.columns([1,1])


with col1:
    with st.container(border=True):
        card_titulo('Posição')
        st.metric(label="Geral", value=f"R$ {fmt_br(total_exposicao, 2)}")

with col2:
    with st.container(border=True):
        card_titulo('Posição')
        st.metric(label="2026", value=f"R$ {fmt_br(total_exposicao_26, 2)}")

gasto_card("Plano de Alocação", total_alocacao, total_alocacao_26)





#-------------TABELA ANALÍTICO----------------
# Preparar dados para tabela expansível
df_filtrado['DATA_AQUISICAO'] = pd.to_datetime(df_filtrado['DATA_AQUISICAO'])

# Define os nomes exatos das colunas com base na data de corte (01/01/2026)
df_filtrado['TIPO'] = df_filtrado['DATA_AQUISICAO'].apply( lambda x: 'ALOCAÇÃO 2026' if x >= pd.to_datetime('2026-01-01') else 'EXPOSICAO_ANTIGA'
)

grp_emissor = df_filtrado.pivot_table(
    index='EMISSOR', 
    columns='TIPO', 
    values='EXPOSICAO', 
    aggfunc='sum'
).reset_index()


grp_emissor = grp_emissor.fillna(0)
grp_emissor.columns.name = None

if 'ALOCAÇÃO 2026' not in grp_emissor.columns:
    grp_emissor['ALOCAÇÃO 2026'] = 0.0
if 'EXPOSICAO_ANTIGA' not in grp_emissor.columns:
    grp_emissor['EXPOSICAO_ANTIGA'] = 0.0

grp_emissor['EXPOSICAO'] = grp_emissor['EXPOSICAO_ANTIGA'] + grp_emissor['ALOCAÇÃO 2026']




df_exibir = df_limites.copy()

df_exibir['EXPOSICAO'] = df_exibir['EXPOSICAO'].fillna(df_exibir['ID_MITRA'].map(grp_emissor.set_index('EMISSOR')['EXPOSICAO'])
).astype('float64')

df_exibir['ALOCAÇÃO 2026'] = df_exibir['ID_MITRA'].map(grp_emissor.set_index('EMISSOR')['ALOCAÇÃO 2026']).fillna(0).astype('float64')

# Agrupar produtos por EMISSOR
grp_produto = df_filtrado.groupby(["EMISSOR", "PRODUTO", "DATA_AQUISICAO", "VENCIMENTO"]).agg({'FINANCEIRO_AQUISICAO': 'sum', 'EXPOSICAO': 'sum', 'TAXA_AQUISICAO': 'mean', 'INDEXADOR': lambda x: x.mode()[0]}).reset_index()
# Ordenar por data de vencimento
grp_produto['Tx. Aquisição'] = grp_produto['INDEXADOR'].astype(str).str.cat(grp_produto['TAXA_AQUISICAO'].apply(lambda x: f"{x:.2f}%"), sep=" + ")
grp_produto = grp_produto.sort_values("DATA_AQUISICAO", ascending=True)


# Preparar colunas para produtos
colunas_produto = ["PRODUTO", "DATA_AQUISICAO", "VENCIMENTO", "Tx. Aquisição", "FINANCEIRO_AQUISICAO","EXPOSICAO"]





tab1, tab2 = st.tabs(["Limites Operacionais", "Classificação de Risco"])
with tab1:
    # ======================================================================
    #-------------------------TABELA EXPANSÍVELHTML-------------------------
    # ======================================================================

    # Calcular largura das colunas dinamicamente
    num_colunas = len(colunas_exibir)
    grid_template = " ".join([f"1fr" for _ in range(num_colunas)])

    # Grid template para produtos com coluna Produto aumentada (3fr em vez de 2fr)
    grid_template_produtos_completo = "3fr 1fr 1fr 1fr 1fr 1fr"  # Produto mais avançada

    # ========== TAMANHO DA FONTE DA TABELA ==========
    tamanho_fonte_tabela = "14px"  
    # ===============================================

    st.html(f"""
    <style>
        .tabela-full {{ 
            width: 100%; 
            border: none; 
            font-family: 'Figtree', sans-serif; 
            font-size: {tamanho_fonte_tabela}; 
            border-collapse: separate;
            border-spacing: 0;
            border-radius: 10px;
            overflow: auto;
            background-color: transparent;
            min-width: 0;
            
        }}
        
        /* MEDIA QUERY PARA TELAS PEQUENAS */
        @media (max-width: 768px) {{
            .tabela-full {{
                font-size: 11px;
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
            }}
        }}
        
        /* CABEÇALHO VERDE */
        .th-master {{ 
            background-color: #0B2F13; 
            color: #A8EC7D; 
            display: grid; 
            grid-template-columns: 2fr {grid_template}; 
            flex-shrink: 0;
            align-items: center;
            padding-left: 20px;
        }}
        .th-master div {{ 
            padding: 12px; 
            text-align: center;
            font-family: 'Figtree', sans-serif;
            font-size: {tamanho_fonte_tabela};
            word-wrap: break-word;
            overflow-wrap: break-word;
            word-break: break-word;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 40px;
        }}
        .th-master div:first-child {{ 
            border-top-left-radius: 10px;
            text-align: left;
            justify-content: flex-start;
        }}
        .th-master div:last-child {{ 
            border-top-right-radius: 10px;
        }}
        
        @media (max-width: 768px) {{
            .th-master div {{
                padding: 8px;
                font-size: 11px;
                min-height: 35px;
            }}
        }}

        /* LINHA DE TOTAIS */
        .th-totais {{ 
            background-color: #0B2F13; 
            color: #A8EC7D; 
            display: grid; 
            grid-template-columns: 2fr {grid_template}; 
            margin-top: 10px;
            flex-shrink: 0;
            align-items: center;
        }}
        .th-totais div {{ 
            padding: 12px; 
            text-align: center;
            font-family: 'Figtree', sans-serif;
            font-size: {tamanho_fonte_tabela};
            font-weight: bold;
            word-wrap: break-word;
            overflow-wrap: break-word;
            word-break: break-word;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 40px;
        }}
        .th-totais div:first-child {{ 
            text-align: left;
            justify-content: flex-start;
        }}
        
        @media (max-width: 768px) {{
            .th-totais div {{
                padding: 8px;
                font-size: 11px;
                min-height: 35px;
            }}
        }}

        /* ESTRUTURA GERAL */
        details {{ width: 100%; }}
        details[open] {{ margin-bottom: 15px; }}
        summary {{ list-style: none; cursor: pointer; align-items: center; }}
        summary::-webkit-details-marker {{ display: none; }}
        .col-val {{ 
            text-align: center; 
            padding: 10px; 
            height: 100%;
            font-family: 'Figtree', sans-serif;
            font-size: {tamanho_fonte_tabela};
            word-wrap: break-word;
            overflow-wrap: break-word;
            word-break: break-word;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 40px;
           
        }}
        
        @media (max-width: 768px) {{
            .col-val {{
                padding: 6px;
                font-size: 11px;
                min-height: 35px;
            }}
        }}

        /* ÍCONES E ALINHAMENTO */
        .label-box {{ 
            display: flex; 
            align-items: center; 
            padding-left: 10px;
            font-family: 'Figtree', sans-serif;
            font-size: 13px;
            word-wrap: break-word;
            overflow-wrap: break-word;
            word-break: break-word;
            min-height: 40px;
            padding-top: 10px;
            padding-bottom: 10px;
        }}
        
        @media (max-width: 768px) {{
            .label-box {{
                padding-left: 5px;
                font-size: 11px;
                min-height: 35px;
            }}
        }}
        
        .icon {{ 
            width: 25px; 
            text-align: center; 
            font-family: monospace; 
            font-weight: bold; 
            margin-right: 5px;
            flex-shrink: 0;
        }}

        /* INSTITUIÇÃO: ÍCONE + - apenas quando tem produtos */
        .row-inst {{ 
            background-color: transparent; 
            transition: background-color 0.2s ease;
            align-items: center;
        }}
        .row-inst:hover {{
            background-color: rgba(1, 104, 55, 0.05);
        }}
        details[open] > summary.row-inst {{
            background-color: rgba(1, 104, 55, 0.05);
        }}
        .row-inst.com-produtos .icon::before {{ content: '+'; color: #016837; }}
        details[open] > .row-inst.com-produtos .icon::before {{ content: '−'; }}
        
        /* INSTITUIÇÃO SEM PRODUTOS: sem ícone */
        .row-inst.sem-produtos {{ 
            background-color: transparent; 
            cursor: pointer;
            transition: background-color 0.2s ease;
            align-items: center;
        }}
        .row-inst.sem-produtos:hover {{
            background-color: rgba(1, 104, 55, 0.05);
        }}
        
        /* ÚLTIMA INSTITUIÇÃO: borda verde escuro */
        .row-inst.sem-produtos:last-child,
        details:last-child > summary {{
            border-bottom: 14px solid #0B2F13;
        }}

        /* CABEÇALHO PRODUTOS */
        .th-produtos {{ 
            background-color: #FBFCEC; 
            display: grid; 
            grid-template-columns: {grid_template_produtos_completo}; 
            margin-left: 0px; 
            margin-right: 0px;
            margin-top: 5px;
            border-bottom: 1px solid #ddd;
            align-items: center;
        }}
        .th-produtos div {{ 
            padding: 10px; 
            text-align: center;
            font-family: 'Source Serif Pro', serif;
            font-size: {tamanho_fonte_tabela};
            font-style: italic;   
            font-weight: bold;
            word-wrap: break-word;
            overflow-wrap: break-word;
            word-break: break-word;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 35px;
        }}
        .th-produtos div:first-child {{ 
            text-align: left;
            justify-content: flex-start;
            padding-left: 40px;
        }}
        .th-produtos div:last-child {{ border-right: none; }}
        
        @media (max-width: 768px) {{
            .th-produtos {{
                margin-left: 0px;
                margin-right: 0px;
            }}
            .th-produtos div {{
                padding: 6px;
                font-size: 11px;
                min-height: 30px;
            }}
        }}

        /* PRODUTO */
        .row-prod {{ 
            background-color: transparent; 
            display: grid; 
            grid-template-columns: {grid_template_produtos_completo}; 
            margin-left: 0px; 
            margin-right: 0px; 
            margin-top: 1px;
            transition: background-color 0.2s ease;
            border-bottom: 1px solid #eee;
            align-items: center;
        }}
        .row-prod div {{ 
            padding: 8px; 
            text-align: center;
            font-family: 'Figtree', sans-serif;
            font-size: {tamanho_fonte_tabela};
            font-style: normal;
            font-weight: 80;
            border-right: 1px solid #eee;
            word-wrap: break-word;
            overflow-wrap: break-word;
            word-break: break-word;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 35px;
        }}
        .row-prod div:last-child {{ border-right: none; }}
        .row-prod div:first-child {{ 
            text-align: left;
            justify-content: flex-start;
            padding-left: 40px;
        }}
        .row-prod:hover {{
            background-color: rgba(1, 104, 55, 0.03);
        }}
        
        @media (max-width: 768px) {{
            .row-prod {{
                margin-left: 0px;
                margin-right: 0px;
            }}
            .row-prod div {{
                padding: 5px;
                font-size: 12px;
                min-height: 30px;
            }}
        }}
    </style>
    """)

    # Mapping de nomes de colunas para exibição
    nome_colunas_exibir = {
        "EXPOSICAO": "Posição R$",
        "EXPOSICAO_2026": "Posição 2026 R$",
        "FINANCEIRO_AQUISICAO": "Alocação 2026 R$",
        "LIMITE_ALOCACAO_2026": "Limite Operacinal R$",
        
    }

    # Montagem do HTML
    html = '<div class="tabela-full"><div class="th-master"><div>Instituição</div>'
    for col in colunas_exibir:
        html += f'<div>{nome_colunas_exibir.get(col, col)}</div>'
    html += '</div>'

    for idx, row in df_principal_exibir.iterrows():
        id_mitra = row['ID_MITRA']
        
        # Filtrar produtos para esta instituição
        produtos_instituicao = grp_produto[grp_produto['EMISSOR'] == id_mitra]
        tem_produtos = len(produtos_instituicao) > 0
        
        # NÍVEL 1: INSTITUIÇÃO
        if tem_produtos:
            # Com produtos: usar <details> expansível com ícone +
            html += f"""
        <details>
            <summary class="row-inst com-produtos" style="display: grid; grid-template-columns: 2fr {grid_template}; align-items: center;">
                <div class="label-box"><span class="icon"></span> {row['INSTITUICAO_FINANCEIRA']}</div>"""
        else:
            # Sem produtos: apenas mostrar com classe sem-produtos
            html += f"""
        <div class="row-inst sem-produtos" style="display: grid; grid-template-columns: 2fr {grid_template}; align-items: center;">
            <div class="label-box"><span style="width: 25px;"></span> {row['INSTITUICAO_FINANCEIRA']}</div>"""
        
        # Adicionar valores de todas as colunas
        for col in colunas_exibir:
            lim_plano = 100000000
            valor = row[col]
            if pd.isna(valor) or valor == 0:
                valor_fmt = "—"
            elif col == "EXPOSICAO" and pd.notna(valor):
                valor_fmt = f"{fmt_br(valor, 2)}"
            elif col == "EXPOSICAO_2026" and pd.notna(valor):
                valor_fmt = f"{fmt_br(valor, 2)}"
            elif col == "FINANCEIRO_AQUISICAO" and pd.notna(valor):
                valor_fmt = f"{fmt_br(valor, 2)}"
            elif col == "LIMITE_ALOCACAO_2026" and pd.notna(valor):
                if valor == lim_plano:
                   valor_fmt = f"{fmt_br(valor, 2)}"
                else: 
                    valor_fmt = f"<strong>{fmt_br(valor, 2)}</strong>"
            elif pd.notna(valor) :
                valor_fmt = str(valor)
            else:
                valor_fmt = "—"
            html += f'<div class="col-val">{valor_fmt}</div>'
        
        if tem_produtos:
            html += """</summary>"""
        else:
            html += """</div>"""
        
        if tem_produtos:
            # Cabeçalho de produtos - COM GRID ESPECÍFICO DE 6 COLUNAS
            html += f"""<div class="th-produtos"><div>Produto</div><div>Aquisição</div><div>Vencimento</div><div>Tx. Aquisição</div><div>Fin. Aquisição</div><div>Posição</div></div>"""
            
            for _, prod in produtos_instituicao.iterrows():
                # Converter Timestamp para DATA_AQUISICAO
                aquisicao = prod['DATA_AQUISICAO']
                if pd.notna(aquisicao):
                    if hasattr(aquisicao, 'strftime'):
                        aquisicao_str = aquisicao.strftime('%d/%m/%Y')
                    else:
                        aquisicao_str = str(aquisicao)
                else:
                    aquisicao_str = '—'
                
                # Converter Timestamp para string de vencimento
                vencimento = prod['VENCIMENTO']
                if pd.notna(vencimento):
                    if hasattr(vencimento, 'strftime'):
                        vencimento_str = vencimento.strftime('%d/%m/%Y')
                    else:
                        vencimento_str = str(vencimento)
                else:
                    vencimento_str = '—'
                
                exposicao_fmt = fmt_br(prod['EXPOSICAO'], 2) if pd.notna(prod['EXPOSICAO']) else "—"
                financeiro_aquisicao_fmt = fmt_br(prod['FINANCEIRO_AQUISICAO'], 2) if pd.notna(prod['FINANCEIRO_AQUISICAO']) else "—"
                
                # NÍVEL 2: PRODUTO - COM GRID ESPECÍFICO DE 6 COLUNAS
                html += f"""
                <div class="row-prod">
                    <div>{prod['PRODUTO']}</div>
                    <div>{aquisicao_str}</div>
                    <div>{vencimento_str}</div>
                    <div><strong>{prod['Tx. Aquisição']}</strong></div>
                    <div><strong>{financeiro_aquisicao_fmt}</strong></div>
                    <div><strong>{exposicao_fmt}</strong></div>
                </div>"""
            
            html += "</details>" # Fecha Instituição

    html += "</div>"
    st.html(html)
    st.markdown('<p style="font-family: \'Source Serif Pro\', serif; font-style: italic; margin-left: 20px;">(*) Não Elegíveis desde maio/2026, (**) Não elegível desde maio/2025.</p>', unsafe_allow_html=True)
   
    
    
with tab2:
    # Mapeamento de nomes de colunas para exibição melhorada    
    html_tabela_risco = gerar_tabela_estilizada(df_risco)
    st.html(html_tabela_risco)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<p style="font-family: \'Source Serif Pro\', serif; font-style: italic; margin-left: 20px;">(*) Não Elegíveis desde maio/2026, (**) Não elegível desde maio/2025.</p>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div style="display:flex; justify-content:flex-end; width:100%;">'f'<p style="font-family: \'Source Serif Pro\', serif; font-style: italic; margin:0;">'
                    f'Fonte: Riskbank - atualização Junho/2025.'
                    f'</p></div>',
                    unsafe_allow_html=True
                    )
    st.space(size='stretch')
#------------------------ANALÍTICO--------------------------------

col1 = st.columns(1)[0]
with col1.container(border=True):
    df_grafico = df_principal_exibir[df_principal_exibir["EXPOSICAO"] > 0].copy()

    # --- Cálculo da Porcentagem do Total ---
    total_exposicao = df_grafico["EXPOSICAO"].sum()
    
    if total_exposicao > 0:
        # Cria textos separados para mostrar o valor absoluto em cima e a porcentagem abaixo
        df_grafico["VALOR_BARRA"] = df_grafico["EXPOSICAO"].apply(
            lambda valor: f"{valor:,.2f}".replace('.', '_').replace(',', '.').replace('_', ',')
        )
        df_grafico["PCT_BARRA"] = df_grafico["EXPOSICAO"].apply(
            lambda valor: f"{(valor / total_exposicao) * 100:.1f}%"
        )
    else:
        df_grafico["VALOR_BARRA"] = "0,00"
        df_grafico["PCT_BARRA"] = "0,0%"

    # --- Cálculo de Altura Dinâmica ---
    altura_dinamica = max(200, len(df_grafico) * 70)

    # Criando o gráfico com Plotly
    barras_ifs = go.Figure()
    config = {'displayModeBar': False}

    # 1. Inversão dos eixos e orientação no Trace
    barras_ifs.add_trace(go.Bar(
        x=df_grafico["INSTITUICAO_FINANCEIRA"],  
        y=df_grafico["EXPOSICAO"],              
        customdata=df_grafico[["VALOR_BARRA", "PCT_BARRA"]],
        
        marker=dict(
            color='#0B2F13',
            cornerradius=7,
            line=dict(width=0) 
        )
    ))

    for _, row in df_grafico.iterrows():
        barras_ifs.add_annotation(
            x=row["INSTITUICAO_FINANCEIRA"],
            y=row["EXPOSICAO"],
            text=f"<b>{row['PCT_BARRA']}</b><br>{row['VALOR_BARRA']}",
            showarrow=False,
            yanchor="bottom",
            
            font=dict(
                family="Figtree",
                size=12,
                color="#0B2F13",
            ),
        )

    
    max_exposicao = df_grafico["EXPOSICAO"].max() if not df_grafico.empty else 100
    
    barras_ifs.update_layout(
        title='Exposição por Emissor',
        bargap=0.04, 
        height=altura_dinamica,  
        autosize=True,
        separators=',.',

        font=dict(
            family="Figtree", 
            size=14,          
            color="#333333"   
        ),
        
        # 2. Configurações nos Eixos
        xaxis=dict(
            categoryorder='total descending', 
            showline=False,      
            showgrid=False,      
            showticklabels=True,
            automargin=True 
        ),

        yaxis=dict(
            showgrid=False, 
            zeroline=False,
            showticklabels=False,
            range=[0, max_exposicao * 1.05]
        ),

        hovermode='closest',
        hoverlabel=dict(
            bgcolor='#FBFCEC',
            bordercolor='#0B2F13',
            font=dict(
                family='Figtree',
                size=12,
                color='#0B2F13',
            ),
        ),

        margin=dict(r=20, t=45, b=30, l=20), 
        plot_bgcolor='rgba(0,0,0,0)'
    )

    barras_ifs.update_traces(
        hovertemplate=(
            '<b>%{x}</b><br>'
            'Valor: R$ %{customdata[0]}<br>'
            'Participação: %{customdata[1]}'
            '<extra></extra>'
        )
    )

    # Exibindo o gráfico no Streamlit
    st.plotly_chart(barras_ifs, config=config, width='stretch')