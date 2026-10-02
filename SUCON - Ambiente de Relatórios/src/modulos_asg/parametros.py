"""
Parâmetros do Índice de Materialidade e Impacto ASG.

Centraliza tudo o que é calibração ou cadastro (DE-PARA de carteiras,
classificação setorial, matrizes de dupla materialidade, cenários do
simulador e avaliação qualitativa de referência). Alterar um peso ou
incluir um emissor novo é sempre aqui, nunca na lógica de cálculo.

Referência normativa: Portaria Previc nº 728/2026 (arts. 9º e 10) e
Resolução Previc nº 23/2023, com redação da Resolução Previc nº 26/2025.
"""

# ---------------------------------------------------------------------------
# Consolidação da carteira
# ---------------------------------------------------------------------------
DE_PARA = {
    '9120': 'EROS FIM CRÉDITO PRIVADO',
    '9122': 'FI AGROCIENCIA AÇÕES',
    '9123': 'CONSOLIDADA FDOS EXCLUSIVOS CERES',
    '9124': 'CERES CONSOLIDADA',
    '9128': 'CERES - EMBRAPA BASICO',
    '9129': 'CERES - EMBRAPA FLEXCERES',
    '9130': 'CERES - CERES BASICO',
    '9139': 'CERES - CERES FLEXCERES',
    '9140': 'CERES - EPAGRI BASICO',
    '9143': 'CERES - EPAGRI SALDADO',
    '9148': 'CERES - EPAGRI FLEXCERES',
    '9149': 'CERES - EMATER BASICO',
    '9150': 'CERES - EMATER SALDADO',
    '9151': 'CERES - EMATER FLEXCERES',
    '9152': 'CERES - EPAMIG BASICO',
    '9153': 'CERES - EPAMIG SALDADO',
    '9154': 'CERES - EPAMIG FLEXCERES',
    '9156': 'CERES - CIDASC FLEXCERES',
    '9157': 'CERES - ADMINISTRATIVO',
    '10657': 'CERES ABDI-FLEXCERES',
    '11431': 'CERES - EMATERDF FLEXCERES',
    '15615': 'PLANO FAMÍLIA CERES',
    '18977': 'CHAPADA DOS VEADEIROS FIF AÇÕES',
    '18995': 'OCEANA SERRA DA CAPIVARA FIF AÇÕES',
    '18996': 'SERRA DO CIPO FIF AÇÕES',
    '19016': 'TIJUCA FIF AÇÕES',
}

CARTEIRA_CONSOLIDADA = "9124"
FUNDOS_LOOK_THROUGH = ["9120", "9122", "18977", "18995", "18996", "19016"]
COD_PAPEL_COTA = {
    "9120": "009120", "9122": "009122", "18977": "CA018977",
    "18995": "018995", "18996": "018996", "19016": "019016",
}
GRUPOS_EXCLUIDOS = ["Evolução de Cotas", "CONT_REC_PAG", "Empréstimo  - D", "OP_FUT"]
ABA_PREFERENCIAL = "Posição de Ativos"

SOBERANO = "Soberano - título público federal"

# ---------------------------------------------------------------------------
# Classificação setorial dos emissores diretos (chave = texto do Estoque)
# ---------------------------------------------------------------------------
SETOR = {
    'BANCO BRADESCO S.A.': 'Bancos',
    'BANCO BTG PACTUAL': 'Bancos',
    'PARANÁ BANCO S/A': 'Bancos',
    'BANCO DAYCOVAL S/A': 'Bancos',
    'BANCO SANTANDER (BRASIL) S/A': 'Bancos',
    'BANCO SAFRA S/A': 'Bancos',
    'BANCO ABC BRASIL S.A.': 'Bancos',
    'BANCO PAN SA': 'Bancos',
    'ITAU UNIBANCO PN N1': 'Bancos',
    'ITAUSAPN      N1': 'Bancos',
    'BRADESCOPN  EB  N1': 'Bancos',
    'SANTANDER UNT     N2': 'Bancos',
    'BTGP BANCO  UNT     N2': 'Bancos',
    'BRASILON  EJ  NM': 'Bancos',
    'INTER CO    DR2 ATZ': 'Bancos',
    'BRASIL SEGURIDADE ON': 'Seguros',
    'BRADSAUDE ON NM': 'Saúde',
    'ENEVA S.A. ON': 'Energia elétrica',
    'EQUATORIALON      N2': 'Energia elétrica',
    'ENERGISA    UNT': 'Energia elétrica',
    'AURE3  ON': 'Energia elétrica',
    'CPFL ENERGIAON      NM': 'Energia elétrica',
    'ENGIE BRASILON      NM': 'Energia elétrica',
    'ISA ENERGIA PN': 'Energia elétrica',
    'COPELON *': 'Energia elétrica',
    'CEMIGPN    N1': 'Energia elétrica',
    'SERENA      ON      NM': 'Energia elétrica',
    'SABESPON *    NM': 'Saneamento',
    'COPASAON      NM': 'Saneamento',
    'VIBRA ON NM': 'Petróleo e combustíveis',
    'PETROBRASPN': 'Petróleo e combustíveis',
    'PETROBRASON': 'Petróleo e combustíveis',
    'PETRORIO ON NM': 'Petróleo e combustíveis',
    'VALE R DOCEON      N1': 'Mineração',
    'SUZANO PAPELON  I06 N1': 'Papel e celulose',
    'CONCESSIONARIA ROTA DAS BANDEIRAS S': 'Concessões e infraestrutura',
    'MOTV ON': 'Concessões e infraestrutura',
    'LOCALIZA RENT A CAR SA': 'Transporte e logística',
    'RENT - LOCALIZA RENT A CAR SA': 'Transporte e logística',
    'LOCALIZAON      NM': 'Transporte e logística',
    'RUMO SA     ON': 'Transporte e logística',
    'TEGMA GESTÃO ON      NM': 'Transporte e logística',
    'LOG-IN ON': 'Transporte e logística',
    'MILLS       ON      NM': 'Transporte e logística',
    'LOJAS RENNERON      NM': 'Varejo e consumo',
    'C&A MODAS S.A. NM': 'Varejo e consumo',
    'NATURAON      NM': 'Varejo e consumo',
    'VIVARA      ON NM': 'Varejo e consumo',
    'SMART FIT SMFT-M2 ON': 'Varejo e consumo',
    'TECEL S JOSEPN': 'Varejo e consumo',
    'CYRELA REALTON      NM': 'Imobiliário e construção',
    'CYRELA REALTPN      NM': 'Imobiliário e construção',
    'MULTIPLAN   ON      N2': 'Imobiliário e construção',
    'IGUATEMI S.AUNT     N1': 'Imobiliário e construção',
    'ALOS - ALLOS S.A.': 'Imobiliário e construção',
    'LAVVI       ON': 'Imobiliário e construção',
    'DIRR - DIRECIONAL ON': 'Imobiliário e construção',
    'CURY CONSTR E INCORPORADORA': 'Imobiliário e construção',
    'SAO CARLOSON      NM': 'Imobiliário e construção',
    'BRAZILIAN SECURITIES COMPANHIA DE S': 'Imobiliário e construção',
    'REDE D OR   ON      NM': 'Saúde',
    'NU HOLDINGS DRN': 'Tecnologia e fintech',
    'XP INC      DR1': 'Tecnologia e fintech',
    'BDR CERT DE DEPOSITO  STONECO': 'Tecnologia e fintech',
    'MERCADOIBRE INC': 'Tecnologia e fintech',
    'B3          ON      NM': 'Tecnologia e fintech',
    'COGNA ON    ON      NM': 'Educação',
    'YDUQS PART': 'Educação',
    'WEGON  EJ  N1': 'Industrial e bens de capital',
    'RANDON PARTPN      N1': 'Industrial e bens de capital',
    'RANDON PARTON      N1': 'Industrial e bens de capital',
    'MARCOPOLOPN      N2': 'Industrial e bens de capital',
    'FRAS-LEON      N1': 'Industrial e bens de capital',
    'GPS         ON      NM': 'Industrial e bens de capital',
    'SAM INDUSTRON *': 'Industrial e bens de capital',
    'ORIZON ON': 'Gestão ambiental e resíduos',
    'TRIS3 ON': 'Agronegócio',
    'TIM         ON      NM': 'Telecomunicações',
    'VIVT - TELEF BRASIL ON': 'Telecomunicações',
    'ISHARES BOVA': 'Fundo de índice',
    'IT NOW IBOV': 'Fundo de índice',
    'GOLD -TREND ETF LBMA OURO FDO': 'Fundo de índice',
    'AXIA ON *    N1': 'Diversos',
    'AXIA PN CLASSE C': 'Diversos',
    'AXIA PNB*    N1': 'Diversos',
    'ORVR BNS ORD': 'Diversos',
}

# Classificação de fundos confirmada manualmente (avaliação pela ótica da
# gestora). Checada antes da heurística por palavra-chave.
TIPO_FUNDO_CONFIRMADO = {
    "SAFRA CMP FICRFDICP": "Fundo de crédito privado",
    "CHAP DIAMANTINA FICM": "Fundo multimercado",
    "CHAPADA GUIMARA FCFM": "Fundo de crédito privado",
    "SPARTA TOP RF FICFI": "Fundo de crédito privado",
    "AZ Q LUCE FICRFCP LP": "Fundo de crédito privado",
    "BNP P C FICFIRF CPLP": "Fundo de crédito privado",
    "TRI FLAGSHIP 60 FICA": "Fundo de crédito privado",
}

# ---------------------------------------------------------------------------
# Dupla materialidade: dois eixos independentes, nunca um score único.
# Financeira (outside-in): quanto o fator ASG afeta o valor do investimento.
# Impacto (inside-out): quanto o investimento afeta ambiente e sociedade.
# As matrizes não são espelhadas: o mesmo setor pesa diferente em cada eixo.
# ---------------------------------------------------------------------------
MATERIALIDADE_FINANCEIRA = {
    'Bancos'                           : {'A': 0.3, 'S': 0.5, 'G': 0.9},
    'Seguros'                          : {'A': 0.3, 'S': 0.5, 'G': 0.8},
    'Energia elétrica'                 : {'A': 0.8, 'S': 0.5, 'G': 0.6},
    'Petróleo e combustíveis'          : {'A': 1.0, 'S': 0.6, 'G': 0.7},
    'Mineração'                        : {'A': 1.0, 'S': 0.8, 'G': 0.6},
    'Papel e celulose'                 : {'A': 0.9, 'S': 0.6, 'G': 0.5},
    'Saneamento'                       : {'A': 0.8, 'S': 0.7, 'G': 0.6},
    'Concessões e infraestrutura'      : {'A': 0.6, 'S': 0.6, 'G': 0.7},
    'Transporte e logística'           : {'A': 0.7, 'S': 0.5, 'G': 0.5},
    'Varejo e consumo'                 : {'A': 0.4, 'S': 0.7, 'G': 0.5},
    'Imobiliário e construção'         : {'A': 0.6, 'S': 0.6, 'G': 0.5},
    'Saúde'                            : {'A': 0.3, 'S': 0.9, 'G': 0.6},
    'Educação'                         : {'A': 0.2, 'S': 0.9, 'G': 0.6},
    'Tecnologia e fintech'             : {'A': 0.2, 'S': 0.6, 'G': 0.7},
    'Industrial e bens de capital'     : {'A': 0.6, 'S': 0.6, 'G': 0.5},
    'Gestão ambiental e resíduos'      : {'A': 0.9, 'S': 0.6, 'G': 0.5},
    'Agronegócio'                      : {'A': 0.9, 'S': 0.7, 'G': 0.5},
    'Telecomunicações'                 : {'A': 0.3, 'S': 0.5, 'G': 0.5},
    'Fundo de índice'                  : {'A': 0.4, 'S': 0.4, 'G': 0.4},
    'Diversos'                         : {'A': 0.4, 'S': 0.4, 'G': 0.4},
    'Soberano - título público federal': {'A': 0.5, 'S': 0.6, 'G': 0.7},
}

MATERIALIDADE_IMPACTO = {
    'Bancos'                           : {'A': 0.5, 'S': 0.6, 'G': 0.7},
    'Seguros'                          : {'A': 0.3, 'S': 0.5, 'G': 0.6},
    'Energia elétrica'                 : {'A': 0.7, 'S': 0.5, 'G': 0.6},
    'Petróleo e combustíveis'          : {'A': 1.0, 'S': 0.7, 'G': 0.6},
    'Mineração'                        : {'A': 1.0, 'S': 0.8, 'G': 0.6},
    'Papel e celulose'                 : {'A': 0.8, 'S': 0.5, 'G': 0.5},
    'Saneamento'                       : {'A': 0.9, 'S': 0.8, 'G': 0.5},
    'Concessões e infraestrutura'      : {'A': 0.6, 'S': 0.7, 'G': 0.6},
    'Transporte e logística'           : {'A': 0.6, 'S': 0.5, 'G': 0.4},
    'Varejo e consumo'                 : {'A': 0.3, 'S': 0.6, 'G': 0.4},
    'Imobiliário e construção'         : {'A': 0.5, 'S': 0.6, 'G': 0.4},
    'Saúde'                            : {'A': 0.3, 'S': 0.9, 'G': 0.5},
    'Educação'                         : {'A': 0.2, 'S': 0.9, 'G': 0.5},
    'Tecnologia e fintech'             : {'A': 0.2, 'S': 0.4, 'G': 0.5},
    'Industrial e bens de capital'     : {'A': 0.5, 'S': 0.5, 'G': 0.4},
    'Gestão ambiental e resíduos'      : {'A': 0.9, 'S': 0.7, 'G': 0.5},
    'Agronegócio'                      : {'A': 0.9, 'S': 0.7, 'G': 0.5},
    'Telecomunicações'                 : {'A': 0.2, 'S': 0.4, 'G': 0.4},
    'Fundo de índice'                  : {'A': 0.4, 'S': 0.4, 'G': 0.4},
    'Diversos'                         : {'A': 0.4, 'S': 0.4, 'G': 0.4},
    'Soberano - título público federal': {'A': 0.8, 'S': 0.9, 'G': 0.8},
}

MATERIALIDADE_FUNDO_FINANCEIRA = {
    "Fundo de crédito privado": {'A': 0.4, 'S': 0.5, 'G': 0.8},
    "Fundo de ações":           {'A': 0.5, 'S': 0.6, 'G': 0.5},
    "Fundo de renda fixa DI":   {'A': 0.2, 'S': 0.2, 'G': 0.4},
    "Fundo imobiliário":        {'A': 0.6, 'S': 0.6, 'G': 0.5},
    "Fundo multimercado":       {'A': 0.4, 'S': 0.4, 'G': 0.5},
    "Fundo - a classificar":    {'A': 0.4, 'S': 0.4, 'G': 0.4},
}

MATERIALIDADE_FUNDO_IMPACTO = {
    "Fundo de crédito privado": {'A': 0.5, 'S': 0.5, 'G': 0.6},
    "Fundo de ações":           {'A': 0.5, 'S': 0.6, 'G': 0.5},
    "Fundo de renda fixa DI":   {'A': 0.2, 'S': 0.2, 'G': 0.3},
    "Fundo imobiliário":        {'A': 0.5, 'S': 0.6, 'G': 0.4},
    "Fundo multimercado":       {'A': 0.4, 'S': 0.4, 'G': 0.4},
    "Fundo - a classificar":    {'A': 0.4, 'S': 0.4, 'G': 0.4},
}

NOTA_NEUTRA = 5.0

# ---------------------------------------------------------------------------
# Simulador de eventos ASG: choque de preço (fração) por setor/tipo de fundo.
# Ilustrativo, no espírito da análise de cenários do TCFD.
# ---------------------------------------------------------------------------
CENARIOS_ASG = {
    "transicao": {
        "nome": "Transição energética abrupta (política de carbono)",
        "descricao": "Precificação de carbono e regulação mais rígida encarecem ativos intensivos em emissões.",
        "choques": {
            "Petróleo e combustíveis": -0.18, "Mineração": -0.12, "Energia elétrica": -0.03,
            "Papel e celulose": -0.04, "Transporte e logística": -0.05,
            "Industrial e bens de capital": -0.03, "Tecnologia e fintech": 0.02,
            "Fundo de crédito privado": -0.03, "Fundo de ações": -0.04,
        },
    },
    "climatico": {
        "nome": "Evento climático físico agudo (enchentes ou seca extrema)",
        "descricao": "Danos diretos a operações e cadeias de suprimento em setores expostos a clima.",
        "choques": {
            "Agronegócio": -0.15, "Saneamento": -0.08, "Seguros": -0.10,
            "Concessões e infraestrutura": -0.07, "Imobiliário e construção": -0.06,
            "Varejo e consumo": -0.03, "Fundo imobiliário": -0.05, "Fundo multimercado": -0.02,
        },
    },
    "governanca": {
        "nome": "Escândalo de governança setorial (fraude ou corrupção)",
        "descricao": "Reprecificação de risco de crédito e reputacional após falha grave de governança.",
        "choques": {
            "Bancos": -0.12, "Seguros": -0.08, "Concessões e infraestrutura": -0.10,
            "Industrial e bens de capital": -0.06, "Fundo de crédito privado": -0.06,
            SOBERANO: -0.03,
        },
    },
    "social": {
        "nome": "Controvérsia social (violação trabalhista ou de direitos humanos)",
        "descricao": "Boicote, litígio ou aperto de crédito após controvérsia social relevante em cadeia de fornecimento.",
        "choques": {
            "Varejo e consumo": -0.08, "Agronegócio": -0.06, "Industrial e bens de capital": -0.05,
            "Mineração": -0.05, "Fundo de crédito privado": -0.03,
        },
    },
    "transicao_positiva": {
        "nome": "Aceleração da transição verde (cenário de oportunidade)",
        "descricao": "Investimento acelerado em energia limpa e tecnologia; ativos fósseis perdem valor por obsolescência.",
        "choques": {
            "Energia elétrica": 0.06, "Tecnologia e fintech": 0.04, "Gestão ambiental e resíduos": 0.10,
            "Agronegócio": 0.02, "Petróleo e combustíveis": -0.08, "Mineração": -0.04,
        },
    },
}

# ---------------------------------------------------------------------------
# Avaliação qualitativa de referência (0-10), com fonte pública declarada.
# Cobre os emissores de maior exposição e relevância reputacional; os demais
# ficam no valor neutro (5), que significa ausência de avaliação.
# ---------------------------------------------------------------------------
AVALIACAO_REFERENCIA = {
    'VALE R DOCEON      N1': {
        'A': 2, 'S': 3, 'G': 5,
        'nota': 'Rompimento da barragem de Brumadinho (2019): reparação em andamento (81-83% concluída em 2026), mas pesquisadores e atingidos apontam falta de transparência ambiental e cortes no benefício social (PTR), gerando novas ações judiciais.',
    },
    'BDR CERT DE DEPOSITO  STONECO': {
        'A': 5, 'S': 5, 'G': 4,
        'nota': "Ações coletivas por fraude em valores mobiliários nos EUA em 2021, ligadas a divulgação de risco de crédito. Sem sinais de problema recorrente desde então; avaliação de crédito recente da Moody's Local trata a governança de forma neutra.",
    },
    'NATURAON      NM': {
        'A': 9, 'S': 9, 'G': 8,
        'nota': 'Líder do Ranking Merco Responsabilidade ESG Brasil por 12 anos consecutivos (2025), primeiro lugar nos três pilares E, S e G.',
    },
    'SUZANO PAPELON  I06 N1': {
        'A': 8, 'S': 6, 'G': 6,
        'nota': 'Top 5 no pilar Ambiental do ranking Merco 2025; reconhecida globalmente na Sustainability Leaders Survey 2025 (GlobeScan) como referência em sustentabilidade no setor de papel e celulose.',
    },
    'ITAU UNIBANCO PN N1': {
        'A': 6, 'S': 6, 'G': 8,
        'nota': 'Primeiro lugar no pilar de Governança Corporativa do ranking Merco 2025.',
    },
    'ITAUSAPN      N1': {
        'A': 6, 'S': 6, 'G': 8,
        'nota': 'Holding do grupo Itaú - mesma avaliação de governança do Itaú Unibanco.',
    },
    'BANCO BRADESCO S.A.': {
        'A': 5, 'S': 7, 'G': 6,
        'nota': 'Top 5 no pilar Social do ranking Merco 2025.',
    },
    'BRADESCOPN  EB  N1': {
        'A': 5, 'S': 7, 'G': 6,
        'nota': 'Mesma avaliação do Bradesco.',
    },
    'LOJAS RENNERON      NM': {
        'A': 6, 'S': 6, 'G': 6,
        'nota': 'Top 6 no pilar Ambiental do ranking Merco 2025, entre as poucas varejistas na lista.',
    },
    'MERCADOIBRE INC': {
        'A': 7, 'S': 7, 'G': 6,
        'nota': 'Terceiro lugar geral no ranking Merco Responsabilidade ESG 2025, bem avaliada nos três pilares.',
    },
    'PETROBRASPN': {
        'A': 3, 'S': 5, 'G': 5,
        'nota': 'Citada como líder setorial (petróleo, gás e biocombustíveis) no Anuário Integridade ESG 2025, refletindo reformas de governança pós-2016, mas materialidade ambiental do setor permanece alta.',
    },
    'PETROBRASON': {
        'A': 3, 'S': 5, 'G': 5,
        'nota': 'Mesma avaliação da Petrobras PN.',
    },
    'CYRELA REALTON      NM': {
        'A': 5, 'S': 5, 'G': 6,
        'nota': 'Citada como líder setorial (empreendimentos imobiliários) no Anuário Integridade ESG 2025.',
    },
    'CYRELA REALTPN      NM': {
        'A': 5, 'S': 5, 'G': 6,
        'nota': 'Mesma avaliação da Cyrela ON.',
    },
    'B3          ON      NM': {
        'A': 5, 'S': 6, 'G': 8,
        'nota': 'Autorreguladora do mercado de capitais brasileiro e criadora dos segmentos de listagem (Novo Mercado); padrão de governança corporativa de referência.',
    },
    'REDE D OR   ON      NM': {
        'A': 5, 'S': 6, 'G': 5,
        'nota': 'Rede hospitalar privada de grande porte; materialidade social de acesso à saúde relevante, sem controvérsia significativa identificada.',
    },
    'BANCO BTG PACTUAL': {
        'A': 5, 'S': 5, 'G': 6,
        'nota': 'Comitê de risco reputacional e programa de compliance (Programa de Integridade) formalizados e divulgados publicamente; sem controvérsia recente relevante identificada.',
    },
    'BTGP BANCO  UNT     N2': {
        'A': 5, 'S': 5, 'G': 6,
        'nota': 'Mesma avaliação do BTG Pactual.',
    },
    'XP INC      DR1': {
        'A': 5, 'S': 5, 'G': 6,
        'nota': 'Fintech de capital aberto com reporte regular à SEC; sem controvérsia relevante identificada.',
    },
    'NU HOLDINGS DRN': {
        'A': 5, 'S': 6, 'G': 6,
        'nota': 'Fintech com forte narrativa de inclusão financeira; alta transparência exigida por listagem em bolsa americana.',
    },
    'WEGON  EJ  N1': {
        'A': 6, 'S': 6, 'G': 7,
        'nota': 'Referência de governança entre as industriais brasileiras, com reconhecimento consistente em rankings de gestão e transparência ao longo dos anos.',
    },
    'LOCALIZA RENT A CAR SA': {
        'A': 5, 'S': 5, 'G': 6,
        'nota': 'Emissor de debênture; avaliação de governança alinhada ao padrão Novo Mercado da Localiza.',
    },
    'RENT - LOCALIZA RENT A CAR SA': {
        'A': 5, 'S': 5, 'G': 6,
        'nota': 'Mesma avaliação da Localiza.',
    },
    'LOCALIZAON      NM': {
        'A': 5, 'S': 5, 'G': 6,
        'nota': 'Listada no Novo Mercado, padrão de governança elevado; sem controvérsia relevante identificada.',
    },
    'COGNA ON    ON      NM': {
        'A': 5, 'S': 5, 'G': 4,
        'nota': 'Setor de educação privada teve episódios de questionamento contábil e de compliance em anos anteriores; governança em recuperação reputacional.',
    },
    'VIBRA ON NM': {
        'A': 4, 'S': 5, 'G': 5,
        'nota': 'Maior distribuidora de combustíveis do país; materialidade ambiental do negócio principal é alta.',
    },
    'ENEVA S.A. ON': {
        'A': 5, 'S': 5, 'G': 5,
        'nota': 'Geração térmica em transição para gás natural; sem avaliação aprofundada específica.',
    },
    'EQUATORIALON      N2': {
        'A': 5, 'S': 5, 'G': 5,
        'nota': 'Distribuidora de energia com histórico de disputas regulatórias sobre qualidade de serviço; sem avaliação aprofundada específica.',
    },
}
