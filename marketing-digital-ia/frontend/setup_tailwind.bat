@echo off
echo === Limpeza de cache e reinstalação de dependencias ===

:: Limpa o cache do npm
npm cache clean --force

:: Remove node_modules e package-lock.json
rmdir /s /q node_modules
del package-lock.json

:: Instala novamente todas as dependencias
npm install

:: Instala Tailwind, PostCSS e Autoprefixer
npm install -g tailwindcss

:: Inicializa Tailwind com postcss.config.js
tailwindcss init -p

echo === Configuração concluída com sucesso! ===
echo Agora ajuste o tailwind.config.js com:
echo content: [\"./src/**/*.{js,jsx,ts,tsx}\"]
echo E no index.css, inclua:
echo @tailwind base;
echo @tailwind components;
echo @tailwind utilities;

pause