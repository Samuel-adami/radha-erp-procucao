# Plano de Integração: Nesting de Polígonos Reais com Heurísticas Avançadas

Este documento apresenta uma proposta de abordagem para incorporar algoritmos de nesting de polígonos irregulares,
com técnicas avançadas de empacotamento, a fim de maximizar o aproveitamento de chapa e evitar colisões/sobreposições.

## 1. Objetivo

- Suportar **nesting de polígonos reais** (não apenas bounding-boxes).
- Aplicar **heurísticas Bottom‑Left, Best‑Fit** e **guilhotina recursiva** para posicionar peças maiores primeiro.
- Utilizar **meta‑heurísticas** (busca local, algoritmos genéticos) para otimização local fina.

## 2. Bibliotecas recomendadas

| Biblioteca  | Recursos principais                                                                                   |
|------------|------------------------------------------------------------------------------------------------------|
| **nestpy** | Nesting 2D de polígonos irregulares com heurísticas Bottom‑Left, Best‑Fit, guilhotina e otimização. |
| **py3dbp** | Packing 2D/3D com heurísticas de guilhotina e reforços.                                              |
| **svgnest**| Ferramenta de nesting baseada em SVG com heurísticas adaptativas (via CLI ou binding).                |

## 3. Proposta de caminho imediato

1. **Adicionar dependência**
   - Incluir a biblioteca escolhida (`nestpy`, `py3dbp` ou `svgnest`) no arquivo de requisitos.
2. **Escrever wrapper** em `producao/backend/src/nesting.py`:
   - Converter polígonos Shapely em objetos de input da biblioteca.
   - Executar o nesting com a heurística desejada (Bottom‑Left, guilhotina recursiva, etc.).
   - Mapear coordenadas e ângulos de volta para nossa estrutura (`x`, `y`, `rotationAngle`, `polygon`).
3. **Testar** com exemplos reais de peças (polígonos simples e complexos).
4. **Ajustar parâmetros** de espaçamento, margens de refilo, número de iterações, heurística padrão.

## 4. Próximos passos

1. Confirmar se devemos prosseguir com esta integração de biblioteca.
2. Definir qual biblioteca priorizar para o protótipo inicial (`nestpy`, `py3dbp` ou `svgnest`).
3. Elaborar patch de integração (instalação, wrapper e exemplos de uso).

--
_Documento gerado automaticamente como proposta de integração de nesting avançado._
