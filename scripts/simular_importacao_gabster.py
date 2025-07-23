#!/usr/bin/env python3
"""Simula a importação de um projeto via Gabster e exibe os dados obtidos.

Este script utiliza as funções `get_projeto` e `parse_gabster_projeto` do
backend comercial para buscar um projeto na API da Gabster e mostrar o
conteúdo estruturado como o Radha ERP grava no banco.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Permitir importar os módulos do backend
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR / "comercial-backend"))

from gabster_api import get_projeto  # type: ignore
from orcamento_gabster import parse_gabster_projeto  # type: ignore


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Baixa projeto da Gabster e exibe os itens encontrados"
    )
    parser.add_argument("codigo", help="Código do projeto na Gabster")
    parser.add_argument("--usuario", help="Usuário da API (ou GABSTER_API_USER)")
    parser.add_argument("--chave", help="Chave da API (ou GABSTER_API_KEY)")
    args = parser.parse_args()

    load_dotenv()

    user = args.usuario or os.getenv("GABSTER_API_USER")
    key = args.chave or os.getenv("GABSTER_API_KEY")

    if not user or not key:
        print(
            "É necessário informar usuário e chave via argumentos ou variáveis de ambiente",
            file=sys.stderr,
        )
        sys.exit(1)

    raw = get_projeto(int(args.codigo), user=user, api_key=key)
    dados = parse_gabster_projeto(raw)

    print("\nJSON estruturado retornado:")
    print(json.dumps(dados, indent=2, ensure_ascii=False))

    projetos = dados.get("projetos", {})
    if projetos:
        print("\nResumo dos itens:")
        for amb, info in projetos.items():
            total = info.get("total", 0)
            print(f"Ambiente: {amb} (Total: {total})")
            for it in info.get("itens", []):
                desc = it.get("descricao")
                qtd = it.get("quantidade")
                unit = it.get("unitario")
                tot = it.get("total")
                print(f"  - {desc}: {qtd} x {unit} = {tot}")
    else:
        print("Nenhum item encontrado no projeto.")


if __name__ == "__main__":
    main()
