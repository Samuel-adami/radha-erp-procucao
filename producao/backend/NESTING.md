# Manual do Módulo Nesting

Este documento descreve detalhadamente o funcionamento do recurso de nesting do Radha ERP, abrangendo arquivos envolvidos, fonte de dados e processo de geração dos programas de corte.

## Visão geral
O módulo "producao/nesting" é composto por duas partes:

- **Frontend React**: tela de execução do nesting (`Nesting.jsx`) e tela de configuração da máquina (`ConfigMaquina.jsx`) localizadas em `frontend-erp/src/modules/Producao/components/`.
- **Backend FastAPI**: endpoints em `producao/backend/src/api.py` que realizam o processamento. A lógica principal está em `producao/backend/src/nesting.py`.

A comunicação acontece via requisições HTTP (fetch) do frontend para a API.

## Como os arquivos se comunicam
1. **Configuração da máquina** (`ConfigMaquina.jsx`)
   - Carrega configurações do backend em `/config-maquina` e as salva no `localStorage` para uso posterior.
   - Parâmetros salvos incluem extensão dos rótulos, posições de homing, layout de etiquetas e outras opções.

2. **Execução do nesting** (`Nesting.jsx`)
   - Primeiro são consultados os layers existentes via `/coletar-layers`.
   - Em seguida é enviado um `POST` para `/executar-nesting` contendo:
     - Pasta do lote (arquivos `.dxt`/`dxf`).
     - Dimensões da chapa.
     - Ferramentas e definições de layers.
     - Configuração da máquina salva no `localStorage`.
   - A resposta traz a disposição preliminar das chapas e eventuais layers faltantes.
   - A tela `VisualizacaoNesting.tsx` carrega essa prévia novamente usando o endpoint `/nesting-preview`.
   - Após a confirmação do operador é feito `POST` em `/executar-nesting-final`, que gera os arquivos definitivos.

3. **Principais endpoints** (`api.py`)
   - `/executar-nesting` – chama `gerar_nesting_preview` e retorna a prévia com a lista de layers encontrados.
   - `/nesting-preview` – repete a geração da prévia para visualização.
   - `/executar-nesting-final` – executa `gerar_nesting`, grava o resultado em `Lote_X/nesting/` e registra na tabela `nestings`.

4. **Função `gerar_nesting`** (`nesting.py`)
   - Lê o arquivo `.dxt` do lote para obter as peças.
   - Consulta a tabela `chapas` para saber tamanho e possibilidade de rotação de cada material.
   - Executa o empacotamento com `rectpack`, criando listas de peças para cada chapa.
   - Para cada chapa resultante, chama funções auxiliares que geram os arquivos de saída (gcodes, cyc, xml, imagens e etiquetas).
   - Os resultados são gravados em `Lote_X/nesting/` e o caminho é retornado ao frontend.

## Geração dos arquivos `.nc`
Na função `_gerar_gcodes`:
1. Monta o código de cada peça considerando as ferramentas, layers e templates definidos na configuração da máquina.
2. Insere cabeçalho e rodapé (templates) e escreve o programa em um arquivo com extensão `.nc` utilizando o prefixo definido.
3. É criado um arquivo para cada chapa posicionada no nesting.

### Pós-Processador
Os dados cadastrados em `producao/nesting/config-maquina` são aplicados na função `_gerar_gcodes` durante a montagem dos programas `.nc`. Quando `introducao` está preenchido, seu conteúdo substitui o cabeçalho padrão e tem as chaves entre colchetes trocadas pelos valores do lote (material, medidas, etc.). Os campos `cabecalho` e `trocaFerramenta` geram respectivamente o bloco da primeira ferramenta e os blocos de troca subsequentes. Caso exista texto em `furos`, ele é inserido logo após o cabeçalho. Ao final das furações, se `comandoFinalFuros` estiver informado, esse comando é acrescentado. O template definido em `rodape` encerra o arquivo.
O valor de `nome` é injetado na variável `[POST_PROCESSOR_NAME]` e aparece no início do arquivo. Já `extensaoArquivo` e `tamanhoNomeArquivo` não possuem uso no backend atual.

### Configurações Extras de Movimentação
Trechos de G-code armazenados nessa seção definem os movimentos básicos usados em cada peça. `movRapida`, `primeiraMovCorte` e `movCorte` são lidos por `_gcode_peca` e aplicados ao gerar os passos de corte. Os campos `primeiraMovCorteHorario`, `movCorteHorario`, `primeiraMovCorteAntiHorario` e `movCorteAntiHorario` estão presentes apenas na interface e ainda não são utilizados.


## Geração dos arquivos `.cyc`
A função `_gerar_cyc`:
1. Cria um XML contendo as posições das etiquetas de cada peça na chapa.
2. Salva o arquivo com o mesmo prefixo do `nc`, mas utilizando a extensão `.cyc`.

## Demais saídas
- `chapas.xml` com a lista de chapas e suas peças.
- Imagens de pré-visualização de cada chapa.
- Etiquetas em imagem (se configurado).

## Fonte de dados
- **Banco `chapas`**: define tamanhos padrões e se o material possui veio (interfere na rotação das peças).
- **Tabelas `config_maquina`, `config_ferramentas` e `config_layers`**: armazenam as preferências utilizadas durante o nesting.
- **Arquivos do lote** (`.dxt` + desenhos DXF): fornecem as dimensões de cada peça a ser cortada.

## Fluxo resumido
1. O operador ajusta os parâmetros em *Configuração da Máquina* e salva as informações.
2. Na tela de *Nesting*, o lote é escolhido e o sistema consulta `/coletar-layers`.
3. Os dados são enviados para `/executar-nesting`, que gera a prévia do arranjo de chapas.
4. A tela de visualização exibe essa prévia obtida de `/nesting-preview`.
5. Confirmando a otimização, o frontend chama `/executar-nesting-final` para gerar os arquivos e registrar a execução.

Com este fluxo, é possível entender de onde cada informação é buscada e como os arquivos `.nc` e `.cyc` são produzidos a partir dos dados da tela de configuração da máquina.
