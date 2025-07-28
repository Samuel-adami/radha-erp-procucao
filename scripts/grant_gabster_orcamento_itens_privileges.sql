-- Script: concede privilégios de acesso à tabela gabster_orcamento_cliente
-- Ajuste <APP_DB_ROLE> para o usuário/role que a aplicação utiliza no banco

GRANT SELECT, INSERT, UPDATE, DELETE
  ON TABLE comercial.gabster_orcamento_itens
  TO radha_admin;
