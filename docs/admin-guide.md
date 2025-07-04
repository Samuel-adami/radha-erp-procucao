# Guia de Manutenção (TI)

Este guia descreve as tarefas básicas de administração do Radha ERP.

## Dependências
Instale Python 3, Node.js e npm. Em sistemas Debian:
```bash
sudo apt install python3 python3-venv nodejs npm
```
Cada módulo possui um `requirements.txt` (backend) ou `package.json` (frontend).

## Inicialização dos Serviços
Os comandos de `rodar_ambientes.txt` mostram como iniciar manualmente cada serviço em terminais diferentes. Para executar todos os componentes de uma vez, utilize o script:
```bash
./start_services.sh
```
Em produção, configure o serviço systemd `radha-erp.service` apontando para o diretório do repositório.

### Variáveis de Ambiente
- `RADHA_ADMIN_USER` e `RADHA_ADMIN_PASS` definem o usuário inicial criado no primeiro acesso.
- `DATABASE_URL` define a conexão com o PostgreSQL utilizado em produção.
- `SECRET_KEY` deve ser igual em todos os serviços para validação de tokens.

## Atualização do Código
Use `update_github.sh` para adicionar commits e enviar alterações para o GitHub.

## Verificação e Logs
Verifique se as portas 8040 (gateway), 8050 (marketing), 8060 (produção) e 8070 (comercial) estão livres. Os logs de cada backend podem ser analisados individualmente caso ocorram erros de inicialização.

### Templates do Comercial
Os modelos de documentos ficam armazenados no banco configurado em `DATABASE_URL`. Para que usuários consigam baixar orçamentos, cadastre templates do tipo **Orçamento** acessando o menu *Cadastros > Templates* no frontend.
### Condições de Pagamento
As condições de pagamento também são gravadas no PostgreSQL. Utilize *Cadastros > Condições de Pagamento* para definir parcelamentos e juros padrão.

