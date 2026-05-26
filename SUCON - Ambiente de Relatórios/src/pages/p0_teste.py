import streamlit as st
import pandas as pd

# 1. DADOS REAIS (Nível mais baixo: MARCAS)
# No seu script, você pode carregar isso de um Excel ou SQL
df_marcas = pd.DataFrame([
    # CATEGORIA A -> PRODUTO A
    {'Cat': 'LIMPEZA', 'Prod': 'Detergente', 'Marca': 'Limpol', 'Qtd': 50, 'Vl': 125.0, 'Vend': 20},
    {'Cat': 'LIMPEZA', 'Prod': 'Detergente', 'Marca': 'Ypê', 'Qtd': 50, 'Vl': 125.0, 'Vend': 20},
    # CATEGORIA A -> PRODUTO B
    {'Cat': 'LIMPEZA', 'Prod': 'Sabão', 'Marca': 'Omo', 'Qtd': 30, 'Vl': 450.0, 'Vend': 5},
    {'Cat': 'LIMPEZA', 'Prod': 'Sabão', 'Marca': 'Brilhante', 'Qtd': 20, 'Vl': 300.0, 'Vend': 5},
    # CATEGORIA B -> PRODUTO C
    {'Cat': 'ALIMENTOS', 'Prod': 'Arroz', 'Marca': 'Tio João', 'Qtd': 100, 'Vl': 2850.0, 'Vend': 50},
    {'Cat': 'ALIMENTOS', 'Prod': 'Arroz', 'Marca': 'Prato Fino', 'Qtd': 100, 'Vl': 3000.0, 'Vend': 50},
])
st.dataframe(df_marcas)  # Apenas para visualização inicial dos dados

# 2. AGREGANDO OS NÍVEIS (Matemática Automática)
# Totais por Produto
df_produtos = df_marcas.groupby(['Cat', 'Prod']).agg({'Qtd': 'sum', 'Vl': 'sum', 'Vend': 'sum'}).reset_index()
# Totais por Categoria
df_categorias = df_produtos.groupby('Cat').agg({'Qtd': 'sum', 'Vl': 'sum', 'Vend': 'sum'}).reset_index()

# 3. ESTILO CSS (Sóbrio, Verde Escuro e Alinhado)
st.html("""
<style>
    .tabela-full { width: 100%; border: 1px solid #333; font-family: sans-serif; font-size: 13px; border-collapse: collapse; }
    
    /* CABEÇALHO VERDE */
    .th-master { background-color: #064e3b; color: white; display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; font-weight: bold; border-bottom: 2px solid #333; }
    .th-master div { padding: 12px; border-right: 1px solid #444; text-align: center; }
    .th-master div:first-child { text-align: left; }

    /* ESTRUTURA GERAL */
    details { width: 100%; border-bottom: 1px solid #bcbcbc; }
    summary { list-style: none; cursor: pointer; display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; align-items: center; }
    summary::-webkit-details-marker { display: none; }
    .col-val { text-align: center; padding: 10px; border-left: 1px solid #bcbcbc; height: 100%; }

    /* ÍCONES E ALINHAMENTO */
    .label-box { display: flex; align-items: center; padding-left: 10px; }
    .icon { width: 25px; text-align: center; font-family: monospace; font-weight: bold; margin-right: 5px; }

    /* CATEGORIA: SETAS (▼ / ▲) */
    .row-cat { background-color: #f2f2f2; font-weight: bold; }
    .row-cat .icon::before { content: '▼'; color: #064e3b; }
    details[open] > .row-cat .icon::before { content: '▲'; }

    /* PRODUTO: MAIS/MENOS (+ / -) */
    .row-prod { background-color: #ffffff; border-top: 1px solid #eee; }
    .row-prod .icon { margin-left: 20px; }
    .row-prod .icon::before { content: '+'; color: #444; }
    details[open] > .row-prod .icon::before { content: '-'; }

    /* MARCA: LINHA FINAL */
    .row-marca { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; background-color: #fafafa; border-top: 1px dashed #ddd; font-style: italic; }
    .row-marca .label-box { padding-left: 55px; color: #666; }
</style>
""")

# 4. MONTAGEM DO HTML
html = '<div class="tabela-full"><div class="th-master"><div>HIERARQUIA (CAT > PROD > MARCA)</div><div>QTD</div><div>VALOR (R$)</div><div>VENDIDOS</div></div>'

for _, cat in df_categorias.iterrows():
    # NÍVEL 1: CATEGORIA
    html += f"""
    <details>
        <summary class="row-cat">
            <div class="label-box"><span class="icon"></span> {cat['Cat']}</div>
            <div class="col-val">{cat['Qtd']}</div>
            <div class="col-val">{cat['Vl']:,.2f}</div>
            <div class="col-val">{cat['Vend']}</div>
        </summary>"""
    
    prods = df_produtos[df_produtos['Cat'] == cat['Cat']]
    for _, prd in prods.iterrows():
        # NÍVEL 2: PRODUTO
        html += f"""
        <details style="margin-left: 0px;">
            <summary class="row-prod">
                <div class="label-box"><span class="icon"></span> {prd['Prod']}</div>
                <div class="col-val">{prd['Qtd']}</div>
                <div class="col-val">{prd['Vl']:,.2f}</div>
                <div class="col-val">{prd['Vend']}</div>
            </summary>"""
        
        marcas = df_marcas[(df_marcas['Cat'] == cat['Cat']) & (df_marcas['Prod'] == prd['Prod'])]
        for _, mrc in marcas.iterrows():
            # NÍVEL 3: MARCA (Linha final sem expansão)
            html += f"""
            <div class="row-marca">
                <div class="label-box">└ {mrc['Marca']}</div>
                <div class="col-val">{mrc['Qtd']}</div>
                <div class="col-val">{mrc['Vl']:,.2f}</div>
                <div class="col-val">{mrc['Vend']}</div>
            </div>"""
        
        html += "</details>" # Fecha Produto
    html += "</details>" # Fecha Categoria

html += "</div>"

st.title("Estoque Consolidado: Categoria > Produto > Marca")
st.html(html)


import streamlit as st
import time

st.title("Dashboard de Metas")

# Criando colunas para simular "Cards" lado a lado
col1, col2 = st.columns(2)

with col1:
    # O container com borda funciona como o nosso Card
    with st.container(border=True):
        st.subheader("Vendas 2026")
        
        # Métrica principal
        st.metric(label="Total Acumulado", value="R$ 85.000", delta="15% vs mês passado")
        
        # Barra de progresso (aceita valores de 0.0 a 1.0 ou de 0 a 100)
        progresso_vendas = 0.85
        st.progress(progresso_vendas, text=f"{int(progresso_vendas * 100)}% da meta atingida")

with col2:
    with st.container(border=True):
        st.subheader("Projetos Concluídos")
        st.metric(label="Sprint Atual", value="12 / 15", delta="-2 tarefas delay", delta_color="inverse")
        
        progresso_projetos = 12 / 15
        st.progress(progresso_projetos, text="Progresso da Sprint")



import streamlit as st
import plotly.graph_objects as go

with st.container(border=True):
    st.write("### Meta de Retenção de Clientes")
    
    # Criando um gráfico do tipo Gauge (Velocímetro)
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = 75,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Score de Satisfação", 'font': {'size': 16}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': "#1f77b4"}, # Cor da barra de progresso
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
        }
    ))
    
    # Ajustando o tamanho para caber direitinho no card
    fig.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=200)
    
    # Exibe o gráfico dentro do card
    st.plotly_chart(fig, use_container_width=True)




    import streamlit as st
from streamlit_elements import elements, mui, html

st.title("Cards de Progresso com Streamlit Elements")

# 1. Inicializa o ambiente do streamlit-elements
with elements("cards_de_progresso"):
    
    # Criamos uma linha (Grid) para organizar os nossos cards
    with mui.Grid(container=True, spacing=3):
        
        # --- CARD 1: PROGRESSO CIRCULAR ---
        with mui.Grid(item=True, xs=12, md=6): # Responsivo: 12 colunas no mobile, 6 no desktop
            
            # Criando o Card com elevação (sombra) e bordas arredondadas
            with mui.Card(variant="elevation", elevation=3, sx={"borderRadius": 3, "padding": 2}):
                
                mui.Typography("Meta de Faturamento", variant="h6", component="div", sx={"fontWeight": "bold"})
                mui.Typography("Q2 - 2026", variant="body2", color="text.secondary", sx={"mb": 2})
                
                # Container flexível para alinhar o gráfico e o texto lado a lado
                with mui.Box(sx={"display": "flex", "alignItems": "center", "justifyContent": "space-around", "minHeight": 120}):
                    
                    # O truque aqui é sobrepor o texto dentro do círculo de progresso
                    with mui.Box(sx={"position": "relative", "display": "inline-flex"}):
                        mui.CircularProgress(variant="determinate", value=78, size=100, thickness=5, color="success")
                        
                        with mui.Box(sx={"top": 0, "left": 0, "bottom": 0, "right": 0, "position": "absolute", "display": "flex", "alignItems": "center", "justifyContent": "center"}):
                            mui.Typography("78%", variant="h6", component="div", color="text.secondary", sx={"fontWeight": "bold"})
                    
                    # Detalhes textuais ao lado do progresso
                    with mui.Box():
                        mui.Typography("R$ 78.000", variant="h5", sx={"fontWeight": "bold", "color": "#2e7d32"})
                        mui.Typography("Meta: R$ 100.000", variant="caption", color="text.secondary")

        # --- CARD 2: PROGRESSO LINEAR ---
        with mui.Grid(item=True, xs=12, md=6):
            with mui.Card(variant="elevation", elevation=3, sx={"borderRadius": 3, "padding": 2}):
                
                mui.Typography("Performance da Equipe", variant="h6", component="div", sx={"fontWeight": "bold"})
                mui.Typography("Tarefas concluídas na Sprint", variant="body2", color="text.secondary", sx={"mb": 4})
                
                # Exibindo o valor atual e o total
                with mui.Box(sx={"display": "flex", "justifyContent": "between", "mb": 1}):
                    mui.Typography("Progresso", variant="body2", sx={"fontWeight": "medium"})
                    mui.Typography("42/60 Devs", variant="body2", color="text.secondary")
                
                # Barra de progresso linear estilizada (com altura maior)
                mui.LinearProgress(variant="determinate", value=70, sx={"height": 10, "borderRadius": 5, "mb": 2})
                
                mui.Typography("Faltam apenas 18 tarefas para fechar a meta!", variant="caption", color="warning.main")




import streamlit as st
from streamlit_elements import elements, mui

st.title("Cards com Alerta de Calor ⚡")

# 1. FUNÇÃO PARA ABORDAGEM EM DEGRADÊ REAL (HEXADECIMAL)
# Vai mudando suavemente de Verde -> Amarelo -> Laranja -> Vermelho
def calcular_cor_calor_hex(porcentagem):
    if porcentagem < 50:
        # Começa verde e vai virando amarelo (mistura de verde e vermelho)
        r = int((porcentagem / 50) * 255)
        g = 200
        b = 50
    else:
        # Vai de amarelo para vermelho puro (diminuindo o verde)
        r = 255
        g = int(200 - ((porcentagem - 50) / 50) * 200)
        b = 50
    return f"rgb({r}, {g}, {b})"


# 2. FUNÇÃO PARA ABORDAGEM POR ABAS DO MATERIAL UI
# Usa o sistema de cores nativo (Success, Warning, Error)
def calcular_cor_mui(porcentagem):
    if porcentagem < 50:
        return "success" # Verde
    elif porcentagem < 85:
        return "warning" # Laranja / Amarelo
    else:
        return "error"   # Vermelho


# --- SIMULAÇÃO DE PROGRESSO ---
# Controle deslizante para testar o efeito de calor em tempo real
progresso = st.slider("Ajuste o progresso para testar o nível de calor:", 0, 100, 88)


# --- RENDERIZAÇÃO DOS CARDS ---
with elements("cards_calor"):
    with mui.Grid(container=True, spacing=3):
        
        # --- CARD 1: DEGRADÊ SUAVE (HEXADECIMAL) ---
        with mui.Grid(item=True, xs=12, md=6):
            cor_atual_hex = calcular_cor_calor_hex(progresso)
            
            with mui.Card(variant="elevation", elevation=3, sx={"borderRadius": 3, "padding": 2}):
                mui.Typography("Temperatura do Servidor (Suave)", variant="h6", sx={"fontWeight": "bold"})
                mui.Typography("Mudança de tom precisa a cada %", variant="body2", color="text.secondary", sx={"mb": 3})
                
                with mui.Box(sx={"position": "relative", "display": "inline-flex", "justifyContent": "center", "width": "100%"}):
                    # Aplicamos a cor calculada no parâmetro 'sx={"color": ...}'
                    mui.CircularProgress(
                        variant="determinate", 
                        value=progresso, 
                        size=120, 
                        thickness=6, 
                        sx={"color": cor_atual_hex} 
                    )
                    with mui.Box(sx={"top": 0, "left": 0, "bottom": 0, "right": 0, "position": "absolute", "display": "flex", "alignItems": "center", "justifyContent": "center"}):
                        mui.Typography(f"{progresso}%", variant="h5", sx={"fontWeight": "bold", "color": cor_atual_hex})

        # --- CARD 2: CORES DO SISTEMA MUI (ESTÁGIOS) ---
        with mui.Grid(item=True, xs=12, md=6):
            cor_atual_mui = calcular_cor_mui(progresso)
            
            with mui.Card(variant="elevation", elevation=3, sx={"borderRadius": 3, "padding": 2}):
                mui.Typography("Uso de Armazenamento (Estágios)", variant="h6", sx={"fontWeight": "bold"})
                mui.Typography("Muda por faixas críticas (Verde/Laranja/Vermelho)", variant="body2", color="text.secondary", sx={"mb": 5})
                
                # Texto indicando o estado
                texto_alerta = "Estável" if progresso < 50 else "Atenção" if progresso < 85 else "CRÍTICO!"
                
                with mui.Box(sx={"display": "flex", "justifyContent": "space-between", "mb": 1}):
                    mui.Typography(texto_alerta, variant="body2", sx={"fontWeight": "bold"})
                    mui.Typography(f"{progresso} / 100 GB", variant="body2", color="text.secondary")
                
                # Aplicamos a cor mapeada direto no parâmetro 'color'
                mui.LinearProgress(
                    variant="determinate", 
                    value=progresso, 
                    color=cor_atual_mui, 
                    sx={"height": 12, "borderRadius": 5}
                )


import streamlit as st
from streamlit_elements import elements, mui

st.title("Cards com Cores de Métrica")

progresso = st.slider("Arraste para testar o nível de calor do card:", 0, 100, 90)

# Função para definir o fundo e a cor do texto baseado no calor
def obter_estilo_calor(porcentagem):
    if porcentagem < 50:
        return {"bg": "#e8f5e9", "texto": "#2e7d32", "barra": "success"} # Verde suave
    elif porcentagem < 85:
        return {"bg": "#fff3e0", "texto": "#ef6c00", "barra": "warning"} # Laranja suave
    else:
        return {"bg": "#ffebee", "texto": "#c62828", "barra": "error"}   # Vermelho suave (Alerta!)

estilo = obter_estilo_calor(progresso)

with elements("card_background_color"):
    with mui.Grid(container=True, spacing=2):
        with mui.Grid(item=True, xs=12, md=6):
            
            # Aplicamos a cor de fundo dinamicamente no 'sx' do Card
            with mui.Card(
                variant="elevation", 
                elevation=2, 
                sx={
                    "borderRadius": 3, 
                    "padding": 3, 
                    "backgroundColor": estilo["bg"], # <-- Cor do fundo muda aqui
                    "transition": "background-color 0.3s ease" # Suaviza a transição de cor
                }
            ):
                # Título do Card (usa a cor de texto combinando)
                mui.Typography(
                    "Temperatura do Servidor", 
                    variant="overline", 
                    sx={"fontWeight": "bold", "color": estilo["texto"], "fontSize": 12}
                )
                
                # Valor da Métrica
                mui.Typography(
                    f"{progresso}°C", 
                    variant="h3", 
                    sx={"fontWeight": "bold", "color": estilo["texto"], "my": 1}
                )
                
                # Barra de Progresso combinando
                mui.LinearProgress(
                    variant="determinate", 
                    value=progresso, 
                    color=estilo["barra"], 
                    sx={"height": 8, "borderRadius": 4, "backgroundColor": "rgba(0,0,0,0.05)"}
                )


import streamlit as st

def gasto_card(titulo: str, gasto: float, limite: float):
    pct = min(max(gasto / limite * 100, 0), 100)

    # Cor interpolada: verde → âmbar → vermelho
    def lerp(a, b, t): return a + (b - a) * t
    p = pct / 100
    if p <= 0.5:
        t = p / 0.5
        r, g, b = int(lerp(99,186,t)), int(lerp(196,117,t)), int(lerp(87,23,t))
    else:
        t = (p - 0.5) / 0.5
        r, g, b = int(lerp(186,226,t)), int(lerp(117,75,t)), int(lerp(23,74,t))
    color = f"rgb({r},{g},{b})"

    # Badge
    if pct < 50:   badge_bg, badge_fg = "#EAF3DE", "#3B6D11"
    elif pct < 75: badge_bg, badge_fg = "#FAEEDA", "#854F0B"
    elif pct < 90: badge_bg, badge_fg = "#FAECE7", "#993C1D"
    else:          badge_bg, badge_fg = "#FCEBEB", "#A32D2D"

    disponivel = limite - gasto
    pct_str = f"{pct:.0f}%"

    st.markdown(f"""
    <div style="background:#1e1e2e; border:1px solid rgba(255,255,255,0.08);
                border-radius:16px; padding:20px 24px; margin-bottom:12px; font-family:'Segoe UI',sans-serif;">

      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
        <div>
          <p style="color:#aaa; font-size:13px; margin:0 0 4px;">💳 {titulo}</p>
          <div style="display:flex; align-items:baseline; gap:6px;">
            <span style="font-size:22px; font-weight:600; color:{color if pct >= 90 else '#e0e0e0'};">
              R$ {gasto:,.2f}
            </span>
            <span style="font-size:14px; color:#888;">/ R$ {limite:,.2f}</span>
          </div>
        </div>
        <span style="background:{badge_bg}; color:{badge_fg}; font-size:12px; font-weight:600;
                     padding:4px 12px; border-radius:99px;">{pct_str}</span>
      </div>

      <div style="background:rgba(255,255,255,0.08); border-radius:99px; height:8px; overflow:hidden; margin-bottom:10px;">
        <div style="width:{pct}%; height:100%; background:{color}; border-radius:99px;
                    box-shadow:0 0 6px {color};"></div>
      </div>

      <div style="display:flex; justify-content:space-between;">
        <span style="font-size:12px; color:#666;">Disponível</span>
        <span style="font-size:12px; font-weight:500; color:{color if pct >= 75 else '#888'};">
          R$ {disponivel:,.2f}
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)


# --- Uso ---
st.title("💰 Limite de Gastos")

gasto = st.slider("Gasto atual (R$)", 0, 2000, 800, step=50)
gasto_card("Cartão Nubank", gasto, 2000)