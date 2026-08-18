import json
import logging
import os
import time

from groq import Groq, APIError, RateLimitError

from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CONFIGURAÇÕES
# ============================================================

ARQUIVO_JSON = "noticias_google_alerts.json"
ARQUIVO_LOG = "classificador.log"

# Recomendo colocar a chave em variável de ambiente:
# Windows PowerShell:
# $env:GROQ_API_KEY="sua_chave"
#
# Linux/macOS:
# export GROQ_API_KEY="sua_chave"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Modelo rápido e barato para uma classificação simples
MODELO = "openai/gpt-oss-120b"

# Máximo desejado pelo usuário
REQUISICOES_POR_MINUTO = 20

# 60 / 20 = 3 segundos entre chamadas
INTERVALO_ENTRE_REQUISICOES = 60 / REQUISICOES_POR_MINUTO

# Tentativas máximas por notícia antes de desistir
MAX_TENTATIVAS = 5


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(ARQUIVO_LOG, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# ============================================================
# CLIENTE GROQ
# ============================================================

if not GROQ_API_KEY:
    raise ValueError(
        "A variável de ambiente GROQ_API_KEY não foi definida."
    )

client = Groq(api_key=GROQ_API_KEY)


# ============================================================
# PROMPT
# ============================================================

PROMPT_SISTEMA = """
Você é um classificador de títulos de notícias.

Sua tarefa é identificar se o título está relacionado a algum dos seguintes eventos:

- recuperação judicial
- recuperação extrajudicial
- liquidação judicial
- liquidação extrajudicial

Responda SOMENTE com uma das duas opções abaixo:

enviar
nao_enviar

REGRAS:

1. Retorne "enviar" se o título indicar que uma empresa, instituição,
grupo econômico ou entidade está envolvida em recuperação judicial,
recuperação extrajudicial, liquidação judicial ou liquidação extrajudicial.

2. Considere também expressões equivalentes ou variações linguísticas,
desde que fique claro pelo título que se trata de algum desses processos.

3. Não dê explicações.

4. Não use markdown.

5. Sua resposta deve ser EXATAMENTE:
enviar
ou
nao_enviar
"""


# ============================================================
# FUNÇÕES
# ============================================================

def carregar_json(caminho):
    """Carrega o arquivo JSON."""

    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def salvar_json(dados, caminho):
    """Salva o JSON mantendo acentos."""

    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(
            dados,
            arquivo,
            ensure_ascii=False,
            indent=2
        )


def classificar_titulo(titulo, max_tentativas=MAX_TENTATIVAS):
    """
    Envia o título ao Groq e retorna:
    enviar
    ou
    nao_enviar

    Desiste após 'max_tentativas' tentativas malsucedidas,
    retornando "nao_enviar" por segurança.
    """

    tentativas = 0

    while tentativas < max_tentativas:
        try:
            resposta = client.chat.completions.create(
                model=MODELO,
                messages=[
                    {
                        "role": "system",
                        "content": PROMPT_SISTEMA
                    },
                    {
                        "role": "user",
                        "content": f"Título da notícia:\n{titulo}"
                    }
                ],
                temperature=0,
                max_tokens=200,
                reasoning_effort="low"
            )

            mensagem = resposta.choices[0].message
            classificacao = (mensagem.content or "").strip().lower()

            # Proteção caso o modelo retorne algo inesperado
            if classificacao == "enviar":
                return "enviar"

            if classificacao in {
                "nao_enviar",
                "não_enviar",
                "não enviar",
                "nao enviar"
            }:
                return "nao_enviar"

            finish_reason = resposta.choices[0].finish_reason
            logger.warning(
                "Resposta inesperada do modelo: %s (finish_reason=%s)",
                repr(classificacao), finish_reason
            )

            # Se veio vazio por ter estourado o limite de tokens
            # (comum em modelos de raciocínio), vale tentar de novo
            # com mais espaço em vez de desistir direto.
            if not classificacao and finish_reason == "length":
                tentativas += 1
                logger.info(
                    "Resposta vazia por truncamento. Tentando novamente (%d/%d)...",
                    tentativas, max_tentativas
                )
                continue

            # Por segurança, não envia
            return "nao_enviar"

        except RateLimitError:
            tentativas += 1
            logger.warning(
                "Rate limit atingido (tentativa %d/%d). Aguardando 60 segundos...",
                tentativas, max_tentativas
            )
            time.sleep(60)

        except APIError as erro:
            tentativas += 1
            logger.error(
                "Erro na API Groq (tentativa %d/%d): %s",
                tentativas, max_tentativas, str(erro)
            )
            time.sleep(10)

        except Exception as erro:
            tentativas += 1
            logger.error(
                "Erro inesperado (tentativa %d/%d): %s",
                tentativas, max_tentativas, str(erro)
            )
            time.sleep(10)

    logger.error(
        "Máximo de tentativas atingido para o título '%s'. "
        "Marcando como nao_enviar por segurança.",
        titulo
    )
    return "nao_enviar"


# ============================================================
# PROCESSAMENTO
# ============================================================

def processar_noticias():
    dados = carregar_json(ARQUIVO_JSON)

    noticias = dados.get("noticias", {})

    # Conta quantas estão pendentes
    pendentes = [
        noticia
        for noticia in noticias.values()
        if noticia.get("status") == "extraida"
    ]

    total = len(pendentes)

    logger.info("=" * 70)
    logger.info("CLASSIFICADOR DE NOTÍCIAS")
    logger.info("=" * 70)
    logger.info("Notícias com status 'extraida': %d", total)
    logger.info("Limite: %d requisições/minuto", REQUISICOES_POR_MINUTO)
    logger.info("Intervalo mínimo: %.1fs", INTERVALO_ENTRE_REQUISICOES)
    logger.info("=" * 70)

    processadas = 0
    enviar = 0
    nao_enviar = 0

    try:
        for id_noticia, noticia in noticias.items():

            # Só processa o que ainda está como extraida
            if noticia.get("status") != "extraida":
                continue

            titulo = noticia.get("title", "").strip()

            processadas += 1

            logger.info("[%d/%d] ID: %s", processadas, total, id_noticia)
            logger.info("Título: %s", titulo)

            # Se não houver título
            if not titulo:
                logger.info("Título vazio -> nao_enviar")

                noticia["status"] = "nao_enviar"
                nao_enviar += 1

                salvar_json(dados, ARQUIVO_JSON)
                continue

            inicio = time.monotonic()

            # Faz classificação
            classificacao = classificar_titulo(titulo)

            # Atualiza status
            noticia["status"] = classificacao

            if classificacao == "enviar":
                enviar += 1
            else:
                nao_enviar += 1

            logger.info("Classificação: %s", classificacao)

            # ----------------------------------------------------
            # SALVA IMEDIATAMENTE
            # ----------------------------------------------------
            # Assim, caso o script seja interrompido, não perde
            # o que já foi processado.
            salvar_json(dados, ARQUIVO_JSON)

            # ----------------------------------------------------
            # RATE LIMIT
            # ----------------------------------------------------

            duracao = time.monotonic() - inicio

            espera = INTERVALO_ENTRE_REQUISICOES - duracao

            if espera > 0 and processadas < total:
                logger.info("Aguardando %.2fs...", espera)
                time.sleep(espera)

    except KeyboardInterrupt:
        logger.warning(
            "Interrompido pelo usuário. Progresso salvo até a notícia %d/%d.",
            processadas, total
        )
        return

    logger.info("=" * 70)
    logger.info("PROCESSAMENTO FINALIZADO")
    logger.info("=" * 70)
    logger.info("Processadas: %d", processadas)
    logger.info("Enviar: %d", enviar)
    logger.info("Não enviar: %d", nao_enviar)
    logger.info("=" * 70)


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    processar_noticias()