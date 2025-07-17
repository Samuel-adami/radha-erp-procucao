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
POST /rd/tokens
{
  "access_token": "...",
  "refresh_token": "...",
  "expires_in": 3600
}
```

Os tokens serão salvos para uso nas demais chamadas à API da RD Station.
