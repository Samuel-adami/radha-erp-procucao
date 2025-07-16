ALTER TABLE chapas_estoque ADD COLUMN IF NOT EXISTS origem TEXT;
ALTER TABLE chapas_estoque ADD COLUMN IF NOT EXISTS reservada INTEGER DEFAULT 0;
CREATE TABLE IF NOT EXISTS chapas_estoque_mov (
    id SERIAL PRIMARY KEY,
    chapa_id INTEGER,
    descricao TEXT,
    comprimento DOUBLE PRECISION,
    largura DOUBLE PRECISION,
    m2 DOUBLE PRECISION,
    custo_m2 DOUBLE PRECISION,
    custo_total DOUBLE PRECISION,
    origem TEXT,
    destino TEXT,
    criado_em TEXT
);
