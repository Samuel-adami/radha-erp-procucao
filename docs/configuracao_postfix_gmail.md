# Configuração do Postfix para Envio de E-mails pelo Gmail (Ubuntu)

## 1. Instale o Postfix e dependências

Se ainda não instalou, rode:
```bash
sudo apt update
sudo apt install postfix mailutils libsasl2-modules
```

> Durante a instalação, escolha a opção **"Internet Site"** e siga as telas (pode deixar o nome padrão ou colocar o domínio do seu servidor).

---

## 2. Configure o Postfix para usar o Gmail como relay

Edite o arquivo principal de configuração:
```bash
sudo nano /etc/postfix/main.cf
```

Adicione (ou ajuste) **ao final do arquivo**:
```conf
relayhost = [smtp.gmail.com]:587
smtp_use_tls = yes
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous
smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt
```

Salve e feche (`Ctrl+O`, `Enter`, `Ctrl+X`).

---

## 3. Gere uma senha de app no Gmail

1. Entre em [https://myaccount.google.com/security](https://myaccount.google.com/security)
2. Ative a verificação em 2 etapas se ainda não estiver ativa.
3. Em **Senhas de app**, crie uma senha para "Correio" ou "Postfix".
4. Guarde essa senha gerada (será usada no próximo passo).

---

## 4. Crie o arquivo de senha SMTP

Crie/edite o arquivo:
```bash
sudo nano /etc/postfix/sasl_passwd
```

Adicione esta linha (substitua com seu e-mail e a senha de app):
```conf
[smtp.gmail.com]:587    seuemail@gmail.com:sua_senha_de_app
```

Salve e feche.

---

## 5. Proteja o arquivo e gere o hash

```bash
sudo chmod 600 /etc/postfix/sasl_passwd
sudo postmap /etc/postfix/sasl_passwd
```

---

## 6. Reinicie o Postfix

```bash
sudo systemctl restart postfix
```

---

## 7. Teste o envio de e-mail

Envie um teste para seu e-mail:
```bash
echo "Teste de email do Postfix" | mail -s "Teste Postfix" seuemail@gmail.com
```

---

## 8. (Opcional) Verifique os logs do Postfix

Se não receber o e-mail ou aparecer erro:
```bash
sudo tail -n 40 /var/log/mail.log
```

---

## 9. Dicas e Notas

- O Gmail pode colocar o e-mail na caixa de spam na primeira vez.
- Use sempre uma senha de app do Gmail e não a senha da conta principal.
- Se alterar `/etc/postfix/sasl_passwd`, repita o comando `postmap` e reinicie o Postfix.

---

## Resumo dos Comandos

```bash
sudo apt update
sudo apt install postfix mailutils libsasl2-modules
sudo nano /etc/postfix/main.cf
sudo nano /etc/postfix/sasl_passwd
sudo chmod 600 /etc/postfix/sasl_passwd
sudo postmap /etc/postfix/sasl_passwd
sudo systemctl restart postfix
echo "Teste" | mail -s "Teste Postfix" seuemail@gmail.com
sudo tail -n 40 /var/log/mail.log
```

---

> **Qualquer dúvida, consulte os logs ou me chame aqui!**

