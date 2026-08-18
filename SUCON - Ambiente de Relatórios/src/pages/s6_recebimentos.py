import streamlit as st
import pandas as pd
from utils.queries.recebimentos import buscar_dados_recebimentos
from datetime import date
import plotly.express as px
import numpy as np 
import altair as alt
from utils.helpers import _NOMES_PLANOS, titulo_section, card_geral, de_para_produto, renderizar_tabela_estilizada



dados_recebimentos = buscar_dados_recebimentos()
dados_recebimentos['TESOURARIA'] = dados_recebimentos['TESOURARIA'].replace(_NOMES_PLANOS)
dados_recebimentos["DATA_PAGAMENTO"] = dados_recebimentos["DATA_PAGAMENTO"].dt.date
dados_recebimentos["DATA_COTACAO"] = dados_recebimentos["DATA_COTACAO"].dt.date
dados_recebimentos["VENCIMENTO"] = dados_recebimentos["VENCIMENTO"].dt.date

#==================CABEÇALHO=========================
st.set_page_config(layout="wide")


st.html("""
<style>
    /* Remove o padding lateral e superior do bloco principal */
    .block-container {
        padding-top: 3.8rem;
        padding-left: 0rem;
        padding-right: 0rem;
    }

    .st-key-meu-container {
        background-color: #0B2F13;
        border-radius: 0px;
        padding: 30px 20px 30px 20px;
        width: 100%;
        box-sizing: border-box;
    }
    
    /* Container do conteúdo COM padding lateral */
    .st-key-conteudo {
        padding-left: 3rem;
        padding-right: 3rem;
    }
        
</style>
""")

with st.container(key="meu-container"):
    st.html("""
        <p style="text-align:center; color:#FAFBEB; margin:0 0; font-size: clamp(20px, 3vw, 29px); font-weight:400;">
            Monitoramento de Recebimentos - 
            <span style='color:#A8EC7D; font-family:"Source Serif 4",serif; font-style:italic; font-weight:600;'>
                Ceres
            </span>
        </p>
    """)

with st.container(horizontal_alignment="center", gap=None, key="conteudo"):
    with st.container(width=1200):


  
        import altair as alt

        import sys
        import importlib.metadata

        st.write("### sys.path")
        for p in sys.path:
            st.code(p)

        st.write("### Todas as distribuições 'altair' encontradas")
        for dist in importlib.metadata.distributions():
            if dist.metadata["Name"] and dist.metadata["Name"].lower() == "altair":
                st.write(f"Versão: {dist.version} — Localização: {dist._path}")

        col1, col2 = st.columns([.80, 0.20])
        with col2:

            #===========SELETOR DE DATA DO RELATÓRIO================
            data_cotacao_selecionada = st.date_input("Selecione a Data do Relatório:",
                                                    min_value=dados_recebimentos['DATA_COTACAO'].min(),
                                                    max_value=dados_recebimentos['DATA_COTACAO'].max(),
                                                    format="DD/MM/YYYY",
                                                    value=dados_recebimentos['DATA_COTACAO'].max())

            dados_filtrados = dados_recebimentos[
                (dados_recebimentos['DATA_COTACAO'] == data_cotacao_selecionada)
            ]

            if dados_filtrados.empty:
                st.warning("Nenhum dado encontrado para a data selecionada.")
                st.stop()
        #===========SELETOR DE TESOURARIA================



        with col1: 
            opcoes = dados_filtrados['TESOURARIA'].unique()
            tesouraria_selecionada = st.multiselect("Selecione a Tesouraria:", opcoes, default=opcoes.tolist())

            dados_filtrados = dados_filtrados[
                (dados_filtrados['TESOURARIA'].isin(tesouraria_selecionada)) &
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
    
        titulo_section(
                            "Recebimento Programados",
                            help="Visualização do fluxo de recebimentos programados, com base na data de pagamento."
                        )
        st.write(f"*Clique em uma célula para filtrar os recebimentos do mês/ano selecionado. Período de recebimentos programados: {dados_recebimentos['DATA_COTACAO'].min().year} a {dados_recebimentos['DATA_PAGAMENTO'].max().year}*")
      
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

        )

        # 5. Exibição no Streamlit com captura do evento de clique
        evento = st.altair_chart(
            heatmap.configure_view(stroke=None).configure_axis(grid=False), 
            width='stretch',
            on_select="rerun"  # <--- REEXECUTA O STREAMLIT AO CLICAR
        )

        # Dicionário de conversão para transformar o texto no número do mês
        depara_meses = {
            "Jan": 1, "Fev": 2, "Mar": 3, "Abr": 4, "Mai": 5, "Jun": 6,
            "Jul": 7, "Ago": 8, "Set": 9, "Out": 10, "Nov": 11, "Dez": 12
        }

        # 6. Salvar e Processar o Mês/Ano Selecionado
        if evento and "selection" in evento and "celula_selecionada" in evento["selection"]:
            pontos_selecionados = evento["selection"]["celula_selecionada"]
            
            if pontos_selecionados:
                item = pontos_selecionados[0]

                st.session_state['ano_selecionado'] = item['Ano_Int']
                
                # Converte o nome do mês (ex: "Ago") para o número (ex: 8)
                mes_nome = item['Mês']
                st.session_state['mes_selecionado'] = depara_meses.get(mes_nome)

        #****************FILTRO DADOS****************   
        # 0. Data mais antiga disponível -> tirada da PRÓPRIA lista de opções
        data_inicial = min(opcao_filtro_pagemento)

        # 1. "Primeira vez" checando existência E valor None
        primeira_vez = st.session_state.get('ano_selecionado') is None

        ano_sel = st.session_state.get('ano_selecionado') or data_inicial.year
        mes_sel = st.session_state.get('mes_selecionado') or data_inicial.month

        # 2. Pílulas visíveis no filtro (todas as datas do ano selecionado)
        opcao_filtro = [d for d in opcao_filtro_pagemento if d.year == ano_sel]

        # 3. Pílulas marcadas por DEFAULT
        if primeira_vez:
            default_pills = [d for d in opcao_filtro if d == data_inicial]
        elif mes_sel is not None:
            default_pills = [d for d in opcao_filtro if d.month == mes_sel]
        else:
            default_pills = opcao_filtro

        # 4. Key única e determinística -> evita herdar valor salvo de sessão anterior
        pills_key = f"pills_{ano_sel}_{mes_sel}_{'init' if primeira_vez else 'sel'}"
     
        filtro_pagamento = st.pills(
            "Filtrar por data de pagamento:",
            options=opcao_filtro,
            format_func=lambda d: d.strftime("%d/%m/%Y"),
            selection_mode="multi",
            default=default_pills,
            key=pills_key
        )

        dados_filtrados = dados_filtrados[dados_filtrados['DATA_PAGAMENTO'].isin(filtro_pagamento)]
        if not filtro_pagamento:
            st.warning("Selecione pelo menos uma opção.")
            st.stop()
        titulo_section(
                                    ""
                                     )
        st.space('xxsmall')
        #METRICS

        col1, col2, col3, col4, col5 = st.columns(5)
        col1, col2, col3, col4, col5 = st.columns(5)

        with col2:
            card_geral('Próximo Recebimento',
                    str(dados_filtrados['DATA_PAGAMENTO'].min().strftime("%d/%m/%Y"))
            )
            
        with col3:
            card_geral(
                "Financeiro Presente",
                f"{dados_filtrados['FINANCEIRO_PRESENTE'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            )
                
        with col4:
            card_geral(
                "Financeiro Projetado",
                f"{dados_filtrados['FINANCEIRO_PROJETADO'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            )
            
        st.space('xxsmall')



        #GRAFICO BARRAS

        titulo_section(
                                "Recebimento Programados",
                                mostrar_linha=False,
                                help="Visualização do fluxo de recebimentos programados, com base na data de pagamento selecionada."
                            )
        # 1. Agrupamento
        dados_agrupados = (
            dados_filtrados
            .groupby(['DATA_PAGAMENTO', 'PAGAMENTO_DU'])[['FINANCEIRO_PRESENTE', 'FINANCEIRO_PROJETADO']]
            .sum()
            .reset_index()
        )

        # 2. Formato Long
        df_melted = dados_agrupados.melt(
            id_vars=['DATA_PAGAMENTO', 'PAGAMENTO_DU'],
            value_vars=['FINANCEIRO_PRESENTE', 'FINANCEIRO_PROJETADO'],
            var_name='Tipo_Financeiro',
            value_name='Valor'
        )

        df_melted['Tipo_Financeiro'] = df_melted['Tipo_Financeiro'].replace({
            'FINANCEIRO_PRESENTE': 'Financeiro Presente',
            'FINANCEIRO_PROJETADO': 'Financeiro Projetado'
        })

        # Formatação COMPLETA em R$ (usada só no tooltip, com precisão total)
        def formatar_real_completo(valor):
            return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        df_melted['Valor_Fmt_Completo'] = df_melted['Valor'].apply(formatar_real_completo)

        # Formatação ABREVIADA em R$ (1M / 850mil) -> usada no rótulo da barra, evita sobreposição
        def formatar_real_abrev(valor):
            sinal = '-' if valor < 0 else ''
            valor_abs = abs(valor)
            if valor_abs >= 1_000_000:
                texto = f"{valor_abs/1_000_000:.1f}".replace('.', ',')
                return f"{sinal}R$ {texto}M"
            elif valor_abs >= 1_000:
                texto = f"{valor_abs/1_000:.0f}"
                return f"{sinal}R$ {texto}mil"
            else:
                texto = f"{valor_abs:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                return f"{sinal}R$ {texto}"

        df_melted['Valor_Fmt'] = df_melted['Valor'].apply(formatar_real_abrev)

        # Formatação da data para exibição
        df_melted['DATA_FMT'] = pd.to_datetime(df_melted['DATA_PAGAMENTO']).dt.strftime('%d/%m/%Y')

        qtd_datas = df_melted['DATA_PAGAMENTO'].nunique()
        largura_dinamica = max(800, qtd_datas * 90)

        # Expressão Vega para o eixo Y também abreviar (1M / 850mil), com vírgula decimal (padrão BR)
        label_expr_eixo_y = (
            "datum.value >= 1000000 ? "
            "'R$ ' + replace(format(datum.value/1000000, '.1f'), '.', ',') + 'M' "
            ": datum.value >= 1000 ? "
            "'R$ ' + format(datum.value/1000, '.0f') + 'mil' "
            ": 'R$ ' + format(datum.value, ',.0f')"
        )

        # 3. Base do gráfico
        base = alt.Chart(df_melted).encode(
            x=alt.X(
                'DATA_FMT:O',
                title=None,
                sort=alt.EncodingSortField(field='DATA_PAGAMENTO', order='ascending'),
                axis=alt.Axis(labelAngle=0, grid=False, domainColor='#D9D9D9', tickColor='#D9D9D9')
            ),
            xOffset='Tipo_Financeiro:N',
            y=alt.Y(
                'Valor:Q',
                title='',
                axis=alt.Axis(
                    grid=False,
                    domainColor='#D9D9D9',
                    tickColor='#D9D9D9',
                    labelExpr=label_expr_eixo_y
                )
            ),
            color=alt.Color(
                'Tipo_Financeiro:N',
                legend=alt.Legend(orient='top', direction='horizontal', title=None),
                scale=alt.Scale(
                    domain=['Financeiro Presente', 'Financeiro Projetado'],
                    range=['#2E7D32', '#B0B0B0']  # verde = real, cinza = projetado
                )
            ),
            tooltip=[
                alt.Tooltip('DATA_FMT:N', title='Data recebimento'),
                alt.Tooltip('PAGAMENTO_DU:N', title='Dias uteis para recebimento'),
            
                alt.Tooltip('Valor_Fmt_Completo:N', title='Valor')  # tooltip mostra o valor exato, sem abreviar
            ]
        )

        # 4. Barras
        barras = base.mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)

        # 5. Rótulos diretos, agora abreviados -> texto mais curto, menos chance de invadir barra vizinha
        rotulos = base.mark_text(
            align='center',
            baseline='bottom',
            dy=-4,
            fontSize=11,
            fontWeight='bold',
            color='#404040'
        ).encode(
            text='Valor_Fmt:N'
        )

        # 6. Combina camadas
        chart = alt.layer(barras, rotulos).configure_view(
            stroke=None
        ).configure_axis(
            grid=False,
            labelColor='#595959',
            titleColor='#595959'
        )

        st.altair_chart(chart, width='stretch')
        #================TABELA FINAL=======================
        # 1. Definição do mapeamento de renomeação de colunas
        DE_PARA_COLUNAS = {
            'TESOURARIA': 'Tesouraria',
            'PRODUTO': 'Produto',
            'CODIGO': 'Código',
            'GRUPO': 'Grupo',
            'DATA_PAGAMENTO': 'Data Pagamento',
            'PAGAMENTO_DU': 'Pagamento DU',
            'FINANCEIRO_PRESENTE': 'Fin. Presente',
            'FINANCEIRO_PROJETADO': 'Fin. Projetado',
            'VENCIMENTO': 'Vencimento'
        }

        grupos = [str(g) for g in dados_filtrados['GRUPO'].dropna().unique().tolist()]

        # Colunas padrão para exibição
        colunas_todas = ['TESOURARIA', 'PRODUTO', 'CODIGO', 'GRUPO', 'DATA_PAGAMENTO', 'PAGAMENTO_DU', 'FINANCEIRO_PRESENTE', 'FINANCEIRO_PROJETADO', 'VENCIMENTO']
        colunas_especifica = ['PRODUTO', 'CODIGO', 'DATA_PAGAMENTO', 'PAGAMENTO_DU', 'FINANCEIRO_PRESENTE', 'FINANCEIRO_PROJETADO', 'VENCIMENTO']

        # 2. Seleciona as colunas com base na tesouraria
        colunas_exibir = colunas_todas if tesouraria_selecionada == 'Todas' else colunas_especifica

        # 3. Processa e formata toda a base UMA ÚNICA VEZ
        df_processado = dados_filtrados.copy()

        if not df_processado.empty:
            # Mapeamento do produto
            if 'PRODUTO' in df_processado.columns:
                df_processado['PRODUTO'] = df_processado['PRODUTO'].apply(de_para_produto)
            
            # Formatação de Datas
            for col_data in ['DATA_PAGAMENTO', 'VENCIMENTO']:
                if col_data in df_processado.columns:
                    df_processado[col_data] = pd.to_datetime(df_processado[col_data], errors='coerce').dt.strftime('%d/%m/%Y')
            
            # Formatação Financeira (trata nulos)
            for col_fin in ['FINANCEIRO_PRESENTE', 'FINANCEIRO_PROJETADO']:
                if col_fin in df_processado.columns:
                    df_processado[col_fin] = df_processado[col_fin].apply(
                        lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if pd.notnull(x) else ""
                    )
                    
            # Formatação de Pagamento DU
            if 'PAGAMENTO_DU' in df_processado.columns:
                df_processado['PAGAMENTO_DU'] = df_processado['PAGAMENTO_DU'].apply(
                    lambda x: f"{int(x)} dias úteis" if pd.notnull(x) else ""
                )

        # 4. Exibição no Streamlit
        if len(grupos) == 0:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")

        else:
            tabs = st.tabs([str(g) for g in grupos])
            
            for tab, grupo in zip(tabs, grupos):
                with tab:
                    # Filtra o grupo atual
                    df_grupo = df_processado[df_processado['GRUPO'].astype(str) == str(grupo)]
                    
                    # Filtra apenas as colunas válidas
                    cols_validas = [c for c in colunas_exibir if c in df_grupo.columns]
                    
                    # Garante que 'GRUPO' fique por último na exibição (se presente nas colunas)
                    if 'GRUPO' in cols_validas:
                        cols_validas.remove('GRUPO')
                        cols_validas.append('GRUPO')
                        
                    df_exibir = df_grupo[cols_validas].copy()
                    
                    # Renomeia para o formato Title Case (Primeira em Maiúsculo / Nomes ajustados)
                    df_exibir = df_exibir.rename(columns=DE_PARA_COLUNAS)
                    
                    # Renderiza a tabela estilizada com colunas renomeadas e 'Grupo' ao final
                    renderizar_tabela_estilizada(
                        df_exibir, 
                        rolagem=True, 
                        altura_max='600px', 
                        ordenacao=True
                    )