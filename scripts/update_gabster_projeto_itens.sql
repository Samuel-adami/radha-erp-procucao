-- Script: Atualiza colunas da tabela gabster_projeto_itens para corresponder ao JSON da Gabster
-- Campos permitidos: id, nome, cd_cliente, nome_arquivo_skp, identificador_arquivo_skp,
-- descricao, observacao, ambiente, projeto_ref
BEGIN;

-- Excluir colunas não previstas no JSON da Gabster
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'gabster_projeto_itens'
          AND column_name NOT IN (
            'id', 'nome', 'cd_cliente', 'nome_arquivo_skp',
            'identificador_arquivo_skp', 'descricao', 'observacao',
            'ambiente', 'projeto_ref'
          )
    LOOP
        EXECUTE format('ALTER TABLE public.gabster_projeto_itens DROP COLUMN IF EXISTS %I CASCADE', r.column_name);
    END LOOP;
END
$$;

-- Garantir existência e tipo corretos das colunas
ALTER TABLE public.gabster_projeto_itens
    ADD COLUMN IF NOT EXISTS id integer,
    ADD COLUMN IF NOT EXISTS nome varchar(200),
    ADD COLUMN IF NOT EXISTS cd_cliente integer,
    ADD COLUMN IF NOT EXISTS nome_arquivo_skp varchar(100),
    ADD COLUMN IF NOT EXISTS identificador_arquivo_skp varchar(100),
    ADD COLUMN IF NOT EXISTS descricao varchar(1000),
    ADD COLUMN IF NOT EXISTS observacao varchar(100),
    ADD COLUMN IF NOT EXISTS ambiente varchar(45),
    ADD COLUMN IF NOT EXISTS projeto_ref integer;

ALTER TABLE public.gabster_projeto_itens
    ALTER COLUMN id TYPE integer USING id::integer,
    ALTER COLUMN nome TYPE varchar(200),
    ALTER COLUMN cd_cliente TYPE integer USING cd_cliente::integer,
    ALTER COLUMN nome_arquivo_skp TYPE varchar(100),
    ALTER COLUMN identificador_arquivo_skp TYPE varchar(100),
    ALTER COLUMN descricao TYPE varchar(1000),
    ALTER COLUMN observacao TYPE varchar(100),
    ALTER COLUMN ambiente TYPE varchar(45),
    ALTER COLUMN projeto_ref TYPE integer USING projeto_ref::integer;

COMMIT;

-- Define primary key on id (se ainda não existir) para permitir UPSERT
DO $$
BEGIN
    -- Remove registros inválidos (id nulo ou vazio) antes de criar a PK
    DELETE FROM public.gabster_projeto_itens WHERE id IS NULL;
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints tc
        WHERE tc.table_schema = 'public'
          AND tc.table_name = 'gabster_projeto_itens'
          AND tc.constraint_type = 'PRIMARY KEY'
    ) THEN
        ALTER TABLE public.gabster_projeto_itens
        ALTER COLUMN id SET NOT NULL;
        ALTER TABLE public.gabster_projeto_itens
        ADD PRIMARY KEY (id);
    END IF;
END
$$;
