from db_ddq import get_connection


def criar_banco() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS gestora (
                id_gestora INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                telefone TEXT,
                email TEXT,
                cnpj TEXT,
                atualizado TEXT,
                status TEXT NOT NULL DEFAULT 'ATIVO'
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_gestora_cnpj
    ON gestora(cnpj);

            CREATE TABLE IF NOT EXISTS preenchimento (
                id_preenchimento INTEGER PRIMARY KEY AUTOINCREMENT,
                id_gestora INTEGER,
                data_envio TEXT NOT NULL,
                versao TEXT,
                FOREIGN KEY (id_gestora)
                    REFERENCES gestora(id_gestora)
                    ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS resposta (
                id_resposta TEXT PRIMARY KEY NOT NULL,
                pergunta TEXT NOT NULL,
                resposta TEXT,
                score_resposta REAL,
                id_preenchimento INTEGER NOT NULL,
                FOREIGN KEY (id_preenchimento)
                    REFERENCES preenchimento(id_preenchimento)
                    ON DELETE CASCADE
            );
            """
        )



if __name__ == "__main__":
    criar_banco()
    print("Banco de dados e tabelas criados com sucesso!")