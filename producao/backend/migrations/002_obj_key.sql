ALTER TABLE lotes RENAME COLUMN pasta TO obj_key;
ALTER TABLE nestings RENAME COLUMN pasta_resultado TO obj_key;
ALTER TABLE lotes_ocorrencias RENAME COLUMN pasta TO obj_key;

-- Converte caminhos antigos em chaves de objeto
UPDATE lotes SET obj_key = 'lotes/' || regexp_replace(obj_key, '.*/', '') || '.zip' WHERE obj_key NOT LIKE 'lotes/%';
UPDATE nestings SET obj_key = 'nestings/' || regexp_replace(obj_key, '.*/([^/]+)$', '\1') || '.zip' WHERE obj_key NOT LIKE 'nestings/%';
UPDATE lotes_ocorrencias SET obj_key = 'ocorrencias/' || regexp_replace(obj_key, '.*/', '') || '.zip' WHERE obj_key NOT LIKE 'ocorrencias/%';
