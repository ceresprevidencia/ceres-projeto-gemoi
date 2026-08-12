import streamlit as st
import pandas as pd
from utils.queries.recebimentos import buscar_dados_recebimentos
from datetime import date
import plotly.express as px
import numpy as np 
import altair as alt



dados_recebimentos = buscar_dados_recebimentos()
dados_recebimentos["DATA_PAGAMENTO"] = dados_recebimentos["DATA_PAGAMENTO"].dt.date
dados_recebimentos["DATA_COTACAO"] = dados_recebimentos["DATA_COTACAO"].dt.date
dados_recebimentos["VENCIMENTO"] = dados_recebimentos["VENCIMENTO"].dt.date


#===========SELETOR DE DATA DO RELATÓRIO================
data_cotacao_selecionada = st.date_input("Selecione a Data do Relatório:",
                                        min_value=dados_recebimentos['DATA_COTACAO'].min(),
                                        max_value=dados_recebimentos['DATA_COTACAO'].max(),
                                        value=dados_recebimentos['DATA_COTACAO'].max())

dados_filtrados = dados_recebimentos[
    (dados_recebimentos['DATA_COTACAO'] == data_cotacao_selecionada)
]

#===========SELETOR DE TESOURARIA================

opcoes = np.append(["Todas"], dados_filtrados['TESOURARIA'].unique())
tesouraria_selecionada = st.selectbox("Selecione a Tesouraria:", opcoes)

if tesouraria_selecionada == "Todas":
    dados_filtrados = dados_filtrados[
        dados_filtrados['DATA_COTACAO'] == data_cotacao_selecionada
    ]
else:
    dados_filtrados = dados_filtrados[
        (dados_filtrados['TESOURARIA'] == tesouraria_selecionada) &
        (dados_filtrados['DATA_COTACAO'] == data_cotacao_selecionada)
    ]
#DADOS AGRUPADOS

dados_agrupados = (
    dados_filtrados
    .groupby('DATA_PAGAMENTO')[['FINANCEIRO_PRESENTE', 'FINANCEIRO_PROJETADO']]
    .sum()
    .reset_index()
)

#===========SELETOR DE PERIODO================
opcao_filtro_pagemento = dados_agrupados['DATA_PAGAMENTO'].tolist()


#============VIEW FLUXO DE RECEBIMENTOS================
st.title("Projeção de Pagamentos Mensais (Estilo GitHub)")

# 1. Sua lista de entradas (exemplo vindo da sua variável)
# opcao_filtro_pagemento = dados_agrupados['DATA_PAGAMENTO'].tolist()

# 2. Processamento dos Dados Reais
df_real = pd.DataFrame({'DATA_PAGAMENTO': pd.to_datetime(opcao_filtro_pagemento)})

if not df_real.empty and df_real['DATA_PAGAMENTO'].notna().any():
    df_real['Ano_Int'] = df_real['DATA_PAGAMENTO'].dt.year
    df_real['Mes_Num'] = df_real['DATA_PAGAMENTO'].dt.month
    df_real['Data_Fmt'] = df_real['DATA_PAGAMENTO'].dt.strftime('%d/%m/%Y')

    # Contagem e Agrupamento das Datas Exatas por Mês/Ano
    agrupado = df_real.groupby(['Ano_Int', 'Mes_Num']).agg(
        Qtd_Pagamentos=('DATA_PAGAMENTO', 'count'),
        Datas_Lista=('Data_Fmt', lambda x: ", ".join(x))  # Une as datas em uma string
    ).reset_index()

    ano_min = int(df_real['Ano_Int'].min())
    ano_max = int(df_real['Ano_Int'].max())
else:
    agrupado = pd.DataFrame(columns=['Ano_Int', 'Mes_Num', 'Qtd_Pagamentos', 'Datas_Lista'])
    ano_min = 2026
    ano_max = 2026

# 3. Construção do Grid Dinâmico (Mês/Ano)
anos_int = list(range(ano_min, ano_max + 1))
anos_curtos = [f"'{str(ano)[-2:]}" for ano in anos_int]
meses_nome = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", 
              "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

grid = []
for ano_val in anos_int:
    ano_curto_str = f"'{str(ano_val)[-2:]}"
    for mes_idx, mes_nome in enumerate(meses_nome, start=1):
        grid.append({
            "Ano_Int": ano_val,
            "Ano": ano_curto_str,
            "Mes_Num": mes_idx,
            "Mês": mes_nome
        })

df_grid = pd.DataFrame(grid)

# Cruzamento do Grid com os Dados Agrupados
df_final = pd.merge(df_grid, agrupado, on=['Ano_Int', 'Mes_Num'], how='left')
df_final['Qtd_Pagamentos'] = df_final['Qtd_Pagamentos'].fillna(0).astype(int)
df_final['Datas_Lista'] = df_final['Datas_Lista'].fillna("Sem recebimentos")

# 4. Configuração da Seleção por Clique e Gráfico Altair
github_colors = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]

# Cria parâmetro de seleção para capturar o clique do usuário
selecao_clique = alt.selection_point(name="celula_selecionada", fields=['Ano_Int', 'Mês'])

base = alt.Chart(df_final).encode(
    x=alt.X('Ano:O', 
        title=None, 
        sort=anos_curtos,
        axis=alt.Axis(
            orient='top',
            labelAngle=0,
            labelOverlap=False,
            grid=False
        )
    ),
    y=alt.Y('Mês:O', 
        title=None, 
        sort=meses_nome,
        axis=alt.Axis(
            labelOverlap=False,
            grid=False
        )
    )
)

heatmap = base.mark_rect(
    cornerRadius=3,
    stroke="white",
    strokeWidth=2,
).encode(
    color=alt.Color('Qtd_Pagamentos:Q', 
        scale=alt.Scale(range=github_colors),
        legend=None  # <--- LEGENDA DESATIVADA
    ),
    # Tooltip detalhado com as datas exatas
    tooltip=[
        alt.Tooltip('Ano_Int:N', title='Ano'),
        alt.Tooltip('Mês:N', title='Mês'),
        alt.Tooltip('Qtd_Pagamentos:Q', title='Qtd. Pagamentos'),
        alt.Tooltip('Datas_Lista:N', title='Datas do Recebimento')
    ]
).add_params(
    selecao_clique  # <--- HABILITA O CLIQUE
).properties(
    width='container',
    height=420,
    title=alt.TitleParams(
        text=f"Projeção Real de Pagamentos ('{str(ano_min)[-2:]} a '{str(ano_max)[-2:]})",
        anchor='start',
        fontSize=16
    )
)

# 5. Exibição no Streamlit com captura do evento de clique
evento = st.altair_chart(
    heatmap.configure_view(stroke=None).configure_axis(grid=False), 
    use_container_width=True,
    on_select="rerun"  # <--- REEXECUTA O STREAMLIT AO CLICAR
)

# 6. Salvar e Processar o Mês/Ano Selecionado
if evento and "selection" in evento and "celula_selecionada" in evento["selection"]:
    pontos_selecionados = evento["selection"]["celula_selecionada"]
    
    if pontos_selecionados:
        item = pontos_selecionados[0]
        st.session_state['ano_selecionado'] = item['Ano_Int']
        st.session_state['mes_selecionado'] = item['Mês']
        
#****************FILTRO DADOS****************   
opcao_filtro = [d for d in opcao_filtro_pagemento if d.year == st.session_state['ano_selecionado']]

# 2. Exibe no st.pills com a lista filtrada
filtro_pagamento = st.pills(
    "Filtrar por Pagamento DU:",
    options=opcao_filtro,
    format_func=lambda d: d.strftime("%d/%m/%Y"),  # Deixa o texto bonito na pílula (ex: 12/08/2026)
    selection_mode="multi",
    default=opcao_filtro[0]
)

dados_filtrados = dados_filtrados[dados_filtrados['DATA_PAGAMENTO'].isin(filtro_pagamento)]


#METRICS

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Próximo Recebimento", 
          str(dados_filtrados['DATA_PAGAMENTO'].min(),
          ))

with col2:
    st.metric("Financeiro Presente", 
          f"R$ {dados_filtrados['FINANCEIRO_PRESENTE'].sum():,.2f}"          )
with col3:
    st.metric("Financeiro Projetado", 
          f"R$ {dados_filtrados['FINANCEIRO_PROJETADO'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
          )




#GRAFICO BARRAS

dados_agrupados = (
    dados_filtrados
    .groupby(['DATA_PAGAMENTO', 'PAGAMENTO_DU'])[['FINANCEIRO_PRESENTE', 'FINANCEIRO_PROJETADO']]
    .sum()
    .reset_index()
)



fig = px.bar(
    dados_agrupados,
    x='DATA_PAGAMENTO',
    y=['FINANCEIRO_PRESENTE', 'FINANCEIRO_PROJETADO'],
    barmode='group',  # Força o posicionamento LADO A LADO
    title='Comparativo: Financeiro Presente vs. Projetado',
    labels={
        'DATA_PAGAMENTO': 'Data de Pagamento',
        'value': 'Valor (R$)',
        'variable': 'Tipo de Financeiro'
    }
)
st.plotly_chart(fig)

#================TABELA FINAL=======================
grupos = [str(g) for g in dados_filtrados['GRUPO'].dropna().unique().tolist()]
# Colunas padrão para exibição
colunas_todas = ['TESOURARIA', 'PRODUTO', 'CODIGO', 'GRUPO', 'DATA_PAGAMENTO', 'PAGAMENTO_DU', 'FINANCEIRO_PRESENTE', 'FINANCEIRO_PROJETADO', 'VENCIMENTO']
colunas_especifica = ['PRODUTO', 'CODIGO', 'GRUPO', 'DATA_PAGAMENTO', 'PAGAMENTO_DU', 'FINANCEIRO_PRESENTE', 'FINANCEIRO_PROJETADO', 'VENCIMENTO']

# Seleciona as colunas com base na tesouraria
colunas_exibir = colunas_todas if tesouraria_selecionada == 'Todas' else colunas_especifica

if len(grupos) == 0:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")

elif len(grupos) == 1:
    grupo = grupos[0]
    tabs = st.tabs([grupo])  # ✅ lista com um elemento
    with tabs[0]:
        df_grupo = dados_filtrados[dados_filtrados['GRUPO'].astype(str) == grupo]
        cols_validas = [c for c in colunas_exibir if c in df_grupo.columns]
        st.dataframe(  # ✅ dentro da aba
            df_grupo[cols_validas].sort_values(by='DATA_PAGAMENTO', ascending=True),
            use_container_width=True
        )

else:
    # Se houver 2 ou mais grupos, exibe com abas
    tabs = st.tabs(grupos)
    for tab, grupo in zip(tabs, grupos):
        with tab:
            df_grupo = dados_filtrados[dados_filtrados['GRUPO'].astype(str) == grupo]
            
            cols_validas = [c for c in colunas_exibir if c in df_grupo.columns]
            st.dataframe(df_grupo[cols_validas].sort_values(by='DATA_PAGAMENTO', ascending=True), use_container_width=True)