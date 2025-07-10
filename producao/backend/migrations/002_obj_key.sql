-- Garantir que as operações ocorram no schema correto
SET search_path TO producao;

ALTER TABLE producao.lotes RENAME COLUMN pasta TO obj_key;
ALTER TABLE producao.nestings RENAME COLUMN pasta_resultado TO obj_key;
ALTER TABLE producao.lotes_ocorrencias RENAME COLUMN pasta TO obj_key;

-- Converte caminhos antigos em chaves de objeto
UPDATE producao.lotes SET obj_key = 'lotes/' || regexp_replace(obj_key, '.*/', '') || '.zip'
WHERE obj_key NOT LIKE 'lotes/%';

UPDATE producao.nestings SET obj_key = 'nestings/' || regexp_replace(obj_key, '.*/([^/]+)$', '\1') || '.zip'
WHERE obj_key NOT LIKE 'nestings/%';

UPDATE producao.lotes_ocorrencias SET obj_key = 'ocorrencias/' || regexp_replace(obj_key, '.*/', '') || '.zip'
WHERE obj_key NOT LIKE 'ocorrencias/%';
