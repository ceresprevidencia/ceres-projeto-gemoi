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

# Controle de Rate Limit (ajuste aqui para evitar RateLimitError)
MAX_WORKERS_API = int(os.getenv("MAX_WORKERS_API", 1))
SLEEP_PER_CALL = float(os.getenv("SLEEP_API", 15.0))

# --------- Utilidades de Log e Sanitização ---------
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

def load_pending_news_e4(engine: create_engine) -> pd.DataFrame:
    """Carrega notícias prontas (Interesse=S, Texto preenchido) e não processadas pela E4."""
    log(f"Buscando notícias prontas (E3=CONCLUIDO, E4=PENDENTE) na tabela '{TABLE_NAME}'...")
    
    # Filtro: Interesse='S' AND status_e3='CONCLUIDO' AND texto IS NOT NULL AND status_e4='PENDENTE'
    query = f"""
    SELECT url, gestora, titulo, subtitulo, texto
    FROM {TABLE_NAME}
    WHERE interesse = 'S' 
      AND status_e3 = 'CONCLUIDO' 
      AND texto IS NOT NULL
      AND (status_e4 IS NULL OR status_e4 = 'PENDENTE')
    """
    try:
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        log(f"🚨 ERRO ao carregar notícias pendentes da E4 do DB: {e}")
        raise

def update_news_alvo(engine: create_engine, data: list):
    """Atualiza as linhas do DB com os resultados da classificação de Alvo."""
    log(f"Iniciando atualização de {len(data)} linhas (Alvo) no DB...")
    
    # Prepara o comando SQL de UPDATE
    update_template = f"""
    UPDATE {TABLE_NAME}
    SET alvo = :alvo,
        descricao = :descricao,
        justificativa_alvo = :justificativa_alvo,
        status_e4 = 'CONCLUIDO'
    WHERE url = :url
    """
    try:
        with engine.begin() as connection:
            connection.execute(text(update_template), data)
        log(f"✅ {len(data)} linhas atualizadas com sucesso no DB (Alvo inserido).")
    except Exception as e:
        log(f"🚨 ERRO ao atualizar o DB (Alvo): {e}")
        raise

# --------- Funções de IA ---------

def build_prompt(gestora, titulo, subtitulo, texto):
    """Constrói o prompt padrão para classificação de alvo."""
    texto_truncado = texto[:1000]
    sufixo = "..." if len(texto) > 1000 else ""
    return f"""
Sua tarefa é determinar se a 'Gestora-alvo' é o sujeito principal da notícia e se é de interesse que a diretoria de uma empresa gaste tempo lendo a notícia na íntegra.
Responda com 'S' ou 'N' a categoria alvo com base nas seguintes regras:
**Responda 'S' (Sim) se:** A notícia é sobre uma ação da gestora, um resultado dela, ou se ela sofreu uma ação (ex: uma multa, uma aquisição).
**Responda 'N' (Não) se:** A gestora ou um de seus funcionários é apenas citado para comentar sobre o mercado, uma outra empresa ou uma tendência geral.
  
Se a sua resposta for S faça uma descrição de no máximo 400 caracteres sobre o motivo da classificação.
Se a sua resposta for N, NÃO ESCREVA NADA.

Responda **somente** com um JSON válido, sem texto extra, no formato:
{{"alvo":"S|N","descricao":"texto aqui ou vazio"}}

Agora, classifique:
Gestora-alvo: {gestora}
Título: {titulo}
Subtítulo: {subtitulo}
Texto: {texto_truncado}{sufixo}
""".strip()

def build_prompt_xp(gestora, titulo, subtitulo, texto):
    """Constrói o prompt específico para a XP Investimentos."""
    texto_truncado = texto[:1000]
    sufixo = "..." if len(texto) > 1000 else ""
    return f"""
O grupo XP Investimentos possui diversas empresas no portifólio, Sua tarefa é determinar se a 'Gestora-alvo' é o sujeito principal da notícia e se é uma dessas empresas
XP Gestão de Recursos, XP Asset.
Responda com 'S' ou 'N' a categoria alvo com base nas seguintes regras:
**Responda 'S' (Sim) se:** A notícia é sobre uma ação da gestora (XP Gestão de Recursos, XP Asset), um resultado dela, ou se ela sofreu uma ação (ex: uma multa, uma aquisição).
**Responda 'N' (Não) se:** A gestora ou um de seus funcionários é apenas citado para comentar sobre o mercado, uma outra empresa ou uma tendência geral ou se for outra empresa do grupo.
  
Se a sua resposta for S faça uma descrição de no máximo 400 caracteres sobre o motivo da classificação.
Se a sua resposta for N, NÃO ESCREVA NADA.

Responda **somente** com um JSON válido, sem texto extra, no formato:
{{"alvo":"S|N","descricao":"texto aqui ou vazio"}}

Agora, classifique:
Gestora-alvo: {gestora}
Título: {titulo}
Subtítulo: {subtitulo}
Texto: {texto_truncado}{sufixo}
""".strip()

def classify_alvo_worker(row: pd.Series, client: Groq):
    """Worker que chama a API em paralelo, trata erros e retorna o resultado formatado."""
    url = row['url']
    gestora = sanitize_text(row.get("gestora", ""))
    titulo = sanitize_text(row.get("titulo", ""))
    subtitulo = sanitize_text(row.get("subtitulo", ""))
    texto = sanitize_text(row.get("texto", ""))

    system_msg = {"role": "system", "content": "Você é um classificador de notícias. Responda APENAS com JSON válido."}
    
    # Escolhe o prompt correto
    if gestora == 'Xp Investimentos':
        prompt_content = build_prompt_xp(gestora, titulo, subtitulo, texto)
    else:
        prompt_content = build_prompt(gestora, titulo, subtitulo, texto)
        
    user_msg = {"role": "user", "content": prompt_content}
    
    # Dados de retorno padrão em caso de falha (para evitar colunas NULL no DB)
    result_data = {
        'url': url,
        'alvo': 'N',
        'descricao': None,
        'justificativa_alvo': 'ERRO_CLASSIFICACAO_E4'
    }

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[system_msg, user_msg],
            temperature=0.0,
        )
        text = resp.choices[0].message.content.strip()
        result_data['justificativa_alvo'] = text

        try:
            data = json.loads(text)
            alvo = str(data.get("alvo", "")).upper()
            descricao = str(data.get("descricao", "")).strip()
            
            if alvo not in {"S", "N"}:
                log(f"Aviso: LLM fora do padrão. URL: {url[:50]}...")
            else:
                result_data['alvo'] = alvo
                # Salva a descrição apenas se o Alvo for 'S'
                result_data['descricao'] = descricao if alvo == 'S' else None 
        
        except json.JSONDecodeError:
            log(f"ERRO: Resposta não é JSON válido. URL: {url[:50]}...")

    except Exception as e:
        log(f"ERRO ao chamar a API para URL {url[:50]}...: {type(e).__name__} (RateLimit?)")
        
    return result_data


# --------- MAIN - FLUXO ORQUESTRADO ---------

def main():
    log("🚀 E4 - INICIANDO CLASSIFICAÇÃO DE ALVO PRINCIPAL (LLM) 🚀")
    load_dotenv()
    
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY não encontrado no .env")

    # 1. Conexão e Carregamento de Dados
    DB_ENGINE = get_db_engine()
    df_pendente = load_pending_news_e4(DB_ENGINE)
    
    total = len(df_pendente)
    log(f"✅ {total} notícias prontas (interesse=S, texto=OK) pendentes de classificação de alvo.")

    if total == 0:
        log("✅ Nenhuma notícia pronta para classificação de alvo. Encerrando E4.")
        return

    # 2. Inicialização da API e Paralelismo
    log(f"Iniciando cliente Groq/LLM com modelo '{MODEL}' e {MAX_WORKERS_API} workers...")
    client = Groq(api_key=GROQ_API_KEY)
    
    resultados_classificacao = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_API) as executor:
        futures = {executor.submit(classify_alvo_worker, row, client): index 
                   for index, row in df_pendente.iterrows()}
        
        for i, future in enumerate(as_completed(futures), 1):
            try:
                result = future.result()
                resultados_classificacao.append(result)
                log(f"[Progresso: {i}/{total}] Classificada -> Alvo={result['alvo']}")
            except Exception as e:
                log(f"AVISO: Thread de classificação falhou: {e}")
            
            # Pausa de controle para evitar Rate Limit
            time.sleep(SLEEP_PER_CALL) 

    log("✅ Classificação de Alvo concluída.")

    # 3. Atualização do Banco de Dados
    if resultados_classificacao:
        update_news_alvo(DB_ENGINE, resultados_classificacao)
    
    log("🏁 PROCESSO E4 CONCLUÍDO. O DB está pronto para a Etapa 5. 🏁")
    
    alvos_s = sum(1 for r in resultados_classificacao if r['alvo'] == 'S')
    log(f"Estatísticas E4: {alvos_s} notícias marcadas como Alvo='S'.")

if __name__ == "__main__":
    main()