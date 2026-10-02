"""
Dupla materialidade, notas qualitativas e simulador de eventos ASG.

O score de cada eixo (financeiro e impacto) é a média das notas A/S/G
ponderada simultaneamente pela exposição de cada posição e pelo peso de
materialidade do setor (ou tipo de fundo) naquele eixo.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import parametros as P

DIMS = ("A", "S", "G")
NOME_DIM = {"A": "Ambiental", "S": "Social", "G": "Governança"}
PREFIXO_FUNDO = "FUNDO:"

# ---------------------------------------------------------------------------
# Notas qualitativas (persistidas em JSON local, ao lado do app)
# ---------------------------------------------------------------------------
ARQUIVO_NOTAS = Path(__file__).resolve().parent / "dados" / "notas_qualitativas_asg.json"


def carregar_notas(caminho: Path = ARQUIVO_NOTAS) -> dict:
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def salvar_notas(notas: dict, caminho: Path = ARQUIVO_NOTAS) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(notas, ensure_ascii=False, indent=1), encoding="utf-8")


def nota(notas: dict, chave: str, dim: str) -> float:
    return float(notas.get(chave, {}).get(dim, P.NOTA_NEUTRA))


def definir_nota(notas: dict, chave: str, dim: str, valor: float) -> None:
    valor = max(0.0, min(10.0, float(valor)))
    notas.setdefault(chave, {})[dim] = valor


def aplicar_avaliacao_referencia(notas: dict) -> int:
    """Carrega as notas pesquisadas em lote (uma única gravação depois)."""
    for emissor, av in P.AVALIACAO_REFERENCIA.items():
        for d in DIMS:
            definir_nota(notas, emissor, d, av[d])
    return len(P.AVALIACAO_REFERENCIA)


def eh_neutro(notas: dict, chave: str) -> bool:
    return all(nota(notas, chave, d) == P.NOTA_NEUTRA for d in DIMS)


# ---------------------------------------------------------------------------
# Cálculo
# ---------------------------------------------------------------------------
def score_ponderado(mat: dict | None, a: float, s: float, g: float) -> float | None:
    if not mat:
        return None
    soma = mat["A"] + mat["S"] + mat["G"]
    return None if soma == 0 else (a * mat["A"] + s * mat["S"] + g * mat["G"]) / soma


def _posicoes(emissores: pd.DataFrame, fundos: pd.DataFrame):
    """Gera (chave, categoria, valor, é_fundo) para todas as posições."""
    for e in emissores.itertuples(index=False):
        yield e.emissor, e.setor, float(e.valor), False
    for f in fundos.itertuples(index=False):
        yield PREFIXO_FUNDO + f.nome, f.tipo, float(f.valor), True


def calcular_eixo(emissores, fundos, notas, mat_setor, mat_fundo) -> dict:
    num = {d: 0.0 for d in DIMS}
    den = {d: 0.0 for d in DIMS}
    for chave, cat, valor, eh_fundo in _posicoes(emissores, fundos):
        mat = (mat_fundo if eh_fundo else mat_setor).get(cat)
        if not mat:
            continue
        for d in DIMS:
            peso = valor * mat[d]
            num[d] += peso * nota(notas, chave, d)
            den[d] += peso
    res = {d: (num[d] / den[d] if den[d] > 0 else None) for d in DIMS}
    res["geral"] = (sum(res[d] for d in DIMS) / 3) if all(res[d] is not None for d in DIMS) else None
    return res


def calcular_scores(emissores, fundos, notas) -> dict:
    return {
        "financeiro": calcular_eixo(emissores, fundos, notas,
                                    P.MATERIALIDADE_FINANCEIRA, P.MATERIALIDADE_FUNDO_FINANCEIRA),
        "impacto": calcular_eixo(emissores, fundos, notas,
                                 P.MATERIALIDADE_IMPACTO, P.MATERIALIDADE_FUNDO_IMPACTO),
    }


def tabela_com_scores(df: pd.DataFrame, notas: dict, eh_fundo: bool) -> pd.DataFrame:
    """Acrescenta notas A/S/G e os dois scores por linha (para exibição)."""
    out = df.copy()
    col_nome, col_cat = ("nome", "tipo") if eh_fundo else ("emissor", "setor")
    mf = P.MATERIALIDADE_FUNDO_FINANCEIRA if eh_fundo else P.MATERIALIDADE_FINANCEIRA
    mi = P.MATERIALIDADE_FUNDO_IMPACTO if eh_fundo else P.MATERIALIDADE_IMPACTO
    chaves = [(PREFIXO_FUNDO + n) if eh_fundo else n for n in out[col_nome]]
    for d in DIMS:
        out[d] = [nota(notas, c, d) for c in chaves]
    out["score_fin"] = [score_ponderado(mf.get(c), a, s, g)
                        for c, a, s, g in zip(out[col_cat], out["A"], out["S"], out["G"])]
    out["score_imp"] = [score_ponderado(mi.get(c), a, s, g)
                        for c, a, s, g in zip(out[col_cat], out["A"], out["S"], out["G"])]
    out["chave"] = chaves
    return out


def nivel(v: float | None) -> tuple[str, str]:
    """Leitura semáforo: (termo, classe css)."""
    if v is None:
        return "não apurável", "neutro"
    if v >= 7:
        return "favorável", "ok"
    if v >= 4:
        return "moderado", "atencao"
    return "exige atenção", "alerta"


# ---------------------------------------------------------------------------
# Simulador de impacto financeiro de eventos ASG
# ---------------------------------------------------------------------------
@dataclass
class ResultadoSimulacao:
    impacto_total: float
    detalhe: pd.DataFrame
    scores_pos: dict


def simular_evento(emissores, fundos, notas, choques: dict[str, float]) -> ResultadoSimulacao:
    e2 = emissores.copy()
    f2 = fundos.copy()
    e2["delta"] = [v * choques.get(s, 0.0) for v, s in zip(e2["valor"], e2["setor"])]
    f2["delta"] = [v * choques.get(t, 0.0) for v, t in zip(f2["valor"], f2["tipo"])]

    partes = []
    if not e2.empty:
        partes.append(e2.rename(columns={"setor": "categoria"})[["categoria", "valor", "delta"]])
    if not f2.empty:
        partes.append(f2.rename(columns={"tipo": "categoria"})[["categoria", "valor", "delta"]])
    base = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=["categoria", "valor", "delta"])
    afetados = base[base["delta"] != 0]
    detalhe = (afetados.groupby("categoria", as_index=False)
               .agg(exposicao=("valor", "sum"), impacto=("delta", "sum")))
    detalhe["choque"] = detalhe["categoria"].map(choques)
    detalhe = detalhe.sort_values("impacto", ignore_index=True)

    e2["valor"] = e2["valor"] + e2["delta"]
    f2["valor"] = f2["valor"] + f2["delta"]
    return ResultadoSimulacao(
        impacto_total=float(base["delta"].sum()) if not base.empty else 0.0,
        detalhe=detalhe,
        scores_pos=calcular_scores(e2.drop(columns="delta"), f2.drop(columns="delta"), notas),
    )


def categorias_simulaveis() -> list[str]:
    return sorted(set(P.MATERIALIDADE_FINANCEIRA) | set(P.MATERIALIDADE_FUNDO_FINANCEIRA))
