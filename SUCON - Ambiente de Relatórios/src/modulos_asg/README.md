# Índice de Materialidade e Impacto ASG · Painel de Controle Ceres

Versão Streamlit do `indice_asg_carteira.html`, no padrão visual do Painel de Controle
(barra de navegação, faixa verde-escura com título, cards bege com ícone de informação,
painéis com borda fina e cards de segmento com anel).

## Rodar
    pip install -r requirements.txt
    streamlit run app.py

## Estrutura
    app.py                  entrada isolada (tema + navbar + página)
    .streamlit/config.toml  tema Ceres
    asg/parametros.py       DE-PARA, setores, matrizes de dupla materialidade, cenários, avaliação de referência
    asg/consolidacao.py     leitura do Estoque, look-through, exclusões, agregação, exportação Excel
    asg/materialidade.py    notas A/S/G, cálculo dos dois eixos, simulador de eventos
    asg/relatorio.py        Divulgação de Impactos ASG (HTML imprimível)
    asg/ui.py               CSS e componentes visuais Ceres
    asg/pagina.py           a tela (render())
    dados/                  notas_qualitativas_asg.json (criado no primeiro uso)

## Integrar ao Painel de Controle
Integrado ao SUCON - Ambiente de Relatórios como pacote `src/modulos_asg/`:

    src/pages/s7_indice_asg.py   wrapper no padrão das demais páginas (faixa verde + conteúdo 1200px)
    src/app.py                   st.Page(url_path="indice-asg") no grupo "ASG" do st.navigation
    src/pages/pg_inicial.py      card "ASG" na home

O wrapper chama `ui.aplicar_tema(integrado=True)` (não esconde o header/menu do app) e
`pagina.render(mostrar_hero=False)` (o cabeçalho é desenhado pela própria página).
As notas qualitativas ficam em `src/modulos_asg/dados/notas_qualitativas_asg.json`
(arquivo único, compartilhado por todos os usuários do servidor).

Calibração (pesos, setores, cenários, notas de referência) muda só em `parametros.py`.
