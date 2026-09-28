# Due Diligence

O módulo de Due Diligence registra gestoras, preenchimentos e respostas de questionários. A interface é composta por páginas de cadastro/configuração, acompanhamento e respostas.

## Fluxo operacional

1. Cadastre ou revise a gestora na página de configurações.
2. Confira o CNPJ e o status da gestora.
3. Faça o preenchimento no Google Sheets configurado.
4. Execute ou aguarde a ETL para importar preenchimentos e respostas.
5. Consulte a página de Due Diligence e acompanhe as respostas.
6. Atualize respostas quando necessário.

## Regras importantes

- O CNPJ é normalizado antes da gravação.
- CNPJs duplicados são rejeitados.
- O status válido da gestora é `ATIVO` ou `INATIVO`.
- E-mails longos são abreviados visualmente, sem alterar o valor armazenado.
- URLs presentes nas respostas são transformadas em links seguros para abertura em nova aba.

## Estrutura local

O banco SQLite fica em `src/data/ddq.db`. As tabelas principais são:

- `gestora`: cadastro e status;
- `preenchimento`: envio e versão do questionário;
- `resposta`: pergunta, resposta e score.

A ETL fica em `src/utils/ddq_utils/etl.py`, o CRUD em `crud.py` e a conexão SQLite em `db_ddq.py`. Esses componentes não dependem diretamente do Streamlit e podem ser usados em rotinas automatizadas ou testes.

## Falhas comuns

- **Planilha sem colunas identificadoras**: confira CNPJ, carimbo de data/hora e razão social.
- **Gestora não encontrada**: cadastre a gestora com o mesmo CNPJ normalizado antes de executar a ETL.
- **Erro de autenticação**: revise o arquivo de credenciais e as variáveis do conector.
- **Dados antigos**: confirme a data de envio e se a ETL foi executada após a atualização da planilha.
