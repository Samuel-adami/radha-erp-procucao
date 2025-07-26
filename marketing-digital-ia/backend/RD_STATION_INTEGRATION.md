# Integração RD Station Marketing (OAuth2)

Este backend utiliza o fluxo oficial OAuth2 para acessar a API pública da RD Station Marketing.

## Variáveis de Ambiente
Configure as seguintes variáveis no `.env`:

```
RDSTATION_CLIENT_ID=<client id>
RDSTATION_CLIENT_SECRET=<client secret>
RDSTATION_REDIRECT_URI=<url de callback>
RDSTATION_CACHE_TTL=<cache ttl em segundos, padrão 900>
```

## Autenticação
1. Acesse `/rd/login` estando autenticado no sistema. Esse endpoint monta a URL de autorização com `scope=contacts` e você será redirecionado para a página da RD Station.
2. Após conceder acesso, a RD Station redireciona para `RDSTATION_REDIRECT_URI`, que deve apontar para `/rd/callback`. Essa rota executa uma requisição POST a `https://api.rd.services/auth/token` incluindo o código de autorização e armazena os tokens na tabela `rdstation_tokens`. Por exemplo:
```json
{
  "client_id": "<CLIENT_ID>",
  "client_secret": "<CLIENT_SECRET>",
  "code": "<AUTHORIZATION_CODE>",
  "grant_type": "authorization_code",
  "redirect_uri": "<RDSTATION_REDIRECT_URI>"
}
```
3. O backend renova automaticamente o `access_token` usando o `refresh_token` quando necessário. A requisição POST de refresh envia o payload:
```json
{
  "client_id": "<CLIENT_ID>",
  "client_secret": "<CLIENT_SECRET>",
  "grant_type": "refresh_token",
  "refresh_token": "<REFRESH_TOKEN>"
}
```
Uma tarefa de fundo (`auto_refresh_tokens`) verifica periodicamente se os
tokens estão prestes a expirar e solicita a renovação.

### Inserção manual de tokens
Se já possuir tokens válidos, envie-os para `/rd/tokens`:

```
curl -X POST https://SEU_DOMINIO/rd/tokens \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "SEU_ACCESS_TOKEN",
    "refresh_token": "SEU_REFRESH_TOKEN",
    "expires_in": 86400
}'


Os tokens serão salvos para uso nas demais chamadas à API da RD Station.

### Reautorização obrigatória
Se as chamadas à API retornarem `401 Unauthorized` mesmo após o backend tentar
atualizar o token, provavelmente o `refresh_token` expirou. Nesse caso remova os
tokens com:

```
DELETE FROM rdstation_tokens WHERE account_id='default';
```

Depois acesse novamente `/rd/login` para realizar uma nova autorização.
Certifique-se de que a página de autorização exiba o escopo **contacts**. Caso o token gerado não contenha esse escopo ou a propriedade `aud` continue apontando para a API antiga, repita o processo de remoção e autorização.

## Diagnóstico da integração
Para coletar informações detalhadas sobre as variáveis de ambiente e tokens salvos, execute:

```bash
python scripts/debug_rdstation_integration.py
```

Um arquivo `rdstation_debug_info.json` será gerado contendo o resultado das tentativas de atualização dos tokens e de uma chamada de teste aos leads. Isso facilita a identificação de problemas quando a integração não está retornando dados.

## Monitoramento e Alertas

Para garantir a disponibilidade do serviço de leads e detectar falhas de forma proativa, é recomendado:

- Expor métricas Prometheus sobre chamadas à API RD Station (sucessos, 4xx, 5xx).  
- Coletar essas métricas (via `prometheus_client` ou exporter dedicado) e configurar alertas em caso de aumento de erro HTTP ou latência.  
- Criar dashboards para monitorar o _throughput_ de leads e falhas de autenticação.
