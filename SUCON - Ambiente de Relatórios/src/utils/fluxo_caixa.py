"""
Motor de cálculo do painel Fluxo de Caixa (Risco de Liquidez).

Sem dependência de Streamlit: usado pela página e pelo PDF.

Bases de comparação (ativo e passivo sempre na MESMA base)
-----------------------------------------------------------
- "nominal"  -> Fluxo de caixa: ativo = FINANCEIRO_PROJETADO (nominal);
                passivo = fluxo atuarial corrigido pela premissa de IPCA.
- "presente" -> Valor presente: ativo = FINANCEIRO_PRESENTE; passivo nominal
                descontado pela curva implícita nos títulos públicos
                (fator = Σ presente ÷ Σ projetado por data de pagamento).

Passivo
-------
FLUXO_PREVIDENCIAL_LIQUIDO (linha RAS com sinal invertido) = benefícios −
contribuições de assistidos. Opcionalmente, deduz CONTRIBUICOES_ATIVOS.
Ano da data-base: pro rata a partir da data-base; demais anos ÷ 12 ou 13 parcelas.

Fundos caixa D0 (opcional)
--------------------------
`caixa_d0` = {tesouraria: saldo}. Entra como recurso disponível no mês da
data-base (coluna CAIXA), somando a recebimentos, saldo acumulado e coberturas.
"""

from __future__ import annotations

import calendar
import re
from datetime import date

import numpy as np
import pandas as pd

from utils.fluxo_previdenciario import CONTRIBUICOES_ATIVOS, FLUXO_PREVIDENCIAL_LIQUIDO

# ── PREMISSAS (confirmar com a atuária) ──────────────────────────────────────
PREMISSAS = {
    # True: planilha em R$ constantes da data de referência; False: já nominal.
    "passivo_em_valores_reais": True,
    "data_referencia_passivo": date(2025, 12, 31),
    "ipca_aa": 0.04,
}

# Fundo investido pelos planos: somar seus recebimentos duplicaria fluxos.
EXCLUIR_DO_CONSOLIDADO = {"EROS FIM CREDITO PRIVADO"}

_PADRAO_PUBLICO = re.compile(r"^(NTN|NTNB|NTNF|NTNC|LTN|LFT|TESOURO)", re.IGNORECASE)
CATEGORIA_PUBLICO = "Títulos públicos"
CATEGORIA_PRIVADO = "Títulos privados"
BASES = {"nominal": "Fluxo de caixa (nominal)", "presente": "Valor presente"}


# ── UTILITÁRIOS ───────────────────────────────────────────────────────────────

def planos_com_fluxo() -> set[str]:
    return set(FLUXO_PREVIDENCIAL_LIQUIDO)


def classificar_emissor(produto_bruto, produto_nome=None) -> str:
    for texto in (produto_bruto, produto_nome):
        if texto is not None and _PADRAO_PUBLICO.match(str(texto).strip().replace("-", "")):
            return CATEGORIA_PUBLICO
    return CATEGORIA_PRIVADO


def _anos_entre(inicio, datas) -> np.ndarray:
    return ((pd.to_datetime(datas) - pd.Timestamp(inicio)) / pd.Timedelta(days=365.25)).to_numpy(dtype=float)


def _pesos_mensais(treze_parcelas: bool) -> np.ndarray:
    if treze_parcelas:
        pesos = np.full(12, 1 / 13)
        pesos[11] = 2 / 13
        return pesos
    return np.full(12, 1 / 12)


def _cobertura(recursos: float, necessidade: float) -> float:
    return recursos / necessidade if necessidade > 0 else np.nan


# ── ATIVO ─────────────────────────────────────────────────────────────────────

def preparar_recebimentos(df: pd.DataFrame, data_base: date, de_para_produto=None) -> pd.DataFrame:
    """Filtra a data-base e padroniza os eventos (mantém presente e projetado)."""
    colunas = ["TESOURARIA", "DATA_PAGAMENTO", "ANO", "MES", "PERIODO", "VALOR_PRESENTE", "VALOR_PROJETADO",
               "CATEGORIA", "EVENTO", "PRODUTO_NOME", "CODIGO", "VENCIMENTO"]
    if df is None or df.empty:
        return pd.DataFrame(columns=colunas)

    dados = df.copy()
    dados["DATA_COTACAO"] = pd.to_datetime(dados["DATA_COTACAO"]).dt.normalize()
    dados = dados[dados["DATA_COTACAO"] == pd.Timestamp(data_base)]
    dados["DATA_PAGAMENTO"] = pd.to_datetime(dados["DATA_PAGAMENTO"]).dt.normalize()
    dados["VENCIMENTO"] = pd.to_datetime(dados["VENCIMENTO"], errors="coerce").dt.normalize()
    dados = dados[dados["DATA_PAGAMENTO"] >= pd.Timestamp(data_base)]

    dados["VALOR_PRESENTE"] = pd.to_numeric(dados["FINANCEIRO_PRESENTE"], errors="coerce").fillna(0.0)
    dados["VALOR_PROJETADO"] = pd.to_numeric(dados["FINANCEIRO_PROJETADO"], errors="coerce").fillna(0.0)
    dados["ANO"] = dados["DATA_PAGAMENTO"].dt.year
    dados["MES"] = dados["DATA_PAGAMENTO"].dt.month
    dados["PERIODO"] = dados["DATA_PAGAMENTO"].dt.to_period("M")

    mapear = de_para_produto or (lambda x: x)
    dados["PRODUTO_NOME"] = dados["PRODUTO"].apply(mapear)
    dados["CATEGORIA"] = [classificar_emissor(b, n) for b, n in zip(dados["PRODUTO"], dados["PRODUTO_NOME"])]
    mesmo_mes = dados["VENCIMENTO"].dt.to_period("M") == dados["PERIODO"]
    dados["EVENTO"] = np.where(mesmo_mes, "Vencimento", "Cupom/juros")
    return dados[colunas].reset_index(drop=True)


def curva_desconto(receb: pd.DataFrame, data_base: date):
    """
    Curva nominal implícita: fator = Σ presente ÷ Σ projetado por data (títulos
    públicos; se não houver, todos). Taxa contínua interpolada no prazo, com
    extrapolação flat. Retorna função datas -> fator de desconto.
    """
    base = receb[receb["CATEGORIA"] == CATEGORIA_PUBLICO]
    if base.empty:
        base = receb
    g = base.groupby("DATA_PAGAMENTO")[["VALOR_PRESENTE", "VALOR_PROJETADO"]].sum()
    g = g[(g["VALOR_PROJETADO"] > 0) & (g["VALOR_PRESENTE"] > 0)]
    t = _anos_entre(data_base, g.index)
    fator = (g["VALOR_PRESENTE"] / g["VALOR_PROJETADO"]).to_numpy()
    ok = (t >= 0.1) & (fator > 0) & (fator <= 1.0001)
    t, taxa = t[ok], -np.log(np.minimum(fator[ok], 1.0)) / t[ok]

    def fator_desconto(datas) -> np.ndarray:
        prazo = np.maximum(_anos_entre(data_base, datas), 0.0)
        if len(t) == 0:
            return np.ones_like(prazo)
        return np.exp(-np.interp(prazo, t, taxa) * prazo)

    return fator_desconto


# ── PASSIVO ───────────────────────────────────────────────────────────────────

def passivo_mensal(
    planos: list[str],
    data_base: date,
    treze_parcelas: bool = False,
    ano_fim: int | None = None,
    deduzir_contrib_ativos: bool = False,
    ipca_aa: float | None = None,
) -> pd.DataFrame:
    """Necessidade líquida mensal em valores do estudo (REAL) e nominais (NOMINAL)."""
    pesos = _pesos_mensais(treze_parcelas)
    dias_mes_base = calendar.monthrange(data_base.year, data_base.month)[1]
    fracao_inicial = (dias_mes_base - data_base.day + 1) / dias_mes_base
    registros = []

    for plano in planos:
        serie = FLUXO_PREVIDENCIAL_LIQUIDO.get(plano)
        if not serie:
            continue
        ativos = CONTRIBUICOES_ATIVOS.get(plano, {}) if deduzir_contrib_ativos else {}
        for ano, valor in serie.items():
            if ano < data_base.year or (ano_fim is not None and ano > ano_fim):
                continue
            valor_anual = valor - ativos.get(ano, 0.0)
            for mes in range(1, 13):
                if ano == data_base.year and mes < data_base.month:
                    continue
                v = valor_anual * pesos[mes - 1]
                dia_medio = 15
                if ano == data_base.year and mes == data_base.month:
                    v *= fracao_inicial
                    dia_medio = (data_base.day + dias_mes_base) // 2
                registros.append((plano, ano, mes, date(ano, mes, dia_medio), v))

    df = pd.DataFrame(registros, columns=["TESOURARIA", "ANO", "MES", "DATA_MEDIA", "REAL"])
    if df.empty:
        return df.assign(PERIODO=pd.Series(dtype="period[M]"), NOMINAL=pd.Series(dtype=float))

    df["PERIODO"] = pd.to_datetime(df["DATA_MEDIA"]).dt.to_period("M")
    ipca = PREMISSAS["ipca_aa"] if ipca_aa is None else ipca_aa
    if PREMISSAS["passivo_em_valores_reais"] and ipca:
        prazo = np.maximum(_anos_entre(PREMISSAS["data_referencia_passivo"], df["DATA_MEDIA"]), 0.0)
        df["NOMINAL"] = df["REAL"] * (1 + ipca) ** prazo
    else:
        df["NOMINAL"] = df["REAL"]
    return df


def _necessidade_na_base(passivo: pd.DataFrame, base: str, fator_desconto) -> pd.Series:
    if base == "presente":
        return passivo["NOMINAL"] * fator_desconto(passivo["DATA_MEDIA"])
    return passivo["NOMINAL"]


# ── BASE MENSAL ──────────────────────────────────────────────────────────────

def base_mensal_por_plano(receb, passivo, data_base, ano_fim, caixa_d0=None) -> pd.DataFrame:
    """Ativo, caixa e passivo por plano e mês (meses sem evento = zero)."""
    cols = ["PUBLICOS", "PRIVADOS", "CAIXA", "NECESSIDADE"]
    r = (
        receb[receb["ANO"] <= ano_fim]
        .pivot_table(index=["TESOURARIA", "PERIODO"], columns="CATEGORIA", values="VALOR", aggfunc="sum", fill_value=0.0)
        .reindex(columns=[CATEGORIA_PUBLICO, CATEGORIA_PRIVADO], fill_value=0.0)
        .rename(columns={CATEGORIA_PUBLICO: "PUBLICOS", CATEGORIA_PRIVADO: "PRIVADOS"})
    ) if not receb.empty else pd.DataFrame(columns=["PUBLICOS", "PRIVADOS"])
    p = passivo.groupby(["TESOURARIA", "PERIODO"])["NECESSIDADE"].sum() if not passivo.empty else pd.Series(dtype=float, name="NECESSIDADE")

    periodo_base = pd.Period(data_base, "M")
    c = pd.Series(
        {(t, periodo_base): v for t, v in (caixa_d0 or {}).items() if v},
        dtype=float, name="CAIXA",
    )
    base = pd.concat([r, c, p], axis=1).fillna(0.0)
    if base.empty:
        return pd.DataFrame(columns=["TESOURARIA", "PERIODO", *cols])
    base.index = base.index.set_names(["TESOURARIA", "PERIODO"])
    base = base.reindex(columns=cols, fill_value=0.0).reset_index()

    periodos = pd.period_range(periodo_base, pd.Period(f"{ano_fim}-12", "M"), freq="M")
    grade = pd.MultiIndex.from_product([base["TESOURARIA"].unique(), periodos], names=["TESOURARIA", "PERIODO"])
    return base.set_index(["TESOURARIA", "PERIODO"]).reindex(grade, fill_value=0.0).reset_index()


def _metricas_fluxo(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "CAIXA" not in df:
        df["CAIXA"] = 0.0
    df["RECEBIMENTOS"] = df["PUBLICOS"] + df["PRIVADOS"]
    df["RECURSOS"] = df["RECEBIMENTOS"] + df["CAIXA"]
    df["SALDO"] = df["RECURSOS"] - df["NECESSIDADE"]
    df["SALDO_ACUM"] = df["SALDO"].cumsum()
    df["COBERTURA"] = df["RECURSOS"] / df["NECESSIDADE"].where(df["NECESSIDADE"] > 0)
    if "PERIODO" in df.columns:
        df["ANO"] = df["PERIODO"].dt.year
        df["MES"] = df["PERIODO"].dt.month
    return df


def consolidar(base_plano: pd.DataFrame, planos: list[str]) -> pd.DataFrame:
    df = (
        base_plano[base_plano["TESOURARIA"].isin(planos)]
        .groupby("PERIODO", as_index=False)[["PUBLICOS", "PRIVADOS", "CAIXA", "NECESSIDADE"]]
        .sum()
        .sort_values("PERIODO")
    )
    return _metricas_fluxo(df)


def anual(mensal: pd.DataFrame) -> pd.DataFrame:
    df = mensal.groupby("ANO", as_index=False)[["PUBLICOS", "PRIVADOS", "CAIXA", "NECESSIDADE"]].sum()
    df = _metricas_fluxo(df)
    return df


# ── INDICADORES ───────────────────────────────────────────────────────────────

def _necessidade_liquidez(mensal: pd.DataFrame, meses: int) -> tuple[float, object]:
    """Maior déficit acumulado na janela (valor positivo) e o mês em que ocorre."""
    janela = mensal.head(meses)
    if janela.empty or janela["SALDO_ACUM"].min() >= 0:
        return 0.0, None
    idx = janela["SALDO_ACUM"].idxmin()
    return float(-janela.at[idx, "SALDO_ACUM"]), janela.at[idx, "PERIODO"]


def _duration(prazos: np.ndarray, valores_pv: np.ndarray) -> float:
    total = np.nansum(valores_pv)
    return float(np.nansum(prazos * valores_pv) / total) if total > 0 else np.nan


def indicadores(mensal, receb, planos, data_base, fator_desconto, base, passivo_total) -> dict:
    """KPIs de 12 meses, 24 meses, 5 anos e prazos."""
    tem_passivo = passivo_total["REAL"].sum() > 0 if not passivo_total.empty else False
    doze, cinco = mensal.head(12), mensal.head(60)
    liq12, mes12 = _necessidade_liquidez(mensal, 12)
    liq24, mes24 = _necessidade_liquidez(mensal, 24)

    anos_completos = mensal.groupby("ANO").filter(lambda g: len(g) == 12)
    an = anual(anos_completos) if not anos_completos.empty else anual(mensal)
    deficit = an.loc[(an["NECESSIDADE"] > 0) & (an["SALDO"] < 0), "ANO"]

    receb_p = receb[receb["TESOURARIA"].isin(planos)]
    dur_ativo = _duration(_anos_entre(data_base, receb_p["DATA_PAGAMENTO"]), receb_p["VALOR_PRESENTE"].to_numpy())
    pv_passivo = (passivo_total["NOMINAL"] * fator_desconto(passivo_total["DATA_MEDIA"])).to_numpy() if tem_passivo else np.array([])
    dur_passivo = _duration(_anos_entre(data_base, passivo_total["DATA_MEDIA"]), pv_passivo) if tem_passivo else np.nan

    ult_ano = int(receb_p["ANO"].max()) if not receb_p.empty else data_base.year
    nec_base = _necessidade_na_base(passivo_total, base, fator_desconto) if tem_passivo else pd.Series(dtype=float)
    nec_pos = nec_base[passivo_total["ANO"] > ult_ano].sum() if tem_passivo else 0.0
    nec_tot = nec_base.sum() if tem_passivo else 0.0

    return {
        "tem_passivo": bool(tem_passivo),
        "caixa": float(mensal["CAIXA"].sum()),
        "receb_12m": doze["RECEBIMENTOS"].sum(),
        "recursos_12m": doze["RECURSOS"].sum(),
        "nec_12m": doze["NECESSIDADE"].sum(),
        "saldo_12m": doze["SALDO"].sum(),
        "cobertura_12m": _cobertura(doze["RECURSOS"].sum(), doze["NECESSIDADE"].sum()),
        "liquidez_12m": liq12, "liquidez_12m_mes": mes12,
        "liquidez_24m": liq24, "liquidez_24m_mes": mes24,
        "cobertura_5a": _cobertura(cinco["RECURSOS"].sum(), cinco["NECESSIDADE"].sum()),
        "primeiro_ano_deficit": int(deficit.iloc[0]) if not deficit.empty else None,
        "duration_ativo": dur_ativo,
        "duration_passivo": dur_passivo,
        "ultimo_ano_receb": ult_ano,
        "nec_pos_receb_pct": nec_pos / nec_tot if nec_tot > 0 else np.nan,
        "nec_pos_receb": nec_pos,
    }


def composicao(receb: pd.DataFrame, planos: list[str], ano_fim: int) -> dict[str, pd.DataFrame]:
    r = receb[receb["TESOURARIA"].isin(planos) & (receb["ANO"] <= ano_fim)]
    total = r["VALOR"].sum()

    def _pct(df):
        df["PCT"] = df["VALOR"] / total if total else 0.0
        return df

    return {
        "categoria": _pct(r.groupby("CATEGORIA", as_index=False)["VALOR"].sum()),
        "evento": _pct(r.groupby(["CATEGORIA", "EVENTO"], as_index=False)["VALOR"].sum()),
        "produtos": _pct(r.groupby(["PRODUTO_NOME", "CATEGORIA"], as_index=False)["VALOR"].sum()
                         .sort_values("VALOR", ascending=False).head(10)),
        "datas": _pct(r.groupby("DATA_PAGAMENTO", as_index=False)["VALOR"].sum()
                      .sort_values("VALOR", ascending=False).head(10)),
    }


# ── ORQUESTRAÇÃO ─────────────────────────────────────────────────────────────

def calcular_painel(
    df_recebimentos: pd.DataFrame,
    data_base: date,
    plano: str,
    ano_fim: int,
    base: str = "nominal",
    treze_parcelas: bool = False,
    consolidado_so_com_fluxo: bool = True,
    deduzir_contrib_ativos: bool = False,
    ipca_aa: float | None = None,
    caixa_d0: dict[str, float] | None = None,
    de_para_produto=None,
) -> dict:
    """Executa todo o cálculo. `plano="[CONSOLIDADO]"` agrega os planos."""
    receb = preparar_recebimentos(df_recebimentos, data_base, de_para_produto)
    fator = curva_desconto(receb, data_base)
    receb["VALOR"] = receb["VALOR_PRESENTE"] if base == "presente" else receb["VALOR_PROJETADO"]

    todas = sorted(set(receb["TESOURARIA"]) | planos_com_fluxo() | set(caixa_d0 or {}))
    if plano == "[CONSOLIDADO]":
        planos_calc = [p for p in todas if p not in EXCLUIR_DO_CONSOLIDADO]
        if consolidado_so_com_fluxo:
            planos_calc = [p for p in planos_calc if p in planos_com_fluxo()]
    else:
        planos_calc = [plano]

    opc = dict(treze_parcelas=treze_parcelas, deduzir_contrib_ativos=deduzir_contrib_ativos, ipca_aa=ipca_aa)
    passivo_total = passivo_mensal(todas, data_base, **opc)
    passivo_total["NECESSIDADE"] = _necessidade_na_base(passivo_total, base, fator) if not passivo_total.empty else []
    passivo_h = passivo_total[passivo_total["ANO"] <= ano_fim]

    base_plano = base_mensal_por_plano(receb, passivo_h, data_base, ano_fim, caixa_d0)
    mensal = consolidar(base_plano, planos_calc)

    def kpis(planos):
        m = mensal if planos == planos_calc else consolidar(base_plano, planos)
        return indicadores(m, receb, planos, data_base, fator, base,
                           passivo_total[passivo_total["TESOURARIA"].isin(planos)])

    ranking = []
    for p in [p for p in todas if p not in EXCLUIR_DO_CONSOLIDADO]:
        k = kpis([p])
        ranking.append({"TESOURARIA": p, **{c: k[c] for c in (
            "tem_passivo", "caixa", "receb_12m", "nec_12m", "cobertura_12m", "liquidez_12m",
            "liquidez_24m", "cobertura_5a", "primeiro_ano_deficit", "duration_ativo", "duration_passivo")}})

    return {
        "data_base": data_base, "plano": plano, "ano_fim": ano_fim, "base": base,
        "treze_parcelas": treze_parcelas, "deduzir_contrib_ativos": deduzir_contrib_ativos,
        "ipca_aa": PREMISSAS["ipca_aa"] if ipca_aa is None else ipca_aa,
        "premissas": PREMISSAS, "com_caixa": bool(caixa_d0),
        "planos_calculo": planos_calc,
        "receb": receb,
        "mensal": mensal,
        "anual": anual(mensal),
        "kpis": kpis(planos_calc),
        "ranking": pd.DataFrame(ranking),
        "composicao": composicao(receb, planos_calc, ano_fim),
    }