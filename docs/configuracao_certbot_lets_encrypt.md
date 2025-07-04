# Configuração e Gerenciamento do Certbot (Let's Encrypt) no Ubuntu

## 1. Instalação do Certbot e plugin Nginx

```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
```

---

## 2. Gerar Certificado SSL para seu domínio

Substitua `erp.radhadigital.com.br` pelo seu domínio real:

```bash
sudo certbot --nginx -d erp.radhadigital.com.br
```

- O certbot vai detectar o bloco do nginx automaticamente e editar para você.
- Siga os prompts e escolha redirecionar todo tráfego HTTP para HTTPS se quiser.

---

## 3. Testar o site em HTTPS

Abra:\
`https://erp.radhadigital.com.br`

---

## 4. Renovação Automática

O Certbot já cria um cronjob para renovar automaticamente. Para testar manualmente:

```bash
sudo certbot renew --dry-run
```

Para rodar em staging (apenas teste, sem consumir cota de certificados):

```bash
sudo certbot --nginx --staging -d erp.radhadigital.com.br
```

---

## 5. Verificar Certificados Ativos

```bash
sudo certbot certificates
```

---

## 6. Verificar logs do Certbot

```bash
sudo tail -n 40 /var/log/letsencrypt/letsencrypt.log
```

---

## 7. Remover certificados de domínios antigos (opcional)

```bash
sudo certbot delete --cert-name dominio_antigo.com.br
```

---

## 8. Dicas Úteis

- Certificados Let's Encrypt duram 90 dias.
- O Certbot renova automaticamente, mas monitore usando os comandos acima.
- O Nginx faz reload automático após a renovação.
- Se houver problemas de DNS, ajuste os apontamentos antes de emitir/renovar certificados.

---

## 9. Como automatizar alertas de expiração do certificado

1. Você pode usar um serviço externo como [Certify The Web](https://certifytheweb.com/) ou [SSL Labs Monitor](https://www.ssllabs.com/ssltest/), ou:
2. Configurar um script simples com `cron` para checar a validade e enviar e-mail:

```bash
sudo nano /usr/local/bin/check_ssl_expiry.sh
```

Conteúdo do script:

```bash
#!/bin/bash
exp_date=$(openssl x509 -enddate -noout -in /etc/letsencrypt/live/erp.radhadigital.com.br/fullchain.pem | cut -d= -f2)
exp_seconds=$(date --date="$exp_date" +%s)
now_seconds=$(date +%s)
diff_days=$(( (exp_seconds-now_seconds)/(60*60*24) ))
if [ $diff_days -lt 15 ]; then
    echo "Certificado SSL expira em $diff_days dias!" | mail -s "[Alerta] Certificado SSL expira em breve" seuemail@seudominio.com
fi
```

Permita execução:

```bash
sudo chmod +x /usr/local/bin/check_ssl_expiry.sh
```

Adicione no cron para rodar diariamente:

```bash
echo "0 8 * * * root /usr/local/bin/check_ssl_expiry.sh" | sudo tee -a /etc/crontab
```

---

## Resumo dos Comandos

```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d erp.radhadigital.com.br
sudo certbot renew --dry-run
sudo certbot certificates
sudo tail -n 40 /var/log/letsencrypt/letsencrypt.log
```

---

> **Dúvidas ou problemas? Consulte os logs, o site oficial do Certbot, ou me chame!**

