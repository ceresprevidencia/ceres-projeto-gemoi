# Navegação e relatórios

A navegação é registrada em `src/app.py` com `st.navigation`. Algumas páginas ficam ocultas do menu porque funcionam como etapas internas ou páginas auxiliares; elas continuam acessíveis pelo fluxo da aplicação.

## Início

A página inicial apresenta os indicadores e referências gerais do ambiente. Use-a como ponto de entrada para validar se as fontes estão respondendo.

### Ticker de rentabilidade

O ticker da página inicial é carregado por `src/utils/queries/benchmark_ticker_pg_inicial.py`. Ele consulta a view `BI_CERES.dbo.VW_RENTABILIDADE` para a performance consolidada e cruza o resultado com `BI_CERES.dbo.VW_META_ATUARIAL`.

O componente:

- identifica a última competência disponível;
- exibe o acumulado anual (`YTD`) por plano;
- compara o resultado com o benchmark anual (`BENCH_YTD`);
- mantém os dados em cache por 24 horas.

Se o ticker estiver vazio ou desatualizado, confirme a conexão SQL Server, a última competência nas views e o cache da aplicação. A página inicial possui uma opção de manutenção para limpar o cache com autorização.

## Enquadramento

- **Enquadramento Planos**: compara posições e limites dos planos com a Política de Investimentos ou com a Resolução 4.994.
- **Fundos**: consulta o enquadramento de fundos.

As linhas com status `DESENQUADRADO` recebem destaque visual. O relatório também pode ser exportado em PDF.

## Risco de Crédito

**Limites Operacionais** monitora exposição em títulos e valores mobiliários de renda fixa emitidos ou coobrigados por instituições financeiras. A tela permite selecionar a data, visualizar posições gerais e de 2026, consultar a classificação de risco e baixar um PDF.

## Risco de Mercado

- **Planos**: apresenta VaR paramétrico, limites internos, cenários de stress e resumo por plano.
- **Risco Mercado Ativos**: detalha o risco dos ativos consultados.

A data escolhida precisa possuir dados. Quando a seleção não está disponível, a aplicação informa datas próximas ou interrompe a exibição.

## Rentabilidade

A tela **Rentabilidade - Planos** cruza rentabilidade mensal, acumulada, IPCA, benchmarks e rentabilidade projetada. Selecione o plano e a data de cotação; os cards e gráficos são recalculados para o contexto escolhido.

## Risco de Liquidez

**Recebimentos** mostra o fluxo programado por data de pagamento. Use a data do relatório e o filtro de tesouraria para restringir a visão; o calendário permite explorar os meses com recebimentos.

## Exportáveis

A **Central de Exportáveis** é uma área separada para visuais que podem ser consultados e exportados. O módulo atualmente registrado é o **RRAS**, implementado em `src/modulos_exportaveis/rras.py`.

O RRAS consulta os dados de risco de mercado por plano e apresenta posição, VaR em reais, VaR percentual, limite interno e status. A lista de visuais é registrada em `src/pages/s5_exportaveis.py`; novos visuais precisam ser adicionados ao dicionário `visuais_disponiveis`.

## Convenções de uso

- Datas são exibidas no padrão brasileiro `DD/MM/YYYY`.
- Valores financeiros usam `R$` e separador decimal brasileiro.
- Se uma fonte não retornar linhas, a tela informa que não há dados para o filtro.
- Valide a data de posição antes de comparar relatórios de períodos diferentes.
