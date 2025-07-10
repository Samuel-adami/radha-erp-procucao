import psycopg2

DATABASE_URL = "postgresql://radha_admin:minhasenha@localhost:5432/producao"

comandos_sql = [
    # Comercial
    "ALTER TABLE comercial.projeto_itens ADD COLUMN IF NOT EXISTS pasta TEXT;",
    "ALTER TABLE comercial.gabster_projeto_itens ADD COLUMN IF NOT EXISTS pasta TEXT;",

    # Produção - sincronizar com obj_key
    "ALTER TABLE producao.lotes ADD COLUMN IF NOT EXISTS pasta TEXT;",
    "UPDATE producao.lotes SET pasta = obj_key WHERE pasta IS NULL;",

    "ALTER TABLE producao.nestings ADD COLUMN IF NOT EXISTS pasta TEXT;",
    "UPDATE producao.nestings SET pasta = obj_key WHERE pasta IS NULL;",

    "ALTER TABLE producao.lotes_ocorrencias ADD COLUMN IF NOT EXISTS pasta TEXT;",
    "UPDATE producao.lotes_ocorrencias SET pasta = obj_key WHERE pasta IS NULL;"
]

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    for sql in comandos_sql:
        print(f"Executando: {sql}")
        cur.execute(sql)

    conn.commit()
    print("Colunas 'pasta' criadas e sincronizadas com sucesso.")

except Exception as e:
    print(f"Erro ao executar comandos SQL: {e}")

finally:
    if cur:
        cur.close()
    if conn:
        conn.close()
