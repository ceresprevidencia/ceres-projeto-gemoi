"""
ETL de preenchimentos e respostas do DDQ.

Lê os dados da planilha (Google Sheets), relaciona cada linha com a
gestora cadastrada no banco (via CNPJ) e grava/atualiza os registros
de `preenchimento` e `resposta`.

Este módulo não depende do Streamlit.
"""

from __future__ import annotations

import hashlib
import logging
import sqlite3
from dataclasses import dataclass, field

import pandas as pd

from .con_gsheets import puxar_dados
from .db_ddq import get_connection


logger = logging.getLogger(__name__)

COLUNA_CNPJ = "CNPJ"
COLUNA_DATA_ENVIO = "Carimbo de data/hora"
COLUNA_EMPRESA = "Nome da Empresa (Razão Social)"

COLUNAS_IDENTIFICADORAS = [
    COLUNA_CNPJ,
    COLUNA_DATA_ENVIO,
    COLUNA_EMPRESA,
]


@dataclass
class ResultadoETL:
    """Resumo da execução da ETL."""

    sucesso: bool

    preenchimentos_adicionados: int = 0
    respostas_adicionadas: int = 0
    respostas_atualizadas: int = 0

    novos_preenchimentos: list[dict] = field(default_factory=list)
    novas_respostas: list[dict] = field(default_factory=list)
    respostas_modificadas: list[dict] = field(default_factory=list)

    cnpjs_nao_encontrados: set[str] = field(default_factory=set)

    mensagem_erro: str | None = None


def _normalizar_cnpj(cnpj: object) -> str | None:
    """Mantém somente os dígitos do CNPJ."""

    if cnpj is None or pd.isna(cnpj):
        return None

    digitos = "".join(
        caractere
        for caractere in str(cnpj)
        if caractere.isdigit()
    )

    return digitos or None


def _carregar_dataframe() -> pd.DataFrame | None:
    """Busca os dados da planilha e devolve um DataFrame limpo."""

    dados = puxar_dados()

    if len(dados) < 2:
        return None

    cabecalho = dados[0]
    total_colunas = len(cabecalho)

    linhas = [
        linha[:total_colunas]
        + [""] * max(0, total_colunas - len(linha))
        for linha in dados[1:]
    ]

    df = pd.DataFrame(
        data=linhas,
        columns=cabecalho,
    )

    colunas_ausentes = (
        set(COLUNAS_IDENTIFICADORAS)
        - set(df.columns)
    )

    if colunas_ausentes:
        raise ValueError(
            "Colunas ausentes: "
            + ", ".join(sorted(colunas_ausentes))
        )

    df[COLUNA_CNPJ] = df[COLUNA_CNPJ].apply(
        _normalizar_cnpj
    )

    datas_convertidas = pd.to_datetime(
        df[COLUNA_DATA_ENVIO],
        errors="coerce",
        dayfirst=True,
    )

    df[COLUNA_DATA_ENVIO] = datas_convertidas.dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    df[COLUNA_EMPRESA] = (
        df[COLUNA_EMPRESA]
        .astype("string")
        .str.strip()
        .fillna("")
    )

    df = df.dropna(
        subset=[
            COLUNA_CNPJ,
            COLUNA_DATA_ENVIO,
        ]
    ).copy()

    return df


def executar_etl() -> ResultadoETL:
    """Executa a ETL e retorna somente o que foi inserido ou atualizado."""

    try:
        df = _carregar_dataframe()

    except ValueError as erro:
        return ResultadoETL(
            sucesso=False,
            mensagem_erro=str(erro),
        )

    except Exception as erro:
        logger.exception(
            "Erro ao carregar dados da planilha."
        )

        return ResultadoETL(
            sucesso=False,
            mensagem_erro=(
                "Erro ao carregar dados da planilha: "
                f"{erro}"
            ),
        )

    if df is None or df.empty:
        return ResultadoETL(
            sucesso=False,
            mensagem_erro=(
                "A planilha não contém dados válidos."
            ),
        )

    colunas_perguntas = [
        coluna
        for coluna in df.columns
        if coluna not in COLUNAS_IDENTIFICADORAS
    ]

    cnpjs_nao_encontrados: set[str] = set()

    novos_preenchimentos: list[dict] = []
    novas_respostas: list[dict] = []
    respostas_modificadas: list[dict] = []

    try:
        with get_connection() as conn:
            gestoras = conn.execute(
                """
                SELECT
                    id_gestora,
                    nome,
                    cnpj
                FROM gestora
                WHERE cnpj IS NOT NULL
                """
            ).fetchall()

            gestoras_por_cnpj: dict[str, dict] = {}

            for gestora in gestoras:
                cnpj_normalizado = _normalizar_cnpj(
                    gestora["cnpj"]
                )

                if cnpj_normalizado:
                    gestoras_por_cnpj[cnpj_normalizado] = {
                        "id_gestora": gestora["id_gestora"],
                        "nome": gestora["nome"],
                    }

            for _, linha in df.iterrows():
                cnpj = _normalizar_cnpj(
                    linha[COLUNA_CNPJ]
                )

                if not cnpj:
                    continue

                data_envio = linha[COLUNA_DATA_ENVIO]
                nome_empresa = str(
                    linha[COLUNA_EMPRESA]
                ).strip()

                dados_gestora = gestoras_por_cnpj.get(cnpj)

                if dados_gestora is None:
                    cnpjs_nao_encontrados.add(cnpj)
                    continue

                id_gestora = dados_gestora["id_gestora"]
                nome_gestora = dados_gestora["nome"]

                preenchimento = conn.execute(
                    """
                    SELECT id_preenchimento
                    FROM preenchimento
                    WHERE id_gestora = ?
                      AND data_envio = ?
                    """,
                    (
                        id_gestora,
                        data_envio,
                    ),
                ).fetchone()

                if preenchimento is None:
                    cursor = conn.execute(
                        """
                        INSERT INTO preenchimento (
                            id_gestora,
                            data_envio
                        )
                        VALUES (?, ?)
                        """,
                        (
                            id_gestora,
                            data_envio,
                        ),
                    )

                    id_preenchimento = cursor.lastrowid

                    novos_preenchimentos.append(
                        {
                            "id_preenchimento": id_preenchimento,
                            "id_gestora": id_gestora,
                            "gestora": nome_gestora,
                            "empresa": nome_empresa,
                            "cnpj": cnpj,
                            "data_envio": data_envio,
                        }
                    )

                else:
                    id_preenchimento = (
                        preenchimento["id_preenchimento"]
                    )

                for pergunta in colunas_perguntas:
                    valor = linha[pergunta]

                    if pd.isna(valor):
                        continue

                    resposta_nova = str(valor).strip()

                    if not resposta_nova:
                        continue

                    pergunta_limpa = str(pergunta).strip()

                    id_resposta = hashlib.sha256(
                        (
                            f"{id_preenchimento}|"
                            f"{pergunta_limpa}"
                        ).encode("utf-8")
                    ).hexdigest()

                    resposta_existente = conn.execute(
                        """
                        SELECT
                            id_resposta,
                            pergunta,
                            resposta,
                            score_resposta
                        FROM resposta
                        WHERE id_resposta = ?
                        """,
                        (id_resposta,),
                    ).fetchone()

                    if resposta_existente is None:
                        conn.execute(
                            """
                            INSERT INTO resposta (
                                id_resposta,
                                pergunta,
                                resposta,
                                score_resposta,
                                id_preenchimento
                            )
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                id_resposta,
                                pergunta_limpa,
                                resposta_nova,
                                None,
                                id_preenchimento,
                            ),
                        )

                        novas_respostas.append(
                            {
                                "id_preenchimento": (
                                    id_preenchimento
                                ),
                                "gestora": nome_gestora,
                                "empresa": nome_empresa,
                                "cnpj": cnpj,
                                "data_envio": data_envio,
                                "pergunta": pergunta_limpa,
                                "resposta": resposta_nova,
                            }
                        )

                        continue

                    resposta_anterior = (
                        resposta_existente["resposta"]
                    )

                    resposta_anterior_normalizada = (
                        ""
                        if resposta_anterior is None
                        else str(resposta_anterior).strip()
                    )

                    if (
                        resposta_anterior_normalizada
                        == resposta_nova
                    ):
                        continue

                    conn.execute(
                        """
                        UPDATE resposta
                        SET
                            pergunta = ?,
                            resposta = ?,
                            id_preenchimento = ?
                        WHERE id_resposta = ?
                        """,
                        (
                            pergunta_limpa,
                            resposta_nova,
                            id_preenchimento,
                            id_resposta,
                        ),
                    )

                    respostas_modificadas.append(
                        {
                            "id_preenchimento": (
                                id_preenchimento
                            ),
                            "gestora": nome_gestora,
                            "empresa": nome_empresa,
                            "cnpj": cnpj,
                            "data_envio": data_envio,
                            "pergunta": pergunta_limpa,
                            "resposta_anterior": (
                                resposta_anterior_normalizada
                            ),
                            "resposta_nova": resposta_nova,
                        }
                    )

            conn.commit()

    except sqlite3.Error as erro:
        logger.exception("Erro ao executar ETL.")

        return ResultadoETL(
            sucesso=False,
            mensagem_erro=str(erro),
        )

    except Exception as erro:
        logger.exception(
            "Erro inesperado ao executar ETL."
        )

        return ResultadoETL(
            sucesso=False,
            mensagem_erro=(
                "Erro inesperado ao executar a ETL: "
                f"{erro}"
            ),
        )

    return ResultadoETL(
        sucesso=True,
        preenchimentos_adicionados=len(
            novos_preenchimentos
        ),
        respostas_adicionadas=len(novas_respostas),
        respostas_atualizadas=len(
            respostas_modificadas
        ),
        novos_preenchimentos=novos_preenchimentos,
        novas_respostas=novas_respostas,
        respostas_modificadas=respostas_modificadas,
        cnpjs_nao_encontrados=cnpjs_nao_encontrados,
    )


def _configurar_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s "
            "[%(levelname)s] "
            "%(message)s"
        ),
    )


def main() -> None:
    """Ponto de entrada para rodar a ETL via terminal."""

    _configurar_logging()

    logger.info("Iniciando ETL...")

    resultado = executar_etl()

    if not resultado.sucesso:
        logger.error(
            "Falha na ETL: %s",
            resultado.mensagem_erro,
        )

        raise SystemExit(1)

    if resultado.cnpjs_nao_encontrados:
        logger.warning(
            "CNPJs sem gestora cadastrada: %s",
            ", ".join(
                sorted(resultado.cnpjs_nao_encontrados)
            ),
        )

    logger.info(
        (
            "ETL concluída: "
            "%s preenchimentos adicionados, "
            "%s respostas adicionadas e "
            "%s respostas atualizadas."
        ),
        resultado.preenchimentos_adicionados,
        resultado.respostas_adicionadas,
        resultado.respostas_atualizadas,
    )


if __name__ == "__main__":
    main()