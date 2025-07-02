# Manual da Interface React do Radha ERP

Este documento descreve onde localizar os arquivos que controlam a aparência e os componentes visuais do painel web em React (`frontend-erp`). Consulte-o sempre que precisar modificar cores, botões ou os templates de documentos.

## Estrutura geral do frontend
- **`frontend-erp/src`** – código fonte do aplicativo React.
- **`frontend-erp/src/modules`** – cada módulo do ERP possui uma pasta aqui (MarketingDigitalIA, Producao, Cadastros, Comercial e Formularios).
- **`frontend-erp/index.html`** – ponto de entrada simples que carrega `src/main.jsx`.

## Estilos e cores
- **Configuração do Tailwind**: `frontend-erp/tailwind.config.js` define as classes utilitárias usadas em todo o frontend.
- **Variáveis de cor e tema**: em `frontend-erp/src/modules/Producao/Producao.css` encontram‑se as variáveis CSS (`--background`, `--primary`, `--chart-1` etc.) aplicadas globalmente. Ajuste esses valores para alterar o esquema de cores.
- **CSS por módulo**: cada módulo possui seu arquivo, por exemplo `Cadastros.css`, `Comercial.css` e `Producao.css`. Neles há classes utilitárias como `.input` e outras regras específicas.
- **Componentes de UI**: botões reutilizáveis e utilidades estão em `frontend-erp/src/modules/Producao/components/ui/`. O principal é `button.jsx`, que define variantes de estilo (padrão, secundário, link, etc.).

## Botões e componentes
- O arquivo `button.jsx` utiliza `class-variance-authority` para combinar classes Tailwind. Altere este arquivo caso deseje mudar o padrão dos botões.
- Outros componentes de formulários ficam nas subpastas de cada módulo, por exemplo `frontend-erp/src/modules/Producao/components/`.

## Templates de documentos
- As telas para gerenciar templates ficam em `frontend-erp/src/modules/Cadastros/templates/`.
  - **`index.jsx`** – roteamento e menu dos tipos de template.
  - **`ListaTemplates.jsx`** – lista, edição e exclusão de templates existentes.
  - **`VisualTemplateBuilder.jsx`** – configurador visual usado na criação e edição de todos os templates.
  - **`TemplatePreview.jsx`** – visualização do template montado.
  - **`AutoFieldSelect.jsx`** – opções de preenchimento automático dos campos (cliente, empresa, negociação etc.).

## Como alterar a interface
1. Modifique os valores em `Producao.css` para trocar as cores globais do sistema.
2. Ajuste ou crie componentes em `components/ui` para alterar a aparência de botões e outros elementos reutilizáveis.
3. Adicione ou edite páginas dentro de `src/modules` de acordo com o módulo correspondente.
4. Para personalizar modelos de documentos (orçamento, pedido, contrato…), edite os arquivos dentro de `src/modules/Cadastros/templates`.

Com essas referências, qualquer desenvolvedor poderá localizar rapidamente os pontos de configuração visual do Radha ERP.
