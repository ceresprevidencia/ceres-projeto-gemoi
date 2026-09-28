# Bot de mercado de crédito

O projeto `bot-mercado-de-credito/` monitora notícias relacionadas a recuperação judicial, recuperação extrajudicial, liquidação judicial e liquidação extrajudicial. O fluxo usa Google Alerts, classificação por LLM e envio de cards ao Google Chat.

## Fluxo

O orquestrador é `pipeline_noticias.py` e executa os scripts na ordem:

| Ordem | Script | Responsabilidade |
| --- | --- | --- |
| 1 | `extrator_link.py` | Baixa feeds Atom do Google Alerts, interpreta XML, limpa links e salva o histórico |
| 2 | `classifica_llm.py` | Classifica títulos como `enviar` ou `nao_enviar` usando Groq |
| 3 | `enviar_noticia.py` | Envia notícias marcadas como `enviar` ao Google Chat em blocos de cards |

A execução sequencial para quando um script retorna erro, pois o pipeline usa `subprocess.run(..., check=True)`.

## Arquivos de entrada e saída

- `noticias_google_alerts.json`: histórico de notícias e status do processamento;
- `classificador.log`: log da classificação por LLM;
- `envio_google_chat.log`: log dos envios;
- `noticias_google_alerts.json`: atualizado após cada envio para preservar o progresso.

O extrator também aceita a variável `GOOGLE_ALERTS_FEEDS`, com URLs separadas por vírgula, para substituir os feeds definidos por padrão.

## Configuração

Crie um `.env` no diretório do bot ou disponibilize as variáveis no ambiente:

```dotenv
GROQ_API_KEY=chave-da-api
GOOGLE_CHAT_WEBHOOK_URL=webhook-do-google-chat
GOOGLE_ALERTS_FEEDS=url1,url2
```

`GROQ_API_KEY` é obrigatório para `classifica_llm.py`. `GOOGLE_CHAT_WEBHOOK_URL` é obrigatório para `enviar_noticia.py`. Nunca grave esses valores nos arquivos JSON, nos logs ou no controle de versão.

## Instalação e execução

```powershell
cd bot-mercado-de-credito
python -m pip install -r requirements.txt
python pipeline_noticias.py
```

Para executar uma etapa isolada:

```powershell
python extrator_link.py
python classifica_llm.py
python enviar_noticia.py
```

A classificação limita as chamadas a 20 requisições por minuto, com intervalo de aproximadamente três segundos e até cinco tentativas por notícia. O envio agrupa até 30 notícias por bloco e faz novas tentativas em falhas de rede ou rate limit.

## Status do processamento

- `extraida`: notícia coletada e aguardando classificação;
- `enviar`: notícia classificada para alerta;
- `nao_enviar`: notícia fora do escopo ou recusada por segurança;
- `enviado`: notícia enviada com sucesso ao Google Chat.

Em caso de falha na API, a classificação tende a `nao_enviar` por segurança. Em caso de falha de envio, o status permanece disponível para nova tentativa posterior.

## Cuidados operacionais

- mantenha o JSON e os logs em armazenamento persistente;
- faça backup antes de alterações manuais no histórico;
- confirme o webhook em ambiente de teste antes de enviar mensagens reais;
- monitore duplicidades e falhas de rede;
- considere o conteúdo externo não confiável e evite executar HTML ou scripts recebidos nas notícias;
- atualize os feeds e as regras de classificação junto com a documentação.
