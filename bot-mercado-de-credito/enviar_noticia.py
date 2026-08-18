import json
import logging
import os
import re
import time
from datetime import datetime
from urllib.parse import urlparse, parse_qs

import requests
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CONFIGURAÇÕES
# ============================================================

ARQUIVO_JSON = "noticias_google_alerts.json"
WEBHOOK_URL = os.getenv("GOOGLE_CHAT_WEBHOOK_URL")
CHAVE_URL = "link"

NOTICIAS_POR_BLOCO = 30 
MAX_TENTATIVAS = 3

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("envio_google_chat.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

if not WEBHOOK_URL:
    raise ValueError("A variável GOOGLE_CHAT_WEBHOOK_URL não foi definida.")

# ============================================================
# FUNÇÕES
# ============================================================

def carregar_json(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)

def salvar_json(dados, caminho):
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)

def limpar_titulo(titulo):
    return re.sub(r"<[^>]+>", "", titulo).strip()

def extrair_url_real(url_google_alerts):
    if "google.com/url" in url_google_alerts:
        try:
            parsed = urlparse(url_google_alerts)
            query_params = parse_qs(parsed.query)
            if 'url' in query_params:
                return query_params['url'][0]
        except Exception as e:
            logger.warning(f"Não foi possível parsear a URL: {e}")
    return url_google_alerts

def montar_blocos_cards(pendentes, cabecalho_data, total):
    """
    Agrupa as notícias criando blocos de payload no formato CardsV2.
    O cabeçalho é exibido apenas no primeiro bloco.
    """
    blocos = []
    primeiro_bloco = True
    
    for i in range(0, len(pendentes), NOTICIAS_POR_BLOCO):
        lote = pendentes[i:i + NOTICIAS_POR_BLOCO]
        widgets = []
        indices_atual = []
        
        for index_no_lote, (id_noticia, noticia) in enumerate(lote):
            indice_real = i + index_no_lote
            indices_atual.append(indice_real)
            
            titulo = limpar_titulo(noticia.get("title", ""))
            url_bruta = noticia.get(CHAVE_URL, "").strip()
            url = extrair_url_real(url_bruta)
            
            if not url:
                url = "#"
                texto_link = "[URL não encontrada]"
            else:
                texto_link = url
            
            texto_widget = f"<b>{titulo}</b><br><a href=\"{url}\">{texto_link}</a>"
            
            widgets.append({
                "textParagraph": {
                    "text": texto_widget
                }
            })
            
            # Adiciona divisor entre as notícias (exceto na última do lote)
            if index_no_lote < len(lote) - 1:
                widgets.append({"divider": {}})

        # Monta a estrutura base do Card
        card_content = {
            "sections": [
                {
                    "widgets": widgets
                }
            ]
        }
        
        # Adiciona o cabeçalho SOMENTE se for o primeiro bloco
        if primeiro_bloco:
            card_content["header"] = {
                "title": "🚨🚨 Novas notícias no Radar! 🚨🚨",
                "subtitle": f"Total: {total} notícia(s) | {cabecalho_data}"
            }
            primeiro_bloco = False

        payload = {
            "cardsV2": [
                {
                    "cardId": f"bloco-noticias-{i}",
                    "card": card_content
                }
            ]
        }
        
        blocos.append((indices_atual, payload))
        
    return blocos

def enviar_para_chat(payload, max_tentativas=MAX_TENTATIVAS):
    tentativas = 0
    while tentativas < max_tentativas:
        try:
            resposta = requests.post(WEBHOOK_URL, json=payload, timeout=10)
            if resposta.status_code == 200:
                return True

            tentativas += 1
            logger.warning("Falha ao enviar (tentativa %d/%d). Status: %d - %s",
                           tentativas, max_tentativas, resposta.status_code, resposta.text)

            if resposta.status_code == 429:
                logger.info("Rate limit atingido. Aguardando 30s...")
                time.sleep(30)
            else:
                time.sleep(5)

        except requests.RequestException as erro:
            tentativas += 1
            logger.error("Erro de rede ao enviar (tentativa %d/%d): %s",
                         tentativas, max_tentativas, str(erro))
            time.sleep(5)

    logger.error("Máximo de tentativas atingido. Mensagem não enviada.")
    return False

# ============================================================
# PROCESSAMENTO
# ============================================================

def enviar_noticias():
    dados = carregar_json(ARQUIVO_JSON)
    noticias = dados.get("noticias", {})

    pendentes = [
        (id_noticia, noticia)
        for id_noticia, noticia in noticias.items()
        if noticia.get("status") == "enviar"
    ]

    total = len(pendentes)

    logger.info("=" * 70)
    logger.info("ENVIO DE NOTÍCIAS AO GOOGLE CHAT (FORMATO CARD)")
    logger.info("=" * 70)
    logger.info("Notícias marcadas como 'enviar': %d", total)

    if not pendentes:
        logger.info("Nenhuma notícia para enviar.")
        return

    agora = datetime.now().strftime("%d/%m/%Y às %H:%M")

    blocos = montar_blocos_cards(pendentes, agora, total)

    enviadas = 0
    falhas = 0

    try:
        for numero_bloco, (indices, payload_bloco) in enumerate(blocos, start=1):
            logger.info("Enviando bloco %d/%d (%d notícia(s))...",
                        numero_bloco, len(blocos), len(indices))

            sucesso = enviar_para_chat(payload_bloco)

            if sucesso:
                for indice in indices:
                    id_noticia, noticia = pendentes[indice]
                    noticia["status"] = "enviado"
                
                enviadas += len(indices)
                logger.info("Bloco %d enviado com sucesso.", numero_bloco)
            else:
                falhas += len(indices)
                logger.error("Bloco %d falhou. Tentaremos novamente na próxima.", numero_bloco)

            salvar_json(dados, ARQUIVO_JSON)

    except KeyboardInterrupt:
        logger.warning("Interrompido pelo usuário. Progresso salvo.")
        return

    logger.info("=" * 70)
    logger.info("ENVIO FINALIZADO - Enviadas: %d | Falhas: %d", enviadas, falhas)
    logger.info("=" * 70)

if __name__ == "__main__":
    enviar_noticias()