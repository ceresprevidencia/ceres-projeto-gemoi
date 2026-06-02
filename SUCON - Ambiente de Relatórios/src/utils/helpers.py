from datetime import date, timedelta


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

def get_css_global():
    """
    CSS GLOBAL - Estrutura base do site
    Use no início de cada página.
    """
    return """
    <style>
        /* ============================================================================
           FONT IMPORTS
           ============================================================================ */
        @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600;700&display=swap');

        /* ============================================================================
           GLOBAL STYLES
           ============================================================================ */
        html, body, [data-testid="stMarkdownContainer"] p, .stText, label {
            font-family: 'Figtree', sans-serif !important;
        }


        /* ============================================================================
           RESPONSIVE - TABLETS (≤ 1200px)
           ============================================================================ */
        @media (max-width: 1200px) {
            .th-custom div, .col-custom {
                padding: 10px;
                font-size: 13px;
                min-height: 38px;
            }

            .col-custom:first-child {
                padding-left: 15px;
            }
        }

        /* ============================================================================
           RESPONSIVE - MOBILE (≤ 768px)
           ============================================================================ */
        @media (max-width: 768px) {
            .th-custom div, .col-custom {
                padding: 8px;
                font-size: 11px;
                min-height: 35px;
            }

            .col-custom:first-child {
                padding-left: 10px;
            }
        }

        /* ============================================================================
           RESPONSIVE - SMALL MOBILE (≤ 480px)
           ============================================================================ */
        @media (max-width: 480px) {
            .th-custom div, .col-custom {
                padding: 6px;
                font-size: 9px;
                min-height: 32px;
            }

            .col-custom:first-child {
                padding-left: 6px;
            }
        }
    </style>
    """



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


def gerar_tabela_estilizada(df, nomes_colunas=None, primeira_coluna_larga=True):
    import pandas as pd

    if nomes_colunas is None:
        nomes_colunas = {col: col for col in df.columns}

    num_colunas = len(df.columns)
    primeira = "2fr" if primeira_coluna_larga else "1fr"
    resto = " ".join(["1fr"] * (num_colunas - 1))
    grid = f"{primeira} {resto}" if num_colunas > 1 else "1fr"

    css = """
    <style>
        /* ========== CONTAINER EXTERNO DA TABELA ========== */
        .tabela-custom-wrapper {
            overflow: hidden;      /* Remove scrollbar da borda */
            width: 100%;           /* Ocupa toda a largura disponível */
            border-radius: 10px;   /* Arredonda as pontas (visualmente não aparece) */
        }
        
        /* ========== CABEÇALHO (HEADER) ========== */
        .th-custom {
            background-color: #0B2F13;  /* Cor de fundo verde escuro */
            color: #A8EC7D;             /* Cor do texto verde claro */
            display: grid;              /* Layout em grid para alinhar colunas */
            align-items: center;        /* Centraliza verticalmente */
            flex-shrink: 0;             /* Não diminui de tamanho */
            padding-left: 12px;         /* Espaço à esquerda do cabeçalho */
        }
        
        /* CÉLULAS DO CABEÇALHO (cada coluna) */
        .th-custom div {
            padding: 12px;                        /* Espaço interno das células */
            text-align: center;                   /* Centraliza texto horizontalmente */
            font-family: 'Figtree', sans-serif;   /* Fonte customizada */
            font-size: 14px;                      /* Tamanho da letra */
            word-wrap: break-word;                /* Quebra palavras longas */
            overflow-wrap: break-word;           /* Alternativa para quebra de palavras */
            word-break: break-word;               /* Quebra no meio da palavra se necessário */
            display: flex;                        /* Layout flexível */
            align-items: center;                  /* Centraliza verticalmente */
            justify-content: center;              /* Centraliza horizontalmente */
            min-height: 43px;                     /* Altura mínima da célula */
        }
        
        /* PRIMEIRA COLUNA DO CABEÇALHO */
        .th-custom div:first-child {
            justify-content: flex-start;  /* Alinha à esquerda */
            padding-left: 20px;           /* Espaço maior à esquerda */
        }
        
        /* ========== LINHAS DE DADOS ========== */
        .row-custom {
            display: grid;                           /* Layout em grid para alinhar colunas */
            align-items: center;                     /* Centraliza verticalmente */
            background-color: transparent;          /* Sem cor de fundo */
            transition: background-color 0.15s ease;/* Transição suave ao hover */
            padding-left: 15px;
            
        }
        
        /* EFEITO HOVER (quando passa mouse em uma linha) */
        .row-custom:hover {
            background-color: rgba(11, 47, 19, 0.04);  /* Cor verde muito suave (quase branco) */
        }
        
        /* ÚLTIMA LINHA (com borda verde escuro) */
        .row-custom:last-child {
            border-bottom: 14px solid #0B2F13;  /* Borda verde escuro proporcional à tabela */
        }
        
        /* ========== CÉLULAS DE DADOS ========== */
        .col-custom {
            padding: 10px 14px;                       /* Espaço interno: 10px acima/abaixo, 14px esquerda/direita */
            font-family: 'Figtree', sans-serif;       /* Fonte customizada */
            font-size: 13px;                          /* Tamanho da letra */
            display: flex;                            /* Layout flexível */
            align-items: center;                      /* Centraliza verticalmente */
            justify-content: center;                  /* Centraliza horizontalmente */
            min-height: 42px;                         /* Altura mínima */
            word-break: break-word;                   /* Quebra palavras longas */
        }
        
        /* PRIMEIRA COLUNA DE DADOS */
        .col-custom:first-child {
            justify-content: flex-start;  /* Alinha à esquerda */
            padding-left: 20px;           /* Espaço maior à esquerda */
            font-weight: normal;          /* Peso normal (não negrito) */
        }
        
        /* ========== RESPONSIVIDADE - TELAS PEQUENAS (768px ou menos) ========== */
        @media (max-width: 768px) {
            .th-custom div, .col-custom {
                font-size: 11px;          /* Fonte menor em telas pequenas */
                padding: 8px;             /* Padding menor */
                min-height: 35px;         /* Altura menor */
            }
            .th-custom div:first-child, .col-custom:first-child {
                padding-left: 10px;       /* Padding menor na primeira coluna */
            }
        }
    </style>
    """

    html = css
    html += '<div class="tabela-custom-wrapper">'

    # Cabeçalho
    html += f'<div class="th-custom" style="grid-template-columns:{grid};">'
    for col in df.columns:
        html += f'<div>{nomes_colunas.get(col, col)}</div>'
    html += '</div>'

    # Linhas
    for _, row in df.iterrows():
        html += f'<div class="row-custom" style="grid-template-columns:{grid};">'
        for col in df.columns:
            valor = row[col]
            if isinstance(valor, (int, float)) and not pd.isna(valor):
                col_lower = col.lower()
                if 'r$' in col_lower or '%' in col_lower:
                    valor_fmt = fmt_br(valor, 2)
                else:
                    valor_fmt = f"{valor:.2f}"
            else:
                valor_fmt = str(valor) if pd.notna(valor) else "—"
            html += f'<div class="col-custom">{valor_fmt}</div>'
        html += '</div>'

    html += '</div>'
    return html


def primeiro_dia_util(ano: int) -> date:
    feriados_fixos = {
        (1, 1),   
    }
    dia = date(ano, 1, 1)
    while True:
        if dia.weekday() >= 5:         
            dia += timedelta(days=1)
            continue
        if (dia.day, dia.month) in feriados_fixos:
            dia += timedelta(days=1)
            continue
        return dia