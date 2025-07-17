# Integração RD Station Marketing (OAuth2)

Este backend utiliza o fluxo oficial OAuth2 para acessar a API pública da RD Station Marketing.

## Variáveis de Ambiente
Configure as seguintes variáveis no `.env`:

```
RDSTATION_CLIENT_ID=<client id>
RDSTATION_CLIENT_SECRET=<client secret>
RDSTATION_REDIRECT_URI=<url de callback>
```

## Autenticação
1. Acesse `/rd/login` estando autenticado no sistema. Você será redirecionado para a página de autorização da RD Station.
2. Após conceder acesso, a RD Station redireciona para `RDSTATION_REDIRECT_URI`, que deve apontar para `/rd/callback`. Essa rota troca o `code` pelos tokens e armazena tudo na tabela `rdstation_tokens`.
3. O backend renova automaticamente o `access_token` usando o `refresh_token` quando necessário.

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
