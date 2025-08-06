-- Migração: aumentar precisão do campo valor em gabster_orcamento_itens
ALTER TABLE comercial.gabster_orcamento_itens
    ALTER COLUMN valor TYPE numeric(12,2);
