import psycopg2
import json

DATABASE_URL = "postgresql://radha_admin:minhasenha@localhost:5432/producao"

estrutura = {}

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Listar todos os schemas (exceto os do sistema)
    cur.execute("""
        SELECT schema_name 
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('information_schema', 'pg_catalog')
    """)
    schemas = [row[0] for row in cur.fetchall()]

    for schema in schemas:
        estrutura[schema] = {}

        # Listar tabelas do schema
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_type='BASE TABLE'
        """, (schema,))
        tabelas = [row[0] for row in cur.fetchall()]

        for tabela in tabelas:
            estrutura[schema][tabela] = {"colunas": [], "amostras": []}

            # Listar colunas
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = %s AND table_name = %s
            """, (schema, tabela))
            colunas = cur.fetchall()
            estrutura[schema][tabela]["colunas"] = [
                {"nome": col[0], "tipo": col[1]} for col in colunas
            ]

            # Trazer até 5 registros da tabela
            try:
                cur.execute(f'SELECT * FROM {schema}.{tabela} LIMIT 5')
                registros = cur.fetchall()
                estrutura[schema][tabela]["amostras"] = registros
            except Exception as e:
                estrutura[schema][tabela]["amostras"] = [f"Erro ao consultar dados: {e}"]

    # Salvar em JSON
    with open("estrutura_banco_producao.json", "w", encoding="utf-8") as f:
        json.dump(estrutura, f, indent=2, ensure_ascii=False, default=str)

    print("Estrutura completa salva em estrutura_banco_producao.json")

except Exception as e:
    print(f"Erro ao conectar ou consultar o banco: {e}")

finally:
    if cur:
        cur.close()
    if conn:
        conn.close()
