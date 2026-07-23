"""
Camada de acesso a dados da tabela `gestora`.

Sem dependência do Streamlit, para poder ser usada por uma página
Streamlit, por um script de linha de comando ou por testes automatizados.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from .db_ddq import get_connection


STATUS_VALIDOS = {"ATIVO", "INATIVO"}


class CnpjDuplicadoError(Exception):
    """Levantado quando o CNPJ informado já pertence a outra gestora."""


@dataclass
class Gestora:
    id_gestora: int
    nome: str
    telefone: str | None
    email: str | None
    cnpj: str | None
    atualizado: str
    status: str


def normalizar_cnpj(
    cnpj: str | None,
) -> str | None:
    """Mantém somente os dígitos do CNPJ."""

    if not cnpj:
        return None

    digitos = "".join(
        caractere
        for caractere in str(cnpj)
        if caractere.isdigit()
    )

    return digitos or None


def normalizar_status(
    status: str | None,
) -> str:
    """Normaliza e valida o status da gestora."""

    status_normalizado = (
        str(status or "ATIVO")
        .strip()
        .upper()
    )

    if status_normalizado not in STATUS_VALIDOS:
        raise ValueError(
            "O status deve ser ATIVO ou INATIVO."
        )

    return status_normalizado


def _agora() -> str:
    return datetime.now().isoformat(
        timespec="seconds"
    )


def inserir_gestora(
    nome: str,
    telefone: str | None = None,
    email: str | None = None,
    cnpj: str | None = None,
    status: str = "ATIVO",
) -> int:
    """Insere uma nova gestora e retorna o ID gerado."""

    nome = nome.strip()

    if not nome:
        raise ValueError(
            "O nome da gestora é obrigatório."
        )

    telefone = (
        (telefone or "").strip()
        or None
    )

    email = (
        (email or "").strip()
        or None
    )

    cnpj = normalizar_cnpj(cnpj)
    status = normalizar_status(status)
    atualizado = _agora()



    try:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO gestora (
                    nome,
                    telefone,
                    email,
                    cnpj,
                    atualizado,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    nome,
                    telefone,
                    email,
                    cnpj,
                    atualizado,
                    status,
                ),
            )

            conn.commit()

            return cursor.lastrowid

    except sqlite3.IntegrityError as erro:
        if "gestora.cnpj" in str(erro):
            raise CnpjDuplicadoError(
                "Já existe uma gestora cadastrada "
                "com esse CNPJ."
            ) from erro

        raise


def atualizar_gestora(
    id_gestora: int,
    nome: str,
    telefone: str | None = None,
    email: str | None = None,
    cnpj: str | None = None,
    status: str = "ATIVO",
) -> None:
    """Atualiza os dados de uma gestora."""

    nome = nome.strip()

    if not nome:
        raise ValueError(
            "O nome da gestora é obrigatório."
        )

    telefone = (
        (telefone or "").strip()
        or None
    )

    email = (
        (email or "").strip()
        or None
    )

    cnpj = normalizar_cnpj(cnpj)

    
    if status == 'Inativa':
        status = status + datetime.now().strftime(" - %d/%m/%Y %H:%M:%S")
    atualizado = _agora()

    """if cnpj and len(cnpj) != 14:
        raise ValueError(
            "O CNPJ deve possuir 14 dígitos."
        )
"""
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE gestora
                SET
                    nome = ?,
                    telefone = ?,
                    email = ?,
                    cnpj = ?,
                    atualizado = ?,
                    status = ?
                WHERE id_gestora = ?
                """,
                (
                    nome,
                    telefone,
                    email,
                    cnpj,
                    atualizado,
                    status,
                    id_gestora,
                ),
            )

            if cursor.rowcount == 0:
                raise ValueError(
                    f"Gestora com ID {id_gestora} "
                    "não encontrada."
                )

            conn.commit()

    except sqlite3.IntegrityError as erro:
        if "gestora.cnpj" in str(erro):
            raise CnpjDuplicadoError(
                "Já existe uma gestora cadastrada "
                "com esse CNPJ."
            ) from erro

        raise


def atualizar_status_gestora(
    id_gestora: int,
    status: str,
) -> None:
    """Atualiza somente o status de uma gestora."""

    status = normalizar_status(status)

    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE gestora
            SET
                status = ?,
                atualizado = ?
            WHERE id_gestora = ?
            """,
            (
                status,
                _agora(),
                id_gestora,
            ),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                f"Gestora com ID {id_gestora} "
                "não encontrada."
            )

        conn.commit()


def listar_gestoras() -> pd.DataFrame:
    """Retorna todas as gestoras, ordenadas por nome."""

    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT
                id_gestora,
                nome,
                telefone,
                email,
                cnpj,
                atualizado,
                status
            FROM gestora
            ORDER BY nome
            """,
            conn,
        )


def buscar_gestora(
    id_gestora: int,
) -> Gestora | None:
    """Busca uma gestora pelo ID."""

    with get_connection() as conn:
        linha = conn.execute(
            """
            SELECT
                id_gestora,
                nome,
                telefone,
                email,
                cnpj,
                atualizado,
                status
            FROM gestora
            WHERE id_gestora = ?
            """,
            (id_gestora,),
        ).fetchone()

    if linha is None:
        return None

    return Gestora(**dict(linha))


def listar_respostas() -> pd.DataFrame:
    """Retorna respostas com gestora e preenchimento."""

    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT
                *
            FROM resposta AS r
            ORDER BY
                r.id_resposta
            """,
            conn,
        )


def listar_preenchimentos() -> pd.DataFrame:
    """Retorna todos os preenchimentos."""

    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT
                id_preenchimento,
                id_gestora,
                data_envio,
                versao
            FROM preenchimento
            ORDER BY id_preenchimento
            """,
            conn,
        )


def listar_gestoras_preenchimento() -> pd.DataFrame:
    """Retorna gestoras e seu preenchimento mais recente."""

    with get_connection() as conn:
        return pd.read_sql_query(
            """
            WITH ultimos_preenchimentos AS (
                SELECT
                    id_gestora,
                    MAX(id_preenchimento)
                        AS id_ultimo_preenchimento
                FROM preenchimento
                GROUP BY id_gestora
            )
            SELECT
                g.id_gestora,
                g.nome,
                g.telefone,
                g.email,
                g.cnpj,
                g.status,
                g.atualizado,
                p.id_preenchimento,
                p.data_envio
            FROM gestora AS g
            LEFT JOIN ultimos_preenchimentos AS up
                ON up.id_gestora = g.id_gestora
            LEFT JOIN preenchimento AS p
                ON p.id_preenchimento =
                   up.id_ultimo_preenchimento
            ORDER BY g.nome
            """,
            conn,
        )


def excluir_gestoras(
    ids_gestoras: list[int],
) -> int:
    """Exclui gestoras e retorna a quantidade excluída."""

    ids_validos = sorted(
        {
            int(id_gestora)
            for id_gestora in ids_gestoras
            if id_gestora is not None
        }
    )

    if not ids_validos:
        raise ValueError(
            "Selecione pelo menos uma gestora "
            "para excluir."
        )

    placeholders = ", ".join(
        "?"
        for _ in ids_validos
    )

    with get_connection() as conn:
        cursor = conn.execute(
            f"""
            DELETE FROM gestora
            WHERE id_gestora IN ({placeholders})
            """,
            ids_validos,
        )

        quantidade_excluida = cursor.rowcount
        conn.commit()

    return quantidade_excluida

def atualizar_resposta(
    id_resposta: str,
    nova_resposta: str | None,
) -> None:
    """Atualiza somente o conteúdo de uma resposta existente.

    Levanta ValueError se o ID estiver vazio ou se a resposta
    não for encontrada.
    """

    id_resposta = str(id_resposta).strip()

    if not id_resposta:
        raise ValueError("O ID da resposta é obrigatório.")

    resposta = (
        str(nova_resposta).strip()
        if nova_resposta is not None
        else None
    )

    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE resposta
            SET resposta = ?
            WHERE id_resposta = ?
            """,
            (
                resposta,
                id_resposta,
            ),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                f"Resposta com ID {id_resposta} não encontrada."
            )

        conn.commit()