# Arquitetura

## Camadas

```text
src/app.py
  -> páginas Streamlit em src/pages/
      -> consultas em src/utils/queries/
          -> conexões em src/utils/db_oracle.py e db_sqlserver.py
      -> helpers, gráficos e PDFs em src/utils/
      -> módulos exportáveis em src/modulos_exportaveis/

Projetos auxiliares no mesmo nível do manual:

```text
bot-monitoramento/
    -> pipeline E1-E5 e monitores independentes E6/E7
bot-mercado-de-credito/
    -> coleta de Google Alerts, classificação LLM e envio ao Google Chat
```
```

## Entrada e navegação

`src/app.py` configura logo, páginas e navegação. Cada página é um script Streamlit que carrega os dados, aplica filtros e renderiza a interface.

## Consultas

Os módulos em `src/utils/queries/` encapsulam consultas específicas. O padrão esperado é uma função `buscar_dados_*` que retorna um `pandas.DataFrame`. Isso mantém a página desacoplada do SQL e facilita a validação do formato de dados.

Principais grupos:

| Grupo | Exemplos |
| --- | --- |
| Enquadramento | `enquadramento.py` |
| Limites | `lim_operacionais.py` |
| Rentabilidade | `rent_planos.py`, `rent_produtos.py`, `rent_grupos.py`, `rent_mensal_planos.py` |
| Mercado | `risco_mercado_planos.py`, `risco_mercado_ativos.py`, `risco_mercado_segmentos.py` |
| Apoio | `ipca.py`, `bench_acumulado.py`, `benchmark_ticker_pg_inicial.py` |

## Dados e apresentação

A camada de apresentação usa `pandas`, Plotly, Altair, Matplotlib e componentes HTML/CSS do Streamlit. Helpers em `utils/helpers.py` padronizam nomes de planos, valores, percentuais, cores e componentes visuais.

## Alterações recomendadas

- mantenha credenciais fora do código;
- preserve o contrato das colunas retornadas pelas queries;
- faça cópia dos DataFrames antes de transformações destrutivas;
- atualize a documentação ao incluir uma página ou exportação;
- valide a página com dados vazios, data inválida e conexão indisponível.
- mantenha os projetos de bot documentados quando houver mudança no pipeline, nas credenciais ou nos destinos de alerta.
