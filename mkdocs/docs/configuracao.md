# Configuração e segurança

## Arquivo `.env`

O arquivo `.env` deve ficar na raiz do projeto, ao lado de `src/`. O código carrega esse arquivo antes de abrir as conexões.

Variáveis usadas pelo acesso Oracle:

```dotenv
MITRA_USER=usuario
MITRA_PASSWORD=senha
MITRA_DSN=conexao
```

> Atualmente `src/utils/db_oracle.py` monta o DSN Oracle com host, porta e service name definidos no código. A variável `MITRA_DSN` aparece no exemplo de configuração, mas não substitui essa montagem na implementação atual.

Variáveis usadas pelo acesso SQL Server:

```dotenv
CERES_SERVER=servidor
CERES_USER=usuario
CERES_PASSWORD=senha
DB=banco
```

O módulo SQL Server usa o **ODBC Driver 18**, conexão criptografada e `TrustServerCertificate=yes`.

## Google Sheets e Due Diligence

O módulo de Due Diligence usa as credenciais do Google e as configurações do conector em `src/utils/ddq_utils/con_gsheets.py`. Consulte esse módulo para os nomes exatos das variáveis exigidas no ambiente instalado.

Mantenha `credentials/` fora de ambientes públicos. Em produção, prefira um cofre de segredos ou uma identidade de serviço gerenciada.

## Banco local da Due Diligence

O banco SQLite do módulo é criado automaticamente em:

```text
src/data/ddq.db
```

A criação das tabelas pode ser executada por `src/utils/ddq_utils/criar_db.py`. O arquivo é local e contém dados operacionais; trate-o como informação sensível e faça backup conforme a política da equipe.

## Checklist de segurança

- confirme que `.env` está ignorado pelo Git;
- remova tokens e credenciais que tenham sido expostos;
- conceda apenas permissões de leitura às consultas que não precisam escrever;
- não copie dados reais para exemplos, testes ou screenshots;
- revise o acesso ao SQLite e à pasta `credentials/`;
- após trocar uma credencial, valide o acesso com uma consulta simples.
