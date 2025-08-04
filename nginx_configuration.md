## Nginx Configuration
The production server uses Nginx as a reverse proxy in front of the
FastAPI backends and the React frontend. Below are the configuration
files currently enabled under `/etc/nginx/sites-available`.

### /etc/nginx/sites-available/erp.radhadigital.com.br
```
server {
    listen 80;
    server_name erp.radhadigital.com.br;

    # Redireciona tudo para HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name erp.radhadigital.com.br;

    # SSL
    ssl_certificate /etc/letsencrypt/live/erp.radhadigital.com.br/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/erp.radhadigital.com.br/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    client_max_body_size 200m;

    # FRONTEND (React build, na porta 3015 via serve ou similar)
    location / {
        proxy_pass http://127.0.0.1:3015;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # History-fallback para BrowserRouter (rotas limpas sem #)
        try_files $uri $uri/ /index.html;
    }

    # Não cachear o HTML principal
    location ~* \.html$ {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # Cache longo para assets versionados (hash no nome)
    location ~* \.(js|css|png|jpg|jpeg|svg)$ {
        add_header Cache-Control "public, max-age=31536000, immutable";
    }


    # GATEWAY (backend FastAPI rodando na porta 8040)
    # Rotas /auth, /clientes, /fornecedores, /empresa,
    # /condicoes-pagamento e /templates vão para o backend
    location /auth/ {
        proxy_pass http://127.0.0.1:8040;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location /clientes {
        proxy_pass http://127.0.0.1:8040;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location /fornecedores {
        proxy_pass http://127.0.0.1:8040;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location /empresa {
        proxy_pass http://127.0.0.1:8040;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location /condicoes-pagamento {
        proxy_pass http://127.0.0.1:8040;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location /templates {
        proxy_pass http://127.0.0.1:8040;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location /usuarios {
        proxy_pass http://127.0.0.1:8040;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location /comercial/ {
        proxy_pass http://127.0.0.1:8040;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # Operações de importação/consulta podem demorar e exceder o timeout padrão,
        # elevamos para evitar 504 Gateway Time-out sem alterar a lógica da aplicação.
        proxy_connect_timeout 300s;
        proxy_send_timeout    300s;
        proxy_read_timeout    300s;
    }
    location ~ ^/marketing-ia/rd/ {
        proxy_pass http://127.0.0.1:8040;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location /marketing-ia/ {
        proxy_pass http://127.0.0.1:8040;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location /finance/ {
        proxy_pass http://127.0.0.1:8040;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location /producao/ {
        proxy_pass http://127.0.0.1:8040;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # Operações de nesting podem demorar e exceder o
        # timeout padrão de 60s do Nginx, resultando em erro 504.
        # Esses limites estendidos evitam o problema sem
        # alterar a lógica da aplicação.
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

### /etc/nginx/sites-available/radha-gateway-https
```
server {
    listen 443 ssl;
    server_name erp.radhadigital.com.br;

    ssl_certificate /etc/letsencrypt/live/erp.radhadigital.com.br/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/erp.radhadigital.com.br/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8040;   # Gateway backend
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # Estende timeouts para chamadas longas (importação Gabster etc.)
        proxy_connect_timeout 300s;
        proxy_send_timeout    300s;
        proxy_read_timeout    300s;
    }
}
```