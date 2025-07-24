-- Migração: adicionar coluna tarefa_id em gabster_projeto_itens
ALTER TABLE comercial.gabster_projeto_itens
    ADD COLUMN IF NOT EXISTS tarefa_id integer;
