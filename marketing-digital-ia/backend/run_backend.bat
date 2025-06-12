@echo off
echo === Ativando o ambiente virtual ===
call venv\Scripts\activate

echo === Iniciando o backend com Uvicorn ===
uvicorn main:app --reload --port 8015

pause