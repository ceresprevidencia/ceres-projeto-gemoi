from __future__ import annotations

import argparse
import html
import json
import logging
import os
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
from typing import Dict, List


# Os feeds padrão podem ser sobrescritos pela variável de ambiente
# GOOGLE_ALERTS_FEEDS (separados por vírgula), para não deixar os
# IDs de alerta fixos no código-fonte.
_ENV_FEEDS = os.environ.get("GOOGLE_ALERTS_FEEDS", "")

DEFAULT_FEEDS = (
    [url.strip() for url in _ENV_FEEDS.split(",") if url.strip()]
    if _ENV_FEEDS
    else [
        "https://www.google.com.br/alerts/feeds/09404460482838700245/7623443554147141048",
        "https://www.google.com.br/alerts/feeds/09404460482838700245/9527617168737178189",
        "https://www.google.com.br/alerts/feeds/09404460482838700245/10578397006262216121",
        "https://www.google.com.br/alerts/feeds/09404460482838700245/872769734660157836",
    ]
)

DEFAULT_HISTORY_FILE = "noticias_google_alerts.json"

ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom"
}

logger = logging.getLogger("google_alerts_reader")


def configure_logging(verbose: bool = False) -> None:
    """
    Configura o logging para saída em console com timestamp.
    """

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def clean_google_alert_link(link: str) -> str:
    """
    Extrai a URL real do veículo a partir do link de redirecionamento
    do Google Alerts.

    Exemplo:
    https://www.google.com/url?...&url=https://www.cnnbrasil.com.br/...&...

    Retorna:
    https://www.cnnbrasil.com.br/...
    """

    if not link:
        return ""

    link = link.strip()

    try:
        parsed = urlparse(link)

        google_domains = {
            "google.com",
            "www.google.com",
            "google.com.br",
            "www.google.com.br",
        }

        if parsed.netloc.lower() in google_domains and parsed.path == "/url":
            params = parse_qs(parsed.query)

            real_url = params.get("url", [""])[0]

            if real_url:
                return unquote(real_url).strip()

    except Exception:
        logger.debug("Falha ao limpar link do Google Alerts: %s", link, exc_info=True)

    return link


def element_content(element: ET.Element | None) -> str:
    """
    Retorna o conteúdo de um elemento XML preservando o HTML interno.
    """

    if element is None:
        return ""

    partes = []

    if element.text:
        partes.append(element.text)

    for child in element:
        partes.append(
            ET.tostring(
                child,
                encoding="unicode",
                method="html"
            )
        )

        if child.tail:
            partes.append(child.tail)

    return html.unescape("".join(partes).strip())


def fetch_xml(url: str, timeout: int = 30, retries: int = 3) -> bytes:
    """
    Baixa o conteúdo XML do feed, com algumas tentativas em caso de
    falha temporária de rede (backoff exponencial simples).
    """

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; google-alerts-reader/1.0)",
            "Accept": (
                "application/atom+xml,"
                "application/rss+xml,"
                "application/xml,"
                "text/xml"
            ),
        },
        method="GET",
    )

    last_exc: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()

        except (urllib.error.URLError, TimeoutError) as exc:
            last_exc = exc

            if attempt < retries:
                wait_seconds = 2 ** (attempt - 1)
                logger.warning(
                    "Tentativa %d/%d falhou para %s (%s). Nova tentativa em %ds.",
                    attempt,
                    retries,
                    url,
                    exc,
                    wait_seconds,
                )
                time.sleep(wait_seconds)
            else:
                logger.error(
                    "Todas as %d tentativas falharam para %s.",
                    retries,
                    url,
                )

    assert last_exc is not None
    raise last_exc


def parse_google_alerts(xml_bytes: bytes) -> List[Dict[str, str]]:
    """
    Interpreta o feed Atom do Google Alerts e retorna as notícias.
    """

    root = ET.fromstring(xml_bytes)

    noticias = []

    for entry in root.findall("atom:entry", ATOM_NS):

        link_element = entry.find("atom:link", ATOM_NS)

        google_alert_id = (
            entry.findtext(
                "atom:id",
                default="",
                namespaces=ATOM_NS
            )
            or ""
        ).strip()

        title = element_content(
            entry.find("atom:title", ATOM_NS)
        )

        link_original = (
            (
                link_element.get("href")
                if link_element is not None
                else ""
            )
            or ""
        ).strip()

        published = (
            entry.findtext(
                "atom:published",
                default="",
                namespaces=ATOM_NS
            )
            or ""
        ).strip()

        updated = (
            entry.findtext(
                "atom:updated",
                default="",
                namespaces=ATOM_NS
            )
            or ""
        ).strip()

        content = element_content(
            entry.find("atom:content", ATOM_NS)
        )

        item = {
            "id": google_alert_id,
            "title": title,
            "link": clean_google_alert_link(link_original),
            "published": published,
            "updated": updated,
            "content": content,
            "status": "extraida",
        }

        if not item["link"]:
            logger.warning("Notícia ignorada por não possuir link: %s", title)
            continue

        noticias.append(item)

    return noticias


def load_history(history_path: Path) -> Dict[str, dict]:
    """
    Carrega o histórico salvo no JSON.

    Também adiciona status='extraida' às notícias antigas
    que ainda não possuem essa chave.
    """

    if not history_path.exists():
        return {}

    try:
        with open(history_path, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

    except (
        json.JSONDecodeError,
        OSError,
    ) as exc:
        logger.error(
            "Falha ao carregar historico em %s: %s. "
            "Iniciando com historico vazio.",
            history_path,
            exc,
        )
        return {}

    noticias = dados.get("noticias", {})

    if not isinstance(noticias, dict):
        return {}

    noticias_por_link = {}
    alterado = False

    for chave_atual, noticia in noticias.items():

        if not isinstance(noticia, dict):
            continue

        if "status" not in noticia:
            noticia["status"] = "extraida"
            alterado = True

        link = clean_google_alert_link(str(noticia.get("link") or "").strip())
        if not link:
            logger.warning(
                "Notícia sem link ignorada ao migrar o histórico: %s",
                chave_atual,
            )
            alterado = True
            continue

        noticia["link"] = link
        if chave_atual != link:
            alterado = True

        if link in noticias_por_link:
            logger.warning(
                "Link duplicado no histórico; mantendo a primeira ocorrência: %s",
                link,
            )
            alterado = True
            continue

        noticias_por_link[link] = noticia

    if alterado:
        save_history(history_path, noticias_por_link)

    return noticias_por_link


def save_history(
    history_path: Path,
    noticias: Dict[str, dict],
) -> None:
    """
    Salva o histórico diretamente no JSON.
    """

    history_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    payload = {
        "noticias": noticias
    }

    with open(
        history_path,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            payload,
            arquivo,
            ensure_ascii=False,
            indent=2,
        )


def process_feeds(
    feed_urls: List[str],
    history_path: Path,
) -> int:
    """
    Processa os feeds e salva apenas notícias novas.

    O histórico é salvo uma vez ao final de cada feed (não a cada
    notícia individual), para evitar reescrever o arquivo inteiro
    repetidamente quando há muitas notícias novas de uma vez. Em
    caso de falha no meio do processamento de um feed, apenas as
    notícias já persistidas em feeds anteriores ficam garantidas.
    """

    noticias_salvas = load_history(history_path)

    logger.info(
        "Historico carregado: %d noticia(s) ja salva(s).",
        len(noticias_salvas),
    )

    total_novas = 0

    for feed_url in feed_urls:

        logger.info("Processando feed: %s", feed_url)

        try:
            xml_bytes = fetch_xml(feed_url)

            items = parse_google_alerts(xml_bytes)

        except urllib.error.URLError as exc:
            logger.error("Falha ao baixar feed %s: %s", feed_url, exc)
            continue

        except ET.ParseError as exc:
            logger.error("XML invalido no feed %s: %s", feed_url, exc)
            continue

        except Exception as exc:
            # Rede de segurança: um feed com problema inesperado não
            # deve interromper o processamento dos demais feeds.
            logger.exception(
                "Falha inesperada ao processar feed %s: %s",
                feed_url,
                exc,
            )
            continue

        novas_no_feed = 0

        for item in items:

            link = item["link"]

            # Se o link já estiver salvo,
            # pula para a próxima notícia.
            if link in noticias_salvas:
                continue

            noticias_salvas[link] = item

            novas_no_feed += 1
            total_novas += 1

            logger.info("[NOVA] %s", item["title"])
            logger.debug(
                "%s",
                json.dumps(item, ensure_ascii=False, indent=2),
            )

        if novas_no_feed:
            # Salva uma única vez, já com todas as notícias novas
            # encontradas neste feed.
            save_history(history_path, noticias_salvas)

        logger.info("Novas neste feed: %d", novas_no_feed)

    logger.info("=" * 80)
    logger.info("Total de noticias novas: %d", total_novas)
    logger.info("Total no historico: %d", len(noticias_salvas))
    logger.info("=" * 80)

    return total_novas


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Le feeds do Google Alerts "
            "e salva noticias novas em JSON."
        )
    )

    parser.add_argument(
        "--feed",
        action="append",
        dest="feeds",
        help=(
            "URL de feed adicional. "
            "Pode ser usado varias vezes."
        ),
    )

    parser.add_argument(
        "--history-file",
        default=DEFAULT_HISTORY_FILE,
        help=(
            "Arquivo JSON de historico. "
            f"Padrao: {DEFAULT_HISTORY_FILE}"
        ),
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Ativa logs de nivel DEBUG.",
    )

    return parser.parse_args()


def main() -> int:

    args = parse_args()

    configure_logging(verbose=args.verbose)

    feeds = (
        args.feeds
        if args.feeds
        else DEFAULT_FEEDS
    )

    if not feeds:
        logger.error(
            "Nenhum feed configurado. Defina GOOGLE_ALERTS_FEEDS, "
            "use --feed ou ajuste DEFAULT_FEEDS."
        )
        return 1

    history_path = Path(
        args.history_file
    )

    process_feeds(
        feed_urls=feeds,
        history_path=history_path,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())