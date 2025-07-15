SET search_path TO producao;
CREATE TABLE IF NOT EXISTS chapas_estoque (
    id SERIAL PRIMARY KEY,
    chapa_id INTEGER REFERENCES chapas(id),
    descricao TEXT,
    comprimento DOUBLE PRECISION,
    largura DOUBLE PRECISION,
    m2 DOUBLE PRECISION,
    custo_m2 DOUBLE PRECISION,
    custo_total DOUBLE PRECISION
);
