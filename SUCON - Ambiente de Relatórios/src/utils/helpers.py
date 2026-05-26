def estilizar_tabela(styled):
    """Aplica fonte Figtree e estilos visuais ao Styler com a 1ª coluna à esquerda."""
    
    # Pegamos o nome da primeira coluna dinamicamente
    primeira_coluna = styled.data.columns[0]

    return styled.set_properties(**{
        'font-family': 'Figtree, sans-serif',
        'font-size': '14px',
        'text-align': 'center',
        'padding': '8px',
    }).set_properties(
        subset=[primeira_coluna], # Aplica apenas na primeira coluna
        **{'text-align': 'left'}  # Sobrescreve para alinhamento à esquerda
    ).set_table_styles([
        {'selector': 'th', 'props': [
            ('font-family', 'Figtree, sans-serif'),
            ('font-size', '14px'),
            ('padding', '8px'),
            ('background-color', '#016837'),
            ('color', '#ffffff'),
            ('border-bottom', '2px solid #014d2a'),
            ('text-align', 'center'), # Cabeçalhos centralizados por padrão
        ]},
        {'selector': 'th:first-child', 'props': [
            ('border-top-left-radius', '10px'),
            ('text-align', 'center'), # Alinha o cabeçalho da 1ª coluna à esquerda
        ]},
        {'selector': 'th:last-child', 'props': [
            ('border-top-right-radius', '10px'),
        ]},
        {'selector': 'tr:last-child td:first-child', 'props': [
            ('border-bottom-left-radius', '10px'),
        ]},
        {'selector': 'tr:last-child td:last-child', 'props': [
            ('border-bottom-right-radius', '10px'),
        ]},
        {'selector': 'table', 'props': [
            ('width', '100%'),
            ('border-collapse', 'separate'),
            ('border-spacing', '0'),
            ('border-radius', '10px'),
            ('overflow', 'hidden'),
        ]},
        {'selector': 'td', 'props': [
            ('border-bottom', '1px solid #eee'),
            ('transition', 'background-color 0.2s ease'),
        ]},
        {'selector': 'tbody tr:hover td', 'props': [
            ('background-color', 'rgba(1, 104, 55, 0.1)'),
        ]},
    ]).hide(axis='index')

def get_css_responsivo():
    """Retorna o CSS responsivo para tabelas."""
    return """
<style>
.tabela-responsiva {
    width: 100%;
    overflow-x: auto;
    display: block;
}

.tabela-responsiva table {
    width: 100%;
    border-collapse: collapse;
}

.tabela-responsiva table td,
.tabela-responsiva table th {
    padding: 12px;
    text-align: center;
    word-wrap: break-word;
    overflow-wrap: break-word;
    word-break: break-word;
}

@media (max-width: 1200px) {
    .tabela-responsiva table td,
    .tabela-responsiva table th {
        padding: 10px;
        font-size: 13px;
    }
}

@media (max-width: 768px) {
    .tabela-responsiva {
        font-size: 11px;
    }
    
    .tabela-responsiva table td,
    .tabela-responsiva table th {
        padding: 6px;
    }
}

@media (max-width: 480px) {
    .tabela-responsiva {
        font-size: 9px;
    }
    
    .tabela-responsiva table td,
    .tabela-responsiva table th {
        padding: 4px;
    }
}
</style>
"""

def aplicar_destaque(df_exibir, mask_desenquadrado):
    """Aplica background vermelho nas linhas desenquadradas e estiliza a tabela."""
    styled = df_exibir.style.apply(
        lambda row: ["background-color: #ffcccc"] * len(row)
        if mask_desenquadrado.loc[row.name] else [""] * len(row),
        axis=1
    )
    return estilizar_tabela(styled)

def remove_grp(palavra):
    if 'grupo' in palavra.lower():
        grupo = palavra.split('=')[-1]
    return grupo      

def limpar_texto(texto):
    if 'Art.' in texto:
        return str(texto)[8:]
    else:
        return texto

def formatar_percentual_br(valor):
    if valor is None:
        return "—"
    valor_formatado = str(valor).replace('.', ',')
    return f"{valor_formatado}%"


def fmt_br(valor, decimais=2):
    import pandas as pd
    """Formata número para padrão brasileiro (vírgula decimal, ponto de milhar)"""
    if pd.isna(valor):
        return "—"
    if decimais == 0:
        resultado = f"{valor:,.0f}"
    else:
        resultado = f"{valor:,.{decimais}f}"
    # Trocar ponto por vírgula e vice-versa
    return resultado.replace(",", "X").replace(".", ",").replace("X", ".") 


def nome_plano(valor_original):
    """Extrai a parte após 'Tesouraria=' (se existir) e mapeia para nome amigável."""
    NOMES_PLANOS = {
    "Ceres FlexCeres_CV": "Ceres FlexCeres",
    "Epagri Saldado_BD": "Epagri Saldado",
    "Epagri Básico_BD": "Epagri Básico",
    "Epamig Básico_BD": "Epamig Básico",
    "Embrapa FlexCeres_CV": "Embrapa FlexCeres",
    "ABDI FlexCeres_CD": "ABDI FlexCeres",
    "Cidasc FlexCeres_CV": "Cidasc FlexCeres",
    "Epamig FlexCeres_CV": "Epamig FlexCeres",
    "Emater DF FlexCeres_CV": "EmaterDF FlexCeres",
    "Ceres Básico_BD": "Ceres Básico",
    "Emater MG Básico_BD": "EmaterMG Básico",
    "Família Ceres_CD": "Família Ceres",
    "Epagri FlexCeres_CV": "Epagri FlexCeres",
    "Embrapa Básico_BD": "Embrapa Básico",
    "Emater MG FlexCeres_CV": "EmaterMG FlexCeres",
    "Epamig Saldado_BD": "Epamig Saldado",
    "Emater MG Saldado_BD": "EmaterMG Saldado",
    "PGA": "PGA",
    "[CERES TOTAL]": "Consolidado"
}

    chave = valor_original.split("=", 1)[-1] if "=" in valor_original else valor_original
    return NOMES_PLANOS.get(chave, chave)



