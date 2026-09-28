# Bot de monitoramento

O projeto `bot-monitoramento/` coleta notícias, classifica conteúdo com LLM, extrai textos, identifica a gestora-alvo e envia alertas. Ele também possui monitores independentes para CVM e Ceres.

## Pipeline principal

O orquestrador é `executar_tudo.py`. A sequência prevista é:

| Etapa | Script | Responsabilidade |
| --- | --- | --- |
| E1 | `E1_extracao_DB.py` | Coleta feeds RSS/Google Alerts, resolve links, extrai metadados e grava novas notícias |
| E2 | `E2_interesse_DB.py` | Classifica interesse de `L0` a `L5` usando Groq |
| E3 | `E3_noticia_DB.py` | Extrai o texto principal das notícias relevantes com Newspaper |
| E4 | `E4_alvo_DB.py` | Avalia se a gestora é o alvo principal da notícia usando Groq |
| E5 | `E5_alerta_DB.py` | Envia alertas de notícias ao Google Chat |

A etapa E7 está registrada no orquestrador, mas sua chamada aparece comentada no código atual. A etapa E6 é o monitoramento da CVM.

## Monitores independentes

### E6: CVM

`E6_cvm_monitor_DB.py` consulta o site da CVM com Selenium para palavras-chave de gestoras. O banco SQLite `cvm_sent.db` evita o envio duplicado no mesmo dia por gestora e link. O alerta é enviado pelo webhook `CHAT_WEBHOOK_URL_MUNIN`.

### E7: Ceres

`E7_ceres_monitor_DB.py` consulta um feed RSS, escolhe o link mais recente ainda não enviado, gera um resumo com Groq e envia a mensagem ao Google Chat. O histórico é salvo em `sent_links.db`; o webhook esperado é `CHAT_WEBHOOK_URL_HALL`.

## Banco e persistência

O pipeline principal usa a tabela `noticias`, criada por `setup_db.py`. O banco pode ser SQLite ou outro backend compatível com SQLAlchemy por meio de `DB_URL`. Os monitores E6 e E7 usam bancos SQLite separados no diretório definido por `DATA_DIR`.

O `db_viewer.py` permite visualizar as tabelas dos três bancos:

```powershell
python db_viewer.py
```

Em CI/CD, monte um volume persistente para os bancos em `data/`; sem persistência, o histórico de deduplicação será perdido entre execuções.

## Configuração mínima

```dotenv
DB_URL=sqlite:///./data/noticias_pipeline.db
GROQ_API_KEY=chave-da-api
GROQ_MODEL=mixtral-8x7b-32768
CHAT_WEBHOOK_URL_SAURON=webhook-do-alerta-principal
CHAT_WEBHOOK_URL_MUNIN=webhook-do-monitor-cvm
CHAT_WEBHOOK_URL_HALL=webhook-do-monitor-ceres
DATA_DIR=./data
```

Os nomes podem variar por etapa. Consulte o script que será executado antes de alterar uma variável de produção.

## Execução

Instale as dependências:

```powershell
cd bot-monitoramento
python -m pip install -r requirements.txt
```

Inicialize o banco principal:

```powershell
python setup_db.py
```

Execute o fluxo principal:

```powershell
python executar_tudo.py
```

Para executar um monitor isolado:

```powershell
python E6_cvm_monitor_DB.py
python E7_ceres_monitor_DB.py
```

O projeto depende de rede, Chrome/WebDriver para as etapas com Selenium, APIs externas e webhooks. Valide cada integração em ambiente controlado antes de executar em produção.

## Operação

- acompanhe o log de cada etapa e o código de saída do orquestrador;
- não execute novamente uma etapa sem conferir os status no banco;
- preserve `data/` entre execuções;
- monitore rate limits da Groq e do Google Chat;
- não registre chaves, webhooks ou conteúdo sensível nos logs.
