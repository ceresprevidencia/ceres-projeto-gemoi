from dotenv import load_dotenv
import os
import time
import json
from groq import Groq
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- CONFIGURAÇÕES DE DB E AMBIENTE (PADRÃO CI/CD) ---
load_dotenv()
DB_URL = os.getenv("DB_URL", "sqlite:///./bot-monitoramento/data/noticias_pipeline.db")
TABLE_NAME = "noticias" 
MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Controle de Rate Limit (Importante para evitar o erro anterior)
MAX_WORKERS_API = int(os.getenv("MAX_WORKERS_API", 1)) 
SLEEP_PER_CALL = float(os.getenv("SLEEP_API", 20)) # Aumentado para 1.0s

# --------- Utilidades de log e sanitização ---------
def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def sanitize_text(x):
    if pd.isna(x):
        return ""
    return str(x).strip()

# --------- Funções de DB ---------

def get_db_engine():
    """Cria e retorna a engine do SQLAlchemy."""
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return engine
    except SQLAlchemyError as e:
        log(f"🚨 ERRO CRÍTICO: Falha na conexão com o Banco de Dados. Erro: {e}")
        raise RuntimeError("Falha na conexão com o DB.")

def load_pending_news(engine: create_engine) -> pd.DataFrame:
    """Carrega apenas as notícias que a Etapa 1 inseriu e ainda não foram classificadas."""
    log(f"Buscando notícias com status_e2='PENDENTE' na tabela '{TABLE_NAME}'...")
    
    # Seleciona apenas as colunas necessárias e filtra pelo status
    query = f"""
    SELECT url, titulo, subtitulo
    FROM {TABLE_NAME}
    WHERE status_e2 = 'PENDENTE'
    """
    try:
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        log(f"🚨 ERRO ao carregar notícias pendentes do DB: {e}")
        raise

def update_news_classification(engine: create_engine, data: list):
    """Atualiza as linhas do DB com os resultados da classificação."""
    log(f"Iniciando atualização de {len(data)} linhas no DB...")
    
    # Prepara o comando SQL de UPDATE
    update_template = f"""
    UPDATE {TABLE_NAME}
    SET interesse = :interesse,
        classificacao = :classificacao,
        resposta_modelo = :resposta_modelo,
        status_e2 = 'CONCLUIDO'
    WHERE url = :url
    """
    try:
        with engine.begin() as connection:
            # Executa o comando UPDATE para cada resultado
            connection.execute(text(update_template), data)
        log(f"✅ {len(data)} linhas atualizadas com sucesso.")
    except Exception as e:
        log(f"🚨 ERRO ao atualizar o DB: {e}")
        raise
        
# --------- Funções de IA ---------

def build_prompt(titulo, subtitulo):
    """Constrói o prompt de classificação para o LLM."""
    return f"""
Sua função é classificar se o conteúdo do título e subtítulo é do meu interesse e rotular com L0-L5.

Temas de interesse (exemplos de rótulo):
- Ações de órgãos reguladores como CVM ou Banco Central contra gestoras de investimentos. (L5)
- Fusões, aquisições de fundos/empresas/gestoras ou mudanças significativas na estrutura societária de gestoras de investimentos. (L3)
- Problemas de compliance, fraudes, investigações ou processos judiciais contra gestoras de investimentos. (L4)
- Instabilidades tecnológicas ou problemas operacionais de gestoras de investimentos. (L1)
- Mudança no c-level e demissões em massa em gestoras de investimentos. (L2)

Critérios de irrelevância (classifique como L0 e interesse=N se QUALQUER um for verdadeiro):
- A notícia é apenas um boletim/lista de várias empresas sem um evento principal claro.
- A notícia é sobre marketing, análise de mercado genérica ou lançamento de produtos.

Exemplos:
- Título: CVM abre processo administrativo contra XYZ Gestora por supostas irregularidades
  Subtítulo: Regulador investiga possíveis infrações e falhas de compliance na Info Asset.
  Interesse: "S", Classificacao: "L4"
... (Outros exemplos omitidos para brevidade)

Responda **somente** com um JSON válido, sem texto extra, no formato:
{{"interesse":"S|N","classificacao":"L0|L1|L2|L3|L4|L5"}}

Agora, classifique:
Título: {titulo}
Subtítulo: {subtitulo}
""".strip()

def classify_worker(row: pd.Series, client: Groq):
    """Worker que chama a API, trata erros e retorna o resultado formatado."""
    url = row['url']
    titulo = sanitize_text(row.get("titulo", ""))
    subtitulo = sanitize_text(row.get("subtitulo", ""))

    system_msg = {"role": "system", "content": "Você é um classificador de notícias. Responda APENAS com JSON válido."}
    user_msg = {"role": "user", "content": build_prompt(titulo, subtitulo)}
    
    # Dados de retorno padrão em caso de falha
    result_data = {
        'url': url,
        'interesse': 'N',
        'classificacao': 'L0',
        'resposta_modelo': 'ERRO_CLASSIFICACAO'
    }

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[system_msg, user_msg],
            temperature=0.0,
        )
        text = resp.choices[0].message.content.strip()
        result_data['resposta_modelo'] = text

        try:
            data = json.loads(text)
            interesse = str(data.get("interesse", "")).upper()
            classificacao = str(data.get("classificacao", "")).upper()

            # Validação: se o LLM falhar no formato, forçamos 'N' e 'L0'
            if interesse not in {"S", "N"} or not classificacao.startswith("L"):
                log(f"Aviso: LLM fora do padrão. URL: {url[:50]}...")
            else:
                result_data['interesse'] = interesse
                result_data['classificacao'] = classificacao
        
        except json.JSONDecodeError:
            log(f"ERRO: Resposta não é JSON válido. URL: {url[:50]}...")

    except Exception as e:
        log(f"ERRO ao chamar a API para URL {url[:50]}...: {type(e).__name__} (RateLimit?)")
        
    return result_data


# --------- MAIN - LÓGICA DO PIPELINE ---------

def main():
    log("🚀 E2 - INICIANDO CLASSIFICAÇÃO DE INTERESSE COM IA 🚀")
    load_dotenv()
    
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY não encontrado no .env")

    # 1. Conexão e Carregamento de Dados
    DB_ENGINE = get_db_engine()
    df_pendente = load_pending_news(DB_ENGINE)
    
    total = len(df_pendente)
    log(f"✅ {total} notícias pendentes de classificação carregadas do DB.")

    if total == 0:
        log("✅ Nenhuma notícia nova para classificar. Encerrando E2.")
        return

    # 2. Inicialização da API e Paralelismo
    log(f"Iniciando cliente Groq/LLM com modelo '{MODEL}' e {MAX_WORKERS_API} workers...")
    client = Groq(api_key=GROQ_API_KEY)
    
    resultados_classificacao = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_API) as executor:
        # Mapeia cada linha do DataFrame para a função classify_worker
        futures = {executor.submit(classify_worker, row, client): index 
                   for index, row in df_pendente.iterrows()}
        
        for i, future in enumerate(as_completed(futures), 1):
            try:
                result = future.result()
                resultados_classificacao.append(result)
                log(f"[Progresso: {i}/{total}] Classificada -> interesse={result['interesse']} | classificacao={result['classificacao']}")
            except Exception as e:
                log(f"AVISO: Thread de classificação falhou: {e}")
            
            # Pausa de controle para evitar Rate Limit (Chave para o sucesso em CI/CD com APIs externas)
            time.sleep(SLEEP_PER_CALL) 

    log("✅ Classificação de todas as notícias concluída.")

    # 3. Atualização do Banco de Dados
    if resultados_classificacao:
        update_news_classification(DB_ENGINE, resultados_classificacao)
    
    log("🏁 PROCESSO E2 CONCLUÍDO. O DB está pronto para a Etapa 3. 🏁")

if __name__ == "__main__":
    main()