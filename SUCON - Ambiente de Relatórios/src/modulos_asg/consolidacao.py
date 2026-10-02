"""
Consolidação da carteira a partir do arquivo diário de Estoque.

Passos (mesma regra do app HTML, agora em pandas):
1. Normaliza o código da carteira (o Excel traz texto com zero à esquerda).
2. Parte da CERES CONSOLIDADA (9124), retirando as cotas dos 6 fundos abertos.
3. Acrescenta os ativos finais desses 6 fundos (look-through).
4. Remove o que não é exposição de investimento (evolução de cotas, contas a
   receber/pagar, empréstimos, operações futuras, caixa).
5. Agrupa por Carteira + Nome Grupo + Emissor, sem sobreposição.
"""
from __future__ import annotations

import io
import re

import pandas as pd

from . import parametros as P

COLUNAS_OBRIGATORIAS = ["Carteira", "Nome Grupo", "Emissor", "Valor Mercado"]


def _normalizar_carteira(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    texto = str(v).strip()
    try:
        return str(int(float(texto)))
    except ValueError:
        return texto


def ler_estoque(arquivo) -> pd.DataFrame:
    """Lê o Excel de Estoque (aba 'Posição de Ativos' ou a primeira)."""
    xls = pd.ExcelFile(arquivo)
    aba = P.ABA_PREFERENCIAL if P.ABA_PREFERENCIAL in xls.sheet_names else xls.sheet_names[0]
    df = pd.read_excel(xls, sheet_name=aba, dtype={"Carteira": str, "Cod Papel": str})
    faltando = [c for c in COLUNAS_OBRIGATORIAS if c not in df.columns]
    if faltando:
        raise ValueError(
            f"A aba '{aba}' não tem as colunas esperadas: {', '.join(faltando)}. "
            "Confira se o arquivo é o Estoque diário."
        )
    return df


def data_base_do_nome(nome_arquivo: str | None) -> str | None:
    """Extrai a data-base do nome do arquivo (ex.: 20260529_Estoque.xlsx)."""
    if not nome_arquivo:
        return None
    m = re.search(r"(20\d{2})(\d{2})(\d{2})", nome_arquivo)
    if not m:
        return None
    return f"{m.group(3)}/{m.group(2)}/{m.group(1)}"


def consolidar(df_bruto: pd.DataFrame) -> pd.DataFrame:
    """Retorna DataFrame [carteira, nome_grupo, emissor, valor] consolidado."""
    df = pd.DataFrame({
        "carteira": df_bruto["Carteira"].map(_normalizar_carteira),
        "nome_grupo": df_bruto["Nome Grupo"].fillna("").astype(str),
        "emissor": df_bruto["Emissor"].fillna("").astype(str),
        "valor": pd.to_numeric(df_bruto["Valor Mercado"], errors="coerce").fillna(0.0),
        "cod_papel": (df_bruto["Cod Papel"].fillna("").astype(str).str.strip()
                      if "Cod Papel" in df_bruto.columns else ""),
    })

    codigos_cota = set(P.COD_PAPEL_COTA.values())
    base = df[(df["carteira"] == P.CARTEIRA_CONSOLIDADA) & (~df["cod_papel"].isin(codigos_cota))]
    abertos = df[df["carteira"].isin(P.FUNDOS_LOOK_THROUGH)]
    partes = pd.concat([base, abertos], ignore_index=True)

    partes = partes[~partes["nome_grupo"].isin(P.GRUPOS_EXCLUIDOS)]
    tem_caixa = (partes["nome_grupo"].str.upper().str.contains("CAIXA")
                 | partes["emissor"].str.upper().str.contains("CAIXA"))
    partes = partes[~tem_caixa]

    partes = partes.assign(carteira=partes["carteira"].map(lambda c: P.DE_PARA.get(c, c)))
    consolidado = (partes.groupby(["carteira", "nome_grupo", "emissor"], as_index=False)["valor"].sum()
                   .sort_values("valor", ascending=False, ignore_index=True))
    return consolidado


# ---------------------------------------------------------------------------
# Classificação
# ---------------------------------------------------------------------------
def classificar_setor(emissor: str, nome_grupo: str) -> str:
    if nome_grupo and ("NTN" in nome_grupo or "LTN" in nome_grupo):
        return P.SOBERANO
    return P.SETOR.get(emissor, "Diversos")


def classificar_fundo(nome: str) -> str:
    if nome in P.TIPO_FUNDO_CONFIRMADO:
        return P.TIPO_FUNDO_CONFIRMADO[nome]
    n = (nome or "").upper()
    if "FIA" in n:
        return "Fundo de ações"
    if "FII" in n:
        return "Fundo imobiliário"
    if re.search(r"\bCP\b|CRE|CREDIT", n):
        return "Fundo de crédito privado"
    if re.search(r"\bDI\b", n):
        return "Fundo de renda fixa DI"
    if "FIM" in n or "MULTI" in n:
        return "Fundo multimercado"
    return "Fundo - a classificar"


def filtrar_soberano(consolidado: pd.DataFrame, excluir: bool) -> pd.DataFrame:
    if not excluir:
        return consolidado
    eh_soberano = [classificar_setor(e, g) == P.SOBERANO
                   for e, g in zip(consolidado["emissor"], consolidado["nome_grupo"])]
    return consolidado[[not x for x in eh_soberano]].reset_index(drop=True)


def agregar_emissores(consolidado: pd.DataFrame) -> pd.DataFrame:
    """Emissores diretos: tudo o que não é cota de fundo fechado."""
    diretos = consolidado[consolidado["nome_grupo"] != "Cotas"]
    if diretos.empty:
        return pd.DataFrame(columns=["emissor", "nome_grupo", "valor", "setor"])
    agg = (diretos.groupby("emissor", as_index=False, sort=False)
           .agg(nome_grupo=("nome_grupo", "first"), valor=("valor", "sum"))
           .sort_values("valor", ascending=False, ignore_index=True))
    agg["setor"] = [classificar_setor(e, g) for e, g in zip(agg["emissor"], agg["nome_grupo"])]
    return agg


def agregar_fundos(consolidado: pd.DataFrame) -> pd.DataFrame:
    """Fundos avaliados pela gestora: qualquer cota que sobrou no consolidado
    (da CERES CONSOLIDADA ou de dentro de um fundo aberto, como o Eros)."""
    cotas = consolidado[consolidado["nome_grupo"] == "Cotas"]
    if cotas.empty:
        return pd.DataFrame(columns=["nome", "valor", "origem", "tipo"])
    agg = (cotas.groupby("emissor", as_index=False, sort=False)
           .agg(valor=("valor", "sum"),
                origem=("carteira", lambda s: ", ".join(dict.fromkeys(s))))
           .rename(columns={"emissor": "nome"})
           .sort_values("valor", ascending=False, ignore_index=True))
    agg["tipo"] = agg["nome"].map(classificar_fundo)
    return agg


def exportar_excel(consolidado: pd.DataFrame, emissores: pd.DataFrame, fundos: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        consolidado.rename(columns={"carteira": "Carteira", "nome_grupo": "Nome Grupo",
                                    "emissor": "Emissor", "valor": "Valor Mercado"}) \
            .to_excel(xw, sheet_name="Consolidado", index=False)
        emissores.to_excel(xw, sheet_name="Emissores", index=False)
        fundos.to_excel(xw, sheet_name="Fundos gestora", index=False)
    return buf.getvalue()
