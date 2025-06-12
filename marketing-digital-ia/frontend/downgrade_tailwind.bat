@echo off
echo === Removendo Tailwind CSS atual ===
npm uninstall tailwindcss

echo === Instalando Tailwind CSS 2.2.19, PostCSS 8 e Autoprefixer 10 ===
npm install -D tailwindcss@2.2.19 postcss@8 autoprefixer@10

echo === Criando postcss.config.js com a configuração correta ===
echo module.exports = { > postcss.config.js
echo   plugins: [ >> postcss.config.js
echo     require('tailwindcss'), >> postcss.config.js
echo     require('autoprefixer'), >> postcss.config.js
echo   ], >> postcss.config.js
echo } >> postcss.config.js

echo === Downgrade concluído com sucesso! ===
echo Agora, ajuste o index.css (se ainda não fez) para conter:
echo @tailwind base; && echo @tailwind components; && echo @tailwind utilities;

pause